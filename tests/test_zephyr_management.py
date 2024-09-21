"""Test the SMP Zephyr Management group."""

from __future__ import annotations

from typing import Any, Dict, Type, TypeVar

import cbor2

from smp import header as smphdr
from smp import message as smpmsg
from smp import zephyr_management as smpz
from tests.helpers import make_assert_header

zephyrcmd = smphdr.CommandId.ZephyrManagement

T = TypeVar("T", bound=smpmsg._MessageBase)


def _do_test(
    msg: Type[T],
    op: smphdr.OP,
    command_id: smphdr.CommandId.ZephyrManagement,
    data: Dict[str, Any],
) -> T:
    cbor = cbor2.dumps(data)
    assert_header = make_assert_header(smphdr.GroupId.ZEPHYR_MANAGEMENT, op, command_id, len(cbor))

    def _assert_common(r: smpmsg._MessageBase) -> None:
        assert_header(r)
        for k, v in data.items():
            assert v == getattr(r, k)
        assert cbor == r.BYTES[8:]

    r = msg(**data)

    _assert_common(r)  # serialize
    _assert_common(msg.loads(r.BYTES))  # deserialize

    return r


def test_EraseStorageRequest() -> None:
    _do_test(
        smpz.EraseStorageRequest,
        smphdr.OP.WRITE,
        zephyrcmd.ERASE_STORAGE,
        {},
    )


def test_EraseStorageResponse() -> None:
    _do_test(
        smpz.EraseStorageResponse,
        smphdr.OP.WRITE_RSP,
        zephyrcmd.ERASE_STORAGE,
        {},
    )
