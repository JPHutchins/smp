"""Tests for user-defined inheritance of classes."""


import struct
from enum import IntEnum
from typing import Final, Type

import pytest

from smp import message as smpmsg

USER_GROUP_ID_MIN: Final = 64


def test_custom_ReadRequest() -> None:
    """Test ReadRequest inheritance."""

    class A(smpmsg.ReadRequest):
        _GROUP_ID = USER_GROUP_ID_MIN
        _COMMAND_ID = 0

    a = A()
    assert a._GROUP_ID == USER_GROUP_ID_MIN
    assert a._COMMAND_ID == 0

    class B(smpmsg.ReadRequest):
        _GROUP_ID = 65
        _COMMAND_ID = 0

    b = B()
    assert b._GROUP_ID == 65
    assert b._COMMAND_ID == 0

    class MyGroupId(IntEnum):
        C = 64
        D = 65

    class C(smpmsg.ReadRequest):
        _GROUP_ID = MyGroupId.C
        _COMMAND_ID = 0

    c = C()
    assert c._GROUP_ID == MyGroupId.C
    assert c._COMMAND_ID == 0

    class D(smpmsg.ReadRequest):
        _GROUP_ID = MyGroupId.D
        _COMMAND_ID = 0

    d = D()
    assert d._GROUP_ID == MyGroupId.D
    assert d._COMMAND_ID == 0


@pytest.mark.parametrize(
    "cls",
    [
        smpmsg.ReadRequest,
        smpmsg.WriteRequest,
        smpmsg.ReadResponse,
        smpmsg.WriteResponse,
        smpmsg.Request,
        smpmsg.Response,
    ],
)
@pytest.mark.parametrize("group_id", [USER_GROUP_ID_MIN, 0xFFFF])
@pytest.mark.parametrize("command_id", [0, 1, 0xFF])
def test_custom_message(cls: Type[smpmsg._MessageBase], group_id: int, command_id: int) -> None:
    """Test ReadRequest inheritance."""

    class CustomInts(cls):  # type: ignore
        _OP = getattr(cls, "_OP", 0)
        _GROUP_ID = group_id
        _COMMAND_ID = command_id

    m = CustomInts()
    assert m._GROUP_ID == group_id
    assert m._COMMAND_ID == command_id


def test_invalid_group_id() -> None:
    """Test invalid group_id."""

    with pytest.raises(struct.error):

        class A(smpmsg.ReadRequest):
            _GROUP_ID = 0x10000
            _COMMAND_ID = 0

        A()

    with pytest.raises(struct.error):

        class B(smpmsg.ReadRequest):
            _GROUP_ID = -1
            _COMMAND_ID = 0

        B()


def test_invalid_command_id() -> None:
    """Test invalid command_id."""

    with pytest.raises(struct.error):

        class A(smpmsg.ReadRequest):
            _GROUP_ID = USER_GROUP_ID_MIN
            _COMMAND_ID = 0x100

        A()

    with pytest.raises(struct.error):

        class B(smpmsg.ReadRequest):
            _GROUP_ID = USER_GROUP_ID_MIN
            _COMMAND_ID = -1

        B()
