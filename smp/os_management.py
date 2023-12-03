"""The Simple Management Protocol (SMP) OS Management group."""


from enum import IntEnum, auto, unique

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


@unique
class OS_MGMT_RET_RC(IntEnum):
    OK = 0
    """No error, this is implied if there is no ret value in the response."""

    UNKNOWN = auto()
    """Unknown error occurred."""

    INVALID_FORMAT = auto()
    """The provided format value is not valid."""


class OSManagementErrorV0(error.ErrorV0[OS_MGMT_RET_RC]):
    _GROUP_ID = header.GroupId.OS_MANAGEMENT


class OSManagementErrorV1(error.ErrorV1[OS_MGMT_RET_RC]):
    _GROUP_ID = header.GroupId.OS_MANAGEMENT
