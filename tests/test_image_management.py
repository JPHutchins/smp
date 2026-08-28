"""Test the SMP Image Management group."""

from __future__ import annotations

from typing import cast

import cbor2
import pytest

from smp import header as smpheader
from smp import image_management as smpimg
from tests.helpers import assert_frame

imgcmd = smpheader.CommandId.ImageManagement
IMG = smpheader.GroupId.IMAGE_MANAGEMENT


def test_ImageStatesReadRequest() -> None:
    assert_frame(
        smpimg.ImageStatesReadRequest(),
        op=smpheader.OP.READ,
        group_id=IMG,
        command_id=imgcmd.STATE,
        length=1,
    )


@pytest.mark.slow
@pytest.mark.parametrize("slot", [0, 1])
@pytest.mark.parametrize("version", ["0.1.0"])
@pytest.mark.parametrize("image", [0, 1, None])
@pytest.mark.parametrize("hash", [b"A", None])
@pytest.mark.parametrize("bootable", [True, False, None])
@pytest.mark.parametrize("pending", [True, False, None])
@pytest.mark.parametrize("confirmed", [True, False, None])
@pytest.mark.parametrize("active", [True, False, None])
@pytest.mark.parametrize("permanent", [True, False, None])
@pytest.mark.parametrize("splitStatus", [0, 1, None])
def test_ImageStatesReadResponse(
    slot: int,
    version: str,
    image: int | None,
    hash: bytes | None,
    bootable: bool | None,
    pending: bool | None,
    confirmed: bool | None,
    active: bool | None,
    permanent: bool | None,
    splitStatus: int | None,
) -> None:
    image_state = smpimg.ImageState(
        slot=slot,
        version=version,
        image=image,
        hash=hash,
        bootable=bootable,
        pending=pending,
        confirmed=confirmed,
        active=active,
        permanent=permanent,
    )
    frame = assert_frame(
        smpimg.ImageStatesReadResponse(images=[image_state, image_state], splitStatus=splitStatus),
        op=smpheader.OP.READ_RSP,
        group_id=IMG,
        command_id=imgcmd.STATE,
    )

    payload = cast("dict", cbor2.loads(bytes(frame)[smpheader.Header.SIZE :]))
    for i, decoded_state in enumerate(frame.data.images):
        assert decoded_state.slot == slot
        assert decoded_state.version == version
        assert decoded_state.image == image
        assert decoded_state.hash == hash
        assert decoded_state.bootable == bootable
        assert decoded_state.pending == pending
        assert decoded_state.confirmed == confirmed
        assert decoded_state.active == active
        assert decoded_state.permanent == permanent

        for field in type(decoded_state).__struct_fields__:
            if getattr(decoded_state, field) is None:
                assert field not in payload["images"][i]

    assert frame.data.splitStatus == splitStatus


def test_ImageEraseRequest() -> None:
    assert_frame(
        smpimg.ImageEraseRequest(),
        op=smpheader.OP.WRITE,
        group_id=IMG,
        command_id=imgcmd.ERASE,
        length=1,
    )

    frame = assert_frame(
        smpimg.ImageEraseRequest(slot=0),
        op=smpheader.OP.WRITE,
        group_id=IMG,
        command_id=imgcmd.ERASE,
    )
    assert frame.data.slot == 0


def test_ImageEraseResponse() -> None:
    assert_frame(
        smpimg.ImageEraseResponse(),
        op=smpheader.OP.WRITE_RSP,
        group_id=IMG,
        command_id=imgcmd.ERASE,
        length=1,
    )


def test_ImageUploadWriteRequest() -> None:
    frame = assert_frame(
        smpimg.ImageUploadWriteRequest(
            off=0,
            data=b"hello",
            image=1,
            len=5,
            sha=b"world",
            upgrade=True,
        ),
        op=smpheader.OP.WRITE,
        group_id=IMG,
        command_id=imgcmd.UPLOAD,
    )
    assert frame.data.off == 0
    assert frame.data.data == b"hello"
    assert frame.data.image == 1
    assert frame.data.len == 5
    assert frame.data.sha == b"world"
    assert frame.data.upgrade is True

    frame = assert_frame(
        smpimg.ImageUploadWriteRequest(off=10, data=b"hello"),
        op=smpheader.OP.WRITE,
        group_id=IMG,
        command_id=imgcmd.UPLOAD,
    )
    assert frame.data.off == 10
    assert frame.data.data == b"hello"


@pytest.mark.parametrize("off", [None, 0, 1, 0xFFFF, 0xFFFFFFFF])
@pytest.mark.parametrize("match", [None, True, False])
def test_ImageUploadWriteResponse(off: int | None, match: bool | None) -> None:
    frame = assert_frame(
        smpimg.ImageUploadWriteResponse(off=off, match=match),
        op=smpheader.OP.WRITE_RSP,
        group_id=IMG,
        command_id=imgcmd.UPLOAD,
    )
    assert frame.data.off == off
    assert frame.data.match == match


@pytest.mark.parametrize("off", [None, 0, 1, 0xFFFF, 0xFFFFFFFF])
@pytest.mark.parametrize("match", [None, True, False])
@pytest.mark.parametrize("rc", [None, 0, 1, -23478934])
def test_legacy_ImageUploadWriteResponse(
    off: int | None, match: bool | None, rc: int | None
) -> None:
    frame = assert_frame(
        smpimg.ImageUploadWriteResponse(off=off, match=match, rc=rc),
        op=smpheader.OP.WRITE_RSP,
        group_id=IMG,
        command_id=imgcmd.UPLOAD,
    )
    assert frame.data.off == off
    assert frame.data.match == match
    assert frame.data.rc == rc
