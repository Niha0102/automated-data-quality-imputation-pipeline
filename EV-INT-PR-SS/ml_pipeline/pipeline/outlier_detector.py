"""Outlier detection — Requirements 5.1, 5.2, 5.3, 5.4, 5.5."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

Method = Literal["isolation_forest", "zscore", "iqr", "dbscan"]
HandlingStrategy = Literal["remove", "cap", "median"]

ENSEMBLE_MIN_AGREEMENT = 2  # Requirement 5.4: flag when ≥2 methods agree


@dataclass
class OutlierReport:
    """Per-column outlier detection results."""
    column: str
    outlier_indices: list[int]          # row indices flagged by ensemble
    method_flags: dict[str, list[int]]  # method → list of flagged indices
    outlier_count: int
    outlier_pct: float


@dataclass
class DetectionResult:
    df_cleaned: pd.DataFrame            # DataFrame after handling strategy applied
    reports: list[OutlierReport]
    strategy_used: HandlingStrategy


# ── Public API ────────────────────────────────────────────────────────────────

def detect_and_handle(
    df: pd.DataFrame,
    handling: HandlingStrategy = "cap",
) -> DetectionResult:
    """Detect outliers via ensemble and apply the chosen handling strategy.

    Requirements 5.1–5.5
    """
    reports: list[OutlierReport] = []
    df_out = df.copy()

    for col in df.select_dtypes(include=[np.number]).columns:
        series = df[col].dropna()
        if len(series) < 5:
            continue

        flags = _ensemble_flags(series)
        outlier_idx = list(flags["ensemble"])
        report = OutlierReport(
            column=col,
            outlier_indices=outlier_idx,
            method_flags={k: list(v) for k, v in flags.items() if k != "ensemble"},
            outlier_count=len(outlier_idx),
            outlier_pct=round(len(outlier_idx) / len(series) * 100, 4),
        )
        reports.append(report)

        if outlier_idx:
            df_out = _apply_handling(df_out, col, outlier_idx, handling)

    return DetectionResult(df_cleaned=df_out, reports=reports, strategy_used=handling)


# ── Individual detectors ──────────────────────────────────────────────────────

def detect_isolation_forest(series: pd.Series) -> set[int]:
    """Isolation Forest outlier detection. Returns set of outlier indices."""
    values = series.values.reshape(-1, 1)
    clf = IsolationForest(contamination=0.05, random_state=42)
    preds = clf.fit_predict(values)
    return set(series.index[preds == -1].tolist())


def detect_zscore(series: pd.Series, threshold: float = 3.0) -> set[int]:
    """Z-score outlier detection. Returns set of outlier indices."""
    mean = series.mean()
    std = series.std()
    if std == 0:
        return set()
    z = (series - mean) / std
    return set(series.index[z.abs() > threshold].tolist())


def detect_iqr(series: pd.Series, factor: float = 1.5) -> set[int]:
    """IQR outlier detection. Returns set of outlier indices."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    return set(series.index[(series < lower) | (series > upper)].tolist())


def detect_dbscan(series: pd.Series, eps: float = 0.5, min_samples: int = 5) -> set[int]:
    """DBSCAN outlier detection (noise points = -1). Returns set of outlier indices."""
    values = series.values.reshape(-1, 1)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(values)
    labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(scaled)
    return set(series.index[labels == -1].tolist())


# ── Ensemble ──────────────────────────────────────────────────────────────────

def _ensemble_flags(series: pd.Series) -> dict[str, set[int]]:
    """Run all 4 detectors; flag a point only when ≥2 methods agree."""
    flags: dict[str, set[int]] = {
        "isolation_forest": detect_isolation_forest(series),
        "zscore": detect_zscore(series),
        "iqr": detect_iqr(series),
        "dbscan": detect_dbscan(series),
    }

    # Count votes per index
    vote_count: dict[int, int] = {}
    for method_flags in flags.values():
        for idx in method_flags:
            vote_count[idx] = vote_count.get(idx, 0) + 1

    flags["ensemble"] = {idx for idx, votes in vote_count.items() if votes >= ENSEMBLE_MIN_AGREEMENT}
    return flags


# ── Handling strategies ───────────────────────────────────────────────────────

def _apply_handling(
    df: pd.DataFrame,
    col: str,
    outlier_idx: list[int],
    strategy: HandlingStrategy,
) -> pd.DataFrame:
    """Apply removal, capping (winsorization), or median imputation."""
    if strategy == "remove":
        df = df.drop(index=outlier_idx)

    elif strategy == "cap":
        # Winsorize to [p1, p99]
        p1 = df[col].quantile(0.01)
        p99 = df[col].quantile(0.99)
        df.loc[outlier_idx, col] = df.loc[outlier_idx, col].clip(lower=p1, upper=p99)

    elif strategy == "median":
        median_val = df[col].median()
        df.loc[outlier_idx, col] = median_val

    return df
