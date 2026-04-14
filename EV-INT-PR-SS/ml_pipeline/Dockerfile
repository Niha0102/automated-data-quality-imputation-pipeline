FROM python:3.11-slim

WORKDIR /app

# Java is required for PySpark
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jdk-headless \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD celery -A pipeline.celery_app inspect ping || exit 1

CMD ["celery", "-A", "pipeline.celery_app", "worker", "--loglevel=info", "--concurrency=2"]
