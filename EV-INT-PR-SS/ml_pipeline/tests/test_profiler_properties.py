"""
Property tests for the data profiler.

Feature: ai-data-quality-platform
Property: Profiler shape and missing_pct invariants
Validates: Requirements 3.1, 10.2
"""
import math
import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st


# ── Strategies ────────────────────────────────────────────────────────────────

def _df_strategy():
    """Generate DataFrames with 1–50 rows and 1–8 columns, some NaN values."""
    return st.builds(
        _build_df,
        n_rows=st.integers(min_value=1, max_value=50),
        n_cols=st.integers(min_value=1, max_value=8),
        seed=st.integers(min_value=0, max_value=2**31),
    )


def _build_df(n_rows: int, n_cols: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = {}
    for i in range(n_cols):
        col = rng.standard_normal(n_rows).astype(float)
        # Randomly introduce NaN values
        mask = rng.random(n_rows) < 0.2
        col[mask] = np.nan
        data[f"col_{i}"] = col
    return pd.DataFrame(data)


# ── Properties ────────────────────────────────────────────────────────────────

@given(df=_df_strategy())
@settings(max_examples=100, deadline=None)
def test_profiler_shape_matches_dataframe(df: pd.DataFrame):
    """For any DataFrame, profile.row_count == len(df) and
    profile.column_count == len(df.columns).
    Validates: Requirements 3.1, 10.2"""
    from pipeline.profiler import profile_dataframe

    profile = profile_dataframe(df)
    assert profile.row_count == len(df)
    assert profile.column_count == len(df.columns)
    assert len(profile.columns) == len(df.columns)


@given(df=_df_strategy())
@settings(max_examples=100, deadline=None)
def test_profiler_missing_pct_matches_actual(df: pd.DataFrame):
    """For any DataFrame, each column's missing_pct equals
    (missing_count / row_count) * 100 within floating-point tolerance.
    Validates: Requirements 3.1, 10.2"""
    from pipeline.profiler import profile_dataframe

    profile = profile_dataframe(df)
    for col_profile in profile.columns:
        col = df[col_profile.name]
        expected_missing = int(col.isna().sum())
        expected_pct = (expected_missing / len(df) * 100) if len(df) > 0 else 0.0

        assert col_profile.missing_count == expected_missing, (
            f"Column {col_profile.name}: expected missing_count={expected_missing}, "
            f"got {col_profile.missing_count}"
        )
        assert math.isclose(col_profile.missing_pct, expected_pct, rel_tol=1e-4, abs_tol=1e-6), (
            f"Column {col_profile.name}: expected missing_pct={expected_pct:.4f}, "
            f"got {col_profile.missing_pct:.4f}"
        )


@given(df=_df_strategy())
@settings(max_examples=100, deadline=None)
def test_profiler_numeric_stats_within_bounds(df: pd.DataFrame):
    """For any numeric column, min <= q1 <= median <= q3 <= max.
    Validates: Requirements 3.4, 3.5"""
    from pipeline.profiler import profile_dataframe

    profile = profile_dataframe(df)
    for cp in profile.columns:
        if cp.min is not None and cp.max is not None:
            assert cp.min <= cp.max, f"Column {cp.name}: min > max"
        if cp.q1 is not None and cp.q3 is not None:
            assert cp.q1 <= cp.q3, f"Column {cp.name}: q1 > q3"
        if cp.median is not None and cp.q1 is not None and cp.q3 is not None:
            assert cp.q1 <= cp.median <= cp.q3, (
                f"Column {cp.name}: median not in [q1, q3]"
            )
