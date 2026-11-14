import argparse
import json
from pathlib import Path

import pandas as pd

from app.data import load_secom, prepare_chronological_split
from app.detect import (
    SPCDetector,
    fit_predict_isolation_forest,
    fit_predict_one_class_svm,
    fit_predict_random_forest,
)
from app.evaluation.metrics import evaluate_predictions


def run_comparison() -> list[dict[str, float | int | str]]:
    prepared = prepare_chronological_split(load_secom())
    spc = SPCDetector().fit(prepared.x_train, prepared.y_train).predict(prepared.x_test)
    predictions = [
        ("SPC", spc.predictions),
        (
            "IsolationForest",
            fit_predict_isolation_forest(prepared.x_train, prepared.x_test).predictions,
        ),
        (
            "OneClassSVM",
            fit_predict_one_class_svm(prepared.x_train, prepared.x_test).predictions,
        ),
        (
            "RandomForest",
            fit_predict_random_forest(
                prepared.x_train, prepared.y_train, prepared.x_test
            ).predictions,
        ),
    ]
    rows: list[dict[str, float | int | str]] = []
    for name, predicted in predictions:
        metrics = evaluate_predictions(prepared.y_test, predicted)
        rows.append(
            {
                "model": name,
                **metrics.as_dict(),
                "predicted_anomalies": int((predicted == 1).sum()),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare SPC and ML detectors on SECOM")
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/model_comparison.json")
    )
    args = parser.parse_args()
    rows = run_comparison()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    columns = ["model", "precision", "recall", "f1", "false_positive_rate"]
    print(pd.DataFrame(rows)[columns].to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print(f"\nSaved: {args.output}")


if __name__ == "__main__":
    main()
