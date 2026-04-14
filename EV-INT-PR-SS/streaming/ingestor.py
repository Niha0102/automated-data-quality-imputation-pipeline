"""Kafka streaming ingestor — Requirements 2.6, 11.5."""
from __future__ import annotations

import csv
import io
import json
import logging
import time
from collections import defaultdict
from typing import Optional

import httpx

from config import settings

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


def health_check() -> dict:
    return {"status": "ok", "service": "streaming"}


class StreamIngestor:
    """Kafka consumer that batches records and submits pipeline jobs.

    Requirements 2.6, 11.5
    """

    def __init__(self):
        self._consumer = None
        self._http = httpx.Client(
            base_url=settings.BACKEND_API_URL,
            headers={"Authorization": f"Bearer {settings.BACKEND_API_TOKEN}"},
            timeout=30.0,
        )
        self._batches: dict[str, list[dict]] = defaultdict(list)
        self._batch_start: dict[str, float] = {}

    def _get_consumer(self):
        if self._consumer is not None:
            return self._consumer
        try:
            from confluent_kafka import Consumer
            self._consumer = Consumer({
                "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                "group.id": settings.KAFKA_GROUP_ID,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": True,
            })
            self._consumer.subscribe([settings.KAFKA_TOPIC])
            logger.info("Kafka consumer connected to %s, topic=%s", settings.KAFKA_BOOTSTRAP_SERVERS, settings.KAFKA_TOPIC)
            return self._consumer
        except ImportError:
            logger.warning("confluent-kafka not installed; running in stub mode")
            return None
        except Exception as exc:
            logger.error("Failed to connect to Kafka: %s", exc)
            return None

    def _decode_message(self, raw: bytes) -> Optional[dict]:
        """Decode JSON or CSV-encoded Kafka message."""
        text = raw.decode("utf-8", errors="replace").strip()
        # Try JSON first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Try CSV (single row)
        try:
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
            if rows:
                return rows[0]
        except Exception:
            pass
        return None

    def _submit_batch(self, dataset_id: str, records: list[dict]):
        """Submit accumulated batch as a pipeline job via internal API."""
        if not records:
            return
        try:
            # Convert records to CSV bytes
            if records:
                keys = list(records[0].keys())
                buf = io.StringIO()
                writer = csv.DictWriter(buf, fieldnames=keys)
                writer.writeheader()
                writer.writerows(records)
                csv_bytes = buf.getvalue().encode("utf-8")

            # Upload as a dataset
            resp = self._http.post(
                "/api/v1/datasets",
                files={"file": (f"stream_{dataset_id}_{int(time.time())}.csv", csv_bytes, "text/csv")},
            )
            if resp.status_code == 201:
                new_dataset_id = resp.json()["id"]
                # Submit pipeline job
                job_resp = self._http.post(
                    "/api/v1/jobs",
                    json={"dataset_id": new_dataset_id, "pipeline_config": {"source": "stream"}},
                )
                if job_resp.status_code == 201:
                    logger.info("Submitted streaming batch: dataset=%s job=%s records=%d",
                                new_dataset_id, job_resp.json()["id"], len(records))
                else:
                    logger.warning("Job submission failed: %s", job_resp.text)
            else:
                logger.warning("Dataset upload failed: %s", resp.text)
        except Exception as exc:
            logger.error("Failed to submit batch: %s", exc)

    def run(self):
        """Main consumer loop."""
        consumer = self._get_consumer()
        if consumer is None:
            logger.info("Running in stub mode (no Kafka)")
            while True:
                time.sleep(60)
            return

        logger.info("Starting Kafka consumer loop (batch_window=%ds)", settings.KAFKA_BATCH_WINDOW_SECONDS)
        try:
            while True:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    self._flush_expired_batches()
                    continue
                if msg.error():
                    logger.error("Kafka error: %s", msg.error())
                    continue

                record = self._decode_message(msg.value())
                if record is None:
                    continue

                # Use dataset_id from message header or default
                headers = dict(msg.headers() or [])
                dataset_id = headers.get("dataset_id", b"default").decode()

                self._batches[dataset_id].append(record)
                if dataset_id not in self._batch_start:
                    self._batch_start[dataset_id] = time.time()

                self._flush_expired_batches()

        except KeyboardInterrupt:
            logger.info("Shutting down consumer")
        finally:
            consumer.close()
            self._http.close()

    def _flush_expired_batches(self):
        now = time.time()
        for dataset_id in list(self._batch_start.keys()):
            if now - self._batch_start[dataset_id] >= settings.KAFKA_BATCH_WINDOW_SECONDS:
                records = self._batches.pop(dataset_id, [])
                self._batch_start.pop(dataset_id, None)
                if records:
                    self._submit_batch(dataset_id, records)


if __name__ == "__main__":
    logger.info("Streaming ingestor starting — Kafka: %s", settings.KAFKA_BOOTSTRAP_SERVERS)
    ingestor = StreamIngestor()
    ingestor.run()
