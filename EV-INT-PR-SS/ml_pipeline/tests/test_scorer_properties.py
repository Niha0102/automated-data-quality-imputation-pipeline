"""
Property tests for the quality scorer.

Feature: ai-data-quality-platform
Property 1: Data Quality Score bounds invariant
Property 2: Completeness score matches missing value count
Validates: Requirements 10.1, 10.2, 10.3, 10.4
"""
import math
import numpy as np
import pandas as pd
from hypothesis import given, settings, strategies as st


# ── Strategies ────────────────────────────────────────────────────────────────

def _mixed_df_strategy():
    """Generate DataFrames with numeric and string columns, some NaN."""
    return st.builds(
        _build_mixed_df,
        n_rows=st.integers(min_value=1, max_value=100),
        n_numeric=st.integers(min_value=0, max_value=5),
        n_string=st.integers(min_value=0, max_value=3),
        seed=st.integers(min_value=0, max_value=2**31),
    ).filter(lambda df: len(df.columns) > 0)


def _build_mixed_df(n_rows: int, n_numeric: int, n_string: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = {}
    for i in range(n_numeric):
        col = rng.standard_normal(n_rows).astype(float)
        mask = rng.random(n_rows) < 0.15
        col[mask] = np.nan
        data[f"num_{i}"] = col
    for i in range(n_string):
        choices = ["apple", "banana", "cherry", "date", None]
        col = rng.choice(choices, size=n_rows)
        data[f"str_{i}"] = col
    return pd.DataFrame(data)


# ── Property 1: Score bounds ──────────────────────────────────────────────────

@given(df=_mixed_df_strategy())
@settings(max_examples=100, deadline=None)
def test_quality_scores_in_bounds(df: pd.DataFrame):
    """For any DataFrame, all component scores and overall score are in [0, 100].
    Property 1: Data Quality Score bounds invariant
    Validates: Requirements 10.1, 10.2, 10.3, 10.4"""
    from pipeline.scorer import compute_quality_score

    score = compute_quality_score(df)
    for name, value in [
        ("completeness", score.completeness),
        ("consistency", score.consistency),
        ("accuracy", score.accuracy),
        ("overall", score.overall),
    ]:
        assert 0.0 <= value <= 100.0, f"{name}={value} is outside [0, 100]"


@given(df=_mixed_df_strategy())
@settings(max_examples=100, deadline=None)
def test_overall_is_mean_of_components(df: pd.DataFrame):
    """overall == (completeness + consistency + accuracy) / 3.
    Validates: Requirements 10.4"""
    from pipeline.scorer import compute_quality_score

    score = compute_quality_score(df)
    expected = (score.completeness + score.consistency + score.accuracy) / 3.0
    assert math.isclose(score.overall, expected, rel_tol=1e-4, abs_tol=1e-6), (
        f"overall={score.overall} != mean of components={expected}"
    )


# ── Property 2: Completeness formula ─────────────────────────────────────────

@given(df=_mixed_df_strategy())
@settings(max_examples=100, deadline=None)
def test_completeness_matches_missing_count(df: pd.DataFrame):
    """For any DataFrame, completeness = (total_cells - missing_cells) / total_cells * 100.
    Property 2: Completeness score matches missing value count
    Validates: Requirements 10.2, 4.1"""
    from pipeline.scorer import compute_quality_score

    score = compute_quality_score(df)
    total = df.size
    missing = int(df.isna().sum().sum())
    expected = (total - missing) / total * 100.0 if total > 0 else 100.0

    assert math.isclose(score.completeness, expected, rel_tol=1e-4, abs_tol=1e-6), (
        f"completeness={score.completeness} != expected={expected}"
    )
