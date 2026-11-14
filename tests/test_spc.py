import pandas as pd
import pytest

from app.detect import SPCDetector
from app.evaluation import evaluate_predictions


def test_spc_fits_normal_rows_and_flags_limit_violation() -> None:
    features = pd.DataFrame({"sensor_a": [0.0, 1.0, 2.0, 100.0], "sensor_b": [4, 5, 6, 7]})
    labels = pd.Series([-1, -1, -1, 1])
    detector = SPCDetector(sigma=3).fit(features, labels)

    result = detector.predict(pd.DataFrame({"sensor_a": [1.0, 20.0], "sensor_b": [5, 5]}))

    assert result.predictions.tolist() == [-1, 1]
    assert result.violation_counts.tolist() == [0, 1]
    assert detector.mean_["sensor_a"] == pytest.approx(1.0)


def test_spc_requires_fit_and_matching_columns() -> None:
    with pytest.raises(RuntimeError, match="fitted"):
        SPCDetector().predict(pd.DataFrame({"a": [1.0]}))

    detector = SPCDetector().fit(pd.DataFrame({"a": [1.0, 2.0]}))
    with pytest.raises(ValueError, match="match"):
        detector.predict(pd.DataFrame({"b": [1.0]}))


def test_detection_metrics_include_false_positive_rate() -> None:
    metrics = evaluate_predictions(
        pd.Series([-1, -1, 1, 1]),
        pd.Series([-1, 1, 1, -1]),
    )
    assert metrics.precision == pytest.approx(0.5)
    assert metrics.recall == pytest.approx(0.5)
    assert metrics.f1 == pytest.approx(0.5)
    assert metrics.false_positive_rate == pytest.approx(0.5)
    assert (metrics.true_positives, metrics.false_positives) == (1, 1)
