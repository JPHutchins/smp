"""This tests locked de/serializations."""

import importlib
import json
from pathlib import Path
from typing import Any, Final, List, NamedTuple

import pytest

import smp.message as smpmsg
from smp.file_management import FileHashChecksumResponse


class Record(NamedTuple):
    message: str
    version: int
    sequence: int
    kwargs: dict
    bytes: str


records: Final[List[Record]] = []
for file in list(Path("tests", "binary_regressions", "records").rglob("*.json")):
    with open(file) as f:
        records.extend(map(lambda x: Record(**json.loads(x)), f.readlines()))


def import_class(full_class_path: str) -> smpmsg.SMPData:
    module_path, class_name = full_class_path.rsplit('.', 1)
    return getattr(importlib.import_module(module_path), class_name)


def compare_values(expected: Any, actual: Any) -> None:
    """Recursively compare expected and actual values."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            actual = actual.model_dump()
        for k, v in expected.items():
            assert k in actual, f"Key {k} not found in actual"
            compare_values(v, actual[k])
    elif isinstance(expected, (list, tuple)):
        assert len(expected) == len(
            actual
        ), f"Expected list of length {len(expected)}, got {len(actual)}"
        for e, a in zip(expected, actual):
            compare_values(e, a)
    else:
        assert expected == actual, f"Expected {expected}, got {actual}"


@pytest.mark.parametrize("record", records)
def test_binary_lock(record: Record) -> None:
    cls: Final = import_class(record.message)

    if "data" in record.kwargs:
        record.kwargs["data"] = bytes.fromhex(record.kwargs["data"])
    if "images" in record.kwargs:
        for image in record.kwargs["images"]:
            if "hash" in image:
                image["hash"] = b"A"
    if "sha" in record.kwargs:
        record.kwargs["sha"] = bytes.fromhex(record.kwargs["sha"])
    if "val" in record.kwargs:
        record.kwargs["val"] = bytes.fromhex(record.kwargs["val"])
    if (
        cls is FileHashChecksumResponse
        and "output" in record.kwargs
        and isinstance(record.kwargs["output"], str)
    ):
        record.kwargs["output"] = bytes.fromhex(record.kwargs["output"])

    # Test serialization match
    serialized_message = cls(**record.kwargs).to_frame(version=record.version, sequence=record.sequence)  # type: ignore # noqa
    assert bytes(serialized_message) == bytes.fromhex(record.bytes)

    # Test deserialization match
    deserialized_message = cls.loads(bytes.fromhex(record.bytes))

    assert serialized_message == deserialized_message

    for k, v in record.kwargs.items():
        actual_value: Any = getattr(deserialized_message.smp_data, k)
        compare_values(v, actual_value)
