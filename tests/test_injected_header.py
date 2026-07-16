"""Test the case where the user forms the header separately."""

import pytest

from smp import header as smphdr
from smp import image_management as smpimg
from smp.exceptions import SMPMismatchedGroupId


def test_ImageUploadWriteRequest_injected_header() -> None:
    data = bytes([0x00] * 50)

    header = smphdr.Header(
        op=smphdr.OP.WRITE,
        version=smphdr.Version.V1,
        flags=smphdr.Flag(0),
        length=76,
        group_id=smphdr.GroupId.IMAGE_MANAGEMENT,
        sequence=0,
        command_id=smphdr.CommandId.ImageManagement.UPLOAD,
    )

    frame = smpimg.ImageUploadWriteRequest.load(
        header, {"off": 0, "data": data, "image": 1, "len": 50}
    )

    assert frame.header == header
    assert frame.header.length == 76
    assert len(bytes(frame)) == 76 + smphdr.Header.SIZE
    assert frame.data.off == 0
    assert frame.data.data == data
    assert frame.data.image == 1
    assert frame.data.len == 50

    assert smpimg.ImageUploadWriteRequest.loads(bytes(frame)) == frame

    with pytest.raises(SMPMismatchedGroupId):
        smpimg.ImageUploadWriteRequest.load(
            smphdr.Header(
                op=smphdr.OP.WRITE,
                version=smphdr.Version.V1,
                flags=smphdr.Flag(0),
                length=76,
                group_id=smphdr.GroupId.OS_MANAGEMENT,
                sequence=0,
                command_id=smphdr.CommandId.OSManagement.ECHO,
            ),
            {"off": 0, "data": data, "image": 1, "len": 50},
        )


def test_ImageUploadWriteResponse_injected_header() -> None:
    header = smphdr.Header(
        op=smphdr.OP.WRITE_RSP,
        version=smphdr.Version.V1,
        flags=smphdr.Flag(0),
        length=6,
        group_id=smphdr.GroupId.IMAGE_MANAGEMENT,
        sequence=0,
        command_id=smphdr.CommandId.ImageManagement.UPLOAD,
    )

    frame = smpimg.ImageUploadWriteResponse.load(header, {"off": 0})

    assert frame.header == header
    assert frame.header.length == 6
    assert len(bytes(frame)) == 6 + smphdr.Header.SIZE
    assert frame.data.off == 0

    assert smpimg.ImageUploadWriteResponse.loads(bytes(frame)) == frame
