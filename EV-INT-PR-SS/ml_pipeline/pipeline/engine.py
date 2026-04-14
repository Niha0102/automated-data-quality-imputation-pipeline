"""Processing engine abstraction — Requirement 13.1.

Defines the ProcessingEngine Protocol and a factory that returns
SparkEngine when PySpark is available, otherwise DaskEngine.
"""
from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

import pandas as pd

logger = logging.getLogger(__name__)


@runtime_checkable
class ProcessingEngine(Protocol):
    """Common interface for Spark and Dask processing engines."""

    def read_dataset(self, s3_path: str, fmt: str) -> pd.DataFrame:
        """Read a dataset from S3/MinIO into a pandas-compatible DataFrame."""
        ...

    def write_dataset(self, df: pd.DataFrame, s3_path: str, fmt: str) -> str:
        """Write a DataFrame to S3/MinIO. Returns the written S3 path."""
        ...

    def apply(self, df: pd.DataFrame, func) -> pd.DataFrame:
        """Apply a transformation function to the DataFrame in a distributed manner."""
        ...

    def shutdown(self) -> None:
        """Release engine resources."""
        ...


# ── Factory ───────────────────────────────────────────────────────────────────

def get_engine() -> ProcessingEngine:
    """Return SparkEngine if PySpark is available, else DaskEngine."""
    try:
        from pipeline.spark_engine import SparkEngine  # type: ignore
        engine = SparkEngine()
        logger.info("Using SparkEngine for processing")
        return engine
    except Exception as exc:
        logger.warning("SparkEngine unavailable (%s); falling back to DaskEngine", exc)
        from pipeline.dask_engine import DaskEngine  # type: ignore
        engine = DaskEngine()
        logger.info("Using DaskEngine for processing")
        return engine
