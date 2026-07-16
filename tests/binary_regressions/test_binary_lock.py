"""This tests locked de/serializations."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, NamedTuple

import pytest

from smp import header

if TYPE_CHECKING:
    from smp.message import Data

pytestmark = pytest.mark.slow


class Record(NamedTuple):
    message: str
    version: int
    sequence: int
    kwargs: dict[str, Any]
    bytes: str


records: Final[list[Record]] = [
    Record(**json.loads(line))
    for file in Path("tests", "binary_regressions", "records").rglob("*.json")
    for line in file.read_text().splitlines()
]


def import_class(full_class_path: str) -> type[Data]:
    module_path, class_name = full_class_path.rsplit(".", 1)
    return getattr(importlib.import_module(module_path), class_name)


def fixup(kwargs: dict[str, Any], message: str) -> dict[str, Any]:
    out = dict(kwargs)
    for key in ("data", "sha", "val"):
        if isinstance(out.get(key), str):
            out[key] = bytes.fromhex(out[key])
    if message.endswith("FileHashChecksumResponse") and isinstance(out.get("output"), str):
        out["output"] = bytes.fromhex(out["output"])
    if "images" in out:
        out["images"] = [
            {**image, **({"hash": b"A"} if "hash" in image else {})} for image in out["images"]
        ]
    return out


@pytest.mark.parametrize("record", records)
def test_binary_lock(record: Record) -> None:
    cls = import_class(record.message)
    frame = cls._convert_mapping(fixup(record.kwargs, record.message)).to_frame(
        version=header.Version(record.version), sequence=record.sequence
    )
    assert bytes(frame) == bytes.fromhex(record.bytes)
    assert cls.loads(bytes.fromhex(record.bytes)) == frame
