from __future__ import annotations

from typing import TYPE_CHECKING, Any

import cbor2

from smp import header as smpheader

if TYPE_CHECKING:
    from collections.abc import Callable

    from smp.message import _MessageBase


def make_assert_header(
    group_id: smpheader.GroupId | smpheader.UserGroupId,
    op: smpheader.OP,
    command_id: smpheader.AnyCommandId,
    length: int | None,
) -> Callable[[_MessageBase], None]:
    """Return an `assert_header` function."""

    def f(
        r: _MessageBase,
    ) -> None:
        h = r.header
        assert op == h.op
        assert h.version == smpheader.Version.V2
        assert h.flags == 0
        if length is not None:
            assert length == h.length
        else:
            assert 0 <= h.length <= 0xFFFF
        assert group_id == h.group_id
        assert 0 <= h.sequence <= 0xFF
        assert command_id == h.command_id

        assert bytes(r) == r.BYTES

    return f


def make_frame(
    group_id: smpheader.GroupIdField,
    op: smpheader.OP,
    command_id: smpheader.AnyCommandId,
    payload: dict[str, Any],
) -> bytes:
    """Return an SMP frame carrying `payload` as canonical CBOR."""
    d = cbor2.dumps(payload, canonical=True)
    return (
        smpheader.Header(
            op=op,
            version=smpheader.Version.V2,
            flags=smpheader.Flag(0),
            length=len(d),
            group_id=group_id,
            sequence=0,
            command_id=command_id,
        ).BYTES
        + d
    )
