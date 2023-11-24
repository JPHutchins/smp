"""Test the SMP Error responses."""

from enum import IntEnum
from functools import partial

import cbor2
import pytest
from pydantic import ValidationError

from smp import header as smpheader
from smp.error import ErrorV0, ErrorV1


class FAKE_ERR(IntEnum):
    OK = 0
    ERR = 1


class FakeErrorV0(ErrorV0[FAKE_ERR]):
    _GROUP_ID = smpheader.GroupId.IMAGE_MANAGEMENT


class FakeErrorV1(ErrorV1[FAKE_ERR]):
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


@pytest.mark.parametrize("rc", [FAKE_ERR.OK, FAKE_ERR.ERR, 2])
@pytest.mark.parametrize("rsn", ["something", None])
def test_ErrorV0(rc: FAKE_ERR, rsn: str | None) -> None:
    d = cbor2.dumps({"rc": rc} if rsn is None else {"rc": rc, "rsn": rsn})  # type: ignore
    h = make_header(length=len(d))

    if rc > max(FAKE_ERR):
        with pytest.raises(ValidationError):
            FakeErrorV0.loads(h.BYTES + d)
        return

    e = FakeErrorV0.loads(h.BYTES + d)
    assert FAKE_ERR is type(e.rc)
    assert rc == e.rc
    if rsn is not None:
        assert rsn == e.rsn
    else:
        assert None is e.rsn

    with pytest.raises(ValidationError):
        FakeErrorV1.loads(h.BYTES + d)


@pytest.mark.parametrize("rc", [FAKE_ERR.OK, FAKE_ERR.ERR, 2])
@pytest.mark.parametrize(
    "group", [smpheader.GroupId.OS_MANAGEMENT, smpheader.GroupId.IMAGE_MANAGEMENT]
)
def test_ErrorV1(rc: FAKE_ERR, group: smpheader.GroupId) -> None:
    d = cbor2.dumps({"err": {"rc": rc, "group": group}})
    h = make_header(length=len(d))

    if rc > max(FAKE_ERR):
        with pytest.raises(ValidationError):
            FakeErrorV1.loads(h.BYTES + d)
        return

    e = FakeErrorV1.loads(h.BYTES + d)
    assert FAKE_ERR is type(e.err.rc)
    assert rc == e.err.rc
    assert group == e.err.group

    with pytest.raises(ValidationError):
        FakeErrorV0.loads(h.BYTES + d)
