"""Test the packet functions, encode and decode."""

import struct
from base64 import b64decode

import pytest
from crcmod.predefined import mkPredefinedCrcFun  # type: ignore
from pydantic import ValidationError

from smp import header, image_management
from smp.exceptions import SMPBadContinueDelimiter, SMPBadCRC, SMPBadStartDelimiter
from smp.packet import decode, encode

crc16_func = mkPredefinedCrcFun("xmodem")

off = 42
image = 0
length = 13
sha = "trust me bro".encode()
upgrade = False


def _assert_header(frame: bytes) -> None:
    # deserialize the header
    h = header.Header.loads(frame[: header.Header.SIZE])
    assert header.OP.WRITE == h.op
    assert header.Version.V0 == h.version
    assert 0 == h.flags
    assert h.length != 0  # TODO: unsure how to check length more specifically
    assert header.GroupId.IMAGE_MANAGEMENT == h.group_id
    assert header.CommandId.ImageManagement.UPLOAD == h.command_id


def _assert_payload(frame: bytes, data: bytes) -> None:
    # deserialize the original request itself
    r = image_management.ImageUploadWriteRequest.loads(frame)
    assert off == r.off
    assert image == r.image
    assert length == r.len
    assert sha == r.sha
    assert upgrade == r.upgrade

    # finally, check the image update payload
    assert data == r.data


@pytest.mark.parametrize("line_length", [16, 20, 89, 128, 251, 313, 512, 1024, 1609, 4096, 8192])
@pytest.mark.parametrize("line_length_ratio", [0.1, 1 / 3, 0.5, 1, 2, 3, 4, 7])
def test_encode(line_length: int, line_length_ratio: float) -> None:
    data = bytes([i % 0xFF for i in range(round(line_length * line_length_ratio))])

    r = image_management.ImageUploadWriteRequest(
        off=off, data=data, image=image, len=length, sha=sha, upgrade=upgrade
    )

    reconstruct = bytearray([])
    for i, p in enumerate(encode(r.BYTES, line_length=line_length)):
        # assert that packet delimiters are correct
        if i == 0:
            assert bytes([6, 9]) == p[:2]
        else:
            assert bytes([4, 20]) == p[:2]
        assert b"\n" == bytes([p[-1]])

        # and reassemble
        reconstruct.extend(p[2:-1])

    # print(i + 1)  # this is how many packets it took to encode the data

    # the encode function used b64
    remaining = b64decode(reconstruct)

    while len(remaining) > 0:
        # unpack every frame, AKA request
        (frame_length,) = struct.unpack("!H", remaining[:2])
        frame = remaining[2 : frame_length + 2]  # first 2 bytes are length, last 2 are CRC

        assert crc16_func(frame[:-2]) == struct.unpack("!H", frame[-2:])[0]

        _assert_header(frame)
        _assert_payload(frame[:-2], data)

        remaining = remaining[frame_length + 2 :]


@pytest.mark.parametrize("line_length", [16, 20, 89, 128, 251, 313, 512, 1024, 1609, 4096, 8192])
@pytest.mark.parametrize("line_length_ratio", [0.1, 1 / 3, 0.5, 1, 2, 3, 4, 7])
def test_decode(line_length: int, line_length_ratio: float) -> None:
    data = bytes([i % 0xFF for i in range(round(line_length * line_length_ratio))])

    req = image_management.ImageUploadWriteRequest(
        off=off, data=data, image=image, len=length, sha=sha, upgrade=upgrade
    )
    packets = []
    for p in encode(req.BYTES, line_length=line_length):
        packets.append(p)

    decoder = decode()
    next(decoder)

    for packet in packets:
        try:
            decoder.send(packet)
        except StopIteration as e:
            frame = e.value
            break

    _assert_header(frame)
    _assert_payload(frame, data)


def test_decode_raises_SMPBadStartDelimiter() -> None:
    req = image_management.ImageUploadWriteRequest(
        off=off, data=b"hello!", image=image, len=length, sha=sha, upgrade=upgrade
    )
    packets = []
    for p in encode(req.BYTES):
        packets.append(p)

    # malform the start delimiter
    packets[0] = bytes([0, 0]) + packets[0][2:]

    decoder = decode()
    next(decoder)

    with pytest.raises(SMPBadStartDelimiter):
        for packet in packets:
            try:
                decoder.send(packet)
            except StopIteration as e:
                _ = e.value
                break


def test_decode_raises_SMPBadContinueDelimiter() -> None:
    line_length = 512

    req = image_management.ImageUploadWriteRequest(
        off=off,
        data=bytes([i % 0xFF for i in range(line_length * 4)]),
        image=image,
        len=length,
        sha=sha,
        upgrade=upgrade,
    )
    packets = []
    for p in encode(req.BYTES, line_length=line_length):
        packets.append(p)

    assert len(packets) > 1

    # malform the continue delimiter
    packets[1] = bytes([0, 0]) + packets[1][2:]

    decoder = decode()
    next(decoder)

    with pytest.raises(SMPBadContinueDelimiter):
        for packet in packets:
            try:
                decoder.send(packet)
            except StopIteration as e:
                _ = e.value
                break


@pytest.mark.parametrize("j", [0, 1, 2, 3])
@pytest.mark.parametrize("i", [i for i in range(4, 124)])
def test_decode_raises_SMPBadCRC(j: int, i: int) -> None:
    line_length = 128

    req = image_management.ImageUploadWriteRequest(
        off=off,
        data=bytes([i % 0xFF for i in range(line_length * 2)]),
        image=image,
        len=length,
        sha=sha,
        upgrade=upgrade,
    )

    packets = []
    for p in encode(req.BYTES, line_length=line_length):
        packets.append(p)

    assert len(packets) == 4

    if i < len(packets[j]):
        # change 1 byte in the data to another base64 character
        len_before = len(packets[j])
        packets[j] = (
            packets[j][:i] + (b"Z" if packets[j][i] != b"Z" else b"0") + packets[j][i + 1 :]
        )
        assert len_before == len(packets[j])

        decoder = decode()
        next(decoder)

        with pytest.raises((SMPBadCRC, ValidationError)):
            for packet in packets:
                try:
                    decoder.send(packet)
                except StopIteration as e:
                    frame = e.value
                    break

            # 1 byte difference may not be caught by CRC16
            print(f"CRC slipped by with {j=} {i=}")

            # so ensure that it gets caught in deserialization by raising ValidationError
            image_management.ImageStatesWriteRequest.loads(frame)
