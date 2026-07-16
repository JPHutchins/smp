"""This file is here to prevent specific regressions."""

from typing import Final

import msgspec
import pytest

import smp.header as smphdr
import smp.image_management as smpimg


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
