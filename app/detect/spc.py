from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SPCResult:
    predictions: pd.Series
    violation_counts: pd.Series
    violations: pd.DataFrame


class SPCDetector:
    """Per-sensor Shewhart-style limits fitted from known-normal training rows."""

    def __init__(self, sigma: float = 3.0, min_violations: int = 1) -> None:
        if sigma <= 0:
            raise ValueError("sigma must be positive")
        if min_violations < 1:
            raise ValueError("min_violations must be at least 1")
        self.sigma = sigma
        self.min_violations = min_violations
        self.mean_: pd.Series | None = None
        self.std_: pd.Series | None = None
        self.lower_: pd.Series | None = None
        self.upper_: pd.Series | None = None

    def fit(self, features: pd.DataFrame, labels: pd.Series | None = None) -> "SPCDetector":
        reference = features
        if labels is not None:
            if len(features) != len(labels):
                raise ValueError("features and labels must have the same row count")
            reference = features.loc[labels.to_numpy() == -1]
        if reference.empty:
            raise ValueError("SPC fitting requires at least one normal reference row")

        means = reference.mean()
        stds = reference.std(ddof=0)
        valid = stds.notna() & (stds > 0)
        if not valid.all():
            invalid = stds.index[~valid].tolist()
            raise ValueError(f"SPC received constant or invalid features: {invalid}")
        self.mean_ = means
        self.std_ = stds
        self.lower_ = means - self.sigma * stds
        self.upper_ = means + self.sigma * stds
        return self

    def predict(self, features: pd.DataFrame) -> SPCResult:
        if self.lower_ is None or self.upper_ is None:
            raise RuntimeError("SPCDetector must be fitted before prediction")
        expected = list(self.lower_.index)
        if list(features.columns) != expected:
            raise ValueError("Prediction features must match fitted feature names and order")

        violations = features.lt(self.lower_, axis="columns") | features.gt(
            self.upper_, axis="columns"
        )
        counts = violations.sum(axis=1)
        predictions = pd.Series(
            np.where(counts >= self.min_violations, 1, -1),
            index=features.index,
            name="prediction",
            dtype="int8",
        )
        return SPCResult(predictions=predictions, violation_counts=counts, violations=violations)
