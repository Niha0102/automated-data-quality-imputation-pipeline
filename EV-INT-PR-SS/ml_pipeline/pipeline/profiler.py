"""Data profiler — Requirements 3.1, 3.2, 3.4, 3.5."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ColumnProfile:
    name: str
    dtype: str                          # detected semantic type
    missing_count: int
    missing_pct: float                  # 0–100
    # Numeric stats (None for non-numeric columns)
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    q1: Optional[float] = None
    q3: Optional[float] = None
    # Categorical stats
    cardinality: int = 0
    top_values: list[dict[str, Any]] = field(default_factory=list)  # [{value, count, pct}]


@dataclass
class DataProfile:
    row_count: int
    column_count: int
    columns: list[ColumnProfile]
    correlation_matrix: Optional[dict[str, dict[str, float]]] = None  # col → col → r


# ── Profiler ──────────────────────────────────────────────────────────────────

def profile_dataframe(df: pd.DataFrame, top_n: int = 10) -> DataProfile:
    """Compute a full profile of a pandas DataFrame.

    Requirements 3.1, 3.2, 3.4, 3.5
    """
    row_count = len(df)
    column_count = len(df.columns)
    columns: list[ColumnProfile] = []

    for col in df.columns:
        series = df[col]
        missing_count = int(series.isna().sum())
        missing_pct = (missing_count / row_count * 100) if row_count > 0 else 0.0
        dtype = _detect_dtype(series)
        cardinality = int(series.nunique(dropna=True))

        # Top-N value frequencies
        vc = series.value_counts(dropna=True).head(top_n)
        top_values = [
            {"value": str(v), "count": int(c), "pct": round(c / row_count * 100, 2)}
            for v, c in vc.items()
        ]

        cp = ColumnProfile(
            name=col,
            dtype=dtype,
            missing_count=missing_count,
            missing_pct=round(missing_pct, 4),
            cardinality=cardinality,
            top_values=top_values,
        )

        # Numeric descriptive stats
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().sum() > 0:
            cp.mean = float(numeric.mean())
            cp.median = float(numeric.median())
            cp.std = float(numeric.std()) if len(numeric.dropna()) > 1 else 0.0
            cp.min = float(numeric.min())
            cp.max = float(numeric.max())
            cp.q1 = float(numeric.quantile(0.25))
            cp.q3 = float(numeric.quantile(0.75))

        columns.append(cp)

    # Correlation matrix (numeric columns only)
    corr_matrix: Optional[dict[str, dict[str, float]]] = None
    numeric_df = df.select_dtypes(include=[np.number])
    if len(numeric_df.columns) >= 2:
        corr = numeric_df.corr()
        corr_matrix = {
            col: {c: round(float(v), 4) for c, v in row.items()}
            for col, row in corr.to_dict().items()
        }

    return DataProfile(
        row_count=row_count,
        column_count=column_count,
        columns=columns,
        correlation_matrix=corr_matrix,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _detect_dtype(series: pd.Series) -> str:
    """Detect a human-readable semantic type for a column."""
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "float"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    # Try numeric coercion
    numeric = pd.to_numeric(series.dropna(), errors="coerce")
    if numeric.notna().all() and len(numeric) > 0:
        if (numeric % 1 == 0).all():
            return "integer"
        return "float"

    # Try datetime coercion
    try:
        pd.to_datetime(series.dropna().head(20))
        return "datetime"
    except Exception:
        pass

    return "string"
