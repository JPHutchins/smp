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
    r = smpimg.ImageStatesReadRequest().to_frame()

    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(bytes(r))

    r = smpimg.ImageStatesReadRequest.loads(bytes(r))
    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(bytes(r))

    r = smpimg.ImageStatesReadRequest.load(r.header, {})
    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(bytes(r))


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

    assert_header(r1.to_frame(sequence=0))

    def assert_response(r: smpimg.ImageStatesReadResponse) -> None:
        d = cast(dict, cbor2.loads(bytes(r)))
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

    r2 = smpimg.ImageStatesReadResponse.loads(bytes(r1.to_frame(sequence=0)))
    assert_header(r2)
    assert_response(r2.smp_data)

    r3 = smpimg.ImageStatesReadResponse.load(r1.to_frame(sequence=0).header, r1.model_dump())
    assert_header(r3)
    assert_response(r3.smp_data)


def test_ImageEraseRequest() -> None:
    assert_header = make_assert_header(
        smpheader.GroupId.IMAGE_MANAGEMENT,
        smpheader.OP.WRITE,
        smpheader.CommandId.ImageManagement.ERASE,
        1,  # empty map
    )
    r = smpimg.ImageEraseRequest().to_frame()

    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(bytes(r))

    r = smpimg.ImageEraseRequest.loads(bytes(r))
    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(bytes(r))

    r = smpimg.ImageEraseRequest.load(r.header, {})
    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(bytes(r))

    assert_header = make_assert_header(
        smpheader.GroupId.IMAGE_MANAGEMENT,
        smpheader.OP.WRITE,
        smpheader.CommandId.ImageManagement.ERASE,
        None,
    )
    r1 = smpimg.ImageEraseRequest(slot=0)

    assert_header(r1.to_frame())
    assert r1.slot == 0

    r = smpimg.ImageEraseRequest.loads(bytes(r1.to_frame()))
    assert_header(r)
    assert r.smp_data.slot == 0


def test_ImageEraseResponse() -> None:
    assert_header = make_assert_header(
        smpheader.GroupId.IMAGE_MANAGEMENT,
        smpheader.OP.WRITE_RSP,
        smpheader.CommandId.ImageManagement.ERASE,
        1,  # empty map
    )
    r = smpimg.ImageEraseResponse().to_frame()

    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(bytes(r))

    r = smpimg.ImageEraseResponse.loads(bytes(r))
    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(bytes(r))

    r = smpimg.ImageEraseResponse.load(r.header, {})
    assert_header(r)
    assert smpheader.Header.SIZE + 1 == len(bytes(r))


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
    ).to_frame()

    assert_header(r)

    r = smpimg.ImageUploadWriteRequest.loads(bytes(r))
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
    ).to_frame()

    assert_header(r)
    assert r.smp_data.off == 0
    assert r.smp_data.data == b"hello"
    assert r.smp_data.image == 1
    assert r.smp_data.len == 5
    assert r.smp_data.sha == b"world"
    assert r.smp_data.upgrade is True

    r = smpimg.ImageUploadWriteRequest.loads(bytes(r))
    assert_header(r)
    assert r.smp_data.off == 0
    assert r.smp_data.data == b"hello"
    assert r.smp_data.image == 1
    assert r.smp_data.len == 5
    assert r.smp_data.sha == b"world"
    assert r.smp_data.upgrade is True

    # when off != 0 do not send image, len, sha, or upgrade
    r = smpimg.ImageUploadWriteRequest(off=10, data=b"hello").to_frame()
    assert_header(r)
    assert r.smp_data.off == 10
    assert r.smp_data.data == b"hello"


@pytest.mark.parametrize("off", [None, 0, 1, 0xFFFF, 0xFFFFFFFF])
@pytest.mark.parametrize("match", [None, True, False])
def test_ImageUploadWriteResponse(off: int | None, match: bool | None) -> None:
    assert_header = make_assert_header(
        smpheader.GroupId.IMAGE_MANAGEMENT,
        smpheader.OP.WRITE_RSP,
        smpheader.CommandId.ImageManagement.UPLOAD,
        None,
    )
    r = smpimg.ImageUploadWriteResponse(off=off, match=match).to_frame()

    assert_header(r)
    assert r.smp_data.off == off
    assert r.smp_data.match == match

    r = smpimg.ImageUploadWriteResponse.loads(bytes(r))
    assert_header(r)
    assert r.smp_data.off == off
    assert r.smp_data.match == match

    if sys.version_info >= (3, 9):
        cbor_dict = (
            {}
            | ({"off": off} if off is not None else {})
            | ({"match": match} if match is not None else {})
        )
    else:
        cbor_dict = {}
        if off is not None:
            cbor_dict["off"] = off
        if match is not None:
            cbor_dict["match"] = match

    r = smpimg.ImageUploadWriteResponse.load(r.header, cbor_dict)
    assert_header(r)
    assert r.smp_data.off == off
    assert r.smp_data.match == match


@pytest.mark.parametrize("off", [None, 0, 1, 0xFFFF, 0xFFFFFFFF])
@pytest.mark.parametrize("match", [None, True, False])
@pytest.mark.parametrize("rc", [None, 0, 1, -23478934])
def test_legacy_ImageUploadWriteResponse(
    off: int | None, match: bool | None, rc: int | None
) -> None:
    assert_header = make_assert_header(
        smpheader.GroupId.IMAGE_MANAGEMENT,
        smpheader.OP.WRITE_RSP,
        smpheader.CommandId.ImageManagement.UPLOAD,
        None,
    )
    r = smpimg.ImageUploadWriteResponse(off=off, match=match, rc=rc).to_frame()

    assert_header(r)
    assert r.smp_data.off == off
    assert r.smp_data.match == match
    assert r.smp_data.rc == rc

    r = smpimg.ImageUploadWriteResponse.loads(bytes(r))
    assert_header(r)
    assert r.smp_data.off == off
    assert r.smp_data.match == match
    assert r.smp_data.rc == rc

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
    assert r.smp_data.off == off
    assert r.smp_data.match == match
    assert r.smp_data.rc == rc
