"""Test the SMP Error responses."""

from __future__ import annotations

from enum import IntEnum
from functools import partial

import cbor2
import msgspec
import pytest

from smp import header as smpheader
from smp.error import MGMT_ERR, ErrorV1, ErrorV2


class FAKE_ERR(IntEnum):
    OK = 0
    ERR = 1


class FakeErrorV1(ErrorV1, frozen=True):
    _GROUP_ID = smpheader.GroupId.IMAGE_MANAGEMENT


class FakeErrorV2(ErrorV2[FAKE_ERR], frozen=True):
    _GROUP_ID = smpheader.GroupId.IMAGE_MANAGEMENT


make_header = partial(
    smpheader.Header,
    op=smpheader.OP.READ,
    version=smpheader.Version.V1,
    flags=smpheader.Flag(0),
    group_id=smpheader.GroupId.IMAGE_MANAGEMENT,
    sequence=0,
    command_id=smpheader.CommandId.ImageManagement.STATE,
)


@pytest.mark.parametrize("rc", [e.value for e in MGMT_ERR])
@pytest.mark.parametrize("rsn", ["something", None])
def test_ErrorV1(rc: int, rsn: str | None) -> None:
    d = cbor2.dumps({"rc": rc} if rsn is None else {"rc": rc, "rsn": rsn})
    h = make_header(length=len(d))

    frame = FakeErrorV1.loads(bytes(h) + d)
    assert MGMT_ERR is type(frame.data.rc)
    assert rc == frame.data.rc
    if rsn is not None:
        assert rsn == frame.data.rsn
    else:
        assert frame.data.rsn is None

    with pytest.raises(msgspec.ValidationError):
        FakeErrorV2.loads(bytes(h) + d)


@pytest.mark.parametrize("rc", [FAKE_ERR.OK, FAKE_ERR.ERR, 2])
@pytest.mark.parametrize(
    "group", [smpheader.GroupId.OS_MANAGEMENT, smpheader.GroupId.IMAGE_MANAGEMENT]
)
def test_ErrorV2(rc: int, group: smpheader.GroupId) -> None:
    d = cbor2.dumps({"err": {"rc": rc, "group": group}})
    h = make_header(length=len(d))

    if rc > max(FAKE_ERR):
        with pytest.raises(msgspec.ValidationError):
            FakeErrorV2.loads(bytes(h) + d)
        return

    frame = FakeErrorV2.loads(bytes(h) + d)
    assert FAKE_ERR is type(frame.data.err.rc)
    assert rc == frame.data.err.rc
    assert group == frame.data.err.group

    with pytest.raises(msgspec.ValidationError):
        FakeErrorV1.loads(bytes(h) + d)


def test_ErrorV2_rejects_missing_err() -> None:
    d = cbor2.dumps({})
    h = make_header(length=len(d))
    with pytest.raises(msgspec.ValidationError):
        FakeErrorV2.loads(bytes(h) + d)


def test_ErrorV2_rejects_unknown_err_field() -> None:
    d = cbor2.dumps({"err": {"group": 0, "rc": 0, "bogus": 1}})
    h = make_header(length=len(d))
    with pytest.raises(msgspec.ValidationError):
        FakeErrorV2.loads(bytes(h) + d)


def test_ErrorV2_rc_type_requires_parametrization() -> None:
    with pytest.raises(TypeError):
        ErrorV2._rc_type()
