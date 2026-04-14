"""Tests for drift detector — Requirements 8.1, 8.2 (Property 11 + unit tests)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from pipeline.drift_detector import detect_drift, DRIFT_P_VALUE_THRESHOLD


# ── Property 11: Self-consistency ────────────────────────────────────────────

@given(st.data())
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
def test_no_drift_same_distribution(data):
    """Property 11: detect_drift(df, df) should report 0 drifted columns for identical data."""
    n = data.draw(st.integers(30, 100))
    n_cols = data.draw(st.integers(1, 4))
    rng = np.random.default_rng(data.draw(st.integers(0, 9999)))

    df_data = {f"col_{i}": rng.normal(0, 1, n).tolist() for i in range(n_cols)}
    df = pd.DataFrame(df_data)

    report = detect_drift(df, df)

    assert report.drifted_count == 0, (
        f"Expected 0 drifted columns when comparing df to itself, got {report.drifted_count}: "
        f"{report.drifted_columns}"
    )


# ── Unit tests ────────────────────────────────────────────────────────────────

def test_drift_detected_different_distributions():
    """Clearly different distributions should be flagged as drifted."""
    rng = np.random.default_rng(42)
    baseline = pd.DataFrame({"x": rng.normal(0, 1, 500)})
    current = pd.DataFrame({"x": rng.normal(10, 1, 500)})  # mean shifted by 10

    report = detect_drift(current, baseline)
    assert report.drifted_count > 0, "Expected drift to be detected for clearly different distributions"
    assert "x" in report.drifted_columns


def test_no_drift_same_data():
    """Identical dataframes should produce 0 drifted columns."""
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"a": rng.normal(0, 1, 200), "b": rng.normal(5, 2, 200)})
    report = detect_drift(df, df)
    assert report.drifted_count == 0


def test_categorical_drift_detected():
    """Chi-squared test should detect drift in categorical columns."""
    baseline = pd.DataFrame({"cat": ["a"] * 100 + ["b"] * 100})
    current = pd.DataFrame({"cat": ["a"] * 10 + ["b"] * 190})  # heavily skewed

    report = detect_drift(current, baseline)
    assert report.drifted_count > 0, "Expected categorical drift to be detected"


def test_categorical_no_drift_same_distribution():
    """Same categorical distribution should not be flagged."""
    cats = ["a", "b", "c"]
    rng = np.random.default_rng(7)
    values = rng.choice(cats, size=300).tolist()
    df = pd.DataFrame({"cat": values})
    report = detect_drift(df, df)
    assert report.drifted_count == 0


def test_total_columns_count():
    """total_columns should equal number of common columns tested."""
    df1 = pd.DataFrame({"a": [1.0, 2.0, 3.0] * 20, "b": [4.0, 5.0, 6.0] * 20})
    df2 = pd.DataFrame({"a": [1.0, 2.0, 3.0] * 20, "c": [7.0, 8.0, 9.0] * 20})  # 'b' not in df2
    report = detect_drift(df1, df2)
    assert report.total_columns == 1  # only 'a' is common


def test_p_value_threshold_respected():
    """All drifted columns should have p_value < DRIFT_P_VALUE_THRESHOLD."""
    rng = np.random.default_rng(42)
    baseline = pd.DataFrame({"x": rng.normal(0, 1, 300), "y": rng.normal(0, 1, 300)})
    current = pd.DataFrame({"x": rng.normal(5, 1, 300), "y": rng.normal(0, 1, 300)})

    report = detect_drift(current, baseline)
    for col_result in report.column_results:
        if col_result.drifted:
            assert col_result.p_value < DRIFT_P_VALUE_THRESHOLD


def test_empty_series_skipped():
    """Columns with all NaN in current should be skipped gracefully."""
    baseline = pd.DataFrame({"a": [1.0, 2.0, 3.0] * 10})
    current = pd.DataFrame({"a": [float("nan")] * 30})
    # Should not raise
    report = detect_drift(current, baseline)
    assert report.total_columns == 0
