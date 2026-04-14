"""Drift detection — Requirements 8.1, 8.2."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

DRIFT_P_VALUE_THRESHOLD = 0.05  # Requirement 8.2: flag columns with p-value < 0.05


@dataclass
class ColumnDriftResult:
    column: str
    test: str           # "ks" or "chi2"
    statistic: float
    p_value: float
    drifted: bool       # p_value < threshold


@dataclass
class DriftReport:
    drifted_columns: list[str]
    column_results: list[ColumnDriftResult]
    total_columns: int
    drifted_count: int


def detect_drift(
    current: pd.DataFrame,
    baseline: pd.DataFrame,
) -> DriftReport:
    """Compare current dataset against baseline for distribution drift.

    - Numeric columns: Kolmogorov-Smirnov test (Requirement 8.1)
    - Categorical columns: Chi-squared test (Requirement 8.1)
    - Flags columns with p-value < 0.05 (Requirement 8.2)
    """
    results: list[ColumnDriftResult] = []
    common_cols = [c for c in current.columns if c in baseline.columns]

    for col in common_cols:
        cur_series = current[col].dropna()
        base_series = baseline[col].dropna()

        if len(cur_series) == 0 or len(base_series) == 0:
            continue

        # Determine test type
        if pd.api.types.is_numeric_dtype(cur_series) and pd.api.types.is_numeric_dtype(base_series):
            result = _ks_test(col, cur_series, base_series)
        else:
            result = _chi2_test(col, cur_series, base_series)

        results.append(result)

    drifted = [r.column for r in results if r.drifted]
    return DriftReport(
        drifted_columns=drifted,
        column_results=results,
        total_columns=len(results),
        drifted_count=len(drifted),
    )


# ── Individual tests ──────────────────────────────────────────────────────────

def _ks_test(col: str, current: pd.Series, baseline: pd.Series) -> ColumnDriftResult:
    """Two-sample Kolmogorov-Smirnov test for numeric columns."""
    stat, p_value = stats.ks_2samp(current.values, baseline.values)
    return ColumnDriftResult(
        column=col,
        test="ks",
        statistic=float(stat),
        p_value=float(p_value),
        drifted=p_value < DRIFT_P_VALUE_THRESHOLD,
    )


def _chi2_test(col: str, current: pd.Series, baseline: pd.Series) -> ColumnDriftResult:
    """Chi-squared test for categorical columns."""
    # Build aligned frequency tables
    all_cats = set(current.unique()) | set(baseline.unique())
    cur_counts = current.value_counts()
    base_counts = baseline.value_counts()

    observed = np.array([cur_counts.get(c, 0) for c in all_cats], dtype=float)
    expected = np.array([base_counts.get(c, 0) for c in all_cats], dtype=float)

    # Avoid zero expected frequencies
    expected = np.where(expected == 0, 1e-10, expected)
    # Scale expected to match observed total
    expected = expected / expected.sum() * observed.sum()
    expected = np.where(expected == 0, 1e-10, expected)

    if observed.sum() == 0:
        return ColumnDriftResult(col, "chi2", 0.0, 1.0, False)

    stat, p_value = stats.chisquare(observed, f_exp=expected)
    return ColumnDriftResult(
        column=col,
        test="chi2",
        statistic=float(stat),
        p_value=float(p_value),
        drifted=p_value < DRIFT_P_VALUE_THRESHOLD,
    )
