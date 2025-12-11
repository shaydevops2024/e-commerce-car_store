import os
import json
import time
from decimal import Decimal
from datetime import datetime

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from dotenv import load_dotenv
import redis
import pika
import docker

from models import get_connection, cars, orders, order_items
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from prometheus_metrics import REQUESTS, REQUEST_LATENCY, ORDERS_PROCESSED

load_dotenv()

# Config
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

RABBIT_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBIT_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBIT_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBIT_PASS = os.getenv('RABBITMQ_PASS', 'guest')
RABBIT_QUEUE = os.getenv('RABBITMQ_QUEUE', 'orders')

FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 8000))

# container names (can be overridden in env if needed)
SERVICE_CONTAINER_MAP = {
    "redis": os.getenv("REDIS_CONTAINER", "carstore-redis"),
    "rabbit": os.getenv("RABBIT_CONTAINER", "carstore-rabbitmq"),
    "postgres": os.getenv("POSTGRES_CONTAINER", "carstore-postgres"),
}

# App setup
app = Flask(__name__, static_folder='../frontend', static_url_path='/static')
CORS(app, resources={r"/api/*": {"origins": "*"}})

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

docker_client = docker.from_env()


def rabbit_connection():
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT, credentials=credentials)
    return pika.BlockingConnection(params)


def record_request(start, endpoint, method, status):
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(time.time() - start)
    REQUESTS.labels(method=method, endpoint=endpoint, http_status=str(status)).inc()


def now_ts():
    return datetime.utcnow().isoformat() + "Z"


# Routes
@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/api/cars', methods=['GET'])
def get_cars():
    t0 = time.time()
    conn = get_connection()
    status = 500
    try:
        result = conn.execute(cars.select()).mappings().all()
        data = []
        for row in result:
            data.append({
                'id': row['id'],
                'make': row['make'],
                'model': row['model'],
                'year': row['year'],
                'price': float(row['price']),
                'description': row['description'],
                'image': row['image'] or ''
            })
        status = 200
        return jsonify(data), status
    finally:
        conn.close()
        record_request(t0, '/api/cars', request.method, status)


@app.route('/api/cart', methods=['GET', 'POST', 'DELETE'])
def cart():
    t0 = time.time()
    session_id = request.cookies.get('session_id')
    if not session_id:
        session_id = request.remote_addr + "-" + str(int(time.time() * 1000))
    key = f"cart:{session_id}"

    if request.method == 'GET':
        items = r.get(key)
        data = json.loads(items) if items else []
        resp = jsonify({'session_id': session_id, 'items': data})
        status = 200

    elif request.method == 'POST':
        payload = request.get_json()
        items = r.get(key)
        items = json.loads(items) if items else []

        found = False
        for it in items:
            if it['car_id'] == payload['car_id']:
                it['quantity'] = it.get('quantity', 0) + int(payload.get('quantity', 1))
                found = True

        if not found:
            items.append({
                'car_id': int(payload['car_id']),
                'quantity': int(payload.get('quantity', 1))
            })

        r.set(key, json.dumps(items), ex=60 * 60 * 24)  # 24 hours
        resp = jsonify({'session_id': session_id, 'items': items})
        status = 201

    else:  # DELETE
        r.delete(key)
        resp = jsonify({'session_id': session_id, 'items': []})
        status = 200

    response = make_response(resp, status)
    response.set_cookie('session_id', session_id, httponly=False, samesite='Lax')
    record_request(t0, '/api/cart', request.method, status)
    return response


@app.route('/api/checkout', methods=['POST'])
def checkout():
    t0 = time.time()
    data = request.get_json()
    session_id = data.get('session_id') or request.cookies.get('session_id')

    if not session_id:
        return jsonify({'error': 'no session'}), 400

    cart_key = f"cart:{session_id}"
    items = r.get(cart_key)
    if not items:
        return jsonify({'error': 'cart empty'}), 400

    items = json.loads(items)

    conn = get_connection()
    trans = conn.begin()
    try:
        total = 0
        car_map = {}
        ids = [it['car_id'] for it in items]

        if ids:
            q = conn.execute(cars.select().where(cars.c.id.in_(ids))).mappings().all()
            for row in q:
                car_map[row['id']] = float(row['price'])

        for it in items:
            total += car_map.get(it['car_id'], 0) * int(it.get('quantity', 1))

        res = conn.execute(orders.insert().values(
            total=Decimal(total),
            customer_name=data.get('customer_name'),
            customer_email=data.get('customer_email')
        ))
        order_id = res.inserted_primary_key[0]

        for it in items:
            conn.execute(order_items.insert().values(
                order_id=order_id,
                car_id=it['car_id'],
                quantity=it['quantity'],
                price=Decimal(car_map.get(it['car_id'], 0))
            ))

        trans.commit()

    except Exception as e:
        trans.rollback()
        conn.close()
        record_request(t0, '/api/checkout', request.method, 500)
        return jsonify({'error': str(e)}), 500

    conn.close()

    # RabbitMQ (non-critical)
    try:
        conn_r = rabbit_connection()
        ch = conn_r.channel()
        ch.queue_declare(queue=RABBIT_QUEUE, durable=True)
        order_msg = {
            'order_id': order_id,
            'session_id': session_id,
            'items': items,
            'total': float(total),
            'customer_name': data.get('customer_name'),
            'customer_email': data.get('customer_email')
        }
        ch.basic_publish(
            exchange='',
            routing_key=RABBIT_QUEUE,
            body=json.dumps(order_msg),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        conn_r.close()
        ORDERS_PROCESSED.inc()
    except Exception as e:
        print("RabbitMQ publish failed:", e)

    r.delete(cart_key)

    record_request(t0, '/api/checkout', request.method, 201)
    return jsonify({'order_id': order_id, 'status': 'created'}), 201


@app.route('/metrics')
def metrics():
    resp = make_response(generate_latest())
    resp.headers['Content-Type'] = CONTENT_TYPE_LATEST
    return resp


@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    t0 = time.time()
    conn = get_connection()
    status = 500
    try:
        o = conn.execute(orders.select().where(orders.c.id == order_id)).mappings().first()
        if not o:
            status = 404
            return jsonify({'error': 'not found'}), 404

        items_q = conn.execute(order_items.select().where(order_items.c.order_id == order_id)).mappings().all()
        items_list = [
            {'car_id': it['car_id'], 'quantity': it['quantity'], 'price': float(it['price'])}
            for it in items_q
        ]

        resp = jsonify({'order': dict(o), 'items': items_list})
        status = 200
        return resp, status

    finally:
        conn.close()
        record_request(t0, '/api/orders/<id>', request.method, status)


# ============================
# SERVICE DASHBOARD STATUS
# ============================

@app.route("/api/status/redis")
def status_redis():
    try:
        pong = r.ping()
        return jsonify({"redis": "OK", "ping": pong}), 200
    except Exception as e:
        return jsonify({"redis": "DOWN", "error": str(e)}), 500


@app.route("/api/status/rabbit")
def status_rabbit():
    try:
        conn_r = rabbit_connection()
        ch = conn_r.channel()
        q = ch.queue_declare(queue=RABBIT_QUEUE, durable=True, passive=True)
        count = q.method.message_count
        conn_r.close()
        return jsonify({
            "rabbitmq": "OK",
            "queue": RABBIT_QUEUE,
            "messages": count
        }), 200
    except Exception as e:
        return jsonify({"rabbitmq": "DOWN", "error": str(e)}), 500


@app.route("/api/status/orders")
def status_orders():
    conn = get_connection()
    try:
        rows = conn.execute(
            orders.select().order_by(orders.c.id.desc()).limit(10)
        ).mappings().all()

        output = [
            {
                "id": row["id"],
                "total": float(row["total"]),
                "customer_name": row.get("customer_name"),
                "customer_email": row.get("customer_email")
            }
            for row in rows
        ]

        return jsonify({"orders": output}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ============================
# SERVICE CONTROL VIA DOCKER
# ============================

@app.route("/api/service/<service>/<action>", methods=["POST"])
def control_service(service, action):
    """
    service: redis | rabbit | postgres
    action: start | stop | status
    """
    if service not in SERVICE_CONTAINER_MAP:
        return jsonify({"log": f"[{now_ts()}] Unknown service: {service}"}), 400

    if action not in ("start", "stop", "status"):
        return jsonify({"log": f"[{now_ts()}] Unknown action: {action}"}), 400

    log_lines = []

    def log(msg):
        log_lines.append(f"[{now_ts()}] {msg}")

    container_name = SERVICE_CONTAINER_MAP[service]

    # STOP / START via Docker
    if action in ("start", "stop"):
        try:
            c = docker_client.containers.get(container_name)
        except Exception as e:
            log(f"ERROR: cannot find container {container_name}: {e}")
            return jsonify({"log": "\n".join(log_lines)}), 500

        try:
            if action == "stop":
                log(f"Stopping container {container_name}...")
                c.stop()
                log("Container stopped.")
            elif action == "start":
                log(f"Starting container {container_name}...")
                c.start()
                log("Container started.")
        except Exception as e:
            log(f"ERROR while {action} {container_name}: {e}")
            return jsonify({"log": "\n".join(log_lines)}), 500

        return jsonify({"log": "\n".join(log_lines)}), 200

    # STATUS logic per service (replaces ping)
    if action == "status":
        try:
            if service == "redis":
                log("Checking Redis using redis-py ping()...")
                pong = r.ping()
                log(f"Redis OK, ping={pong}")
                return jsonify({"log": "\n".join(log_lines)}), 200

            elif service == "rabbit":
                log("Checking RabbitMQ using rabbitmqctl list_queues inside container...")
                c = docker_client.containers.get(container_name)
                exec_res = c.exec_run("rabbitmqctl list_queues", demux=False)
                output = exec_res.output.decode(errors="ignore")
                log(output)
                return jsonify({"log": "\n".join(log_lines)}), 200

            elif service == "postgres":
                log("Checking Postgres using pg_isready inside container...")
                c = docker_client.containers.get(container_name)
                exec_res = c.exec_run("pg_isready", demux=False)
                output = exec_res.output.decode(errors="ignore")
                log(output)
                return jsonify({"log": "\n".join(log_lines)}), 200

        except Exception as e:
            log(f"ERROR during status of {service}: {e}")
            return jsonify({"log": "\n".join(log_lines)}), 500

    # Should never reach here
    log("Invalid request.")
    return jsonify({"log": "\n".join(log_lines)}), 400


if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT)
