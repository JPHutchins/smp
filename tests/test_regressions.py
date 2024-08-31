"""This file is here to prevent specific regressions."""

from typing import Final

import pytest

import smp.header as smphdr
import smp.image_management as smpimg


def test_smpclient_41() -> None:
    """https://github.com/intercreate/smpclient/issues/41"""

    RESPONSE: Final = b"\x03\x00\x00\x0c\x00\x01\x02\x01\xbfbrc\x00coff\x18\xa5\xff"
    """A legacy `ImageUploadWriteResponse` that contains the rc field."""

    r: Final = smpimg.ImageUploadWriteResponse.loads(RESPONSE)

    assert r.header.op == smphdr.OP.WRITE_RSP
    assert r.header.version == smphdr.Version.V1
    assert r.header.flags == smphdr.Flag(0)
    assert r.header.length == 12
    assert r.header.group_id == smphdr.GroupId.IMAGE_MANAGEMENT
    assert r.header.sequence == 2
    assert r.header.command_id == smphdr.CommandId.ImageManagement.UPLOAD

    assert r.off == 165
    assert r.rc == 0

    with pytest.raises(ValueError):
        smpimg.ImageManagementErrorV1.loads(RESPONSE)

    with pytest.raises(ValueError):
        smpimg.ImageManagementErrorV2.loads(RESPONSE)
