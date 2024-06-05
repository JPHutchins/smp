from __future__ import annotations

from typing import Callable

from smp import header as smpheader
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
        assert smpheader.Version.V2 == h.version
        assert 0 == h.flags
        if length is not None:
            assert length == h.length
        else:
            assert 0 <= h.length <= 0xFFFF
        assert group_id == h.group_id
        assert 0 <= h.sequence <= 0xFF
        assert command_id == h.command_id

        assert r.BYTES == bytes(r)

    return f
