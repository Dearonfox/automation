import argparse
import json
from pathlib import Path

from app.data.loader import load_secom
from app.data.preprocessing import prepare_chronological_split


def build_summary() -> dict[str, object]:
    dataset = load_secom()
    prepared = prepare_chronological_split(dataset)
    return {
        "rows": len(dataset.features),
        "raw_features": dataset.features.shape[1],
        "retained_features": prepared.x_train.shape[1],
        "removed_low_variance_or_empty_features": len(prepared.removed_features),
        "missing_values": int(dataset.features.isna().sum().sum()),
        "anomaly_rows": int((dataset.labels == 1).sum()),
        "normal_rows": int((dataset.labels == -1).sum()),
        "train_rows": len(prepared.x_train),
        "test_rows": len(prepared.x_test),
        "train_start": prepared.train_timestamps.iloc[0].isoformat(),
        "train_end": prepared.train_timestamps.iloc[-1].isoformat(),
        "test_start": prepared.test_timestamps.iloc[0].isoformat(),
        "test_end": prepared.test_timestamps.iloc[-1].isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a reproducible SECOM EDA summary")
    parser.add_argument("--output", type=Path, default=Path("artifacts/eda_summary.json"))
    args = parser.parse_args()
    summary = build_summary()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
