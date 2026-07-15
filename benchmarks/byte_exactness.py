"""Prove the msgspec PoC is byte-identical to the locked binary regressions.

Mirrors ``tests/binary_regressions/test_binary_lock.py`` but drives the new
``Frame``/``Data`` API: build the payload from the record's kwargs, wrap it in a
``Frame`` with the record's version + sequence, and assert the serialized bytes
match the locked value. Also round-trips via ``loads``.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple

import msgspec

if TYPE_CHECKING:
    from smp.message import Data, Frame

_RECORDS = Path("tests", "binary_regressions", "records")


class Record(NamedTuple):
    message: str
    version: int
    sequence: int
    kwargs: dict[str, Any]
    bytes: str


def load_records(prefix: str) -> list[Record]:
    return [
        Record(**json.loads(line))
        for file in sorted(_RECORDS.glob(f"{prefix}*.json"))
        for line in file.read_text().splitlines()
    ]


def import_class(path: str) -> type[Data]:
    module_path, class_name = path.rsplit(".", 1)
    return getattr(importlib.import_module(module_path), class_name)


def fixup(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Apply the same hex->bytes coercions as the regression test."""
    out = dict(kwargs)
    for key in ("data", "sha", "val"):
        if isinstance(out.get(key), str):
            out[key] = bytes.fromhex(out[key])
    if "images" in out:
        out["images"] = [
            {**img, **({"hash": b"A"} if "hash" in img else {})} for img in out["images"]
        ]
    return out


def check(record: Record) -> tuple[bool, bool]:
    cls = import_class(record.message)
    payload = msgspec.convert(fixup(record.kwargs), type=cls)
    frame: Frame[Data] = payload.to_frame(version=record.version, sequence=record.sequence)
    serialized_ok = bytes(frame) == bytes.fromhex(record.bytes)
    roundtrip_ok = cls.loads(bytes.fromhex(record.bytes)).data == payload
    return serialized_ok, roundtrip_ok


def main() -> None:
    prefix = sys.argv[1] if len(sys.argv) > 1 else "smp.image_management"
    records = load_records(prefix)
    outcomes = [(r, *check(r)) for r in records]
    ser_fail = [r for r, ser, _ in outcomes if not ser]
    rt_fail = [r for r, _, rt in outcomes if not rt]
    print(f"{prefix}: {len(records)} records")
    print(f"  serialize byte-identical:   {len(records) - len(ser_fail)}/{len(records)}")
    print(f"  deserialize round-trip:     {len(records) - len(rt_fail)}/{len(records)}")
    for r in (ser_fail + rt_fail)[:5]:
        print(f"  FAIL {r.message} seq={r.sequence} kwargs={r.kwargs}")
    raise SystemExit(1 if ser_fail or rt_fail else 0)


if __name__ == "__main__":
    main()
