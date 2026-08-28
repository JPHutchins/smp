from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from smp import header as smpheader
from smp import message as smpmessage

if TYPE_CHECKING:
    from types_bits import u8

T = TypeVar("T", bound=smpmessage.Data)


def assert_frame(
    data: T,
    *,
    op: smpheader.OP,
    group_id: smpheader.GroupIdField,
    command_id: smpheader.AnyCommandId,
    length: int | None = None,
    version: smpheader.Version = smpheader.Version.V2,
    flags: smpheader.Flag = smpheader.Flag.UNUSED,
    sequence: u8 = 0,
) -> smpmessage.Frame[T]:
    """Assert `data`'s header and a byte-exact round-trip; returns the decoded Frame."""
    frame = data.to_frame(version=version, flags=flags, sequence=sequence)
    header = frame.header
    assert header.op == op
    assert header.version == version
    assert header.flags == flags
    assert header.group_id == group_id
    assert header.command_id == command_id
    assert header.sequence == sequence
    assert 0 <= header.length <= 0xFFFF
    if length is not None:
        assert header.length == length

    wire = bytes(frame)
    assert wire[: smpheader.Header.SIZE] == bytes(header)

    decoded = type(data).loads(wire)
    assert decoded == frame
    return decoded
