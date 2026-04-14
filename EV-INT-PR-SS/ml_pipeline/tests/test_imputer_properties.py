"""Property and edge-case tests for the imputer — Requirements 4.1, 4.2, 4.5."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from pipeline.imputer import impute, HIGH_MISSING_THRESHOLD, Strategy


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_df_with_missing(n_rows: int, n_cols: int, missing_frac: float) -> pd.DataFrame:
    """Build a numeric DataFrame with a controlled fraction of NaNs."""
    rng = np.random.default_rng(42)
    data = rng.standard_normal((n_rows, n_cols))
    mask = rng.random((n_rows, n_cols)) < missing_frac
    data[mask] = np.nan
    return pd.DataFrame(data, columns=[f"col_{i}" for i in range(n_cols)])


# ── Property 3: Imputation eliminates missing values ─────────────────────────
# For any DataFrame and any supported strategy, after imputation the column
# contains zero null/NaN values.  (Requirements 4.1, 4.2)

STRATEGIES: list[Strategy] = ["mean", "median", "knn", "mice"]


@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@given(
    n_rows=st.integers(min_value=20, max_value=100),
    n_cols=st.integers(min_value=1, max_value=5),
    missing_frac=st.floats(min_value=0.05, max_value=0.75),
)
def test_imputation_eliminates_nulls(n_rows: int, n_cols: int, missing_frac: float):
    """After imputation, no imputable column should contain NaN values."""
    df = _make_df_with_missing(n_rows, n_cols, missing_frac)

    for strategy in STRATEGIES:
        result = impute(df.copy(), strategy=strategy)
        imputed_df = result.df

        for col in imputed_df.columns:
            if col in result.flagged_columns:
                continue  # flagged columns are intentionally left as-is
            null_count = imputed_df[col].isna().sum()
            assert null_count == 0, (
                f"Strategy '{strategy}', column '{col}': "
                f"expected 0 nulls after imputation, got {null_count}"
            )


# ── Edge-case tests: >80% missing flagged, ≤80% imputed ──────────────────────
# Requirement 4.5

def test_column_above_threshold_is_flagged_not_imputed():
    """A column with exactly 81% missing is flagged and left unchanged."""
    n = 100
    data = {"normal": np.random.randn(n), "sparse": [np.nan] * 81 + list(np.random.randn(19))}
    df = pd.DataFrame(data)

    result = impute(df, strategy="mean")

    assert "sparse" in result.flagged_columns, "Column with 81% missing should be flagged"
    # The flagged column must NOT have been imputed — still has NaNs
    assert result.df["sparse"].isna().sum() == 81, (
        "Flagged column should retain its original NaN values"
    )


def test_column_below_threshold_is_imputed():
    """A column with 79% missing is NOT flagged and IS imputed."""
    n = 100
    data = {"normal": np.random.randn(n), "mostly_missing": [np.nan] * 79 + list(np.random.randn(21))}
    df = pd.DataFrame(data)

    result = impute(df, strategy="mean")

    assert "mostly_missing" not in result.flagged_columns, (
        "Column with 79% missing should not be flagged"
    )
    assert result.df["mostly_missing"].isna().sum() == 0, (
        "Column with 79% missing should be fully imputed"
    )


def test_exactly_80_percent_missing_is_not_flagged():
    """A column with exactly 80% missing is at the boundary — not flagged (threshold is >80%)."""
    n = 100
    data = {"col": [np.nan] * 80 + list(np.random.randn(20))}
    df = pd.DataFrame(data)

    result = impute(df, strategy="mean")

    assert "col" not in result.flagged_columns, (
        "Column with exactly 80% missing should NOT be flagged (threshold is strictly >80%)"
    )
    assert result.df["col"].isna().sum() == 0


def test_no_missing_values_unchanged():
    """A DataFrame with no missing values passes through untouched."""
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]})
    result = impute(df, strategy="mean")
    assert result.flagged_columns == []
    pd.testing.assert_frame_equal(result.df, df)
