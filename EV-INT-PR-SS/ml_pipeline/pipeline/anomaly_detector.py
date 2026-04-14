"""Anomaly detection via Autoencoder — Requirements 6.1, 6.2, 6.3, 6.4."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ANOMALY_PERCENTILE = 95  # Requirement 6.2: flag records above 95th percentile


@dataclass
class AnomalyReport:
    anomaly_indices: list[int]
    reconstruction_errors: list[float]
    threshold: float
    anomaly_count: int
    anomaly_pct: float


class AutoencoderDetector:
    """Keras Autoencoder for anomaly detection.

    Requirements 6.1, 6.2, 6.3, 6.4
    """

    def __init__(self, encoding_dim: int = 8, epochs: int = 50, batch_size: int = 32):
        self.encoding_dim = encoding_dim
        self.epochs = epochs
        self.batch_size = batch_size
        self._model = None
        self._threshold: Optional[float] = None
        self._input_dim: Optional[int] = None

    def _build_model(self, input_dim: int):
        """Build encoder-decoder architecture."""
        try:
            import tensorflow as tf
            from tensorflow import keras

            inputs = keras.Input(shape=(input_dim,))
            # Encoder
            enc = keras.layers.Dense(max(self.encoding_dim * 2, 4), activation="relu")(inputs)
            enc = keras.layers.Dense(max(self.encoding_dim, 2), activation="relu")(enc)
            # Decoder
            dec = keras.layers.Dense(max(self.encoding_dim * 2, 4), activation="relu")(enc)
            outputs = keras.layers.Dense(input_dim, activation="linear")(dec)

            model = keras.Model(inputs, outputs)
            model.compile(optimizer="adam", loss="mse")
            return model
        except ImportError:
            logger.warning("TensorFlow not available; using numpy-based fallback autoencoder")
            return None

    def fit(self, df: pd.DataFrame) -> "AutoencoderDetector":
        """Train the autoencoder on clean data. Requirement 6.1."""
        X = self._preprocess(df)
        self._input_dim = X.shape[1]

        model = self._build_model(self._input_dim)
        if model is not None:
            model.fit(
                X, X,
                epochs=self.epochs,
                batch_size=self.batch_size,
                validation_split=0.1,
                verbose=0,
            )
            self._model = model
        else:
            # Fallback: store mean for trivial reconstruction
            self._mean = X.mean(axis=0)

        # Compute threshold on training data
        errors = self._reconstruction_errors(X)
        self._threshold = float(np.percentile(errors, ANOMALY_PERCENTILE))
        logger.info("Autoencoder trained. Threshold (p%d): %.6f", ANOMALY_PERCENTILE, self._threshold)
        return self

    def predict(self, df: pd.DataFrame) -> AnomalyReport:
        """Flag records with reconstruction error above threshold. Requirement 6.2."""
        if self._threshold is None:
            raise RuntimeError("Call fit() before predict()")

        X = self._preprocess(df)
        errors = self._reconstruction_errors(X)
        anomaly_mask = errors > self._threshold
        anomaly_indices = list(np.where(anomaly_mask)[0])

        return AnomalyReport(
            anomaly_indices=anomaly_indices,
            reconstruction_errors=errors.tolist(),
            threshold=self._threshold,
            anomaly_count=len(anomaly_indices),
            anomaly_pct=round(len(anomaly_indices) / len(df) * 100, 4),
        )

    def retrain(self, df: pd.DataFrame) -> "AutoencoderDetector":
        """Retrain on new data. Requirement 6.4."""
        self._model = None
        self._threshold = None
        return self.fit(df)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _preprocess(self, df: pd.DataFrame) -> np.ndarray:
        """Select numeric columns, fill NaN with column mean, return numpy array."""
        numeric = df.select_dtypes(include=[np.number])
        if numeric.empty:
            raise ValueError("No numeric columns found for anomaly detection")
        filled = numeric.fillna(numeric.mean())
        # Normalize to [0, 1] per column
        col_min = filled.min()
        col_max = filled.max()
        denom = (col_max - col_min).replace(0, 1)
        normalized = (filled - col_min) / denom
        return normalized.values.astype(np.float32)

    def _reconstruction_errors(self, X: np.ndarray) -> np.ndarray:
        """Compute per-record MSE reconstruction error."""
        if self._model is not None:
            X_pred = self._model.predict(X, verbose=0)
        else:
            # Fallback: reconstruct with mean
            X_pred = np.tile(self._mean, (len(X), 1))
        return np.mean((X - X_pred) ** 2, axis=1)
