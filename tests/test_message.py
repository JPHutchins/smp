"""Tests for user-defined inheritance of classes."""

import struct
from enum import IntEnum
from typing import Final

import pytest

from smp import header as smphdr
from smp import image_management as smpimg
from smp import message as smpmsg
from smp import os_management as smpos
from smp.exceptions import SMPMalformed, SMPMismatchedGroupId

USER_GROUP_ID_MIN: Final = 64


def test_custom_ReadRequest() -> None:
    """Test ReadRequest inheritance."""

    class A(smpmsg.ReadRequest, frozen=True):
        _GROUP_ID = USER_GROUP_ID_MIN
        _COMMAND_ID = 0

    a = A()
    assert a._GROUP_ID == USER_GROUP_ID_MIN
    assert a._COMMAND_ID == 0

    class B(smpmsg.ReadRequest, frozen=True):
        _GROUP_ID = 65
        _COMMAND_ID = 0

    b = B()
    assert b._GROUP_ID == 65
    assert b._COMMAND_ID == 0

    class MyGroupId(IntEnum):
        C = 64
        D = 65

    class C(smpmsg.ReadRequest, frozen=True):
        _GROUP_ID = MyGroupId.C
        _COMMAND_ID = 0

    c = C()
    assert c._GROUP_ID == MyGroupId.C
    assert c._COMMAND_ID == 0

    class D(smpmsg.ReadRequest, frozen=True):
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
def test_custom_message(cls: type[smpmsg.Data], group_id: int, command_id: int) -> None:
    """Test ReadRequest inheritance."""

    class CustomInts(cls):  # type: ignore[valid-type, misc]
        _OP = getattr(cls, "_OP", smphdr.OP.READ)
        _GROUP_ID = group_id
        _COMMAND_ID = command_id

    m = CustomInts()
    assert group_id == m._GROUP_ID
    assert command_id == m._COMMAND_ID


def test_invalid_group_id() -> None:
    """Test invalid group_id."""

    class A(smpmsg.ReadRequest, frozen=True):
        _GROUP_ID = 0x10000
        _COMMAND_ID = 0

    with pytest.raises(struct.error):
        A().to_frame(sequence=0)

    class B(smpmsg.ReadRequest, frozen=True):
        _GROUP_ID = -1
        _COMMAND_ID = 0

    with pytest.raises(struct.error):
        B().to_frame(sequence=0)


def test_invalid_command_id() -> None:
    """Test invalid command_id."""

    class A(smpmsg.ReadRequest, frozen=True):
        _GROUP_ID = USER_GROUP_ID_MIN
        _COMMAND_ID = 0x100

    with pytest.raises(struct.error):
        A().to_frame(sequence=0)

    class B(smpmsg.ReadRequest, frozen=True):
        _GROUP_ID = USER_GROUP_ID_MIN
        _COMMAND_ID = -1

    with pytest.raises(struct.error):
        B().to_frame(sequence=0)


@pytest.mark.parametrize("sequence", [0, 1, 0x2A, 0xFF])
def test_to_frame_sequence_is_caller_owned(sequence: int) -> None:
    """The caller's sequence reaches the wire verbatim; `smp` never assigns one."""
    frame = smpimg.ImageStatesReadRequest().to_frame(sequence)
    assert frame.header.sequence == sequence
    assert smpimg.ImageStatesReadRequest.loads(bytes(frame)) == frame


def test_to_frame_requires_sequence() -> None:
    with pytest.raises(TypeError):
        smpimg.ImageStatesReadRequest().to_frame()  # type: ignore[call-arg]


@pytest.mark.parametrize("sequence", [-1, 0x100])
def test_to_frame_rejects_out_of_range_sequence(sequence: int) -> None:
    with pytest.raises(struct.error):
        smpimg.ImageStatesReadRequest().to_frame(sequence=sequence)


def test_loads_rejects_mismatched_group_id() -> None:
    wire = bytes(smpimg.ImageStatesReadRequest().to_frame(sequence=0))
    with pytest.raises(SMPMismatchedGroupId):
        smpos.EchoWriteResponse.loads(wire)


def test_loads_rejects_length_mismatch() -> None:
    wire = bytearray(bytes(smpimg.ImageStatesReadRequest().to_frame(sequence=0)))
    wire[2:4] = b"\xff\xff"  # corrupt the header length field
    with pytest.raises(SMPMalformed):
        smpimg.ImageStatesReadRequest.loads(bytes(wire))
