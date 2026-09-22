"""Test the SMP Shell Management group."""

from __future__ import annotations

from smp import header as smphdr
from smp import shell_management as smpshell
from tests.helpers import assert_frame

shellcmd = smphdr.CommandId.ShellManagement


def test_ExecuteRequest() -> None:
    frame = assert_frame(
        smpshell.ExecuteRequest(argv=["echo", "Hello"]),
        op=smphdr.OP.WRITE,
        group_id=smphdr.GroupId.SHELL_MANAGEMENT,
        command_id=shellcmd.EXECUTE,
    )
    assert frame.data.argv == ["echo", "Hello"]


def test_ExecuteResponse() -> None:
    frame = assert_frame(
        smpshell.ExecuteResponse(o="Hello", ret=0),
        op=smphdr.OP.WRITE_RSP,
        group_id=smphdr.GroupId.SHELL_MANAGEMENT,
        command_id=shellcmd.EXECUTE,
    )
    assert frame.data.o == "Hello"
    assert frame.data.ret == 0
