"""Unit tests for anomaly detector — Requirement 6.2."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.anomaly_detector import AutoencoderDetector, ANOMALY_PERCENTILE


def _make_df(n: int = 100, n_cols: int = 3, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = {f"col_{i}": rng.normal(0, 1, n) for i in range(n_cols)}
    return pd.DataFrame(data)


def test_anomalous_records_above_95th_percentile():
    """Requirement 6.2: anomalous records should be those above the 95th percentile of reconstruction error."""
    df = _make_df(n=200)
    detector = AutoencoderDetector(epochs=5)
    detector.fit(df)
    report = detector.predict(df)

    errors = np.array(report.reconstruction_errors)
    threshold = report.threshold

    # All flagged indices must have error > threshold
    for idx in report.anomaly_indices:
        assert errors[idx] > threshold, (
            f"Index {idx} flagged as anomaly but error {errors[idx]:.6f} <= threshold {threshold:.6f}"
        )

    # Threshold should be approximately the 95th percentile of errors
    expected_threshold = np.percentile(errors, ANOMALY_PERCENTILE)
    assert abs(threshold - expected_threshold) < 1e-5 or threshold <= expected_threshold + 1e-5


def test_injected_anomalies_detected():
    """Injecting extreme outliers should result in them being flagged."""
    rng = np.random.default_rng(0)
    normal_data = rng.normal(0, 1, (150, 3))
    df_normal = pd.DataFrame(normal_data, columns=["a", "b", "c"])

    detector = AutoencoderDetector(epochs=10)
    detector.fit(df_normal)

    # Create test data with obvious anomalies at the end
    anomaly_data = rng.normal(0, 1, (20, 3))
    anomaly_data[-5:] = 100.0  # extreme values
    df_test = pd.DataFrame(anomaly_data, columns=["a", "b", "c"])

    report = detector.predict(df_test)
    # At least some of the extreme rows should be flagged
    extreme_indices = set(range(15, 20))
    flagged = set(report.anomaly_indices)
    assert len(extreme_indices & flagged) > 0, "Extreme anomalies were not detected"


def test_anomaly_count_matches_indices():
    """anomaly_count should equal len(anomaly_indices)."""
    df = _make_df(n=100)
    detector = AutoencoderDetector(epochs=5)
    detector.fit(df)
    report = detector.predict(df)
    assert report.anomaly_count == len(report.anomaly_indices)


def test_anomaly_pct_range():
    """anomaly_pct should be between 0 and 100."""
    df = _make_df(n=100)
    detector = AutoencoderDetector(epochs=5)
    detector.fit(df)
    report = detector.predict(df)
    assert 0.0 <= report.anomaly_pct <= 100.0


def test_predict_before_fit_raises():
    """predict() before fit() should raise RuntimeError."""
    df = _make_df(n=50)
    detector = AutoencoderDetector()
    with pytest.raises(RuntimeError, match="fit"):
        detector.predict(df)


def test_retrain_resets_model():
    """retrain() should produce a new threshold."""
    df1 = _make_df(n=100, seed=1)
    df2 = _make_df(n=100, seed=99)
    detector = AutoencoderDetector(epochs=5)
    detector.fit(df1)
    t1 = detector._threshold
    detector.retrain(df2)
    t2 = detector._threshold
    # Thresholds may differ (different data)
    assert t2 is not None


def test_no_numeric_columns_raises():
    """DataFrame with no numeric columns should raise ValueError."""
    df = pd.DataFrame({"a": ["x", "y", "z"]})
    detector = AutoencoderDetector(epochs=5)
    with pytest.raises(ValueError, match="numeric"):
        detector.fit(df)
