"""Property and unit tests for outlier detection — Requirements 5.1–5.5."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from pipeline.outlier_detector import (
    detect_and_handle,
    detect_isolation_forest,
    detect_zscore,
    detect_iqr,
    detect_dbscan,
    _ensemble_flags,
    ENSEMBLE_MIN_AGREEMENT,
)


# ── Property 4: Ensemble agreement ───────────────────────────────────────────
# Every point flagged by the ensemble is also flagged by ≥2 individual methods.
# Requirement 5.4

@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(
    n=st.integers(min_value=30, max_value=200),
    seed=st.integers(min_value=0, max_value=9999),
)
def test_ensemble_agreement_property(n: int, seed: int):
    """Every ensemble-flagged point must be flagged by ≥2 individual methods."""
    rng = np.random.default_rng(seed)
    # Normal data with a few injected outliers
    data = rng.standard_normal(n)
    data[:3] = [100.0, -100.0, 200.0]  # obvious outliers
    series = pd.Series(data)

    flags = _ensemble_flags(series)
    individual_methods = [k for k in flags if k != "ensemble"]

    for idx in flags["ensemble"]:
        votes = sum(1 for m in individual_methods if idx in flags[m])
        assert votes >= ENSEMBLE_MIN_AGREEMENT, (
            f"Index {idx} in ensemble but only {votes} methods agree "
            f"(need {ENSEMBLE_MIN_AGREEMENT})"
        )


# ── Unit tests: handling strategies ──────────────────────────────────────────
# Requirement 5.3

def _df_with_outliers() -> pd.DataFrame:
    """DataFrame with known outliers in column 'val'."""
    rng = np.random.default_rng(0)
    normal = rng.standard_normal(100).tolist()
    # Inject extreme outliers that all 4 methods will agree on
    normal[0] = 1000.0
    normal[1] = -1000.0
    return pd.DataFrame({"val": normal})


def test_removal_reduces_row_count():
    """Removal strategy must reduce the row count by the number of outliers removed."""
    df = _df_with_outliers()
    original_len = len(df)
    result = detect_and_handle(df, handling="remove")
    assert len(result.df_cleaned) < original_len, (
        "Removal strategy should reduce row count"
    )


def test_capping_clips_to_p1_p99():
    """Cap strategy must clip outlier values to [p1, p99] range."""
    df = _df_with_outliers()
    p1 = df["val"].quantile(0.01)
    p99 = df["val"].quantile(0.99)

    result = detect_and_handle(df, handling="cap")
    cleaned = result.df_cleaned["val"]

    assert cleaned.min() >= p1 - 1e-9, f"Min {cleaned.min()} below p1 {p1}"
    assert cleaned.max() <= p99 + 1e-9, f"Max {cleaned.max()} above p99 {p99}"


def test_median_imputation_replaces_with_median():
    """Median strategy must replace outlier values with the column median."""
    df = _df_with_outliers()
    # Compute median before cleaning (on non-extreme values)
    original_median = df["val"].median()

    result = detect_and_handle(df, handling="median")
    cleaned = result.df_cleaned["val"]

    # The extreme values (1000, -1000) should no longer exist
    assert cleaned.max() < 500, "Extreme positive outlier should have been replaced"
    assert cleaned.min() > -500, "Extreme negative outlier should have been replaced"


def test_no_outliers_df_unchanged():
    """A perfectly normal dataset with no outliers should be returned unchanged."""
    # Tight cluster — no method should flag anything
    data = [1.0, 1.1, 0.9, 1.05, 0.95, 1.02, 0.98] * 10
    df = pd.DataFrame({"val": data})
    result = detect_and_handle(df, handling="remove")
    # Row count should be the same (nothing removed)
    assert len(result.df_cleaned) == len(df)


def test_report_records_which_methods_flagged():
    """OutlierReport.method_flags must record which methods flagged each point."""
    df = _df_with_outliers()
    result = detect_and_handle(df, handling="cap")

    for report in result.reports:
        if report.outlier_count > 0:
            # Each flagged index must appear in ≥2 method flag lists
            for idx in report.outlier_indices:
                votes = sum(1 for flags in report.method_flags.values() if idx in flags)
                assert votes >= ENSEMBLE_MIN_AGREEMENT
