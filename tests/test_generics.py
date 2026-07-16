"""Runtime behavior of the `smp.generics` type-narrowing helpers."""

from __future__ import annotations

from smp import error, header
from smp import image_management as img
from smp.generics import error as is_error
from smp.generics import error_v1, error_v2, success

_SUCCESS = img.ImageStatesReadResponse(images=[])
_ERR_V1 = img.ImageManagementErrorV1(rc=error.MGMT_ERR.EUNKNOWN)
_ERR_V2 = img.ImageManagementErrorV2(
    err=error.Err(group=header.GroupId.IMAGE_MANAGEMENT, rc=img.IMG_MGMT_ERR.UNKNOWN)
)


def test_success() -> None:
    assert success(_SUCCESS) is True
    assert success(_ERR_V1) is False
    assert success(_ERR_V2) is False


def test_error_v1() -> None:
    assert error_v1(_ERR_V1) is True
    assert error_v1(_SUCCESS) is False
    assert error_v1(_ERR_V2) is False


def test_error_v2() -> None:
    assert error_v2(_ERR_V2) is True
    assert error_v2(_SUCCESS) is False
    assert error_v2(_ERR_V1) is False


def test_error() -> None:
    assert is_error(_ERR_V1) is True
    assert is_error(_ERR_V2) is True
    assert is_error(_SUCCESS) is False
