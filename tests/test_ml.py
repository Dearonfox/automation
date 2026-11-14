import pandas as pd

from app.detect.ml import (
    fit_predict_isolation_forest,
    fit_predict_one_class_svm,
    fit_predict_random_forest,
)


def sample_data() -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    normal = [[float(i), float(i % 3)] for i in range(20)]
    anomalies = [[80.0, 80.0], [90.0, 90.0]]
    train = pd.DataFrame(normal + anomalies, columns=["a", "b"])
    labels = pd.Series([-1] * 20 + [1, 1], dtype="int8")
    test = pd.DataFrame([[3.0, 1.0], [100.0, 100.0]], columns=["a", "b"])
    return train, labels, test


def test_unsupervised_detectors_return_secom_labels() -> None:
    train, _, test = sample_data()
    isolation = fit_predict_isolation_forest(
        train, test, contamination=0.1, random_state=7
    )
    svm = fit_predict_one_class_svm(train, test, nu=0.1)
    assert set(isolation.predictions) <= {-1, 1}
    assert set(svm.predictions) <= {-1, 1}
    assert isolation.predictions.index.equals(test.index)


def test_supervised_detector_is_reproducible() -> None:
    train, labels, test = sample_data()
    first = fit_predict_random_forest(train, labels, test, random_state=7)
    second = fit_predict_random_forest(train, labels, test, random_state=7)
    assert first.predictions.equals(second.predictions)
    assert first.name == "RandomForest"
