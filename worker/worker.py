import os
import json
import time
import pika
import psycopg2
from psycopg2.extras import RealDictCursor

RABBIT_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBIT_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBIT_USER = os.getenv("RABBITMQ_USER", "guest")
RABBIT_PASS = os.getenv("RABBITMQ_PASS", "guest")
RABBIT_QUEUE = os.getenv("RABBITMQ_QUEUE", "orders")

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_DB = os.getenv("POSTGRES_DB", "carstore")
PG_USER = os.getenv("POSTGRES_USER", "caruser")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "carpass")


def get_db():
    return psycopg2.connect(
        host=PG_HOST,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASS,
        cursor_factory=RealDictCursor
    )


def process_order(order_id):
    """Update DB order status safely."""
    print(f"[worker] Processing ORDER #{order_id}")

    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "UPDATE orders SET status = %s WHERE id = %s",
            ("processed", order_id)
        )
        conn.commit()

        print(f"[worker] SUCCESS → Order {order_id} marked as processed.")

    except Exception as e:
        print(f"[worker] DB ERROR: {e}")

    finally:
        if 'conn' in locals():
            conn.close()


def callback(ch, method, properties, body):
    """Main consumer — now SAFE and VALIDATION-FIRST."""
    print(f"[worker] Received RAW message: {body}")

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print("[worker] ERROR: Non-JSON message received. Skipping.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    order_id_raw = data.get("order_id")

    # Validate that the message contains a valid order_id
    if order_id_raw is None:
        print(f"[worker] SKIP: Message has no order_id → {data}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        order_id = int(order_id_raw)
    except (ValueError, TypeError):
        print(f"[worker] SKIP: Invalid order_id value → {order_id_raw}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    # Only now call process_order()
    process_order(order_id)

    # ACK the message
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_worker():
    print("[worker] Worker is starting...")

    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(
        host=RABBIT_HOST,
        port=RABBIT_PORT,
        credentials=credentials
    )

    while True:
        try:
            print("[worker] Connecting to RabbitMQ...")
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue=RABBIT_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=RABBIT_QUEUE, on_message_callback=callback)

            print("[worker] Waiting for messages...")
            channel.start_consuming()

        except Exception as e:
            print(f"[worker] ERROR: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)


if __name__ == "__main__":
    start_worker()
