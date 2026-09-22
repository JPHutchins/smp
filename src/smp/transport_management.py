"""The Simple Management Protocol (SMP) Transport Management group."""

from __future__ import annotations

import re
from enum import IntEnum, unique
from typing import Annotated, Any, Literal, TypeAlias

import msgspec
import msgspec_cbor

import smp.error as smperr
import smp.header as smphdr
import smp.message as smpmsg
from smp.exceptions import SMPMalformed

GROUP_ID: smphdr.GroupIdField = smphdr.GroupId.TRANSPORT_MANAGEMENT
"""The group ID that this module's messages are addressed to.

A device may serve this group from another group ID; subclass the messages that
such a device is sent and override `_GROUP_ID`.
"""

UInt32: TypeAlias = Annotated[int, msgspec.Meta(ge=0, le=0xFFFFFFFF)]


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

    @classmethod
    def _missing_(cls, value: object) -> TransportType | None:
        """A device may serve a transport this package does not name."""
        if type(value) is int and 0 <= value <= 0xFFFFFFFF:
            unknown = int.__new__(cls, value)
            unknown._name_ = f"UNKNOWN_{value}"
            unknown._value_ = value
            return unknown
        return None


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


_BLUETOOTH_ADDRESS_PATTERN = r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"
_BLUETOOTH_ADDRESS = re.compile(_BLUETOOTH_ADDRESS_PATTERN)

BluetoothAddress: TypeAlias = Annotated[str, msgspec.Meta(pattern=_BLUETOOTH_ADDRESS_PATTERN)]


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


class TransportManagementErrorV1(smperr.ErrorV1, frozen=True):
    """Error response to a transport management command."""

    _GROUP_ID = GROUP_ID


class TransportManagementErrorV2(smperr.ErrorV2[TRANSPORT_MGMT_ERR], frozen=True):
    """Error response to a transport management command."""

    _GROUP_ID = GROUP_ID


class _TransportGroupBase:
    _ErrorV1 = TransportManagementErrorV1
    _ErrorV2 = TransportManagementErrorV2


class ConnectResponse(smpmsg.WriteResponse, frozen=True):
    """Success response to a connect (bridge) request."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.CONNECT


class ConnectRequest(smpmsg.WriteRequest, _TransportGroupBase, frozen=True):
    """Bridge to a transport that takes no parameters beyond `transport` and `mode`.

    A transport that takes parameters gets its own request type, the way
    `BluetoothConnectRequest` does.
    """

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.CONNECT
    _Response = ConnectResponse

    transport: TransportType
    """The transport to bridge the transport that receives this request to.

    Bluetooth is excluded; it takes parameters, so it has its own request type.
    """
    mode: UInt32 | None = None
    """The configuration mode of the transport to use.

    May be omitted to use the default value of 0.
    """

    def __post_init__(self) -> None:
        if self.transport == TransportType.BLUETOOTH:
            raise msgspec.ValidationError(
                "Bluetooth takes connect parameters; use BluetoothConnectRequest"
            )


class BluetoothConnectRequest(smpmsg.WriteRequest, _TransportGroupBase, frozen=True):
    """Bridge to the Bluetooth transport."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.CONNECT
    _Response = ConnectResponse

    transport: Literal[TransportType.BLUETOOTH]
    address: BluetoothAddress
    """The address of the peripheral to connect to."""
    address_type: BluetoothAddressType | None = None
    """The type of `address`."""
    le_coded: bool | None = None
    """Request the LE Coded PHY instead of the 1M PHY."""
    mode: UInt32 | None = None
    """The configuration mode of the transport to use.

    May be omitted to use the default value of 0.
    """

    def __post_init__(self) -> None:
        if self.transport != TransportType.BLUETOOTH:
            raise msgspec.ValidationError(f"transport {self.transport!r} is not Bluetooth")
        if _BLUETOOTH_ADDRESS.match(self.address) is None:
            raise msgspec.ValidationError(f"address {self.address!r} is not a Bluetooth address")

    @classmethod
    def _convert_mapping(cls, data: dict[str, Any]) -> BluetoothConnectRequest:
        cls._validate_mapping(data)
        if msgspec.convert(data["transport"], type=UInt32) != TransportType.BLUETOOTH:
            raise msgspec.ValidationError("transport is not Bluetooth")
        return cls(
            transport=TransportType.BLUETOOTH,
            address=msgspec.convert(data["address"], type=BluetoothAddress),
            address_type=msgspec.convert(data["address_type"], type=BluetoothAddressType)
            if "address_type" in data
            else None,
            le_coded=msgspec.convert(data["le_coded"], type=bool) if "le_coded" in data else None,
            mode=msgspec.convert(data["mode"], type=UInt32) if "mode" in data else None,
        )


AnyConnectRequest: TypeAlias = BluetoothConnectRequest | ConnectRequest
"""The connect (bridge) request variants."""


class DisconnectResponse(smpmsg.WriteResponse, frozen=True):
    """Success response to any of the disconnect requests."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.DISCONNECT


class DisconnectRequest(smpmsg.WriteRequest, _TransportGroupBase, frozen=True):
    """Disconnect the bridge of the transport that receives this request."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.DISCONNECT
    _Response = DisconnectResponse


class DisconnectTransportRequest(smpmsg.WriteRequest, _TransportGroupBase, frozen=True):
    """Disconnect the bridge of the given transport."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.DISCONNECT
    _Response = DisconnectResponse

    transport: TransportType
    """The transport to disconnect the bridge from."""


class DisconnectAllRequest(smpmsg.WriteRequest, _TransportGroupBase, frozen=True):
    """Disconnect all active bridges."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.DISCONNECT
    _Response = DisconnectResponse

    all: smpmsg.Present


AnyDisconnectRequest: TypeAlias = (
    DisconnectAllRequest | DisconnectTransportRequest | DisconnectRequest
)
"""The disconnect request variants."""


class UnbridgedStatusResponse(smpmsg.ReadResponse, frozen=True):
    """The status of a transport that is not bridged."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.STATUS

    supported: UInt32
    """How many bridges can be active at a given time."""
    active: UInt32
    """How many bridges are currently active."""


class BridgedStatusResponse(smpmsg.ReadResponse, frozen=True):
    """The status of a bridged transport whose peer the device did not name."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.STATUS

    supported: UInt32
    """How many bridges can be active at a given time."""
    active: UInt32
    """How many bridges are currently active."""
    bridged: smpmsg.Present


class BridgedToTransportStatusResponse(smpmsg.ReadResponse, frozen=True):
    """The status of a bridged transport, naming the transport it is bridged to."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.STATUS

    supported: UInt32
    """How many bridges can be active at a given time."""
    active: UInt32
    """How many bridges are currently active."""
    bridged: smpmsg.Present
    transport: TransportType
    """The transport that the transport that received the request is bridged to."""


AnyStatusResponse: TypeAlias = (
    BridgedToTransportStatusResponse | BridgedStatusResponse | UnbridgedStatusResponse
)
"""The status response variants."""

AnyStatusFrame: TypeAlias = (
    smpmsg.Frame[BridgedToTransportStatusResponse]
    | smpmsg.Frame[BridgedStatusResponse]
    | smpmsg.Frame[UnbridgedStatusResponse]
)
"""A `Frame` carrying one of the status response variants."""


class StatusRequest(smpmsg.ReadRequest, _TransportGroupBase, frozen=True):
    """Request information on active bridges and on what the device supports."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.STATUS
    _Response = UnbridgedStatusResponse


def loads_status_response(
    frame: bytes,
    unbridged: type[UnbridgedStatusResponse] = UnbridgedStatusResponse,
    bridged: type[BridgedStatusResponse] = BridgedStatusResponse,
    bridged_to_transport: type[BridgedToTransportStatusResponse] = BridgedToTransportStatusResponse,
) -> AnyStatusFrame:
    """Deserialize a status response as the variant that its payload names.

    A device that serves this group from another group ID is read by passing
    the variants that carry its `_GROUP_ID`.
    """
    header = smphdr.Header.loads(frame[: smphdr.Header.SIZE])
    payload = frame[smphdr.Header.SIZE :]
    if header.length != len(payload):
        raise SMPMalformed(f"header.length {header.length} != payload length {len(payload)}")

    mapping: dict[str, Any] = msgspec_cbor.decode(payload, type=dict)

    if "transport" in mapping:
        return bridged_to_transport.load(header, mapping)
    if "bridged" in mapping:
        return bridged.load(header, mapping)
    return unbridged.load(header, mapping)


class Transport(msgspec.Struct, frozen=True, omit_defaults=True, forbid_unknown_fields=True):
    """A transport that supports bridging."""

    id: TransportType
    """The transport's ID."""
    name: str | None = None
    """The transport's name, if available."""


class ListOfTransportsResponse(smpmsg.ReadResponse, frozen=True):
    """SMP transport list response."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.LIST

    transports: tuple[Transport, ...]
    """The transports that support bridging."""


class ListOfTransportsRequest(smpmsg.ReadRequest, _TransportGroupBase, frozen=True):
    """Request information on the transports that the device supports."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.LIST
    _Response = ListOfTransportsResponse


class Mode(msgspec.Struct, frozen=True, omit_defaults=True, forbid_unknown_fields=True):
    """A configuration mode of a transport."""

    id: UInt32
    """The mode's ID, to be passed as the `mode` of a connect request."""
    description: str
    """A description of the mode."""
    incoming: smpmsg.Present | None = None
    """The mode supports incoming bridge connections."""
    outgoing: smpmsg.Present | None = None
    """The mode supports outgoing bridge connections."""


class TransportModesResponse(smpmsg.ReadResponse, frozen=True):
    """SMP transport modes response."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.GET_MODES

    modes: tuple[Mode, ...]
    """The modes that the requested transport supports."""


class TransportModesRequest(smpmsg.ReadRequest, _TransportGroupBase, frozen=True):
    """Request information on the modes of a transport."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.GET_MODES
    _Response = TransportModesResponse

    transport: TransportType
    """The transport to get the modes of."""


class ConfigDetail(msgspec.Struct, frozen=True, omit_defaults=True, forbid_unknown_fields=True):
    """A configuration item of a transport's mode."""

    name: str
    """The name of the configuration item, to be used as the key of the
    transport specific entry of a connect request.
    """
    type: ConfigType
    """The type of the configuration item."""
    required: smpmsg.Present | None = None
    """Present and true if the configuration item is required."""


class TransportConfigDetailsResponse(smpmsg.ReadResponse, frozen=True):
    """SMP transport configuration details response."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.GET_CONFIG_DETAILS

    configs: tuple[ConfigDetail, ...]
    """The configuration items that the requested transport's mode accepts.

    Empty for a transport that takes no configuration.
    """


class TransportConfigDetailsRequest(smpmsg.ReadRequest, _TransportGroupBase, frozen=True):
    """Request the configuration that a transport's mode accepts."""

    _GROUP_ID = GROUP_ID
    _COMMAND_ID = smphdr.CommandId.TransportManagement.GET_CONFIG_DETAILS
    _Response = TransportConfigDetailsResponse

    transport: TransportType
    """The transport to get configuration information for."""
    mode: UInt32
    """The mode of the transport to get configuration information for."""
