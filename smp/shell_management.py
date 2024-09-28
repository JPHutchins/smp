"""The Simple Management Protocol (SMP) Shell Management group."""


from enum import IntEnum, unique
from typing import List

from smp import error, header, message


class ExecuteRequest(message.WriteRequest):
    """Execute a shell command."""

    _GROUP_ID = header.GroupId.SHELL_MANAGEMENT
    _COMMAND_ID = header.CommandId.ShellManagement.EXECUTE

    argv: List[str]


class ExecuteResponse(message.WriteResponse):
    """Success response to a shell command execution."""

    _GROUP_ID = header.GroupId.SHELL_MANAGEMENT
    _COMMAND_ID = header.CommandId.ShellManagement.EXECUTE

    o: str
    ret: int


@unique
class SHELL_MGMT_RET_RC(IntEnum):
    """Return codes for the shell management group."""

    OK = 0
    """No error, this is implied if there is no ret value in the response."""

    UNKNOWN = 1
    """Unknown error occurred."""

    INVALID_FORMAT = 2
    """The provided format value is not valid."""


class ShellManagementErrorV1(error.ErrorV1):
    """Error response to a shell command execution."""

    _GROUP_ID = header.GroupId.SHELL_MANAGEMENT


class ShellManagementErrorV2(error.ErrorV2[SHELL_MGMT_RET_RC]):
    """Error response to a shell command execution."""

    _GROUP_ID = header.GroupId.SHELL_MANAGEMENT
