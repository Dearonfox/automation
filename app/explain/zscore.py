from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SensorDeviation:
    sensor: str
    value: float
    reference_mean: float
    z_score: float


def explain_sample(
    normal_reference: pd.DataFrame, sample: pd.Series, *, top_n: int = 5
) -> list[SensorDeviation]:
    if top_n < 1:
        raise ValueError("top_n must be at least 1")
    if list(normal_reference.columns) != list(sample.index):
        raise ValueError("Sample features must match the reference feature names and order")
    if normal_reference.empty:
        raise ValueError("A normal reference is required")

    means = normal_reference.mean()
    stds = normal_reference.std(ddof=0)
    valid = stds > 0
    scores = ((sample[valid] - means[valid]) / stds[valid]).abs().sort_values(ascending=False)
    return [
        SensorDeviation(
            sensor=sensor,
            value=float(sample[sensor]),
            reference_mean=float(means[sensor]),
            z_score=float(scores[sensor]),
        )
        for sensor in scores.head(top_n).index
    ]
