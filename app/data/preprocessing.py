from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer

from app.data.loader import SecomDataset


@dataclass(frozen=True)
class PreparedData:
    x_train: pd.DataFrame
    x_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    train_timestamps: pd.Series
    test_timestamps: pd.Series
    removed_features: tuple[str, ...]


def prepare_chronological_split(
    dataset: SecomDataset,
    *,
    train_fraction: float = 0.8,
    variance_threshold: float = 1e-12,
) -> PreparedData:
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    split_at = int(len(dataset.features) * train_fraction)
    if split_at <= 0 or split_at >= len(dataset.features):
        raise ValueError("Dataset is too small for the requested split")

    raw_train = dataset.features.iloc[:split_at].copy()
    raw_test = dataset.features.iloc[split_at:].copy()
    train_variances = raw_train.var(skipna=True)
    keep_mask = train_variances.notna() & (train_variances > variance_threshold)
    kept = train_variances.index[keep_mask].tolist()
    removed = tuple(train_variances.index[~keep_mask].tolist())
    if not kept:
        raise ValueError("No features remain after variance filtering")

    imputer = SimpleImputer(strategy="median")
    train_values = imputer.fit_transform(raw_train[kept])
    test_values = imputer.transform(raw_test[kept])
    if not np.isfinite(train_values).all() or not np.isfinite(test_values).all():
        raise ValueError("Preprocessing produced non-finite values")

    return PreparedData(
        x_train=pd.DataFrame(train_values, columns=kept, index=raw_train.index),
        x_test=pd.DataFrame(test_values, columns=kept, index=raw_test.index),
        y_train=dataset.labels.iloc[:split_at].copy(),
        y_test=dataset.labels.iloc[split_at:].copy(),
        train_timestamps=dataset.timestamps.iloc[:split_at].copy(),
        test_timestamps=dataset.timestamps.iloc[split_at:].copy(),
        removed_features=removed,
    )
