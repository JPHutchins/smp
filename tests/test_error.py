"""Test the SMP Error responses."""

from __future__ import annotations

from enum import IntEnum
from functools import partial

import cbor2
import pytest
from pydantic import ValidationError

from smp import header as smpheader
from smp.error import MGMT_ERR, ErrorV1, ErrorV2


class FAKE_ERR(IntEnum):
    OK = 0
    ERR = 1


class FakeErrorV1(ErrorV1):
    _GROUP_ID = smpheader.GroupId.IMAGE_MANAGEMENT


class FakeErrorV2(ErrorV2[FAKE_ERR]):
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
def test_ErrorV1(rc: MGMT_ERR, rsn: str | None) -> None:
    d = cbor2.dumps({"rc": rc} if rsn is None else {"rc": rc, "rsn": rsn})  # type: ignore
    h = make_header(length=len(d))

    if rc > max(MGMT_ERR):
        with pytest.raises(ValidationError):
            FakeErrorV1.loads(h.BYTES + d)
        return

    _, e = FakeErrorV1.loads(h.BYTES + d)
    assert MGMT_ERR is type(e.rc)
    assert rc == e.rc
    if rsn is not None:
        assert rsn == e.rsn
    else:
        assert None is e.rsn

    with pytest.raises(ValidationError):
        FakeErrorV2.loads(h.BYTES + d)


@pytest.mark.parametrize("rc", [FAKE_ERR.OK, FAKE_ERR.ERR, 2])
@pytest.mark.parametrize(
    "group", [smpheader.GroupId.OS_MANAGEMENT, smpheader.GroupId.IMAGE_MANAGEMENT]
)
def test_ErrorV2(rc: FAKE_ERR, group: smpheader.GroupId) -> None:
    d = cbor2.dumps({"err": {"rc": rc, "group": group}})
    h = make_header(length=len(d))

    if rc > max(FAKE_ERR):
        with pytest.raises(ValidationError):
            FakeErrorV2.loads(h.BYTES + d)
        return

    _, e = FakeErrorV2.loads(h.BYTES + d)
    assert FAKE_ERR is type(e.err.rc)
    assert rc == e.err.rc
    assert group == e.err.group

    with pytest.raises(ValidationError):
        FakeErrorV1.loads(h.BYTES + d)
