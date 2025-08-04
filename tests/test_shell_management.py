"""Test the SMP Shell Management group."""

from __future__ import annotations

from smp import header as smphdr
from smp import shell_management as smpshell
from tests.helpers import make_do_test

shellcmd = smphdr.CommandId.ShellManagement


_do_test = make_do_test(smphdr.GroupId.SHELL_MANAGEMENT)


def test_ExecuteRequest() -> None:
    r = _do_test(
        smpshell.ExecuteRequest,
        smphdr.OP.WRITE,
        shellcmd.EXECUTE,
        {"argv": ["echo", "Hello"]},
    )
    assert r.argv == ["echo", "Hello"]


def test_ExecuteResponse() -> None:
    r = _do_test(
        smpshell.ExecuteResponse,
        smphdr.OP.WRITE_RSP,
        shellcmd.EXECUTE,
        {"o": "Hello", "ret": 0},
    )
    assert r.o == "Hello"
    assert r.ret == 0
