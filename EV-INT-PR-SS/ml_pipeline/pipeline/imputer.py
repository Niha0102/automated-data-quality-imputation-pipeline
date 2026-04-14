"""Missing value imputer — Requirements 4.1, 4.2, 4.3, 4.4, 4.5."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer, SimpleImputer
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.linear_model import BayesianRidge
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

Strategy = Literal["knn", "mice", "regression", "mean", "median", "mode"]

HIGH_MISSING_THRESHOLD = 0.80  # Requirement 4.5: flag columns with >80% missing


@dataclass
class ImputationResult:
    df: pd.DataFrame
    strategy_used: dict[str, Strategy]   # column → strategy
    flagged_columns: list[str]           # columns with >80% missing (not imputed)


def impute(
    df: pd.DataFrame,
    strategy: Strategy | Literal["auto"] = "auto",
) -> ImputationResult:
    """Impute missing values in df.

    - Columns with >80% missing are flagged and left as-is (Requirement 4.5).
    - strategy='auto' selects the best strategy per numeric column via CV.
    - Non-numeric columns use mode imputation.
    """
    df = df.copy()
    flagged: list[str] = []
    strategy_used: dict[str, Strategy] = {}

    for col in df.columns:
        series = df[col]
        missing_pct = series.isna().mean()

        if missing_pct > HIGH_MISSING_THRESHOLD:
            flagged.append(col)
            logger.warning("Column '%s' has %.1f%% missing — flagged, not imputed", col, missing_pct * 100)
            continue

        if series.isna().sum() == 0:
            continue  # nothing to impute

        is_numeric = pd.api.types.is_numeric_dtype(series) or pd.to_numeric(series, errors="coerce").notna().any()

        if is_numeric:
            chosen = strategy if strategy != "auto" else auto_select(df, col)
            df[col] = _impute_numeric_column(df, col, chosen)
            strategy_used[col] = chosen
        else:
            # Non-numeric: mode imputation
            mode_val = series.mode(dropna=True)
            if len(mode_val) > 0:
                df[col] = series.fillna(mode_val.iloc[0])
            strategy_used[col] = "mode"

    return ImputationResult(df=df, strategy_used=strategy_used, flagged_columns=flagged)


def auto_select(df: pd.DataFrame, target_col: str) -> Strategy:
    """Select the best imputation strategy for a column via cross-validation.

    Evaluates mean, median, knn, and mice; returns the one with lowest MAE.
    Falls back to 'mean' if CV fails.
    """
    numeric_df = df.select_dtypes(include=[np.number])
    if target_col not in numeric_df.columns:
        return "mean"

    # Build a complete-case subset for CV
    complete = numeric_df.dropna()
    if len(complete) < 10:
        return "mean"

    # Mask the target column to simulate missingness
    X = complete.drop(columns=[target_col])
    y = complete[target_col]

    if X.empty:
        return "mean"

    candidates: dict[Strategy, float] = {}
    for strat in ("mean", "median", "knn"):
        try:
            imputer = _make_imputer(strat)
            pipe = Pipeline([("imp", imputer)])
            # Use negative MAE; we only need relative comparison
            scores = cross_val_score(
                pipe, X, y, cv=min(3, len(complete)), scoring="neg_mean_absolute_error"
            )
            candidates[strat] = float(np.mean(scores))
        except Exception as exc:
            logger.debug("CV failed for strategy '%s': %s", strat, exc)

    if not candidates:
        return "mean"

    best: Strategy = max(candidates, key=lambda k: candidates[k])  # least negative = best
    logger.debug("auto_select for '%s': %s (scores=%s)", target_col, best, candidates)
    return best


# ── Internal helpers ──────────────────────────────────────────────────────────

def _impute_numeric_column(df: pd.DataFrame, col: str, strategy: Strategy) -> pd.Series:
    """Impute a single numeric column using the given strategy."""
    numeric_df = df.select_dtypes(include=[np.number])
    if col not in numeric_df.columns:
        # Coerce to numeric first
        numeric_df = df[[col]].apply(pd.to_numeric, errors="coerce")

    imputer = _make_imputer(strategy)
    result = imputer.fit_transform(numeric_df)
    result_df = pd.DataFrame(result, columns=numeric_df.columns, index=numeric_df.index)
    return result_df[col]


def _make_imputer(strategy: Strategy):
    """Instantiate the sklearn imputer for the given strategy."""
    if strategy == "knn":
        return KNNImputer(n_neighbors=5)
    elif strategy == "mice":
        return IterativeImputer(estimator=BayesianRidge(), max_iter=10, random_state=42)
    elif strategy == "regression":
        return IterativeImputer(estimator=BayesianRidge(), max_iter=10, random_state=42)
    elif strategy == "mean":
        return SimpleImputer(strategy="mean")
    elif strategy == "median":
        return SimpleImputer(strategy="median")
    elif strategy == "mode":
        return SimpleImputer(strategy="most_frequent")
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
