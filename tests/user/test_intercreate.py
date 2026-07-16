"""Test the SMP Intercreate Management group."""

from smp import header as smphdr
from smp.user import intercreate as ic
from tests.helpers import assert_frame


def test_initial_ImageUploadWriteRequest() -> None:
    frame = assert_frame(
        ic.ImageUploadWriteRequest(off=0, data=b"test", image=0, len=132000, sha=b"sha"),
        op=smphdr.OP.WRITE,
        group_id=smphdr.UserGroupId.INTERCREATE,
        command_id=smphdr.CommandId.Intercreate.UPLOAD,
    )
    assert frame.data.off == 0
    assert frame.data.data == b"test"
    assert frame.data.image == 0
    assert frame.data.len == 132000
    assert frame.data.sha == b"sha"


def test_subsequent_ImageUploadWriteRequest() -> None:
    frame = assert_frame(
        ic.ImageUploadWriteRequest(off=105000, data=b"test"),
        op=smphdr.OP.WRITE,
        group_id=smphdr.UserGroupId.INTERCREATE,
        command_id=smphdr.CommandId.Intercreate.UPLOAD,
    )
    assert frame.data.off == 105000
    assert frame.data.data == b"test"
    assert frame.data.image is None
    assert frame.data.len is None
    assert frame.data.sha is None


def test_ImageUploadWriteResponse() -> None:
    frame = assert_frame(
        ic.ImageUploadWriteResponse(off=105000),
        op=smphdr.OP.WRITE_RSP,
        group_id=smphdr.UserGroupId.INTERCREATE,
        command_id=smphdr.CommandId.Intercreate.UPLOAD,
    )
    assert frame.data.off == 105000
