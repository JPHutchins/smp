"""The Simple Management Protocol (SMP) OS Management group."""


from smp import header, message


class EchoWriteRequest(message.WriteRequest):
    """Request that the SMP server echo the provided string."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.ECHO

    d: str
    """The string to echo."""


class EchoWriteResponse(message.WriteResponse):
    """Successful response to `EchoWriteRequest`."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.ECHO

    r: str
    """The echoed string."""


class ResetWriteRequest(message.WriteRequest):
    """Request that the SMP server restart the device."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.RESET


class ResetWriteResponse(message.WriteResponse):
    """Successful response to `ResetWriteRequest`."""

    _GROUP_ID = header.GroupId.OS_MANAGEMENT
    _COMMAND_ID = header.CommandId.OSManagement.RESET
