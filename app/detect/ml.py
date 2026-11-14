from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler
from sklearn.svm import OneClassSVM


@dataclass(frozen=True)
class ModelPrediction:
    name: str
    predictions: pd.Series


def fit_predict_isolation_forest(
    x_train: pd.DataFrame,
    x_test: pd.DataFrame,
    *,
    contamination: float = 0.07,
    random_state: int = 42,
) -> ModelPrediction:
    model = IsolationForest(
        n_estimators=300,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(x_train)
    raw = model.predict(x_test)
    return ModelPrediction("IsolationForest", _to_secom_labels(raw, x_test.index))


def fit_predict_one_class_svm(
    x_train: pd.DataFrame,
    x_test: pd.DataFrame,
    *,
    nu: float = 0.07,
) -> ModelPrediction:
    model = Pipeline(
        [
            ("scale", RobustScaler()),
            ("model", OneClassSVM(kernel="rbf", gamma="scale", nu=nu)),
        ]
    )
    model.fit(x_train)
    raw = model.predict(x_test)
    return ModelPrediction("OneClassSVM", _to_secom_labels(raw, x_test.index))


def fit_predict_random_forest(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_test: pd.DataFrame,
    *,
    random_state: int = 42,
) -> ModelPrediction:
    split_at = int(len(x_train) * 0.8)
    while split_at < len(x_train) - 1 and y_train.iloc[:split_at].nunique() < 2:
        split_at += 1
    if split_at <= 0 or split_at >= len(x_train):
        raise ValueError("Training data is too small for chronological threshold calibration")
    calibration_model = _random_forest(random_state)
    calibration_model.fit(x_train.iloc[:split_at], y_train.iloc[:split_at])
    positive_index = list(calibration_model.classes_).index(1)
    validation_probabilities = calibration_model.predict_proba(x_train.iloc[split_at:])[
        :, positive_index
    ]
    threshold = _best_f1_threshold(y_train.iloc[split_at:], validation_probabilities)

    model = _random_forest(random_state)
    model.fit(x_train, y_train)
    positive_index = list(model.classes_).index(1)
    probabilities = model.predict_proba(x_test)[:, positive_index]
    predictions = pd.Series(
        np.where(probabilities >= threshold, 1, -1),
        index=x_test.index,
        name="prediction",
        dtype="int8",
    )
    return ModelPrediction("RandomForest", predictions)


def _random_forest(random_state: int) -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=400,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=random_state,
        n_jobs=-1,
    )


def _best_f1_threshold(y_true: pd.Series, probabilities: np.ndarray) -> float:
    if not (y_true == 1).any():
        return 0.5
    candidates = np.unique(probabilities)
    scores = [f1_score(y_true, np.where(probabilities >= value, 1, -1)) for value in candidates]
    return float(candidates[int(np.argmax(scores))])


def _to_secom_labels(raw: np.ndarray, index: pd.Index) -> pd.Series:
    values = np.where(raw == -1, 1, -1)
    return pd.Series(values, index=index, name="prediction", dtype="int8")
