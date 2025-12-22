"""Test the case where the user forms the header separately."""


import pytest

from smp import header as smphdr
from smp import image_management as smpimg
from smp import message as smpmsg
from smp.exceptions import SMPMalformed


def test_ImageUploadWriteRequest_injected_header() -> None:
    h = smphdr.Header(
        op=smphdr.OP.WRITE,
        version=smphdr.Version.V1,
        flags=smphdr.Flag(0),
        length=0,
        group_id=smphdr.GroupId.IMAGE_MANAGEMENT,
        sequence=0,
        command_id=smphdr.CommandId.ImageManagement.UPLOAD,
    )

    data = bytes([0x00] * 50)

    r = smpimg.ImageUploadWriteRequest(
        off=0,
        data=data,
        image=1,
        len=50,
    ).to_frame()

    assert r.header.length == 76
    assert len(bytes(r)) == 76 + smphdr.Header.SIZE

    with pytest.raises(SMPMalformed):
        smpimg.ImageUploadWriteRequest.loads(
            bytes(
                smpmsg.Frame(
                    smphdr.Header(
                        op=h.op,
                        version=h.version,
                        flags=h.flags,
                        length=84,
                        group_id=h.group_id,
                        sequence=h.sequence,
                        command_id=h.command_id,
                    ),
                    smpimg.ImageUploadWriteRequest(
                        off=0,
                        data=data,
                        image=1,
                        len=50,
                    ),
                )
            )
        )

    with pytest.raises(SMPMalformed):
        smpimg.ImageUploadWriteRequest.loads(
            bytes(
                smpmsg.Frame(
                    smphdr.Header(
                        op=h.op,
                        version=h.version,
                        flags=h.flags,
                        length=0,
                        group_id=h.group_id,
                        sequence=h.sequence,
                        command_id=h.command_id,
                    ),
                    smpimg.ImageUploadWriteRequest(
                        off=0,
                        data=data,
                        image=1,
                        len=50,
                    ),
                )
            )
        )


def test_ImageUploadWriteResponse_injected_header() -> None:
    h = smphdr.Header(
        op=smphdr.OP.WRITE_RSP,
        version=smphdr.Version.V1,
        flags=smphdr.Flag(0),
        length=0,
        group_id=smphdr.GroupId.IMAGE_MANAGEMENT,
        sequence=0,
        command_id=smphdr.CommandId.ImageManagement.UPLOAD,
    )

    r = smpmsg.Frame(
        smphdr.Header(
            op=h.op,
            version=h.version,
            flags=h.flags,
            length=6,
            group_id=h.group_id,
            sequence=h.sequence,
            command_id=h.command_id,
        ),
        smpimg.ImageUploadWriteResponse(
            off=0,
        ),
    )

    assert r.header.length == 6
    assert len(bytes(r)) == 6 + smphdr.Header.SIZE
