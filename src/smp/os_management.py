"""The Simple Management Protocol (SMP) OS Management group."""

from __future__ import annotations

from enum import IntEnum, unique
from typing import Any, Literal

import msgspec
import msgspec_cbor

from smp import error, header, message


@unique
class OS_MGMT_RET_RC(IntEnum):
    """OS Management return codes."""

    OK = 0
    """No error, this is implied if there is no ret value in the response."""

    UNKNOWN = 1
    """Unknown error occurred."""

    INVALID_FORMAT = 2
    """The provided format value is not valid."""

    QUERY_YIELDS_NO_ANSWER = 3
    """Query was not recognized."""

    RTC_NOT_SET = 4
    """RTC is not set."""

    RTC_COMMAND_FAILED = 5
    """RTC command failed."""


class OSManagementErrorV1(error.ErrorV1, frozen=True):
    """OS Management error response."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT


class OSManagementErrorV2(error.ErrorV2[OS_MGMT_RET_RC], frozen=True):
    """OS Management error response."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT


class _OSGroupBase:
    _ErrorV1 = OSManagementErrorV1
    _ErrorV2 = OSManagementErrorV2


class EchoWriteResponse(message.WriteResponse, frozen=True):
    """Success response to an echo request."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.ECHO

    r: str
    """Echoed string."""


class EchoWriteRequest(message.WriteRequest, _OSGroupBase, frozen=True):
    """Echo back the provided string."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.ECHO
    _Response = EchoWriteResponse

    d: str
    """String to echo."""


@unique
class BootMode(IntEnum):
    """Boot mode requested by the OS management reset command.

    Mirrors Zephyr's `enum BOOT_MODE_TYPES` in
    `include/zephyr/retention/bootmode.h`.
    """

    NORMAL = 0
    """Default (normal) boot, to the user application."""

    BOOTLOADER = 1
    """Bootloader boot mode, e.g. serial recovery for MCUboot."""


class ResetWriteResponse(message.WriteResponse, frozen=True):
    """Success response to a reset request."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.RESET


class ResetWriteRequest(message.WriteRequest, _OSGroupBase, frozen=True):
    """Performs reset of system.

    The device should issue response before resetting so that the SMP client
    could receive information that the command has been accepted. By default,
    this command is accepted in all conditions, however if the
    `CONFIG_MCUMGR_GRP_OS_RESET_HOOK` is enabled and an application registers a
    callback, the callback will be called when this command is issued and can be
    used to perform any necessary tidy operations prior to the module rebooting,
    or to reject the reset request outright altogether with an error response.

    For details on this functionality, see [callbacks](https://docs.zephyrproject.org/latest/services/device_mgmt/mcumgr_callbacks.html#mcumgr-callbacks).  # noqa: E501
    """

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.RESET
    _Response = ResetWriteResponse

    force: Literal[0, 1] | None = None
    """Force reset.

    Normally the command sends an empty CBOR map as data, but if a previous
    reset attempt has responded with “rc” equal to MGMT_ERR_EBUSY then the
    following map may be sent to force a reset
    """

    boot_mode: BootMode | int | None = None
    """Boot mode to set via the retention boot mode module before resetting.

    A value of `BootMode.BOOTLOADER` (1) requests, for example, that an MCUboot
    built with `CONFIG_BOOT_SERIAL_BOOT_MODE` enter serial recovery on the next
    boot. The server casts the value to a `uint8_t`, so any value in `[0, 255]`
    is accepted and passed to `bootmode_set()`; known values are surfaced as
    `BootMode` members.

    Requires the server to be built with `CONFIG_MCUMGR_GRP_OS_RESET_BOOT_MODE`,
    which depends on `CONFIG_RETENTION_BOOT_MODE`. Added to the SMP OS
    management group in Zephyr v4.2.0 (zephyrproject-rtos/zephyr#91510).
    """

    def __post_init__(self) -> None:
        if self.boot_mode is not None and not 0 <= self.boot_mode <= 255:
            raise ValueError(f"boot_mode {self.boot_mode!r} is not a uint8 (0-255)")

    @classmethod
    def _convert_mapping(cls, data: dict[str, Any]) -> ResetWriteRequest:
        cls._validate_mapping(data)
        return cls(
            force=msgspec.convert(data["force"], type=Literal[0, 1]) if "force" in data else None,
            boot_mode=header.resolve_int_enum(
                msgspec.convert(data["boot_mode"], type=int), BootMode
            )
            if "boot_mode" in data
            else None,
        )


class TaskStatistics(msgspec.Struct, frozen=True, omit_defaults=True, forbid_unknown_fields=True):
    """Task statistics."""

    prio: int
    """Task priority."""
    tid: int
    """Numeric task ID."""
    state: int
    """Numeric task state."""
    stkuse: int
    """Stack usage.

    The unit is system dependent and in case of Zephyr this is number of 4 byte words.
    """
    stksiz: int
    """Stack size.

    The unit is system dependent and in case of Zephyr this is number of 4 byte words.
    """
    cswcnt: int
    """Number of context switches."""
    runtime: int
    """Runtime in ticks."""
    last_checkin: int
    """Set to 0 by Zephyr."""
    next_checkin: int
    """Set to 0 by Zephyr."""


class TaskStatisticsZephyr(
    msgspec.Struct, frozen=True, omit_defaults=True, forbid_unknown_fields=True
):
    """Task statistics for Zephyr when CONFIG_MCUMGR_GRP_OS_TASKSTAT_ONLY_SUPPORTED_STATS=y.

    In this configuration, Zephyr may omit fields that are not supported by the underlying RTOS.
    Only prio, tid, and state are guaranteed to be present.
    """

    prio: int
    """Task priority."""
    tid: int
    """Numeric task ID."""
    state: int
    """Numeric task state."""
    stkuse: int | None = None
    """Stack usage.

    The unit is system dependent and in case of Zephyr this is number of 4 byte words.
    """
    stksiz: int | None = None
    """Stack size.

    The unit is system dependent and in case of Zephyr this is number of 4 byte words.
    """
    cswcnt: int | None = None
    """Number of context switches."""
    runtime: int | None = None
    """Runtime in ticks."""
    last_checkin: int | None = None
    """Set to 0 by Zephyr."""
    next_checkin: int | None = None
    """Set to 0 by Zephyr."""


def _discriminate_task(task: dict[str, Any]) -> TaskStatistics | TaskStatisticsZephyr:
    # No wire tag; try the full struct first, fall back to the Zephyr subset.
    try:
        return msgspec.convert(task, type=TaskStatistics)
    except msgspec.ValidationError:
        return msgspec.convert(task, type=TaskStatisticsZephyr)


class TaskStatisticsReadResponse(message.ReadResponse, frozen=True):
    """Task statistics response."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.TASK_STATS

    tasks: dict[str, TaskStatistics | TaskStatisticsZephyr]
    """Task statistics map."""

    @classmethod
    def _convert_mapping(cls, data: dict[str, Any]) -> TaskStatisticsReadResponse:
        cls._validate_mapping(data)
        tasks = msgspec.convert(data["tasks"], type=dict[str, dict[str, Any]])
        return cls(tasks={name: _discriminate_task(t) for name, t in tasks.items()})


class TaskStatisticsReadRequest(message.ReadRequest, _OSGroupBase, frozen=True):
    """Request task statistics."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.TASK_STATS
    _Response = TaskStatisticsReadResponse


class MemoryPoolStatistics(
    msgspec.Struct, frozen=True, omit_defaults=True, forbid_unknown_fields=True
):
    """Memory pool statistics."""

    blksize: int
    """Size of the memory block in the pool."""
    nblks: int
    """Number of memory blocks in the pool."""
    nfree: int
    """Number of free memory blocks in the pool."""
    min: int
    """Lowest number of free blocks the pool reached during run-time."""


class MemoryPoolStatisticsReadResponse(message.ReadResponse, frozen=True):
    """The memory pools are accessed by name."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.MEMORY_POOL_STATS

    pools: dict[str, MemoryPoolStatistics]
    """Memory pool statistics keyed by pool name."""

    def __bytes__(self) -> bytes:
        return msgspec_cbor.encode(self.pools, order="canonical")

    @classmethod
    def _convert_mapping(cls, data: dict[str, Any]) -> MemoryPoolStatisticsReadResponse:
        return cls(pools=msgspec.convert(data, type=dict[str, MemoryPoolStatistics]))


class MemoryPoolStatisticsReadRequest(message.ReadRequest, _OSGroupBase, frozen=True):
    """Request memory pool statistics."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.MEMORY_POOL_STATS
    _Response = MemoryPoolStatisticsReadResponse


class DateTimeReadResponse(message.ReadResponse, frozen=True):
    """Response to a date and time request."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.DATETIME_STRING

    datetime: str


class DateTimeReadRequest(message.ReadRequest, _OSGroupBase, frozen=True):
    """Request the current date and time."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.DATETIME_STRING
    _Response = DateTimeReadResponse


class DateTimeWriteResponse(message.WriteResponse, frozen=True):
    """Success response to a date and time request."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.DATETIME_STRING


class DateTimeWriteRequest(message.WriteRequest, _OSGroupBase, frozen=True):
    """Set the current date and time."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.DATETIME_STRING
    _Response = DateTimeWriteResponse

    datetime: str


class MCUMgrParametersReadResponse(message.ReadResponse, frozen=True):
    """Success response to a MCU Manager parameters request."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.MCUMGR_PARAMETERS

    buf_size: int
    """Single SMP buffer size, this includes SMP header and CBOR payload."""
    buf_count: int
    """Number of SMP buffers."""


class MCUMgrParametersReadRequest(message.ReadRequest, _OSGroupBase, frozen=True):
    """Request MCU Manager parameters."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.MCUMGR_PARAMETERS
    _Response = MCUMgrParametersReadResponse


class OSApplicationInfoReadResponse(message.ReadResponse, frozen=True):
    """Success response to an application information request."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.OS_APPLICATION_INFO

    output: str
    """Text response including requested parameters."""


class OSApplicationInfoReadRequest(message.ReadRequest, _OSGroupBase, frozen=True):
    """Request information about the application running on the device."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.OS_APPLICATION_INFO
    _Response = OSApplicationInfoReadResponse

    format: str | None = None
    """Format specifier of returned response.

    Fields are appended in their natural ascending index order, not the order
    of characters that are received by the command.

    Format specifiers:
    * `s` Kernel name
    * `n` Node name
    * `r` Kernel release
    * `v` Kernel version
    * `b` Build date and time (requires `CONFIG_MCUMGR_GRP_OS_INFO_BUILD_DATE_TIME`)
    * `m` Machine
    * `p` Processor
    * `i` Hardware platform
    * `o` Operating system
    * `a` All fields (shorthand for all above options)

    If this option is not provided, the `s` Kernel name option will be used.
    """


@unique
class MCUbootMode(IntEnum):
    UNKNOWN = -1
    APPLICATION = 0
    SWAP_USING_SCRATCH = 1
    OVERWRITE_ONLY = 2
    SWAP_WITHOUT_SCRATCH = 3
    DIRECT_XIP_WITHOUT_REVERT = 4
    DIRECT_XIP_WITH_REVERT = 5
    RAM_LOADER = 6


class MCUbootModeQueryResponse(
    msgspec.Struct, frozen=True, omit_defaults=True, forbid_unknown_fields=True
):
    """Response to a MCUboot mode query."""

    mode: MCUbootMode
    no_downgrade: bool | None = msgspec.field(name="no-downgrade", default=None)


class BootloaderInformationReadResponse(message.ReadResponse, frozen=True):
    """Success response to a bootloader information request."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.BOOTLOADER_INFO

    bootloader: str
    """String identifying the bootloader.  For MCUboot it will be "MCUboot"."""
    response: MCUbootModeQueryResponse | None = None
    """Response to “query”.

    This is optional and may be left out in case when query yields no response,
    SMP version 2 error code of `OS_MGMT_ERR_QUERY_YIELDS_NO_ANSWER` is
    expected. Response may have more than one parameter reported back or it may
    be a map, that is dependent on bootloader backend and query."""


class BootloaderInformationReadRequest(message.ReadRequest, _OSGroupBase, frozen=True):
    """Request bootloader information."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.BOOTLOADER_INFO
    _Response = BootloaderInformationReadResponse

    query: str | None = None
    """Is string representing query for parameters.

    With no restrictions how the query looks like as processing of query is left
    for bootloader backend. If there is no query, then response will return string
    identifying the bootloader.

    MCUboot supports the query string,"mode".  The response to mode is of type
    `MCUbootMode`.
    """
