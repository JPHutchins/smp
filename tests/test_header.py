"""Test the SMP header de/serialization."""

import struct

import pytest

from smp.header import OP, Flag, GroupId, Header, Version


@pytest.mark.parametrize("op", [OP.READ, OP.READ_RSP, OP.WRITE, OP.WRITE_RSP])
@pytest.mark.parametrize("version", [Version.V0, Version.V1])
@pytest.mark.parametrize("flags", [Flag(0b0), Flag(0b1), Flag(0xFF)])
@pytest.mark.parametrize("length", [0, 1, 0xFFFF])
@pytest.mark.parametrize("group_id", [0, 1, 0xFFFF])
@pytest.mark.parametrize("sequence", [0, 1, 255])
@pytest.mark.parametrize("command_id", [0, 1, 255])
def test_header_serialization(
    op: OP,
    version: Version,
    flags: Flag,
    length: int,
    group_id: GroupId,
    sequence: int,
    command_id: int,
) -> None:
    # the validators will raise exceptions
    if group_id > max(GroupId):
        with pytest.raises((KeyError, ValueError)):
            h = Header(op, version, flags, length, group_id, sequence, command_id)  # type: ignore
        return
    elif command_id > max(Header._MAP_GROUP_ID_TO_COMMAND_ID_ENUM[group_id]):
        with pytest.raises((KeyError, ValueError)):
            h = Header(op, version, flags, length, group_id, sequence, command_id)  # type: ignore
        return

    h = Header(op, version, flags, length, group_id, sequence, command_id)  # type: ignore

    # test the abstract data type
    assert op == h.op
    assert version == h.version
    assert flags == h.flags
    assert length == h.length
    assert group_id == h.group_id
    assert sequence == h.sequence
    assert command_id == h.command_id

    b = h.BYTES
    assert len(b) == 8
    assert len(b) == h.SIZE
    assert b == bytes(h)  # test bytes dunder

    # test the serialization
    assert bytes([op]) == bytes([b[0] & 0b111])  # bit packed
    assert bytes([version]) == bytes([(b[0] >> 3) & 0b11])  # bit packed
    assert bytes([flags]) == b[1:2]
    assert struct.pack("!H", length) == b[2:4]  # big endian
    assert struct.pack("!H", group_id) == b[4:6]  # big endian
    assert bytes([sequence]) == b[6:7]
    assert bytes([command_id]) == b[7:8]


@pytest.mark.parametrize("op", [OP.READ, OP.READ_RSP, OP.WRITE, OP.WRITE_RSP])
@pytest.mark.parametrize("version", [Version.V0, Version.V1])
@pytest.mark.parametrize("flags", [Flag(0b0), Flag(0b1), Flag(0xFF)])
@pytest.mark.parametrize("length", [0, 1, 0xFFFF])
@pytest.mark.parametrize("group_id", [0, 1, 0xFFFF])
@pytest.mark.parametrize("sequence", [0, 1, 255])
@pytest.mark.parametrize("command_id", [0, 1, 255])
def test_header_deserialization(
    op: OP,
    version: Version,
    flags: Flag,
    length: int,
    group_id: GroupId,
    sequence: int,
    command_id: int,
) -> None:
    # the validators will raise exceptions
    if group_id > max(GroupId):
        with pytest.raises((KeyError, ValueError)):
            _h = Header(op, version, flags, length, group_id, sequence, command_id)  # type: ignore
            h = Header.loads(_h.BYTES)
        return
    elif command_id > max(Header._MAP_GROUP_ID_TO_COMMAND_ID_ENUM[group_id]):
        with pytest.raises((KeyError, ValueError)):
            _h = Header(op, version, flags, length, group_id, sequence, command_id)  # type: ignore
            h = Header.loads(_h.BYTES)
        return

    _h = Header(op, version, flags, length, group_id, sequence, command_id)  # type: ignore
    h = Header.loads(_h.BYTES)

    # test the abstract data type
    assert op == h.op
    assert version == h.version
    assert flags == h.flags
    assert length == h.length
    assert group_id == h.group_id
    assert sequence == h.sequence
    assert command_id == h.command_id

    # test the reserialization
    assert _h.BYTES == h.BYTES
