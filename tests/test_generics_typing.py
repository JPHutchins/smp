"""Static request/response narrowing assertions for `smp.SMPRequest`.

These functions are verified by mypy and pyright (the `typecheck` task); they
encode the exhaustiveness contract binding each `Request` to its `Response`,
`ErrorV1`, and `ErrorV2`. They are not executed as runtime tests.

The `TypeIs` narrowing helpers and the `_request` stub below stand in for an SMP
client: they demonstrate that `SMPRequest` and all of its implementations
support exhaustive narrowing, without the `smp` library having to ship them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from typing_extensions import assert_never, assert_type

from smp import SMPRequest
from smp import enumeration_management as enum
from smp import file_management as fs
from smp import header as smpheader
from smp import image_management as img
from smp import message as smpmessage
from smp import os_management as os
from smp import settings_management as settings
from smp import shell_management as shell
from smp import statistics_management as stat
from smp import zephyr_management as zephyr
from smp.user import intercreate as ic

if TYPE_CHECKING:
    from typing_extensions import TypeIs

    from smp import error as smperror

TRep = TypeVar("TRep", bound="smpmessage.ReadResponse | smpmessage.WriteResponse")
TEr1 = TypeVar("TEr1", bound="smperror.ErrorV1")
TEr2 = TypeVar("TEr2", bound="smperror.ErrorV2")


def success(
    response: smpmessage.Response,
) -> TypeIs[smpmessage.ReadResponse | smpmessage.WriteResponse]:
    return response.RESPONSE_TYPE == smpmessage.ResponseType.SUCCESS


def error_v1(response: smpmessage.Response) -> TypeIs[smperror.ErrorV1]:
    return response.RESPONSE_TYPE == smpmessage.ResponseType.ERROR_V1


def error_v2(response: smpmessage.Response) -> TypeIs[smperror.ErrorV2[Any]]:
    return response.RESPONSE_TYPE == smpmessage.ResponseType.ERROR_V2


def error(response: smpmessage.Response) -> TypeIs[smperror.ErrorV1 | smperror.ErrorV2[Any]]:
    return error_v1(response) or error_v2(response)


def _request(request: SMPRequest[TRep, TEr1, TEr2]) -> TRep | TEr1 | TEr2:
    """Stand-in for `smpclient.SMPClient.request` that drives the static checks."""
    raise NotImplementedError


def _client_owned_frame(
    request: SMPRequest[TRep, TEr1, TEr2],
    *,
    sequence: int,
    version: smpheader.Version,
    flags: smpheader.Flag,
) -> smpmessage.Frame[Any]:
    """An SMP client owning its sequence space and its SMP version.

    The sequence space belongs to the client, so `SMPRequest` must expose the
    header knobs that `Data.to_frame` accepts; hiding them forced every client
    onto one process-global counter.
    """
    return request.to_frame(sequence, version=version, flags=flags)


def _check_client_owned_frame() -> None:
    _client_owned_frame(
        os.EchoWriteRequest(d="hello"),
        sequence=0,
        version=smpheader.Version.V1,
        flags=smpheader.Flag.UNUSED,
    )
    _client_owned_frame(
        img.ImageStatesReadRequest(),
        sequence=0xFF,
        version=smpheader.Version.V2,
        flags=smpheader.Flag.UNUSED,
    )


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
