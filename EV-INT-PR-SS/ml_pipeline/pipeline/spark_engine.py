"""Spark processing engine — Requirements 13.1, 13.4, 13.6."""
from __future__ import annotations

import io
import logging
import os
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# S3 / MinIO config from env
_S3_ENDPOINT = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")
_AWS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "adqip_minio")
_AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY", "adqip_minio_secret")


class SparkEngine:
    """PySpark-backed processing engine."""

    def __init__(self) -> None:
        from pyspark.sql import SparkSession  # type: ignore

        self._spark: SparkSession = (
            SparkSession.builder.appName("adqip-pipeline")
            .config("spark.hadoop.fs.s3a.endpoint", _S3_ENDPOINT)
            .config("spark.hadoop.fs.s3a.access.key", _AWS_KEY)
            .config("spark.hadoop.fs.s3a.secret.key", _AWS_SECRET)
            .config("spark.hadoop.fs.s3a.path.style.access", "true")
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
            .config("spark.sql.execution.arrow.pyspark.enabled", "true")
            .getOrCreate()
        )
        self._spark.sparkContext.setLogLevel("WARN")

    # ── Read ──────────────────────────────────────────────────────────────────

    def read_dataset(self, s3_path: str, fmt: str) -> pd.DataFrame:
        """Read CSV/JSON/XLSX from S3 into a pandas DataFrame via Spark."""
        s3a = s3_path.replace("s3://", "s3a://")
        fmt = fmt.lower()

        if fmt == "csv":
            sdf = self._spark.read.option("header", "true").option("inferSchema", "true").csv(s3a)
        elif fmt == "json":
            sdf = self._spark.read.option("multiline", "true").json(s3a)
        elif fmt == "xlsx":
            # Spark doesn't natively read XLSX; download via boto3 and use pandas
            return _read_xlsx_via_pandas(s3_path)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

        return sdf.toPandas()

    # ── Write ─────────────────────────────────────────────────────────────────

    def write_dataset(self, df: pd.DataFrame, s3_path: str, fmt: str) -> str:
        """Write a pandas DataFrame to S3 via Spark. Returns the S3 path."""
        s3a = s3_path.replace("s3://", "s3a://")
        fmt = fmt.lower()
        sdf = self._spark.createDataFrame(df)

        if fmt == "csv":
            sdf.coalesce(1).write.mode("overwrite").option("header", "true").csv(s3a)
        elif fmt == "json":
            sdf.coalesce(1).write.mode("overwrite").json(s3a)
        elif fmt == "xlsx":
            _write_xlsx_via_pandas(df, s3_path)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

        return s3_path

    # ── Apply ─────────────────────────────────────────────────────────────────

    def apply(self, df: pd.DataFrame, func) -> pd.DataFrame:
        """Apply a pandas UDF-style function via Spark Arrow."""
        sdf = self._spark.createDataFrame(df)
        result_sdf = func(sdf)
        if hasattr(result_sdf, "toPandas"):
            return result_sdf.toPandas()
        return result_sdf  # already pandas

    # ── Shutdown ──────────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        self._spark.stop()


# ── XLSX helpers (boto3 + openpyxl) ──────────────────────────────────────────

def _read_xlsx_via_pandas(s3_path: str) -> pd.DataFrame:
    import boto3
    bucket, key = _parse_s3_path(s3_path)
    s3 = boto3.client(
        "s3",
        endpoint_url=_S3_ENDPOINT,
        aws_access_key_id=_AWS_KEY,
        aws_secret_access_key=_AWS_SECRET,
    )
    obj = s3.get_object(Bucket=bucket, Key=key)
    return pd.read_excel(io.BytesIO(obj["Body"].read()), engine="openpyxl")


def _write_xlsx_via_pandas(df: pd.DataFrame, s3_path: str) -> None:
    import boto3
    bucket, key = _parse_s3_path(s3_path)
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    s3 = boto3.client(
        "s3",
        endpoint_url=_S3_ENDPOINT,
        aws_access_key_id=_AWS_KEY,
        aws_secret_access_key=_AWS_SECRET,
    )
    s3.put_object(Bucket=bucket, Key=key, Body=buf.read())


def _parse_s3_path(s3_path: str) -> tuple[str, str]:
    """Parse s3://bucket/key into (bucket, key)."""
    path = s3_path.replace("s3://", "").replace("s3a://", "")
    bucket, _, key = path.partition("/")
    return bucket, key
