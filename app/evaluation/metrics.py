from dataclasses import asdict, dataclass

import pandas as pd
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support


@dataclass(frozen=True)
class DetectionMetrics:
    precision: float
    recall: float
    f1: float
    false_positive_rate: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int

    def as_dict(self) -> dict[str, float | int]:
        return asdict(self)


def evaluate_predictions(y_true: pd.Series, y_pred: pd.Series) -> DetectionMetrics:
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same row count")
    invalid = (set(y_true) | set(y_pred)) - {-1, 1}
    if invalid:
        raise ValueError(f"Labels must use SECOM values -1 and 1; received {sorted(invalid)}")

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=[1], average=None, zero_division=0
    )
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[-1, 1]).ravel()
    false_positive_rate = float(fp / (fp + tn)) if fp + tn else 0.0
    return DetectionMetrics(
        precision=float(precision[0]),
        recall=float(recall[0]),
        f1=float(f1[0]),
        false_positive_rate=false_positive_rate,
        true_positives=int(tp),
        false_positives=int(fp),
        true_negatives=int(tn),
        false_negatives=int(fn),
    )
