import argparse
import json
from pathlib import Path

from app.data import load_secom, prepare_chronological_split
from app.detect import SPCDetector
from app.evaluation.metrics import evaluate_predictions


def run_baseline(*, sigma: float = 3.0, min_violations: int = 1) -> dict[str, object]:
    prepared = prepare_chronological_split(load_secom())
    detector = SPCDetector(sigma=sigma, min_violations=min_violations)
    detector.fit(prepared.x_train, prepared.y_train)
    result = detector.predict(prepared.x_test)
    metrics = evaluate_predictions(prepared.y_test, result.predictions)
    return {
        "model": "SPC",
        "rule": f"any {min_violations}+ sensor(s) outside mean +/- {sigma:g} sigma",
        "fit_rows": int((prepared.y_train == -1).sum()),
        "test_rows": len(prepared.y_test),
        "predicted_anomalies": int((result.predictions == 1).sum()),
        **metrics.as_dict(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the SPC baseline on SECOM")
    parser.add_argument("--sigma", type=float, default=3.0)
    parser.add_argument("--min-violations", type=int, default=1)
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/spc_baseline_metrics.json")
    )
    args = parser.parse_args()
    result = run_baseline(sigma=args.sigma, min_violations=args.min_violations)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
