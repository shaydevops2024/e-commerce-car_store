# CarStore — DevOps Demo Application

A modern full-stack car-commerce application built to demonstrate frontend UI development, backend APIs, and service orchestration using Postgres, Redis, and RabbitMQ.
It includes a live Service Dashboard for controlling services (start/stop/status), streaming logs, and visual LED indicators showing real-time health.

## In this project I:

- practiced real microservice orchestration

- Learned full-stack architecture

## Table of Contents

1. Overview

2. Application Architecture

3. System Components

4. Features

5. Service Dashboard

6. API Overview

7.Running the Application

8. Testing Services

9. Troubleshooting

10. Monitoring

11. Future Improvements

## Overview:

### CarStore is a complete demo system demonstrating:

- Product catalog (cars)

- Cart + checkout flow

- Backend API with database

- Distributed services (RabbitMQ, Redis, Postgres)

- Real-time service control panel

- Live logs + LED health indicators

The system simulates an online store while providing an operational dashboard for inspecting and managing infrastructure components.


## Application Architecture

``` bash
┌──────────────────┐          ┌──────────────────┐
│      Frontend     │  REST    │      Backend      │
│ (HTML/CSS/JS SPA) │◄────────►│   FastAPI / API   │
└──────────────────┘          └─────────┬──────────┘
                                         │
                                         ▼
                 ┌──────────────────────────────────────────────┐
                 │               Core Services                  │
                 │                                               │
                 │  Redis (cache)     RabbitMQ (messaging)       │
                 │  Postgres (orders DB)                         │
                 └──────────────────────────────────────────────┘
```
The system is containerized using Docker and built for modular scalability.

## System Components

### Frontend

-  HTML/CSS/JavaScript

- SPA-style navigation (Catalog / Cart / Service Dashboard)

- LocalStorage persists the current page after refresh

- Dynamic loading of car catalog and cart items

### Backend

- Exposes API endpoints under /api/*

- Handles:

  * Car catalog retrieval

  * Cart operations

  * Checkout workflow

  * Service control APIs

  * Service status APIs

### Postgres

- Stores orders (created during checkout)

- Queried by the dashboard status endpoint

### Redis

- Can be used for caching (future: sessions or car caching)

- Status shown on dashboard

### RabbitMQ

- Responsible for message queueing

- Could handle async processes in real production systems

- Dashboard can fetch queue listing

### Grafana

- read Prometheus as a datasource

- import your custom dashboard (grafana_dashboard.json)

- display real-time system metrics

### Prometheus

- raw metrics inspection

- PromQL queries

- debugging scrapes



## Features

### User-Facing Features

- Car catalog with images

- Add to cart

- Persistent cart using backend session

- Checkout with customer information

- Order creation confirmation modal

### Service Dashboard Features

- View real-time logs per service

- Scrollable log windows

- Independent log areas for each service

- Start / Stop / Status buttons

- LED status indicator:

  * 🟢 Green = Service is up

  * 🔴 Red = Service is down

- Auto-update on refresh

## Service Dashboard Details

Each service panel includes:

- Header + service type chip

- LED indicator

- Buttons:

  * Start
  * Stop
  * Status

## API Overview
``` bash
Catalog
-------
Method	    Endpoint	    Description
GET	        /api/cars	    List all available cars

Cart
----
Method	    Endpoint	    Description
GET	        /api/cart	    Retrieves session cart
POST	    /api/cart	      Add item
DELETE	    /api/cart	    Clear cart
```

Checkout

``` bash | POST | /api/checkout | ```

Body

``` bash
{
  "session_id": "...",
  "customer_name": "John",
  "customer_email": "john@example.com"
}
```

Output:

``` bash
{ "order_id": 123 }
```

Service Control

``` bash
Service Name	              Routes Example
redis	                      /api/service/redis/start
rabbit	                      /api/service/rabbit/status
postgres	                  /api/service/postgres/stop
```

Status Probes

``` bash
Route	                      Description
/api/status/redis	          Returns Redis health
/api/status/rabbit	          Returns RabbitMQ health
/api/status/orders	          Tests DB availability
```

## Running the Application

Using Docker Compose:

``` bash
docker compose up --build
```

This will start:

- Backend

- Frontend

- Redis

- RabbitMQ

- Postgres

- Grafana

- Prometheus
  
Visit in your browser:

``` bash http://localhost:8081 ```

## How to Test Services

Test Redis:

``` bash curl http://localhost:8000/api/status/redis ```

Test RabbitMQ:

``` bash docker exec -it carstore-rabbitmq rabbitmqctl list_queues ```

Test Postgres:

``` bash docker exec -it carstore-postgres pg_isready ```

Test Dashboard Buttons:

Inside UI, click:

- Status → runs probe

- Start → attempts service startup

- Stop → stops container

- LED updates immediately when the service is up

Test Checkout:

- Go to Catalog

- Add any car

- Go to Cart

- Enter name + email

- Click “Complete Purchase”

- Check Postgres to verify order:

``` bash SELECT * FROM orders; ```

## Troubleshooting

Redis LED stays red:

- Container may have crashed

- Run:  ``` bash docker logs carstore-redis ```

RabbitMQ no queues:

- Check if default virtual host / exists

- Run: ``` bash rabbitmqctl list_queues ```

Postgres error:

- Ensure DB is reachable

- Run: ``` bash pg_isready ```

Dashboard always returns "Loading…":

- Backend may not be running

- Check API logs

## Monitoring:

Access Grafana using ``` bash http://localhost:3000 ``` 

Inside Grafana UI, go to "Explore" to see the metrics of Prometheus.

Access Prometheus using ``` bash http://34.240.45.69:9090/targets ```

For custom metrics use ``` bash http://backend:8000/metrics ```

### Overview of the Monitoring Architecture

``` bash
                    ┌─────────────────────┐
                    │     Frontend UI     │
                    └───────────▲─────────┘
                                │
                                │
                        User Interactions
                                │
                                ▼
                ┌────────────────────────────────┐
                │             Backend             │
                │   (FastAPI + Metrics Exporter) │
                └────────────────┬───────────────┘
                                 │ /metrics endpoint
                                 │ (Prometheus format)
                                 ▼
                       ┌────────────────┐
                       │  Prometheus    │
                       │ Scrapes metrics│
                       └───────┬────────┘
                               │
                               │ Prometheus datasource
                               ▼
                     ┌────────────────────┐
                     │      Grafana       │
                     │ Dashboards & Alerts│
                     └────────────────────┘
```



## Future Enhancements

Here are improvement ideas for expanding the system:

- Add Kubernetes deployments

- Add async order processor using RabbitMQ

- Add authentication

- Add caching for catalog in Redis



