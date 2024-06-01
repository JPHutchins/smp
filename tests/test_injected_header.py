"""Test the case where the user forms the header separately."""

from typing import cast

import pytest

from smp import header as smphdr
from smp import image_management as smpimg
from smp.exceptions import SMPMalformed


def test_ImageUploadWriteRequest_injected_header() -> None:
    h = smphdr.Header(
        op=smphdr.OP.WRITE,
        version=smphdr.Version.V0,
        flags=smphdr.Flag(0),
        length=0,
        group_id=smphdr.GroupId.IMAGE_MANAGEMENT,
        sequence=0,
        command_id=smphdr.CommandId.ImageManagement.UPLOAD,
    )

    data = bytes([0x00] * 50)

    r = smpimg.ImageUploadWriteRequest(
        header=smphdr.Header(
            op=h.op,
            version=h.version,
            flags=h.flags,
            length=76,
            group_id=h.group_id,
            sequence=h.sequence,
            command_id=h.command_id,
        ),
        off=0,
        data=data,
        image=1,
        len=50,
    )

    assert cast(smphdr.Header, r.header).length == 76
    assert len(r.BYTES) == 76 + smphdr.Header.SIZE

    with pytest.raises(SMPMalformed):
        r = smpimg.ImageUploadWriteRequest(
            header=smphdr.Header(
                op=h.op,
                version=h.version,
                flags=h.flags,
                length=84,
                group_id=h.group_id,
                sequence=h.sequence,
                command_id=h.command_id,
            ),
            off=0,
            data=data,
            image=1,
            len=50,
        )

    with pytest.raises(SMPMalformed):
        r = smpimg.ImageUploadWriteRequest(
            header=smphdr.Header(
                op=h.op,
                version=h.version,
                flags=h.flags,
                length=0,
                group_id=h.group_id,
                sequence=h.sequence,
                command_id=h.command_id,
            ),
            off=0,
            data=data,
            image=1,
            len=50,
        )


def test_ImageUploadWriteResponse_injected_header() -> None:
    h = smphdr.Header(
        op=smphdr.OP.WRITE_RSP,
        version=smphdr.Version.V0,
        flags=smphdr.Flag(0),
        length=0,
        group_id=smphdr.GroupId.IMAGE_MANAGEMENT,
        sequence=0,
        command_id=smphdr.CommandId.ImageManagement.UPLOAD,
    )

    r = smpimg.ImageUploadWriteResponse(
        header=smphdr.Header(
            op=h.op,
            version=h.version,
            flags=h.flags,
            length=10,
            group_id=h.group_id,
            sequence=h.sequence,
            command_id=h.command_id,
        ),
        rc=0,
        off=0,
    )

    assert cast(smphdr.Header, r.header).length == 10
    assert len(r.BYTES) == 10 + smphdr.Header.SIZE
