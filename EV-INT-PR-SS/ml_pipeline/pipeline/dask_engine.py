"""Dask fallback processing engine — Requirement 13.1."""
from __future__ import annotations

import io
import logging
import os

import pandas as pd

logger = logging.getLogger(__name__)

_S3_ENDPOINT = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")
_AWS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "adqip_minio")
_AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY", "adqip_minio_secret")

# Storage options passed to dask/s3fs
_STORAGE_OPTIONS = {
    "key": _AWS_KEY,
    "secret": _AWS_SECRET,
    "client_kwargs": {"endpoint_url": _S3_ENDPOINT},
}


class DaskEngine:
    """Dask-backed processing engine (fallback when Spark is unavailable)."""

    def __init__(self) -> None:
        import dask.dataframe as dd  # type: ignore  # noqa: F401
        logger.info("DaskEngine initialized")

    # ── Read ──────────────────────────────────────────────────────────────────

    def read_dataset(self, s3_path: str, fmt: str) -> pd.DataFrame:
        """Read CSV/JSON/XLSX from S3 into a pandas DataFrame via Dask."""
        import dask.dataframe as dd  # type: ignore

        fmt = fmt.lower()
        if fmt == "csv":
            ddf = dd.read_csv(s3_path, storage_options=_STORAGE_OPTIONS)
            return ddf.compute()
        elif fmt == "json":
            ddf = dd.read_json(s3_path, storage_options=_STORAGE_OPTIONS, lines=True)
            return ddf.compute()
        elif fmt == "xlsx":
            return _read_xlsx_via_boto3(s3_path)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    # ── Write ─────────────────────────────────────────────────────────────────

    def write_dataset(self, df: pd.DataFrame, s3_path: str, fmt: str) -> str:
        """Write a pandas DataFrame to S3 via Dask. Returns the S3 path."""
        import dask.dataframe as dd  # type: ignore

        fmt = fmt.lower()
        ddf = dd.from_pandas(df, npartitions=1)

        if fmt == "csv":
            ddf.to_csv(s3_path, single_file=True, index=False, storage_options=_STORAGE_OPTIONS)
        elif fmt == "json":
            ddf.to_json(s3_path, orient="records", lines=True, storage_options=_STORAGE_OPTIONS)
        elif fmt == "xlsx":
            _write_xlsx_via_boto3(df, s3_path)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

        return s3_path

    # ── Apply ─────────────────────────────────────────────────────────────────

    def apply(self, df: pd.DataFrame, func) -> pd.DataFrame:
        """Apply a function to the DataFrame using Dask for parallelism."""
        import dask.dataframe as dd  # type: ignore

        ddf = dd.from_pandas(df, npartitions=max(1, len(df) // 10_000))
        result = func(ddf)
        if hasattr(result, "compute"):
            return result.compute()
        return result

    # ── Shutdown ──────────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        pass  # Dask client cleanup if distributed scheduler is used


# ── XLSX helpers ──────────────────────────────────────────────────────────────

def _read_xlsx_via_boto3(s3_path: str) -> pd.DataFrame:
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


def _write_xlsx_via_boto3(df: pd.DataFrame, s3_path: str) -> None:
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
    path = s3_path.replace("s3://", "").replace("s3a://", "")
    bucket, _, key = path.partition("/")
    return bucket, key
