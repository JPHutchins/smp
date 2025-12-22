"""Test the SMP Intercreate Management group."""

from smp.user import intercreate as ic
from tests.helpers import make_assert_header


def test_initial_ImageUploadWriteRequest() -> None:
    r = ic.ImageUploadWriteRequest(
        off=0,
        data=b"test",
        image=0,
        len=132000,
        sha=b"sha",
    ).to_frame()

    assert_header = make_assert_header(
        ic.header.UserGroupId.INTERCREATE,
        ic.header.OP.WRITE,
        ic.header.CommandId.Intercreate.UPLOAD,
        len(bytes(r)) - ic.header.Header.SIZE,
    )

    assert_header(r)

    assert r.smp_data.off == 0
    assert r.smp_data.data == b"test"
    assert r.smp_data.image == 0
    assert r.smp_data.len == 132000
    assert r.smp_data.sha == b"sha"


def test_subsequent_ImageUploadWriteRequest() -> None:
    r = ic.ImageUploadWriteRequest(
        off=105000,
        data=b"test",
    ).to_frame()

    assert_header = make_assert_header(
        ic.header.UserGroupId.INTERCREATE,
        ic.header.OP.WRITE,
        ic.header.CommandId.Intercreate.UPLOAD,
        len(bytes(r)) - ic.header.Header.SIZE,
    )

    assert_header(r)

    assert r.smp_data.off == 105000
    assert r.smp_data.data == b"test"
    assert r.smp_data.image is None
    assert r.smp_data.len is None
    assert r.smp_data.sha is None


def test_ImageUploadWriteResponse() -> None:
    r = ic.ImageUploadWriteResponse(off=105000).to_frame(sequence=0)

    assert_header = make_assert_header(
        ic.header.UserGroupId.INTERCREATE,
        ic.header.OP.WRITE_RSP,
        ic.header.CommandId.Intercreate.UPLOAD,
        len(bytes(r)) - ic.header.Header.SIZE,
    )

    assert_header(r)

    assert r.smp_data.off == 105000
