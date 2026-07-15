"""Test the SMP Shell Management group."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

import cbor2

from smp import header as smphdr
from smp import message as smpmsg
from smp import shell_management as smpshell
from tests.helpers import make_assert_header

if TYPE_CHECKING:
    from pydantic import BaseModel

shellcmd = smphdr.CommandId.ShellManagement


T = TypeVar("T", bound=smpmsg._MessageBase)


def _do_test(
    msg: type[T],
    op: smphdr.OP,
    command_id: smphdr.CommandId.ShellManagement,
    data: dict[str, Any],
    nested_model: type[BaseModel] | None = None,
) -> T:
    cbor = cbor2.dumps(data, canonical=True)
    assert_header = make_assert_header(smphdr.GroupId.SHELL_MANAGEMENT, op, command_id, len(cbor))

    def _assert_common(r: smpmsg._MessageBase) -> None:
        assert_header(r)
        for k, v in data.items():
            if type(v) is dict and nested_model is not None:
                for k2, v2 in v.items():
                    one_deep = getattr(r, k)
                    assert isinstance(one_deep[k2], nested_model)
                    assert v2 == one_deep[k2].model_dump()
            else:
                assert v == getattr(r, k)
        assert cbor == r.BYTES[8:]

    r = msg(**data)

    _assert_common(r)  # serialize
    _assert_common(msg.loads(r.BYTES))  # deserialize

    return r


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
