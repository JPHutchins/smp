"""The Simple Management Protocol (SMP) Shell Management group."""

from enum import IntEnum, unique

from smp import error, header, message


@unique
class SHELL_MGMT_RET_RC(IntEnum):
    """Return codes for the shell management group."""

    OK = 0
    """No error, this is implied if there is no ret value in the response."""

    UNKNOWN = 1
    """Unknown error occurred."""

    INVALID_FORMAT = 2
    """The provided format value is not valid."""


class ShellManagementErrorV1(error.ErrorV1, frozen=True):
    """Error response to a shell command execution."""

    _GROUP_ID = header.GroupId.SHELL_MANAGEMENT


class ShellManagementErrorV2(error.ErrorV2[SHELL_MGMT_RET_RC], frozen=True):
    """Error response to a shell command execution."""

    _GROUP_ID = header.GroupId.SHELL_MANAGEMENT


class _ShellGroupBase:
    _ErrorV1 = ShellManagementErrorV1
    _ErrorV2 = ShellManagementErrorV2


class ExecuteResponse(message.WriteResponse, frozen=True):
    """Success response to a shell command execution."""

    _GROUP_ID = header.GroupId.SHELL_MANAGEMENT
    _COMMAND_ID = header.CommandId.ShellManagement.EXECUTE

    o: str
    ret: int


class ExecuteRequest(message.WriteRequest, _ShellGroupBase, frozen=True):
    """Execute a shell command."""

    _GROUP_ID = header.GroupId.SHELL_MANAGEMENT
    _COMMAND_ID = header.CommandId.ShellManagement.EXECUTE
    _Response = ExecuteResponse

    argv: list[str]
