"""Data transformation — Requirements 7.1, 7.2, 7.3, 7.4."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, RobustScaler, LabelEncoder
from sklearn.preprocessing import PolynomialFeatures

logger = logging.getLogger(__name__)

ScalerType = Literal["standard", "robust"]
EncoderType = Literal["onehot", "label"]


@dataclass
class TransformResult:
    df: pd.DataFrame
    scaler_params: dict[str, dict]      # col → {type, mean, scale, ...}
    encoder_mappings: dict[str, dict]   # col → {type, classes/categories}
    added_columns: list[str]            # new columns created


@dataclass
class TransformPipeline:
    """Stores fitted transformers for inverse_transform / decode."""
    scalers: dict[str, object] = field(default_factory=dict)
    encoders: dict[str, LabelEncoder] = field(default_factory=dict)
    onehot_categories: dict[str, list] = field(default_factory=dict)


# ── Public API ────────────────────────────────────────────────────────────────

def fit_transform(
    df: pd.DataFrame,
    scaler: ScalerType = "standard",
    encode: EncoderType = "onehot",
    polynomial_degree: int = 0,
    interaction_terms: bool = False,
    datetime_decompose: bool = True,
) -> tuple[TransformResult, TransformPipeline]:
    """Fit and apply all transformations. Returns (result, pipeline).

    Requirements 7.1, 7.2, 7.3, 7.4
    """
    df = df.copy()
    pipeline = TransformPipeline()
    scaler_params: dict[str, dict] = {}
    encoder_mappings: dict[str, dict] = {}
    added_columns: list[str] = []

    # 1. Datetime decomposition (Requirement 7.4)
    if datetime_decompose:
        df, new_cols = _decompose_datetime_columns(df)
        added_columns.extend(new_cols)

    # 2. Encode categoricals (Requirement 7.2)
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    for col in cat_cols:
        if encode == "label":
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            pipeline.encoders[col] = le
            encoder_mappings[col] = {"type": "label", "classes": list(le.classes_)}
        else:  # onehot
            dummies = pd.get_dummies(df[col], prefix=col, drop_first=False)
            pipeline.onehot_categories[col] = list(dummies.columns)
            df = df.drop(columns=[col])
            df = pd.concat([df, dummies], axis=1)
            encoder_mappings[col] = {"type": "onehot", "categories": list(dummies.columns)}
            added_columns.extend(list(dummies.columns))

    # 3. Scale numeric columns (Requirement 7.1)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if num_cols:
        sk_scaler = StandardScaler() if scaler == "standard" else RobustScaler()
        df[num_cols] = sk_scaler.fit_transform(df[num_cols])
        pipeline.scalers["__all__"] = sk_scaler
        for i, col in enumerate(num_cols):
            if scaler == "standard":
                scaler_params[col] = {
                    "type": "standard",
                    "mean": float(sk_scaler.mean_[i]),
                    "scale": float(sk_scaler.scale_[i]),
                }
            else:
                scaler_params[col] = {
                    "type": "robust",
                    "center": float(sk_scaler.center_[i]),
                    "scale": float(sk_scaler.scale_[i]),
                }

    # 4. Polynomial features (Requirement 7.3)
    if polynomial_degree >= 2:
        num_cols_now = df.select_dtypes(include=[np.number]).columns.tolist()
        if num_cols_now:
            poly = PolynomialFeatures(degree=polynomial_degree, include_bias=False, interaction_only=False)
            poly_arr = poly.fit_transform(df[num_cols_now])
            poly_names = poly.get_feature_names_out(num_cols_now)
            new_poly_cols = [n for n in poly_names if n not in num_cols_now]
            poly_df = pd.DataFrame(poly_arr, columns=poly_names, index=df.index)
            for c in new_poly_cols:
                df[c] = poly_df[c]
            added_columns.extend(new_poly_cols)

    # 5. Interaction terms (Requirement 7.3)
    if interaction_terms and not polynomial_degree >= 2:
        num_cols_now = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(num_cols_now) >= 2:
            poly = PolynomialFeatures(degree=2, include_bias=False, interaction_only=True)
            inter_arr = poly.fit_transform(df[num_cols_now])
            inter_names = poly.get_feature_names_out(num_cols_now)
            new_inter = [n for n in inter_names if n not in num_cols_now]
            inter_df = pd.DataFrame(inter_arr, columns=inter_names, index=df.index)
            for c in new_inter:
                df[c] = inter_df[c]
            added_columns.extend(new_inter)

    result = TransformResult(
        df=df,
        scaler_params=scaler_params,
        encoder_mappings=encoder_mappings,
        added_columns=added_columns,
    )
    return result, pipeline


def inverse_transform_numeric(df: pd.DataFrame, pipeline: TransformPipeline) -> pd.DataFrame:
    """Reverse scaling on numeric columns. Requirements 7.1, 7.3."""
    df = df.copy()
    sk_scaler = pipeline.scalers.get("__all__")
    if sk_scaler is None:
        return df
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Determine which columns the scaler was fitted on
    fitted_feature_names = getattr(sk_scaler, "feature_names_in_", None)
    if fitted_feature_names is not None:
        fitted_set = set(fitted_feature_names.tolist())
        fitted_cols = [c for c in num_cols if c in fitted_set]
    else:
        fitted_cols = num_cols
    if fitted_cols:
        try:
            df[fitted_cols] = sk_scaler.inverse_transform(df[fitted_cols])
        except Exception as exc:
            logger.warning("inverse_transform failed: %s", exc)
    return df


def decode_labels(df: pd.DataFrame, pipeline: TransformPipeline) -> pd.DataFrame:
    """Reverse label encoding. Requirements 7.2, 7.3.

    Note: call inverse_transform_numeric first if the df was also scaled.
    """
    df = df.copy()
    for col, le in pipeline.encoders.items():
        if col in df.columns:
            # Round to nearest int to handle float values from scaling
            int_vals = df[col].round().astype(int).clip(0, len(le.classes_) - 1)
            df[col] = le.inverse_transform(int_vals)
    return df


# ── Helpers ───────────────────────────────────────────────────────────────────

def _decompose_datetime_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Decompose datetime columns into year/month/day/hour/weekday components."""
    new_cols: list[str] = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            dt = df[col]
        else:
            try:
                dt = pd.to_datetime(df[col], errors="raise")
            except Exception:
                continue

        for part in ("year", "month", "day", "hour", "weekday"):
            new_col = f"{col}_{part}"
            df[new_col] = getattr(dt.dt, part)
            new_cols.append(new_col)

        df = df.drop(columns=[col])

    return df, new_cols
