"""The Simple Management Protocol (SMP) OS Management group."""

from __future__ import annotations

from enum import IntEnum, auto, unique
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field

from smp import error, header, message


class EchoWriteRequest(message.WriteRequest):
    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.ECHO

    d: str


class EchoWriteResponse(message.WriteResponse):
    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.ECHO

    r: str


class ResetWriteRequest(message.WriteRequest):
    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.RESET


class ResetWriteResponse(message.WriteResponse):
    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.RESET


class TaskStatisticsReadRequest(message.ReadRequest):
    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.TASK_STATS


class TaskStatistics(BaseModel):
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
    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.TASK_STATS

    tasks: Dict[str, TaskStatistics]


class MemoryPoolStatisticsReadRequest(message.ReadRequest):
    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.MEMORY_POOL_STATS


class MemoryPoolStatistics(BaseModel):
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
    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.DATETIME_STRING


class DateTimeReadResponse(message.ReadResponse):
    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.DATETIME_STRING

    datetime: str


class DateTimeWriteRequest(message.WriteRequest):
    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.DATETIME_STRING

    datetime: str


class DateTimeWriteResponse(message.WriteResponse):
    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.DATETIME_STRING


class MCUMgrParametersReadRequest(message.ReadRequest):
    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.MCUMGR_PARAMETERS


class MCUMgrParametersReadResponse(message.ReadResponse):
    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.MCUMGR_PARAMETERS

    buf_size: int
    buf_count: int


class OSApplicationInfoReadRequest(message.ReadRequest):
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
    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.OS_APPLICATION_INFO

    output: str


class BootloaderInformationReadRequest(message.ReadRequest):
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
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: MCUbootMode
    no_downgrade: bool | None = Field(alias="no-downgrade", default=None)


class BootloaderInformationReadResponse(message.ReadResponse):
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
    OK = 0
    """No error, this is implied if there is no ret value in the response."""

    UNKNOWN = auto()
    """Unknown error occurred."""

    INVALID_FORMAT = auto()
    """The provided format value is not valid."""

    QUERY_YIELDS_NO_ANSWER = auto()
    """Query was not recognized."""

    RTC_NOT_SET = auto()
    """RTC is not set."""

    RTC_COMMAND_FAILED = auto()
    """RTC command failed."""


class OSManagementErrorV0(error.ErrorV0[OS_MGMT_RET_RC]):
    _GROUP_ID = header.GroupId.OS_MANAGEMENT


class OSManagementErrorV1(error.ErrorV1[OS_MGMT_RET_RC]):
    _GROUP_ID = header.GroupId.OS_MANAGEMENT
