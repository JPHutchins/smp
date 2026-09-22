"""The Simple Management Protocol (SMP) Transport Management group."""

from __future__ import annotations

from enum import IntEnum, unique
from typing import Annotated, Literal, TypeAlias

import cbor2
from pydantic import BaseModel, ConfigDict, Field

import smp.error as smperr
import smp.header as smphdr
import smp.message as smpmsg

GROUP_ID: smphdr.GroupIdField = smphdr.GroupId.TRANSPORT_MANAGEMENT
"""The group ID that this module's messages are addressed to.

A device may serve this group from another group ID; subclass the messages that
such a device is sent and override `_GROUP_ID`.
"""

UInt32: TypeAlias = Annotated[int, Field(ge=0, le=0xFFFFFFFF)]


@unique
class TransportType(IntEnum):
    """The MCUmgr transports that a bridge can be established with."""

    SERIAL = 0
    RAW_SERIAL = 1
    BLUETOOTH = 2
    SHELL = 3
    UDP_IPV4 = 4
    UDP_IPV6 = 5
    LORAWAN = 6
    SPI = 7
    USER_DEFINED = 64


TransportTypeField: TypeAlias = Annotated[TransportType | UInt32, Field(union_mode="left_to_right")]

TransportWithoutConnectParameters: TypeAlias = Annotated[
    Literal[
        TransportType.SERIAL,
        TransportType.RAW_SERIAL,
        TransportType.SHELL,
        TransportType.UDP_IPV4,
        TransportType.UDP_IPV6,
        TransportType.LORAWAN,
        TransportType.SPI,
        TransportType.USER_DEFINED,
    ]
    | Annotated[int, Field(ge=0, lt=TransportType.BLUETOOTH)]
    | Annotated[int, Field(gt=TransportType.BLUETOOTH, le=0xFFFFFFFF)],
    Field(union_mode="left_to_right"),
]
"""Every transport except those whose connect parameters have their own request
type."""


@unique
class ConfigType(IntEnum):
    """The type of a transport configuration item."""

    UINT = 0
    INT = 1
    BOOL = 2
    STRING = 3
    BYTE_STRING = 4


@unique
class BluetoothAddressType(IntEnum):
    """The address types accepted by the Bluetooth transport's bridge."""

    PUBLIC = 0
    RANDOM = 1


class ConnectRequest(smpmsg.WriteRequest):
    """Bridge to a transport that takes no parameters beyond `transport` and `mode`.

    A transport that takes parameters gets its own request type, the way
    `BluetoothConnectRequest` does.
    """

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.CONNECT

    transport: TransportWithoutConnectParameters
    """The transport to bridge the transport that receives this request to."""
    mode: UInt32 | None = None
    """The configuration mode of the transport to use.

    May be omitted to use the default value of 0.
    """


class BluetoothConnectRequest(smpmsg.WriteRequest):
    """Bridge to the Bluetooth transport."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.CONNECT

    transport: Literal[TransportType.BLUETOOTH]
    address: Annotated[str, Field(pattern=r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")]
    """The address of the peripheral to connect to."""
    address_type: BluetoothAddressType | None = None
    """The type of `address`."""
    le_coded: bool | None = None
    """Request the LE Coded PHY instead of the 1M PHY."""
    mode: UInt32 | None = None
    """The configuration mode of the transport to use.

    May be omitted to use the default value of 0.
    """


AnyConnectRequest: TypeAlias = BluetoothConnectRequest | ConnectRequest
"""The connect (bridge) request variants."""


class ConnectResponse(smpmsg.WriteResponse):
    """Success response to a connect (bridge) request."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.CONNECT


class DisconnectRequest(smpmsg.WriteRequest):
    """Disconnect the bridge of the transport that receives this request."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.DISCONNECT


class DisconnectTransportRequest(smpmsg.WriteRequest):
    """Disconnect the bridge of the given transport."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.DISCONNECT

    transport: TransportTypeField
    """The transport to disconnect the bridge from."""


class DisconnectAllRequest(smpmsg.WriteRequest):
    """Disconnect all active bridges."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.DISCONNECT

    all: Literal[True]


AnyDisconnectRequest: TypeAlias = (
    DisconnectAllRequest | DisconnectTransportRequest | DisconnectRequest
)
"""The disconnect request variants."""


class DisconnectResponse(smpmsg.WriteResponse):
    """Success response to any of the disconnect requests."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.DISCONNECT


class StatusRequest(smpmsg.ReadRequest):
    """Request information on active bridges and on what the device supports."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.STATUS


class UnbridgedStatusResponse(smpmsg.ReadResponse):
    """The status of a transport that is not bridged."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.STATUS

    supported: UInt32
    """How many bridges can be active at a given time."""
    active: UInt32
    """How many bridges are currently active."""


class BridgedStatusResponse(smpmsg.ReadResponse):
    """The status of a bridged transport whose peer the device did not name."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.STATUS

    supported: UInt32
    """How many bridges can be active at a given time."""
    active: UInt32
    """How many bridges are currently active."""
    bridged: Literal[True]


class BridgedToTransportStatusResponse(smpmsg.ReadResponse):
    """The status of a bridged transport, naming the transport it is bridged to."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.STATUS

    supported: UInt32
    """How many bridges can be active at a given time."""
    active: UInt32
    """How many bridges are currently active."""
    bridged: Literal[True]
    transport: TransportTypeField
    """The transport that the transport that received the request is bridged to."""


AnyStatusResponse: TypeAlias = (
    BridgedToTransportStatusResponse | BridgedStatusResponse | UnbridgedStatusResponse
)
"""The status response variants."""


def loads_status_response(
    data: bytes,
    unbridged: type[UnbridgedStatusResponse] = UnbridgedStatusResponse,
    bridged: type[BridgedStatusResponse] = BridgedStatusResponse,
    bridged_to_transport: type[BridgedToTransportStatusResponse] = BridgedToTransportStatusResponse,
) -> AnyStatusResponse:
    """Deserialize a status response as the variant that its payload names.

    A device that serves this group from another group ID is read by passing
    the variants that carry its `_GROUP_ID`.
    """
    payload = cbor2.loads(data[smphdr.Header.SIZE :])

    if "transport" in payload:
        return bridged_to_transport.loads(data)
    if "bridged" in payload:
        return bridged.loads(data)
    return unbridged.loads(data)


class Transport(BaseModel):
    """A transport that supports bridging."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: TransportTypeField
    """The transport's ID."""
    name: str | None = None
    """The transport's name, if available."""


class ListOfTransportsRequest(smpmsg.ReadRequest):
    """Request information on the transports that the device supports."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.LIST


class ListOfTransportsResponse(smpmsg.ReadResponse):
    """SMP transport list response."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.LIST

    transports: tuple[Transport, ...]
    """The transports that support bridging."""


class Mode(BaseModel):
    """A configuration mode of a transport."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UInt32
    """The mode's ID, to be passed as the `mode` of a connect request."""
    description: str
    """A description of the mode."""
    incoming: Literal[True] | None = None
    """The mode supports incoming bridge connections."""
    outgoing: Literal[True] | None = None
    """The mode supports outgoing bridge connections."""


class TransportModesRequest(smpmsg.ReadRequest):
    """Request information on the modes of a transport."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.GET_MODES

    transport: TransportTypeField
    """The transport to get the modes of."""


class TransportModesResponse(smpmsg.ReadResponse):
    """SMP transport modes response."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.GET_MODES

    modes: tuple[Mode, ...]
    """The modes that the requested transport supports."""


class ConfigDetail(BaseModel):
    """A configuration item of a transport's mode."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    """The name of the configuration item, to be used as the key of the
    transport specific entry of a connect request.
    """
    type: ConfigType
    """The type of the configuration item."""
    required: Literal[True] | None = None
    """Present and true if the configuration item is required."""


class TransportConfigDetailsRequest(smpmsg.ReadRequest):
    """Request the configuration that a transport's mode accepts."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.GET_CONFIG_DETAILS

    transport: TransportTypeField
    """The transport to get configuration information for."""
    mode: UInt32
    """The mode of the transport to get configuration information for."""


class TransportConfigDetailsResponse(smpmsg.ReadResponse):
    """SMP transport configuration details response."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.GET_CONFIG_DETAILS

    configs: tuple[ConfigDetail, ...]
    """The configuration items that the requested transport's mode accepts.

    Empty for a transport that takes no configuration.
    """


@unique
class TRANSPORT_MGMT_ERR(IntEnum):
    """Return codes for the transport management group."""

    OK = 0
    """No error, this is implied if there is no ret value in the response."""

    UNKNOWN = 1
    """Unknown error occurred."""

    TRANSPORT_MISSING_REQUIRED_FUNCTIONS = 2
    """The transport is missing the required mandatory bridging functions."""

    TRANSPORT_MISSING_INFO_FUNCTIONS = 3
    """The transport is missing the information bridging functions."""

    INVALID_TRANSPORT = 4
    """Invalid, unsupported or no transport ID provided."""

    INVALID_MODE = 5
    """Invalid, unsupported or no mode provided."""

    ALL_CONTEXTS_USED = 6
    """All transport bridging context are in use."""

    BOTH_TRANSPORT_AND_ALL_PARAMETERS = 7
    """The transport or all parameters were both provided and only one should
    be supplied.
    """

    NOT_BRIDGED = 8
    """The transport is not bridged."""

    SAME_BRIDGE_DEVICE_DISALLOWED = 9
    """The transport does not support being used as both the input and output
    bridge device.
    """

    TRANSPORT_INGOING_NOT_SUPPORTED = 10
    """The transport does not support being used as the ingoing part of a
    bridge.
    """

    TRANSPORT_OUTGOING_NOT_SUPPORTED = 11
    """The transport does not support being used as the outgoing part of a
    bridge.
    """

    TRANSPORT_INCOMING_TRANSPORT_ALREADY_BRIDGED = 12
    """The incoming transport is already bridged to another transport."""

    TRANSPORT_OUTGOING_TRANSPORT_ALREADY_BRIDGED = 13
    """The outgoing transport is already bridged to another transport."""

    CONNECT_MISSING_PARAMETER = 14
    """The connection data provided is missing a parameter."""

    CONNECT_INVALID_PARAMETER = 15
    """An item in the connection data provided is invalid."""

    CONNECT_UNSUPPORTED_PARAMETER = 16
    """An item in the connection data provided is valid, but not supported by
    this device.
    """

    CONNECT_FAILED = 17
    """A bridge connection attempt has failed."""


class TransportManagementErrorV1(smperr.ErrorV1):
    """Error response to a transport management command."""

    _GROUP_ID = GROUP_ID


class TransportManagementErrorV2(smperr.ErrorV2[TRANSPORT_MGMT_ERR]):
    """Error response to a transport management command."""

    _GROUP_ID = GROUP_ID
