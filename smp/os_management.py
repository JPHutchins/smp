"""The Simple Management Protocol (SMP) OS Management group."""

from __future__ import annotations

from enum import IntEnum, unique
from typing import Any, Dict, Literal

from pydantic import BaseModel, ConfigDict, Field

from smp import error, header, message


class EchoWriteRequest(message.WriteRequest):
    """Echo back the provided string."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.ECHO

    d: str
    """String to echo."""


class EchoWriteResponse(message.WriteResponse):
    """Success response to an echo request."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.ECHO

    r: str
    """Echoed string."""


class ResetWriteRequest(message.WriteRequest):
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

    force: Literal[0, 1] | None = None
    """Force reset.

    Normally the command sends an empty CBOR map as data, but if a previous
    reset attempt has responded with “rc” equal to MGMT_ERR_EBUSY then the
    following map may be sent to force a reset
    """


class ResetWriteResponse(message.WriteResponse):
    """Success response to a reset request."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.RESET


class TaskStatisticsReadRequest(message.ReadRequest):
    """Request task statistics."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.TASK_STATS


class TaskStatistics(BaseModel):
    """Task statistics."""

    model_config = ConfigDict(extra="forbid", frozen=True)

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
    stksize: int
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


class TaskStatisticsReadResponse(message.ReadResponse):
    """Task statistics response."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.TASK_STATS

    tasks: Dict[str, TaskStatistics]
    """Task statistics map."""


class MemoryPoolStatisticsReadRequest(message.ReadRequest):
    """Request memory pool statistics."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.MEMORY_POOL_STATS


class MemoryPoolStatistics(BaseModel):
    """Memory pool statistics."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    blksize: int
    """Size of the memory block in the pool."""
    nblks: int
    """Number of memory blocks in the pool."""
    nfree: int
    """Number of free memory blocks in the pool."""
    min: int
    """Lowest number of free blocks the pool reached during run-time."""


class MemoryPoolStatisticsReadResponse(message.ReadResponse):
    """The memory pools are accessed by name."""

    model_config = ConfigDict(extra="allow", frozen=True)

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.MEMORY_POOL_STATS


class DateTimeReadRequest(message.ReadRequest):
    """Request the current date and time."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.DATETIME_STRING


class DateTimeReadResponse(message.ReadResponse):
    """Response to a date and time request."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.DATETIME_STRING

    datetime: str


class DateTimeWriteRequest(message.WriteRequest):
    """Set the current date and time."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.DATETIME_STRING

    datetime: str


class DateTimeWriteResponse(message.WriteResponse):
    """Success response to a date and time request."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.DATETIME_STRING


class MCUMgrParametersReadRequest(message.ReadRequest):
    """Request MCU Manager parameters."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.MCUMGR_PARAMETERS


class MCUMgrParametersReadResponse(message.ReadResponse):
    """Success response to a MCU Manager parameters request."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.MCUMGR_PARAMETERS

    buf_size: int
    """Single SMP buffer size, this includes SMP header and CBOR payload."""
    buf_count: int
    """Number of SMP buffers."""


class OSApplicationInfoReadRequest(message.ReadRequest):
    """Request information about the application running on the device."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.OS_APPLICATION_INFO

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


class OSApplicationInfoReadResponse(message.ReadResponse):
    """Success response to an application information request."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.OS_APPLICATION_INFO

    output: str
    """Text response including requested parameters."""


class BootloaderInformationReadRequest(message.ReadRequest):
    """Request bootloader information."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.BOOTLOADER_INFO

    query: str | None = None
    """Is string representing query for parameters.

    With no restrictions how the query looks like as processing of query is left
    for bootloader backend. If there is no query, then response will return string
    identifying the bootloader.

    MCUboot supports the query string,"mode".  The response to mode is of type
    `MCUbootMode`.
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


class MCUbootModeQueryResponse(BaseModel):
    """Response to a MCUboot mode query."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: MCUbootMode
    no_downgrade: bool | None = Field(alias="no-downgrade", default=None)


class BootloaderInformationReadResponse(message.ReadResponse):
    """Success response to a bootloader information request."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.BOOTLOADER_INFO

    bootloader: str
    """String identifying the bootloader.  For MCUboot it will be "MCUboot"."""
    response: MCUbootModeQueryResponse | Any | None = None
    """Response to “query”.

    This is optional and may be left out in case when query yields no response,
    SMP version 2 error code of `OS_MGMT_ERR_QUERY_YIELDS_NO_ANSWER` is
    expected. Response may have more than one parameter reported back or it may
    be a map, that is dependent on bootloader backend and query."""


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


class OSManagementErrorV1(error.ErrorV1):
    """OS Management error response."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT


class OSManagementErrorV2(error.ErrorV2[OS_MGMT_RET_RC]):
    """OS Management error response."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
