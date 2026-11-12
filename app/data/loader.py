from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class DatasetPaths:
    features: Path = Path("data/raw/secom.data")
    labels: Path = Path("data/raw/secom_labels.data")

    def validate(self) -> None:
        missing = [str(path) for path in (self.features, self.labels) if not path.is_file()]
        if missing:
            expected = ", ".join(missing)
            raise FileNotFoundError(
                f"Missing UCI SECOM file(s): {expected}. "
                "Place secom.data and secom_labels.data in data/raw/."
            )


@dataclass(frozen=True)
class SecomDataset:
    features: pd.DataFrame
    labels: pd.Series
    timestamps: pd.Series


def load_secom(paths: DatasetPaths | None = None) -> SecomDataset:
    resolved = paths or DatasetPaths()
    resolved.validate()
    features = pd.read_csv(resolved.features, sep=r"\s+", header=None, na_values="NaN")
    features.columns = [f"sensor_{index:03d}" for index in range(features.shape[1])]
    label_frame = pd.read_csv(
        resolved.labels, sep=r"\s+", header=None, names=["label", "timestamp"]
    )
    if len(features) != len(label_frame):
        raise ValueError("Feature and label files contain different row counts")

    timestamps = pd.to_datetime(label_frame["timestamp"], dayfirst=True, errors="raise")
    labels = label_frame["label"].astype("int8")
    order = timestamps.argsort(kind="stable")
    return SecomDataset(
        features=features.iloc[order].reset_index(drop=True),
        labels=labels.iloc[order].reset_index(drop=True),
        timestamps=timestamps.iloc[order].reset_index(drop=True),
    )
