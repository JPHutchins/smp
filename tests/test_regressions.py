"""This file is here to prevent specific regressions."""

from typing import Final

import cbor2
import msgspec
import pytest

import smp.header as smphdr
import smp.image_management as smpimg
import smp.message as smpmsg
from tests.helpers import assert_frame


def test_smpclient_41() -> None:
    """https://github.com/intercreate/smpclient/issues/41"""

    RESPONSE: Final = b"\x03\x00\x00\x0c\x00\x01\x02\x01\xbfbrc\x00coff\x18\xa5\xff"
    """A legacy `ImageUploadWriteResponse` that contains the rc field."""

    frame: Final = smpimg.ImageUploadWriteResponse.loads(RESPONSE)

    assert frame.header.op == smphdr.OP.WRITE_RSP
    assert frame.header.version == smphdr.Version.V1
    assert frame.header.flags == smphdr.Flag(0)
    assert frame.header.length == 12
    assert frame.header.group_id == smphdr.GroupId.IMAGE_MANAGEMENT
    assert frame.header.sequence == 2
    assert frame.header.command_id == smphdr.CommandId.ImageManagement.UPLOAD

    assert frame.data.off == 165
    assert frame.data.rc == 0

    with pytest.raises(msgspec.ValidationError):
        smpimg.ImageManagementErrorV1.loads(RESPONSE)

    with pytest.raises((msgspec.ValidationError, KeyError)):
        smpimg.ImageManagementErrorV2.loads(RESPONSE)


def test_smp_45() -> None:
    """https://github.com/JPHutchins/smp/issues/45

    An SMP message's CBOR payload may legitimately contain fields named
    `header`, `version`, `sequence`, or `smp_data`. The flattened pre-`Frame`
    design excluded those names from serialization, silently dropping them; the
    payload is now a distinct `Data` struct, so the names survive a round trip.
    """

    USER_GROUP: Final = 0x1234
    COLLIDING: Final = {"header", "version", "sequence", "smp_data"}

    class CollidingReadResponse(smpmsg.ReadResponse, frozen=True):
        _GROUP_ID = USER_GROUP
        _COMMAND_ID = 0

        header: int
        version: str
        sequence: int
        smp_data: bytes

    response = CollidingReadResponse(header=1, version="1.2.3", sequence=7, smp_data=b"\xde\xad")
    assert set(cbor2.loads(bytes(response))) == COLLIDING

    decoded = assert_frame(response, op=smphdr.OP.READ_RSP, group_id=USER_GROUP, command_id=0)
    assert decoded.data == response
    assert decoded.data.header == 1
    assert decoded.data.version == "1.2.3"
    assert decoded.data.sequence == 7
    assert decoded.data.smp_data == b"\xde\xad"

    assert decoded.header.version == smphdr.Version.V2
    assert decoded.header.sequence == 0

    class CollidingWriteRequest(smpmsg.WriteRequest, frozen=True):
        _GROUP_ID = USER_GROUP
        _COMMAND_ID = 0

        header: int
        version: str
        sequence: int
        smp_data: bytes

    request = CollidingWriteRequest(header=2, version="4.5.6", sequence=9, smp_data=b"\xbe\xef")
    assert set(cbor2.loads(bytes(request))) == COLLIDING
    assert (
        assert_frame(request, op=smphdr.OP.WRITE, group_id=USER_GROUP, command_id=0).data == request
    )
