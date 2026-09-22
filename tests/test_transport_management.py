"""Test the SMP Transport Management group."""

from __future__ import annotations

from typing import Any, ClassVar, Literal

import msgspec
import msgspec_cbor
import pytest

from smp import header as smphdr
from smp import message as smpmsg
from smp import transport_management as smptrans
from smp.exceptions import SMPMalformed
from tests.helpers import assert_frame

tcmd = smphdr.CommandId.TransportManagement
GROUP = smphdr.GroupId.TRANSPORT_MANAGEMENT


def _frame(op: smphdr.OP, command_id: smphdr.AnyCommandId, payload: dict[str, Any]) -> bytes:
    data = msgspec_cbor.encode(payload, order="canonical")
    return (
        bytes(
            smphdr.Header(
                op=op,
                version=smphdr.Version.V2,
                flags=smphdr.Flag(0),
                length=len(data),
                group_id=GROUP,
                sequence=0,
                command_id=command_id,
            )
        )
        + data
    )


def test_ConnectRequest() -> None:
    frame = assert_frame(
        smptrans.ConnectRequest(transport=smptrans.TransportType.SHELL),
        op=smphdr.OP.WRITE,
        group_id=GROUP,
        command_id=tcmd.CONNECT,
    )
    assert frame.data.transport is smptrans.TransportType.SHELL

    assert_frame(
        smptrans.ConnectRequest(transport=smptrans.TransportType.RAW_SERIAL, mode=0),
        op=smphdr.OP.WRITE,
        group_id=GROUP,
        command_id=tcmd.CONNECT,
    )


def test_ConnectRequest_names_an_unknown_transport() -> None:
    """The enum is open: an ID this package does not name is still a member."""

    frame = smptrans.ConnectRequest.loads(_frame(smphdr.OP.WRITE, tcmd.CONNECT, {"transport": 9}))

    assert frame.data.transport == 9
    assert isinstance(frame.data.transport, smptrans.TransportType)
    assert frame.data.transport.name == "UNKNOWN_9"


@pytest.mark.parametrize("transport", [smptrans.TransportType.BLUETOOTH, 2])
def test_ConnectRequest_rejects_bluetooth_on_construction(transport: int) -> None:
    """Bluetooth takes parameters, so it is outside this variant's domain.

    The bare `2` is a type error as well; it is here to prove the runtime guard
    catches what a caller ignoring the type checker could still pass.
    """

    with pytest.raises(ValueError):
        smptrans.ConnectRequest(transport=transport)  # type: ignore[arg-type]


def test_ConnectRequest_rejects_bluetooth_on_the_wire() -> None:
    with pytest.raises(msgspec.DecodeError):
        smptrans.ConnectRequest.loads(_frame(smphdr.OP.WRITE, tcmd.CONNECT, {"transport": 2}))


def test_BluetoothConnectRequest() -> None:
    frame = assert_frame(
        smptrans.BluetoothConnectRequest(
            transport=smptrans.TransportType.BLUETOOTH,
            address="C0:FF:EE:C0:FF:EE",
            address_type=smptrans.BluetoothAddressType.RANDOM,
            le_coded=True,
        ),
        op=smphdr.OP.WRITE,
        group_id=GROUP,
        command_id=tcmd.CONNECT,
    )
    assert frame.data.address_type is smptrans.BluetoothAddressType.RANDOM


def test_BluetoothConnectRequest_requires_transport() -> None:
    """The discriminant is data, so a payload lacking it is malformed."""

    with pytest.raises(msgspec.ValidationError):
        smptrans.BluetoothConnectRequest.loads(
            _frame(smphdr.OP.WRITE, tcmd.CONNECT, {"address": "C0:FF:EE:C0:FF:EE"})
        )


def test_BluetoothConnectRequest_rejects_another_transport() -> None:
    with pytest.raises(ValueError):
        smptrans.BluetoothConnectRequest(
            transport=smptrans.TransportType.SHELL,  # type: ignore[arg-type]
            address="C0:FF:EE:C0:FF:EE",
        )

    with pytest.raises(msgspec.DecodeError):
        smptrans.BluetoothConnectRequest.loads(
            _frame(
                smphdr.OP.WRITE,
                tcmd.CONNECT,
                {"transport": 3, "address": "C0:FF:EE:C0:FF:EE"},
            )
        )


@pytest.mark.parametrize(
    "address", ["", "C0:FF:EE:C0:FF", "C0:FF:EE:C0:FF:EE:C0", "C0FFEEC0FFEE", "ZZ:FF:EE:C0:FF:EE"]
)
def test_BluetoothConnectRequest_rejects_a_malformed_address(address: str) -> None:
    with pytest.raises(ValueError):
        smptrans.BluetoothConnectRequest(
            transport=smptrans.TransportType.BLUETOOTH, address=address
        )

    with pytest.raises(msgspec.DecodeError):
        smptrans.BluetoothConnectRequest.loads(
            _frame(smphdr.OP.WRITE, tcmd.CONNECT, {"transport": 2, "address": address})
        )


def test_an_unmodeled_transport_gets_its_own_request_type() -> None:
    """A transport that takes parameters is a sibling variant, never a subclass."""

    class ModbusConnectRequest(smpmsg.WriteRequest, frozen=True):
        _GROUP_ID = smptrans.GROUP_ID
        _COMMAND_ID = tcmd.CONNECT

        transport: Literal[70]
        unit: smptrans.UInt32
        parity: str

    frame = assert_frame(
        ModbusConnectRequest(transport=70, unit=3, parity="even"),
        op=smphdr.OP.WRITE,
        group_id=GROUP,
        command_id=tcmd.CONNECT,
    )

    assert not isinstance(frame.data, smptrans.ConnectRequest)


def test_connect_variants_are_exhaustive() -> None:
    def describe(r: smptrans.AnyConnectRequest) -> str:
        match r:
            case smptrans.BluetoothConnectRequest():
                return f"ble {r.address}"
            case smptrans.ConnectRequest():
                return f"transport {int(r.transport)}"

    ble = smptrans.BluetoothConnectRequest(
        transport=smptrans.TransportType.BLUETOOTH, address="C0:FF:EE:C0:FF:EE"
    )
    serial = smptrans.ConnectRequest(transport=smptrans.TransportType.SERIAL)

    assert describe(ble) == "ble C0:FF:EE:C0:FF:EE"
    assert describe(serial) == "transport 0"

    assert not isinstance(ble, smptrans.ConnectRequest)
    assert not isinstance(serial, smptrans.BluetoothConnectRequest)


def test_ConnectResponse() -> None:
    assert_frame(
        smptrans.ConnectResponse(),
        op=smphdr.OP.WRITE_RSP,
        group_id=GROUP,
        command_id=tcmd.CONNECT,
        length=1,
    )


def test_DisconnectRequest() -> None:
    assert_frame(
        smptrans.DisconnectRequest(),
        op=smphdr.OP.WRITE,
        group_id=GROUP,
        command_id=tcmd.DISCONNECT,
        length=1,
    )


def test_DisconnectTransportRequest() -> None:
    frame = assert_frame(
        smptrans.DisconnectTransportRequest(transport=smptrans.TransportType.BLUETOOTH),
        op=smphdr.OP.WRITE,
        group_id=GROUP,
        command_id=tcmd.DISCONNECT,
    )
    assert frame.data.transport is smptrans.TransportType.BLUETOOTH


def test_DisconnectAllRequest() -> None:
    assert_frame(
        smptrans.DisconnectAllRequest(all=smpmsg.PRESENT),
        op=smphdr.OP.WRITE,
        group_id=GROUP,
        command_id=tcmd.DISCONNECT,
    )

    with pytest.raises(msgspec.DecodeError):
        smptrans.DisconnectAllRequest.loads(
            _frame(smphdr.OP.WRITE, tcmd.DISCONNECT, {"all": False})
        )


def test_DisconnectResponse() -> None:
    assert_frame(
        smptrans.DisconnectResponse(),
        op=smphdr.OP.WRITE_RSP,
        group_id=GROUP,
        command_id=tcmd.DISCONNECT,
        length=1,
    )


def test_disconnect_variants_are_exhaustive() -> None:
    def describe(r: smptrans.AnyDisconnectRequest) -> str:
        match r:
            case smptrans.DisconnectAllRequest():
                return "all"
            case smptrans.DisconnectTransportRequest():
                return f"transport {int(r.transport)}"
            case smptrans.DisconnectRequest():
                return "current"

    assert describe(smptrans.DisconnectAllRequest(all=smpmsg.PRESENT)) == "all"
    assert (
        describe(smptrans.DisconnectTransportRequest(transport=smptrans.TransportType.BLUETOOTH))
        == "transport 2"
    )
    assert describe(smptrans.DisconnectRequest()) == "current"


def test_StatusRequest() -> None:
    assert_frame(
        smptrans.StatusRequest(),
        op=smphdr.OP.READ,
        group_id=GROUP,
        command_id=tcmd.STATUS,
        length=1,
    )


def test_UnbridgedStatusResponse() -> None:
    assert_frame(
        smptrans.UnbridgedStatusResponse(supported=1, active=0),
        op=smphdr.OP.READ_RSP,
        group_id=GROUP,
        command_id=tcmd.STATUS,
    )


def test_BridgedStatusResponse() -> None:
    assert_frame(
        smptrans.BridgedStatusResponse(supported=1, active=1, bridged=smpmsg.PRESENT),
        op=smphdr.OP.READ_RSP,
        group_id=GROUP,
        command_id=tcmd.STATUS,
    )


def test_BridgedToTransportStatusResponse() -> None:
    frame = assert_frame(
        smptrans.BridgedToTransportStatusResponse(
            supported=4,
            active=1,
            bridged=smpmsg.PRESENT,
            transport=smptrans.TransportType.BLUETOOTH,
        ),
        op=smphdr.OP.READ_RSP,
        group_id=GROUP,
        command_id=tcmd.STATUS,
    )
    assert frame.data.transport is smptrans.TransportType.BLUETOOTH


def test_status_variants_are_exhaustive() -> None:
    def describe(r: smptrans.AnyStatusResponse) -> str:
        match r:
            case smptrans.BridgedToTransportStatusResponse():
                return f"bridged to {int(r.transport)}"
            case smptrans.BridgedStatusResponse():
                return "bridged"
            case smptrans.UnbridgedStatusResponse():
                return "unbridged"

    to = smptrans.BridgedToTransportStatusResponse(
        supported=1, active=1, bridged=smpmsg.PRESENT, transport=smptrans.TransportType.BLUETOOTH
    )
    bridged = smptrans.BridgedStatusResponse(supported=1, active=1, bridged=smpmsg.PRESENT)
    unbridged = smptrans.UnbridgedStatusResponse(supported=1, active=0)

    assert describe(to) == "bridged to 2"
    assert describe(bridged) == "bridged"
    assert describe(unbridged) == "unbridged"

    assert not isinstance(to, smptrans.BridgedStatusResponse)
    assert not isinstance(bridged, smptrans.BridgedToTransportStatusResponse)
    assert not isinstance(unbridged, smptrans.BridgedStatusResponse)


@pytest.mark.parametrize(
    ("payload", "variant"),
    [
        ({"supported": 1, "active": 0}, smptrans.UnbridgedStatusResponse),
        ({"supported": 1, "active": 1, "bridged": True}, smptrans.BridgedStatusResponse),
        (
            {"supported": 1, "active": 1, "bridged": True, "transport": 2},
            smptrans.BridgedToTransportStatusResponse,
        ),
    ],
)
def test_loads_status_response_picks_the_variant(
    payload: dict[str, Any], variant: type[smpmsg.Response]
) -> None:
    frame = smptrans.loads_status_response(_frame(smphdr.OP.READ_RSP, tcmd.STATUS, payload))

    assert type(frame.data) is variant


def test_loads_status_response_reads_a_relocated_group() -> None:
    """A device may serve this group from another group ID."""

    class CustomUnbridged(smptrans.UnbridgedStatusResponse, frozen=True):
        _GROUP_ID: ClassVar[smphdr.GroupIdField] = 0xABCD

    class CustomBridged(smptrans.BridgedStatusResponse, frozen=True):
        _GROUP_ID: ClassVar[smphdr.GroupIdField] = 0xABCD

    class CustomBridgedToTransport(smptrans.BridgedToTransportStatusResponse, frozen=True):
        _GROUP_ID: ClassVar[smphdr.GroupIdField] = 0xABCD

    frame = CustomBridgedToTransport(
        supported=1, active=1, bridged=smpmsg.PRESENT, transport=smptrans.TransportType.BLUETOOTH
    ).to_frame(sequence=0)

    assert (
        smptrans.loads_status_response(
            bytes(frame),
            unbridged=CustomUnbridged,
            bridged=CustomBridged,
            bridged_to_transport=CustomBridgedToTransport,
        )
        == frame
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"supported": 1, "active": 0, "bridged": False},
        {"supported": 1, "active": 0, "transport": 2},
        {"supported": 1, "active": 1, "bridged": False, "transport": 2},
    ],
)
def test_no_status_variant_accepts_an_impossible_payload(payload: dict[str, Any]) -> None:
    """`bridged` is only ever true, and `transport` only appears alongside it."""

    frame = _frame(smphdr.OP.READ_RSP, tcmd.STATUS, payload)

    for variant in (
        smptrans.UnbridgedStatusResponse,
        smptrans.BridgedStatusResponse,
        smptrans.BridgedToTransportStatusResponse,
    ):
        with pytest.raises(msgspec.DecodeError):
            variant.loads(frame)

    with pytest.raises(msgspec.DecodeError):
        smptrans.loads_status_response(frame)


def test_ListOfTransportsRequest() -> None:
    assert_frame(
        smptrans.ListOfTransportsRequest(),
        op=smphdr.OP.READ,
        group_id=GROUP,
        command_id=tcmd.LIST,
        length=1,
    )


def test_ListOfTransportsResponse() -> None:
    frame = smptrans.ListOfTransportsResponse.loads(
        _frame(
            smphdr.OP.READ_RSP,
            tcmd.LIST,
            {
                "transports": [
                    {"id": 0, "name": "uart"},
                    {"id": 2},
                    {"id": 9},
                    {"id": 64, "name": "modbus"},
                ]
            },
        )
    )
    transports = frame.data.transports

    assert transports[0].id is smptrans.TransportType.SERIAL
    assert transports[0].name == "uart"
    assert transports[1].name is None
    assert transports[2].id.name == "UNKNOWN_9"
    assert transports[3].id is smptrans.TransportType.USER_DEFINED


def test_TransportModesRequest() -> None:
    assert_frame(
        smptrans.TransportModesRequest(transport=smptrans.TransportType.BLUETOOTH),
        op=smphdr.OP.READ,
        group_id=GROUP,
        command_id=tcmd.GET_MODES,
    )


def test_TransportModesResponse() -> None:
    frame = smptrans.TransportModesResponse.loads(
        _frame(
            smphdr.OP.READ_RSP,
            tcmd.GET_MODES,
            {
                "modes": [
                    {"id": 0, "description": "UART", "incoming": True, "outgoing": True},
                    {"id": 1, "description": "Shell", "incoming": True},
                ]
            },
        )
    )

    assert frame.data.modes[0].outgoing == smpmsg.PRESENT
    assert frame.data.modes[1].outgoing is None


def test_Mode_rejects_a_false_flag() -> None:
    """A flag the protocol only ever emits as true is not a `bool`."""

    with pytest.raises(msgspec.DecodeError):
        smptrans.TransportModesResponse.loads(
            _frame(
                smphdr.OP.READ_RSP,
                tcmd.GET_MODES,
                {"modes": [{"id": 0, "description": "UART", "incoming": False}]},
            )
        )


def test_Mode_rejects_type_in_place_of_id() -> None:
    """A mode's ID is `id`; `type` is not accepted in its place."""

    with pytest.raises(msgspec.ValidationError):
        smptrans.TransportModesResponse.loads(
            _frame(
                smphdr.OP.READ_RSP,
                tcmd.GET_MODES,
                {"modes": [{"type": 0, "description": "Bluetooth Low Energy"}]},
            )
        )


def test_TransportConfigDetailsRequest() -> None:
    assert_frame(
        smptrans.TransportConfigDetailsRequest(transport=smptrans.TransportType.BLUETOOTH, mode=0),
        op=smphdr.OP.READ,
        group_id=GROUP,
        command_id=tcmd.GET_CONFIG_DETAILS,
    )


def test_TransportConfigDetailsResponse() -> None:
    frame = smptrans.TransportConfigDetailsResponse.loads(
        _frame(
            smphdr.OP.READ_RSP,
            tcmd.GET_CONFIG_DETAILS,
            {
                "configs": [
                    {"name": "address_type", "type": 0, "required": True},
                    {"name": "address", "type": 3, "required": True},
                    {"name": "le_coded", "type": 2},
                ]
            },
        )
    )
    configs = frame.data.configs

    assert configs[0].type is smptrans.ConfigType.UINT
    assert configs[1].type is smptrans.ConfigType.STRING
    assert configs[2].required is None


def test_TransportConfigDetailsResponse_empty() -> None:
    """A transport that takes no configuration."""

    frame = assert_frame(
        smptrans.TransportConfigDetailsResponse(configs=()),
        op=smphdr.OP.READ_RSP,
        group_id=GROUP,
        command_id=tcmd.GET_CONFIG_DETAILS,
    )
    assert frame.data.configs == ()


def test_ConfigDetail_rejects_a_false_required() -> None:
    with pytest.raises(msgspec.DecodeError):
        smptrans.TransportConfigDetailsResponse.loads(
            _frame(
                smphdr.OP.READ_RSP,
                tcmd.GET_CONFIG_DETAILS,
                {"configs": [{"name": "port", "type": 3, "required": False}]},
            )
        )


@pytest.mark.parametrize(
    ("msg", "op", "command_id"),
    [
        (smptrans.ConnectRequest, smphdr.OP.WRITE, tcmd.CONNECT),
        (smptrans.DisconnectTransportRequest, smphdr.OP.WRITE, tcmd.DISCONNECT),
        (smptrans.TransportModesRequest, smphdr.OP.READ, tcmd.GET_MODES),
    ],
)
def test_an_unknown_field_is_rejected(
    msg: type[smpmsg.Data], op: smphdr.OP, command_id: smphdr.AnyCommandId
) -> None:
    with pytest.raises(msgspec.ValidationError):
        msg.loads(_frame(op, command_id, {"transport": 3, "unexpected": True}))


@pytest.mark.parametrize(
    ("msg", "op", "command_id"),
    [
        (smptrans.ConnectRequest, smphdr.OP.WRITE, tcmd.CONNECT),
        (smptrans.DisconnectTransportRequest, smphdr.OP.WRITE, tcmd.DISCONNECT),
        (smptrans.TransportModesRequest, smphdr.OP.READ, tcmd.GET_MODES),
        (smptrans.DisconnectAllRequest, smphdr.OP.WRITE, tcmd.DISCONNECT),
    ],
)
def test_a_missing_required_field_is_rejected(
    msg: type[smpmsg.Data], op: smphdr.OP, command_id: smphdr.AnyCommandId
) -> None:
    with pytest.raises(msgspec.ValidationError):
        msg.loads(_frame(op, command_id, {}))


def test_custom_group_id() -> None:
    """A device may serve this group from another group ID."""

    class CustomStatusRequest(smptrans.StatusRequest, frozen=True):
        _GROUP_ID: ClassVar[smphdr.GroupIdField] = 0xABCD

    frame = CustomStatusRequest().to_frame(sequence=0)

    assert frame.header.group_id == 0xABCD
    assert CustomStatusRequest.loads(bytes(frame)) == frame


@pytest.mark.parametrize("command_id", list(smphdr.CommandId.TransportManagement))
def test_header_accepts_every_command_id(
    command_id: smphdr.CommandId.TransportManagement,
) -> None:
    header = smphdr.Header(
        op=smphdr.OP.READ,
        version=smphdr.Version.V2,
        flags=smphdr.Flag(0),
        length=0,
        group_id=GROUP,
        sequence=0,
        command_id=command_id,
    )

    assert header == smphdr.Header.loads(bytes(header))


@pytest.mark.parametrize("command_id", [3, 4, 5, 9, 255])
def test_header_rejects_reserved_and_unassigned_command_ids(command_id: int) -> None:
    """Command IDs 3 to 5 are reserved, and 9 onwards are unassigned."""

    with pytest.raises(ValueError):
        smphdr.Header(
            op=smphdr.OP.READ,
            version=smphdr.Version.V2,
            flags=smphdr.Flag(0),
            length=0,
            group_id=GROUP,
            sequence=0,
            command_id=command_id,
        )


@pytest.mark.parametrize("rc", [e.value for e in smptrans.TRANSPORT_MGMT_ERR])
def test_TransportManagementErrorV2(rc: int) -> None:
    frame = smptrans.TransportManagementErrorV2.loads(
        _frame(smphdr.OP.WRITE_RSP, tcmd.CONNECT, {"err": {"group": GROUP, "rc": rc}})
    )

    assert type(frame.data.err.rc) is smptrans.TRANSPORT_MGMT_ERR
    assert frame.data.err.rc == rc
    assert frame.data.err.group == GROUP


def test_TransportManagementErrorV1() -> None:
    frame = smptrans.TransportManagementErrorV1.loads(
        _frame(smphdr.OP.WRITE_RSP, tcmd.DISCONNECT, {"rc": 3, "rsn": "no such transport"})
    )

    assert frame.data.rc == 3
    assert frame.data.rsn == "no such transport"


def test_a_transport_out_of_uint32_range_is_rejected() -> None:
    with pytest.raises(ValueError):
        smptrans.TransportType(0x100000000)

    with pytest.raises(msgspec.DecodeError):
        smptrans.ConnectRequest.loads(
            _frame(smphdr.OP.WRITE, tcmd.CONNECT, {"transport": 0x100000000})
        )


def test_BluetoothConnectRequest_carries_a_mode() -> None:
    frame = assert_frame(
        smptrans.BluetoothConnectRequest(
            transport=smptrans.TransportType.BLUETOOTH,
            address="C0:FF:EE:C0:FF:EE",
            mode=0,
        ),
        op=smphdr.OP.WRITE,
        group_id=GROUP,
        command_id=tcmd.CONNECT,
    )

    assert frame.data.mode == 0


@pytest.mark.parametrize(
    "variant",
    [smptrans.BridgedStatusResponse, smptrans.BridgedToTransportStatusResponse],
)
def test_a_bridged_status_variant_rejects_a_false_flag(variant: type[smpmsg.Response]) -> None:
    """`bridged` is a `Present`, so `false` has no inhabitant to construct."""

    payload: dict[str, Any] = {"supported": 1, "active": 1, "bridged": False, "transport": 2}

    with pytest.raises(msgspec.DecodeError):
        variant.loads(_frame(smphdr.OP.READ_RSP, tcmd.STATUS, payload))


def test_loads_status_response_rejects_a_length_mismatch() -> None:
    frame = _frame(smphdr.OP.READ_RSP, tcmd.STATUS, {"supported": 1, "active": 0})

    with pytest.raises(SMPMalformed):
        smptrans.loads_status_response(frame + b"\x00")
