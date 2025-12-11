from prometheus_client import Counter, Histogram

REQUESTS = Counter(
    "REQUESTS_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "REQUEST_LATENCY_seconds",
    "Request latency in seconds",
    ["endpoint"]
)

ORDERS_PROCESSED = Counter(
    "ORDERS_PROCESSED_total",
    "Total orders processed"
)

# Mock data so Grafana shows something immediately
REQUESTS.labels(method="GET", endpoint="/api/cars", http_status="200").inc(12)
REQUESTS.labels(method="GET", endpoint="/api/cart", http_status="200").inc(5)
REQUESTS.labels(method="POST", endpoint="/api/cart", http_status="201").inc(7)
REQUESTS.labels(method="POST", endpoint="/api/checkout", http_status="201").inc(3)

ORDERS_PROCESSED.inc(3)

REQUEST_LATENCY.labels(endpoint="/api/cars").observe(0.08)
REQUEST_LATENCY.labels(endpoint="/api/checkout").observe(0.23)
