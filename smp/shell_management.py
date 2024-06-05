"""The Simple Management Protocol (SMP) Shell Management group."""


from enum import IntEnum, auto, unique
from typing import List

from smp import error, header, message


class ExecuteRequest(message.WriteRequest):
    _GROUP_ID = header.GroupId.SHELL_MANAGEMENT
    _COMMAND_ID = header.CommandId.ShellManagement.EXECUTE

    argv: List[str]


class ExecuteResponse(message.WriteResponse):
    _GROUP_ID = header.GroupId.SHELL_MANAGEMENT
    _COMMAND_ID = header.CommandId.ShellManagement.EXECUTE

    o: str
    ret: int


@unique
class SHELL_MGMT_RET_RC(IntEnum):
    OK = 0
    """No error, this is implied if there is no ret value in the response."""

    UNKNOWN = auto()
    """Unknown error occurred."""

    INVALID_FORMAT = auto()
    """The provided format value is not valid."""


class ShellManagementErrorV1(error.ErrorV1):
    _GROUP_ID = header.GroupId.SHELL_MANAGEMENT


class ShellManagementErrorV2(error.ErrorV2[SHELL_MGMT_RET_RC]):
    _GROUP_ID = header.GroupId.SHELL_MANAGEMENT
