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
    )

    assert_header = make_assert_header(
        ic.header.GroupId.INTERCREATE,
        ic.header.OP.WRITE,
        ic.header.CommandId.Intercreate.UPLOAD,
        len(r.BYTES) - ic.header.Header.SIZE,
    )

    assert_header(r)

    assert r.off == 0
    assert r.data == b"test"
    assert r.image == 0
    assert r.len == 132000
    assert r.sha == b"sha"


def test_subsequent_ImageUploadWriteRequest() -> None:
    r = ic.ImageUploadWriteRequest(
        off=105000,
        data=b"test",
    )

    assert_header = make_assert_header(
        ic.header.GroupId.INTERCREATE,
        ic.header.OP.WRITE,
        ic.header.CommandId.Intercreate.UPLOAD,
        len(r.BYTES) - ic.header.Header.SIZE,
    )

    assert_header(r)

    assert r.off == 105000
    assert r.data == b"test"
    assert r.image is None
    assert r.len is None
    assert r.sha is None


def test_ImageUploadWriteResponse() -> None:
    r = ic.ImageUploadWriteResponse(header=None, sequence=0, off=105000)

    assert_header = make_assert_header(
        ic.header.GroupId.INTERCREATE,
        ic.header.OP.WRITE_RSP,
        ic.header.CommandId.Intercreate.UPLOAD,
        len(r.BYTES) - ic.header.Header.SIZE,
    )

    assert_header(r)

    assert r.off == 105000
