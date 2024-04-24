"""Tests for user-defined inheritance of classes."""


import struct
from typing import Final, Type

import pytest

from smp import header as smphdr
from smp import message as smpmsg

GROUP_ID_THAT_IS_NOT_IN_GROUP_ID_ENUM: Final = 65
assert GROUP_ID_THAT_IS_NOT_IN_GROUP_ID_ENUM not in list(smphdr.GroupId)


def test_custom_ReadRequest() -> None:
    """Test ReadRequest inheritance."""

    class CustomInts(smpmsg.ReadRequest):
        _GROUP_ID = GROUP_ID_THAT_IS_NOT_IN_GROUP_ID_ENUM
        _COMMAND_ID = 0

    m = CustomInts()
    assert m._GROUP_ID == GROUP_ID_THAT_IS_NOT_IN_GROUP_ID_ENUM
    assert m._COMMAND_ID == 0


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
@pytest.mark.parametrize("group_id", [GROUP_ID_THAT_IS_NOT_IN_GROUP_ID_ENUM, 0xFFFF])
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
            _GROUP_ID = GROUP_ID_THAT_IS_NOT_IN_GROUP_ID_ENUM
            _COMMAND_ID = 0x100

        A()

    with pytest.raises(struct.error):

        class B(smpmsg.ReadRequest):
            _GROUP_ID = GROUP_ID_THAT_IS_NOT_IN_GROUP_ID_ENUM
            _COMMAND_ID = -1

        B()
