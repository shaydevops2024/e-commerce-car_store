FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /worker

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY worker.py ./worker.py

# Force Python stdout flush so docker logs WORK
ENV PYTHONUNBUFFERED=1

# Run worker unbuffered
CMD ["python", "-u", "worker.py"]
