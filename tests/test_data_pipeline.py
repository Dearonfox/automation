from pathlib import Path

import pandas as pd
import pytest

from app.data.loader import DatasetPaths, load_secom
from app.data.preprocessing import prepare_chronological_split


def write_fixture(tmp_path: Path) -> DatasetPaths:
    features = tmp_path / "secom.data"
    labels = tmp_path / "secom_labels.data"
    features.write_text("1 5 NaN\n2 5 4\n3 5 6\n4 5 8\n5 5 10\n", encoding="utf-8")
    labels.write_text(
        '-1 "02/01/2008 00:00:00"\n'
        '-1 "01/01/2008 00:00:00"\n'
        '1 "04/01/2008 00:00:00"\n'
        '-1 "03/01/2008 00:00:00"\n'
        '1 "05/01/2008 00:00:00"\n',
        encoding="utf-8",
    )
    return DatasetPaths(features=features, labels=labels)


def test_loads_and_sorts_by_timestamp(tmp_path: Path) -> None:
    dataset = load_secom(write_fixture(tmp_path))
    assert dataset.timestamps.is_monotonic_increasing
    assert dataset.features.iloc[0]["sensor_000"] == 2


def test_preprocessing_fits_chronological_train_only(tmp_path: Path) -> None:
    prepared = prepare_chronological_split(load_secom(write_fixture(tmp_path)))
    assert len(prepared.x_train) == 4
    assert len(prepared.x_test) == 1
    assert "sensor_001" in prepared.removed_features
    assert not prepared.x_train.isna().any().any()
    assert prepared.train_timestamps.max() < prepared.test_timestamps.min()


def test_missing_files_have_actionable_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="data/raw"):
        load_secom(DatasetPaths(tmp_path / "missing.data", tmp_path / "missing_labels.data"))


def test_labels_remain_secom_values(tmp_path: Path) -> None:
    dataset = load_secom(write_fixture(tmp_path))
    assert set(dataset.labels) == {-1, 1}
    assert pd.api.types.is_integer_dtype(dataset.labels)
