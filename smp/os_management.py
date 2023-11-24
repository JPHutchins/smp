"""The Simple Management Protocol (SMP) OS Management group."""


from smp import header, message


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
