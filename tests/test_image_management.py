"""Test the SMP Image Management group."""

from __future__ import annotations

import sys
from typing import cast

import cbor2
import pytest

from smp import header as smpheader
from smp import image_management as smpimg
from tests.helpers import make_assert_header


def test_ImageStatesReadRequest() -> None:
    assert_header = make_assert_header(
        smpheader.GroupId.IMAGE_MANAGEMENT,
        smpheader.OP.READ,
        smpheader.CommandId.ImageManagement.STATE,
        1,  # empty map
    )
    r = smpimg.ImageStatesReadRequest()

    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(r.BYTES)

    r = smpimg.ImageStatesReadRequest.loads(r.BYTES)
    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(r.BYTES)

    r = smpimg.ImageStatesReadRequest.load(r.header, {})
    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(r.BYTES)


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
    assert_header = make_assert_header(
        smpheader.GroupId.IMAGE_MANAGEMENT,
        smpheader.OP.READ_RSP,
        smpheader.CommandId.ImageManagement.STATE,
        None,
    )
    r1 = smpimg.ImageStatesReadResponse(
        sequence=0,
        images=[
            smpimg.ImageState(
                slot=slot,
                version=version,
                image=image,
                hash=hash,
                bootable=bootable,
                pending=pending,
                confirmed=confirmed,
                active=active,
                permanent=permanent,
            ),
            smpimg.ImageState(
                slot=slot,
                version=version,
                image=image,
                hash=hash,
                bootable=bootable,
                pending=pending,
                confirmed=confirmed,
                active=active,
                permanent=permanent,
            ),
        ],
        splitStatus=splitStatus,
    )

    assert_header(r1)

    def assert_response(r: smpimg.ImageStatesReadResponse) -> None:
        d = cast(dict, cbor2.loads(r.BYTES[8:]))
        for i, image_state in enumerate(r.images):
            assert slot == image_state.slot
            assert version == image_state.version
            assert image == image_state.image
            assert hash == image_state.hash
            assert bootable == image_state.bootable
            assert pending == image_state.pending
            assert confirmed == image_state.confirmed
            assert active == image_state.active
            assert permanent == image_state.permanent

            for f in image_state.model_fields:
                if getattr(image_state, f) is None:
                    assert f not in d["images"][i]

        assert splitStatus == r.splitStatus

    assert_response(r1)

    r2 = smpimg.ImageStatesReadResponse.loads(r1.BYTES)
    assert_header(r2)
    assert_response(r2)

    r3 = smpimg.ImageStatesReadResponse.load(
        r1.header, r1.model_dump(exclude={'header', 'sequence'})
    )
    assert_header(r3)
    assert_response(r3)


def test_ImageEraseRequest() -> None:
    assert_header = make_assert_header(
        smpheader.GroupId.IMAGE_MANAGEMENT,
        smpheader.OP.WRITE,
        smpheader.CommandId.ImageManagement.ERASE,
        1,  # empty map
    )
    r = smpimg.ImageEraseRequest()

    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(r.BYTES)

    r = smpimg.ImageEraseRequest.loads(r.BYTES)
    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(r.BYTES)

    r = smpimg.ImageEraseRequest.load(r.header, {})
    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(r.BYTES)

    assert_header = make_assert_header(
        smpheader.GroupId.IMAGE_MANAGEMENT,
        smpheader.OP.WRITE,
        smpheader.CommandId.ImageManagement.ERASE,
        None,
    )
    r = smpimg.ImageEraseRequest(slot=0)

    assert_header(r)
    assert r.slot == 0

    r = smpimg.ImageEraseRequest.loads(r.BYTES)
    assert_header(r)
    assert r.slot == 0


def test_ImageEraseResponse() -> None:
    assert_header = make_assert_header(
        smpheader.GroupId.IMAGE_MANAGEMENT,
        smpheader.OP.WRITE_RSP,
        smpheader.CommandId.ImageManagement.ERASE,
        1,  # empty map
    )
    r = smpimg.ImageEraseResponse()

    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(r.BYTES)

    r = smpimg.ImageEraseResponse.loads(r.BYTES)
    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(r.BYTES)

    r = smpimg.ImageEraseResponse.load(r.header, {})
    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(r.BYTES)


def test_ImageUploadWriteRequest() -> None:
    assert_header = make_assert_header(
        smpheader.GroupId.IMAGE_MANAGEMENT,
        smpheader.OP.WRITE,
        smpheader.CommandId.ImageManagement.UPLOAD,
        None,
    )
    r = smpimg.ImageUploadWriteRequest(
        off=0,
        data=b"hello",
        image=1,
        len=5,
        sha=b"world",
        upgrade=True,
    )

    assert_header(r)

    r = smpimg.ImageUploadWriteRequest.loads(r.BYTES)
    assert_header(r)

    assert_header = make_assert_header(
        smpheader.GroupId.IMAGE_MANAGEMENT,
        smpheader.OP.WRITE,
        smpheader.CommandId.ImageManagement.UPLOAD,
        None,
    )
    r = smpimg.ImageUploadWriteRequest(
        off=0,
        data=b"hello",
        image=1,
        len=5,
        sha=b"world",
        upgrade=True,
    )

    assert_header(r)
    assert r.off == 0
    assert r.data == b"hello"
    assert r.image == 1
    assert r.len == 5
    assert r.sha == b"world"
    assert r.upgrade is True

    r = smpimg.ImageUploadWriteRequest.loads(r.BYTES)
    assert_header(r)
    assert r.off == 0
    assert r.data == b"hello"
    assert r.image == 1
    assert r.len == 5
    assert r.sha == b"world"
    assert r.upgrade is True

    # when off != 0 do not send image, len, sha, or upgrade
    r = smpimg.ImageUploadWriteRequest(off=10, data=b"hello")
    assert_header(r)
    assert r.off == 10
    assert r.data == b"hello"


@pytest.mark.parametrize("off", [None, 0, 1, 0xFFFF, 0xFFFFFFFF])
@pytest.mark.parametrize("match", [None, True, False])
@pytest.mark.parametrize("rc", [None, 0, 1, 10])
def test_ImageUploadWriteResponse(off: int | None, match: bool | None, rc: int | None) -> None:
    assert_header = make_assert_header(
        smpheader.GroupId.IMAGE_MANAGEMENT,
        smpheader.OP.WRITE_RSP,
        smpheader.CommandId.ImageManagement.UPLOAD,
        None,
    )
    r = smpimg.ImageUploadWriteResponse(off=off, match=match, rc=rc)

    assert_header(r)
    assert r.off == off
    assert r.match == match
    assert r.rc == rc

    r = smpimg.ImageUploadWriteResponse.loads(r.BYTES)
    assert_header(r)
    assert r.off == off
    assert r.match == match
    assert r.rc == rc

    if sys.version_info >= (3, 9):
        cbor_dict = (
            {}
            | ({"off": off} if off is not None else {})
            | ({"match": match} if match is not None else {})
            | ({"rc": rc} if rc is not None else {})
        )
    else:
        cbor_dict = {}
        if off is not None:
            cbor_dict["off"] = off
        if match is not None:
            cbor_dict["match"] = match
        if rc is not None:
            cbor_dict["rc"] = rc

    r = smpimg.ImageUploadWriteResponse.load(r.header, cbor_dict)
    assert_header(r)
    assert r.off == off
    assert r.match == match
    assert r.rc == rc
