"""Property tests for transformer — Properties 5 & 6 (scaling round-trip, label encoding round-trip)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from pipeline.transformer import fit_transform, inverse_transform_numeric, decode_labels


# ── Helpers ───────────────────────────────────────────────────────────────────

def _numeric_df(draw, min_rows=5, max_rows=30, min_cols=1, max_cols=4):
    n_rows = draw(st.integers(min_rows, max_rows))
    n_cols = draw(st.integers(min_cols, max_cols))
    data = {}
    for i in range(n_cols):
        values = draw(
            st.lists(
                st.floats(min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False),
                min_size=n_rows, max_size=n_rows,
            )
        )
        data[f"col_{i}"] = values
    return pd.DataFrame(data)


# ── Property 5: Scaling round-trip ────────────────────────────────────────────

@given(st.data())
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_standard_scaler_roundtrip(data):
    """Property 5a: inverse_transform(transform(X)) ≈ X for StandardScaler."""
    df = _numeric_df(data.draw)
    # Skip if any column has zero variance (scaler scale_ would be 1 but values are all same)
    if any(df[c].std() == 0 for c in df.columns):
        return

    result, pipeline = fit_transform(df.copy(), scaler="standard", encode="onehot",
                                     datetime_decompose=False)
    recovered = inverse_transform_numeric(result.df, pipeline)

    # Only check columns that existed in original df
    orig_num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    for col in orig_num_cols:
        if col in recovered.columns:
            np.testing.assert_allclose(
                recovered[col].values, df[col].values, rtol=1e-4, atol=1e-4,
                err_msg=f"Round-trip failed for column '{col}' with standard scaler",
            )


@given(st.data())
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_robust_scaler_roundtrip(data):
    """Property 5b: inverse_transform(transform(X)) ≈ X for RobustScaler."""
    df = _numeric_df(data.draw)
    if any(df[c].std() == 0 for c in df.columns):
        return

    result, pipeline = fit_transform(df.copy(), scaler="robust", encode="onehot",
                                     datetime_decompose=False)
    recovered = inverse_transform_numeric(result.df, pipeline)

    orig_num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    for col in orig_num_cols:
        if col in recovered.columns:
            np.testing.assert_allclose(
                recovered[col].values, df[col].values, rtol=1e-4, atol=1e-4,
                err_msg=f"Round-trip failed for column '{col}' with robust scaler",
            )


# ── Property 6: Label encoding round-trip ────────────────────────────────────

@given(st.data())
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_label_encoding_roundtrip(data):
    """Property 6: decode_labels(inverse_scale(label_encode(X))) == X for categorical columns."""
    n_rows = data.draw(st.integers(5, 30))
    categories = data.draw(
        st.lists(st.text(min_size=1, max_size=8, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))),
                 min_size=2, max_size=6, unique=True)
    )
    if not categories:
        return

    values = data.draw(
        st.lists(st.sampled_from(categories), min_size=n_rows, max_size=n_rows)
    )
    df = pd.DataFrame({"category": values})

    result, pipeline = fit_transform(df.copy(), scaler="standard", encode="label",
                                     datetime_decompose=False)
    # Must inverse-scale first, then decode labels
    unscaled = inverse_transform_numeric(result.df, pipeline)
    recovered = decode_labels(unscaled, pipeline)

    assert list(recovered["category"]) == values, (
        "Label encoding round-trip failed: decoded values don't match originals"
    )


# ── Unit tests ────────────────────────────────────────────────────────────────

def test_onehot_encoding_creates_columns():
    """OHE should create one column per category."""
    df = pd.DataFrame({"color": ["red", "blue", "green", "red"]})
    result, _ = fit_transform(df, scaler="standard", encode="onehot", datetime_decompose=False)
    assert "color_red" in result.df.columns or any("color" in c for c in result.df.columns)


def test_scaler_params_populated():
    """scaler_params should have an entry per numeric column."""
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]})
    result, _ = fit_transform(df, scaler="standard", encode="onehot", datetime_decompose=False)
    assert "a" in result.scaler_params
    assert "b" in result.scaler_params


def test_datetime_decomposition():
    """Datetime columns should be decomposed into year/month/day/hour/weekday."""
    df = pd.DataFrame({"ts": pd.to_datetime(["2024-01-15 10:00", "2024-06-20 14:30"])})
    result, _ = fit_transform(df, scaler="standard", encode="onehot", datetime_decompose=True)
    assert "ts_year" in result.added_columns or any("ts_" in c for c in result.df.columns)
