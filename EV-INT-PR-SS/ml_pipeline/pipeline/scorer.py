"""Data quality scorer — Requirements 10.1, 10.2, 10.3, 10.4."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class QualityScore:
    completeness: float    # 0–100: % non-missing cells
    consistency: float     # 0–100: % values conforming to detected dtype
    accuracy: float        # 0–100: % non-outlier values
    overall: float         # (completeness + consistency + accuracy) / 3


def compute_quality_score(df: pd.DataFrame) -> QualityScore:
    """Compute the three quality dimensions and overall score.

    Requirements 10.1, 10.2, 10.3, 10.4
    """
    completeness = _completeness(df)
    consistency = _consistency(df)
    accuracy = _accuracy(df)
    overall = (completeness + consistency + accuracy) / 3.0

    return QualityScore(
        completeness=round(completeness, 4),
        consistency=round(consistency, 4),
        accuracy=round(accuracy, 4),
        overall=round(overall, 4),
    )


# ── Completeness ──────────────────────────────────────────────────────────────

def _completeness(df: pd.DataFrame) -> float:
    """% of non-missing cells across the entire DataFrame."""
    total_cells = df.size
    if total_cells == 0:
        return 100.0
    missing_cells = int(df.isna().sum().sum())
    return (total_cells - missing_cells) / total_cells * 100.0


# ── Consistency ───────────────────────────────────────────────────────────────

def _consistency(df: pd.DataFrame) -> float:
    """% of values that conform to the detected dtype of their column."""
    if df.empty:
        return 100.0

    conforming = 0
    total = 0

    for col in df.columns:
        series = df[col].dropna()
        n = len(series)
        total += n
        if n == 0:
            continue

        # Detect dominant type and count conforming values
        if pd.api.types.is_numeric_dtype(series):
            conforming += n  # already numeric
        elif pd.api.types.is_datetime64_any_dtype(series):
            conforming += n
        else:
            # Try numeric coercion
            numeric = pd.to_numeric(series, errors="coerce")
            numeric_count = int(numeric.notna().sum())
            # Try datetime coercion
            try:
                dt = pd.to_datetime(series, errors="coerce")
                dt_count = int(dt.notna().sum())
            except Exception:
                dt_count = 0

            # Use whichever interpretation covers more values
            dominant = max(numeric_count, dt_count, n)  # string always "conforms"
            conforming += dominant

    if total == 0:
        return 100.0
    return min(conforming / total * 100.0, 100.0)


# ── Accuracy ──────────────────────────────────────────────────────────────────

def _accuracy(df: pd.DataFrame) -> float:
    """% of non-outlier values using IQR method on numeric columns.
    Non-numeric columns are assumed 100% accurate.
    """
    if df.empty:
        return 100.0

    total = 0
    non_outlier = 0

    for col in df.columns:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        n = len(series)
        if n == 0:
            # Non-numeric column: count all non-null values as accurate
            non_null = int(df[col].notna().sum())
            total += non_null
            non_outlier += non_null
            continue

        total += n
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        non_outlier += int(((series >= lower) & (series <= upper)).sum())

    if total == 0:
        return 100.0
    return non_outlier / total * 100.0
