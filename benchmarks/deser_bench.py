"""Serialize/deserialize microbenchmark for the image_management group.

Measures the end-to-end user operations that both the pydantic ("before") and
the msgspec ("after") APIs support:

- serialize:   kwargs -> SMP wire bytes (header + canonical CBOR)
- deserialize: SMP wire bytes -> validated message object

The script auto-detects the API: the msgspec rework exposes ``smp.message.Frame``.
"""

from __future__ import annotations

import timeit
from typing import TYPE_CHECKING, Any

from smp import header as smpheader
from smp import image_management as smpimg
from smp import message as smpmsg

if TYPE_CHECKING:
    from collections.abc import Callable

_AFTER = hasattr(smpmsg, "Frame")

CASES: tuple[tuple[str, type, dict[str, Any]], ...] = (
    (
        "ImageStatesReadResponse(2 images)",
        smpimg.ImageStatesReadResponse,
        {
            "images": [
                {
                    "slot": 0,
                    "version": "0.1.0",
                    "image": 0,
                    "hash": b"A",
                    "bootable": True,
                    "pending": True,
                    "confirmed": True,
                    "active": True,
                    "permanent": True,
                }
            ]
            * 2,
            "splitStatus": 0,
        },
    ),
    (
        "ImageUploadWriteRequest(1KiB)",
        smpimg.ImageUploadWriteRequest,
        {
            "off": 0,
            "data": b"\xa5" * 1024,
            "image": 1,
            "len": 1024,
            "sha": b"\xde" * 32,
            "upgrade": True,
        },
    ),
)


def serialize(cls: type, kwargs: dict[str, Any]) -> bytes:
    if _AFTER:
        return bytes(cls(**kwargs).to_frame(version=smpheader.Version.V2, sequence=0))
    return bytes(cls(version=smpheader.Version.V2, sequence=0, **kwargs))


def _bench(fn: Callable[[], object], number: int, repeat: int = 7) -> float:
    best = min(timeit.repeat(fn, number=number, repeat=repeat))
    return best / number * 1e6  # microseconds per op


def main() -> None:
    print(f"API: {'msgspec (after)' if _AFTER else 'pydantic (before)'}")
    for name, cls, kwargs in CASES:
        wire = serialize(cls, kwargs)
        ser_us = _bench(lambda cls=cls, kw=kwargs: serialize(cls, kw), number=2000)
        deser_us = _bench(lambda cls=cls, w=wire: cls.loads(w), number=2000)
        print(
            f"  {name:36s}  serialize={ser_us:7.2f}us  deserialize={deser_us:7.2f}us  ({len(wire)}B)"
        )


if __name__ == "__main__":
    main()
