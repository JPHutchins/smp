"""Static request/response narrowing assertions for `smp.generics`.

These functions are verified by mypy and pyright (the `typecheck` task); they
encode the exhaustiveness contract binding each `Request` to its `Response`,
`ErrorV1`, and `ErrorV2`. They are not executed as runtime tests.
"""

from __future__ import annotations

from typing_extensions import assert_never, assert_type

from smp import enumeration_management as enum
from smp import file_management as fs
from smp import image_management as img
from smp import os_management as os
from smp import settings_management as settings
from smp import shell_management as shell
from smp import statistics_management as stat
from smp import zephyr_management as zephyr
from smp.generics import SMPRequest, TEr1, TEr2, TRep, error, error_v1, error_v2, success
from smp.user import intercreate as ic


def _request(request: SMPRequest[TRep, TEr1, TEr2]) -> TRep | TEr1 | TEr2:
    """Stand-in for `smpclient.SMPClient.request` that drives the static checks."""
    raise NotImplementedError


def _check_read_narrowing() -> None:
    response = _request(img.ImageStatesReadRequest())
    assert_type(
        response,
        img.ImageStatesReadResponse | img.ImageManagementErrorV1 | img.ImageManagementErrorV2,
    )
    if success(response):
        assert_type(response, img.ImageStatesReadResponse)
    elif error_v1(response):
        assert_type(response, img.ImageManagementErrorV1)
    elif error_v2(response):
        assert_type(response, img.ImageManagementErrorV2)
    else:
        assert_never(response)


def _check_write_narrowing() -> None:
    response = _request(os.EchoWriteRequest(d="hello"))
    assert_type(response, os.EchoWriteResponse | os.OSManagementErrorV1 | os.OSManagementErrorV2)
    if success(response):
        assert_type(response, os.EchoWriteResponse)
    elif error(response):
        assert_type(response, os.OSManagementErrorV1 | os.OSManagementErrorV2)
    else:
        assert_never(response)


def _check_os_reset_binding() -> None:
    response = _request(os.ResetWriteRequest())
    assert_type(response, os.ResetWriteResponse | os.OSManagementErrorV1 | os.OSManagementErrorV2)


def _check_os_task_stats_binding() -> None:
    response = _request(os.TaskStatisticsReadRequest())
    assert_type(
        response,
        os.TaskStatisticsReadResponse | os.OSManagementErrorV1 | os.OSManagementErrorV2,
    )


def _check_file_binding() -> None:
    response = _request(fs.FileDownloadRequest(off=0, name="a"))
    assert_type(
        response,
        fs.FileDownloadResponse | fs.FileSystemManagementErrorV1 | fs.FileSystemManagementErrorV2,
    )


def _check_settings_binding() -> None:
    response = _request(settings.ReadSettingRequest(name="a"))
    assert_type(
        response,
        settings.ReadSettingResponse
        | settings.SettingsManagementErrorV1
        | settings.SettingsManagementErrorV2,
    )


def _check_shell_binding() -> None:
    response = _request(shell.ExecuteRequest(argv=["a"]))
    assert_type(
        response,
        shell.ExecuteResponse | shell.ShellManagementErrorV1 | shell.ShellManagementErrorV2,
    )


def _check_statistics_binding() -> None:
    response = _request(stat.GroupDataRequest(name="a"))
    assert_type(
        response,
        stat.GroupDataResponse
        | stat.StatisticsManagementErrorV1
        | stat.StatisticsManagementErrorV2,
    )


def _check_enumeration_binding() -> None:
    response = _request(enum.GroupDetailsRequest())
    assert_type(
        response,
        enum.GroupDetailsResponse | enum.EnumManagementErrorV1 | enum.EnumManagementErrorV2,
    )


def _check_zephyr_binding() -> None:
    response = _request(zephyr.EraseStorageRequest())
    assert_type(
        response,
        zephyr.EraseStorageResponse
        | zephyr.ZephyrManagementErrorV1
        | zephyr.ZephyrManagementErrorV2,
    )


def _check_intercreate_binding() -> None:
    response = _request(ic.ImageUploadWriteRequest(off=0, data=b""))
    assert_type(response, ic.ImageUploadWriteResponse | ic.ErrorV1 | ic.ErrorV2)
