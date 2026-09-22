"""Test the SMP Transport Management group."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, TypeVar

import cbor2
import pytest
from pydantic import ValidationError

from smp import header as smphdr
from smp import message as smpmsg
from smp import transport_management as smptrans
from tests.helpers import make_assert_header

if TYPE_CHECKING:
    from pydantic import BaseModel

T = TypeVar("T", bound=smpmsg._MessageBase)


def _do_test(
    msg: type[T],
    op: smphdr.OP,
    command_id: smphdr.CommandId.TransportManagement,
    data: dict[str, Any],
    nested_model: type[BaseModel] | None = None,
) -> T:
    cbor = cbor2.dumps(data, canonical=True)
    assert_header = make_assert_header(
        smphdr.GroupId.TRANSPORT_MANAGEMENT, op, command_id, len(cbor)
    )

    def _assert_common(r: smpmsg._MessageBase) -> None:
        assert_header(r)
        for k, v in data.items():
            if type(v) is tuple and nested_model is not None:
                for v2 in v:
                    assert v2 == nested_model(**v2).model_dump(exclude_none=True)
            else:
                assert v == getattr(r, k)
        assert cbor == r.BYTES[8:]

    r = msg(**data)

    _assert_common(r)  # serialize
    _assert_common(msg.loads(r.BYTES))  # deserialize

    return r


def _frame(
    op: smphdr.OP,
    command_id: smphdr.CommandId.TransportManagement,
    payload: dict[str, Any],
) -> bytes:
    d = cbor2.dumps(payload, canonical=True)
    return (
        smphdr.Header(
            op=op,
            version=smphdr.Version.V2,
            flags=smphdr.Flag(0),
            length=len(d),
            group_id=smphdr.GroupId.TRANSPORT_MANAGEMENT,
            sequence=0,
            command_id=command_id,
        ).BYTES
        + d
    )


def test_ConnectRequest() -> None:
    r = _do_test(
        smptrans.ConnectRequest,
        smphdr.OP.WRITE,
        smphdr.CommandId.TransportManagement.CONNECT,
        {"transport": smptrans.TransportType.SHELL},
    )
    assert type(r.transport) is smptrans.TransportType

    _do_test(
        smptrans.ConnectRequest,
        smphdr.OP.WRITE,
        smphdr.CommandId.TransportManagement.CONNECT,
        {"transport": smptrans.TransportType.RAW_SERIAL, "mode": 0},
    )


def test_BluetoothConnectRequest() -> None:
    r = _do_test(
        smptrans.BluetoothConnectRequest,
        smphdr.OP.WRITE,
        smphdr.CommandId.TransportManagement.CONNECT,
        {
            "transport": smptrans.TransportType.BLUETOOTH,
            "address": "C0:FF:EE:C0:FF:EE",
            "address_type": smptrans.BluetoothAddressType.RANDOM,
            "le_coded": True,
        },
    )
    assert r.address_type is smptrans.BluetoothAddressType.RANDOM


def test_BluetoothConnectRequest_requires_transport() -> None:
    """The discriminant is data, so a payload lacking it is malformed."""

    frame = _frame(
        smphdr.OP.WRITE,
        smphdr.CommandId.TransportManagement.CONNECT,
        {"address": "C0:FF:EE:C0:FF:EE"},
    )

    with pytest.raises(ValidationError):
        smptrans.BluetoothConnectRequest.loads(frame)

    with pytest.raises(ValidationError):
        smptrans.BluetoothConnectRequest(address="C0:FF:EE:C0:FF:EE")  # type: ignore[call-arg]


@pytest.mark.parametrize("transport", [smptrans.TransportType.BLUETOOTH, 2])
def test_ConnectRequest_rejects_bluetooth(transport: int) -> None:
    """Bluetooth takes parameters, so it is outside this variant's domain."""

    with pytest.raises(ValidationError):
        smptrans.ConnectRequest(transport=transport)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "address", ["", "C0:FF:EE:C0:FF", "C0:FF:EE:C0:FF:EE:C0", "C0FFEEC0FFEE", "ZZ:FF:EE:C0:FF:EE"]
)
def test_BluetoothConnectRequest_rejects_malformed_address(address: str) -> None:
    with pytest.raises(ValidationError):
        smptrans.BluetoothConnectRequest(
            transport=smptrans.TransportType.BLUETOOTH, address=address
        )


def test_BluetoothConnectRequest_rejects_another_transport() -> None:
    with pytest.raises(ValidationError):
        smptrans.BluetoothConnectRequest(
            transport=smptrans.TransportType.SHELL,  # type: ignore[arg-type]
            address="C0:FF:EE:C0:FF:EE",
        )

    with pytest.raises(ValidationError):
        smptrans.BluetoothConnectRequest.loads(
            smptrans.ConnectRequest(transport=smptrans.TransportType.SHELL).BYTES
        )


def test_an_unmodeled_transport_gets_its_own_request_type() -> None:
    """A transport that takes parameters is a sibling variant, never a subclass."""

    class ModbusConnectRequest(smpmsg.WriteRequest):
        _GROUP_ID = smptrans.GROUP_ID
        _COMMAND_ID = smphdr.CommandId.TransportManagement.CONNECT

        transport: Literal[70]
        unit: smptrans.UInt32
        parity: str

    r = ModbusConnectRequest(transport=70, unit=3, parity="even")

    assert cbor2.loads(r.BYTES[8:]) == {"transport": 70, "unit": 3, "parity": "even"}
    assert r == ModbusConnectRequest.loads(r.BYTES)
    assert not isinstance(r, smptrans.ConnectRequest)


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
    _do_test(
        smptrans.ConnectResponse,
        smphdr.OP.WRITE_RSP,
        smphdr.CommandId.TransportManagement.CONNECT,
        {},
    )


def test_DisconnectRequest() -> None:
    _do_test(
        smptrans.DisconnectRequest,
        smphdr.OP.WRITE,
        smphdr.CommandId.TransportManagement.DISCONNECT,
        {},
    )


def test_DisconnectTransportRequest() -> None:
    r = _do_test(
        smptrans.DisconnectTransportRequest,
        smphdr.OP.WRITE,
        smphdr.CommandId.TransportManagement.DISCONNECT,
        {"transport": smptrans.TransportType.BLUETOOTH},
    )
    assert type(r.transport) is smptrans.TransportType


def test_DisconnectAllRequest() -> None:
    _do_test(
        smptrans.DisconnectAllRequest,
        smphdr.OP.WRITE,
        smphdr.CommandId.TransportManagement.DISCONNECT,
        {"all": True},
    )

    with pytest.raises(ValidationError):
        smptrans.DisconnectAllRequest(all=False)  # type: ignore[arg-type]


def test_DisconnectResponse() -> None:
    _do_test(
        smptrans.DisconnectResponse,
        smphdr.OP.WRITE_RSP,
        smphdr.CommandId.TransportManagement.DISCONNECT,
        {},
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

    assert describe(smptrans.DisconnectAllRequest(all=True)) == "all"
    assert describe(smptrans.DisconnectTransportRequest(transport=2)) == "transport 2"
    assert describe(smptrans.DisconnectRequest()) == "current"


def test_StatusRequest() -> None:
    _do_test(
        smptrans.StatusRequest,
        smphdr.OP.READ,
        smphdr.CommandId.TransportManagement.STATUS,
        {},
    )


def test_UnbridgedStatusResponse() -> None:
    _do_test(
        smptrans.UnbridgedStatusResponse,
        smphdr.OP.READ_RSP,
        smphdr.CommandId.TransportManagement.STATUS,
        {"supported": 1, "active": 0},
    )


def test_BridgedStatusResponse() -> None:
    _do_test(
        smptrans.BridgedStatusResponse,
        smphdr.OP.READ_RSP,
        smphdr.CommandId.TransportManagement.STATUS,
        {"supported": 1, "active": 1, "bridged": True},
    )


def test_BridgedToTransportStatusResponse() -> None:
    r = _do_test(
        smptrans.BridgedToTransportStatusResponse,
        smphdr.OP.READ_RSP,
        smphdr.CommandId.TransportManagement.STATUS,
        {"supported": 4, "active": 1, "bridged": True, "transport": 2},
    )
    assert r.transport is smptrans.TransportType.BLUETOOTH


def test_status_variants_are_exhaustive() -> None:
    def describe(r: smptrans.AnyStatusResponse) -> str:
        match r:
            case smptrans.BridgedToTransportStatusResponse():
                return f"bridged to {int(r.transport)}"
            case smptrans.BridgedStatusResponse():
                return "bridged"
            case smptrans.UnbridgedStatusResponse():
                return "unbridged"

    to = smptrans.BridgedToTransportStatusResponse(supported=1, active=1, bridged=True, transport=2)
    bridged = smptrans.BridgedStatusResponse(supported=1, active=1, bridged=True)
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
    frame = _frame(smphdr.OP.READ_RSP, smphdr.CommandId.TransportManagement.STATUS, payload)

    assert type(smptrans.loads_status_response(frame)) is variant


def test_loads_status_response_reads_a_relocated_group() -> None:
    """A device may serve this group from another group ID."""

    class CustomUnbridged(smptrans.UnbridgedStatusResponse):
        _GROUP_ID = 0xABCD

    class CustomBridged(smptrans.BridgedStatusResponse):
        _GROUP_ID = 0xABCD

    class CustomBridgedToTransport(smptrans.BridgedToTransportStatusResponse):
        _GROUP_ID = 0xABCD

    r = CustomBridgedToTransport(supported=1, active=1, bridged=True, transport=2)

    assert (
        smptrans.loads_status_response(
            r.BYTES,
            unbridged=CustomUnbridged,
            bridged=CustomBridged,
            bridged_to_transport=CustomBridgedToTransport,
        )
        == r
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

    frame = _frame(smphdr.OP.READ_RSP, smphdr.CommandId.TransportManagement.STATUS, payload)

    for variant in (
        smptrans.UnbridgedStatusResponse,
        smptrans.BridgedStatusResponse,
        smptrans.BridgedToTransportStatusResponse,
    ):
        with pytest.raises(ValidationError):
            variant.loads(frame)

    with pytest.raises(ValidationError):
        smptrans.loads_status_response(frame)


def test_ListOfTransportsRequest() -> None:
    _do_test(
        smptrans.ListOfTransportsRequest,
        smphdr.OP.READ,
        smphdr.CommandId.TransportManagement.LIST,
        {},
    )


def test_ListOfTransportsResponse() -> None:
    r = _do_test(
        smptrans.ListOfTransportsResponse,
        smphdr.OP.READ_RSP,
        smphdr.CommandId.TransportManagement.LIST,
        {
            "transports": (
                {"id": 0, "name": "uart"},
                {"id": 2},
                {"id": 9},
                {"id": 64, "name": "modbus"},
            )
        },
        nested_model=smptrans.Transport,
    )

    assert type(r.transports[0].id) is smptrans.TransportType
    assert r.transports[0].id is smptrans.TransportType.SERIAL
    assert r.transports[1].name is None
    assert type(r.transports[2].id) is int
    assert r.transports[3].id is smptrans.TransportType.USER_DEFINED


def test_TransportModesRequest() -> None:
    _do_test(
        smptrans.TransportModesRequest,
        smphdr.OP.READ,
        smphdr.CommandId.TransportManagement.GET_MODES,
        {"transport": 2},
    )


def test_TransportModesResponse() -> None:
    r = _do_test(
        smptrans.TransportModesResponse,
        smphdr.OP.READ_RSP,
        smphdr.CommandId.TransportManagement.GET_MODES,
        {
            "modes": (
                {"id": 0, "description": "UART", "incoming": True, "outgoing": True},
                {"id": 1, "description": "Shell", "incoming": True},
            )
        },
        nested_model=smptrans.Mode,
    )

    assert r.modes[1].outgoing is None


def test_Mode_rejects_type_in_place_of_id() -> None:
    """A mode's ID is `id`; `type` is not accepted in its place."""

    with pytest.raises(ValidationError):
        smptrans.Mode(type=0, description="Bluetooth Low Energy")  # type: ignore[call-arg]


def test_TransportConfigDetailsRequest() -> None:
    _do_test(
        smptrans.TransportConfigDetailsRequest,
        smphdr.OP.READ,
        smphdr.CommandId.TransportManagement.GET_CONFIG_DETAILS,
        {"transport": 2, "mode": 0},
    )


def test_TransportConfigDetailsResponse() -> None:
    r = _do_test(
        smptrans.TransportConfigDetailsResponse,
        smphdr.OP.READ_RSP,
        smphdr.CommandId.TransportManagement.GET_CONFIG_DETAILS,
        {
            "configs": (
                {"name": "address_type", "type": 0, "required": True},
                {"name": "address", "type": 3, "required": True},
                {"name": "le_coded", "type": 2},
            )
        },
        nested_model=smptrans.ConfigDetail,
    )

    assert r.configs[0].type is smptrans.ConfigType.UINT
    assert r.configs[1].type is smptrans.ConfigType.STRING
    assert r.configs[2].required is None


def test_TransportConfigDetailsResponse_empty() -> None:
    """A transport that takes no configuration."""

    r = _do_test(
        smptrans.TransportConfigDetailsResponse,
        smphdr.OP.READ_RSP,
        smphdr.CommandId.TransportManagement.GET_CONFIG_DETAILS,
        {"configs": ()},
    )
    assert r.configs == ()


@pytest.mark.parametrize(
    ("msg", "op", "command_id"),
    [
        (
            smptrans.ConnectRequest,
            smphdr.OP.WRITE,
            smphdr.CommandId.TransportManagement.CONNECT,
        ),
        (
            smptrans.DisconnectTransportRequest,
            smphdr.OP.WRITE,
            smphdr.CommandId.TransportManagement.DISCONNECT,
        ),
        (
            smptrans.TransportModesRequest,
            smphdr.OP.READ,
            smphdr.CommandId.TransportManagement.GET_MODES,
        ),
    ],
)
def test_extra_fields_are_forbidden(
    msg: type[smpmsg.Request],
    op: smphdr.OP,
    command_id: smphdr.CommandId.TransportManagement,
) -> None:
    with pytest.raises(ValidationError):
        msg.loads(_frame(op, command_id, {"transport": 3, "unexpected": True}))


def test_custom_group_id() -> None:
    """A device may serve this group from another group ID."""

    class CustomStatusRequest(smptrans.StatusRequest):
        _GROUP_ID = 0xABCD

    r = CustomStatusRequest()

    assert r.header.group_id == 0xABCD
    assert r == CustomStatusRequest.loads(r.BYTES)


@pytest.mark.parametrize("rc", [e.value for e in smptrans.TRANSPORT_MGMT_ERR])
def test_TransportManagementErrorV2(rc: int) -> None:
    d = cbor2.dumps({"err": {"group": smphdr.GroupId.TRANSPORT_MANAGEMENT, "rc": rc}})
    h = smphdr.Header(
        op=smphdr.OP.WRITE_RSP,
        version=smphdr.Version.V2,
        flags=smphdr.Flag(0),
        length=len(d),
        group_id=smphdr.GroupId.TRANSPORT_MANAGEMENT,
        sequence=0,
        command_id=smphdr.CommandId.TransportManagement.CONNECT,
    )

    e = smptrans.TransportManagementErrorV2.loads(h.BYTES + d)

    assert smptrans.TRANSPORT_MGMT_ERR is type(e.err.rc)
    assert rc == e.err.rc
    assert e.err.group == smphdr.GroupId.TRANSPORT_MANAGEMENT


def test_TransportManagementErrorV1() -> None:
    d = cbor2.dumps({"rc": 3, "rsn": "no such transport"})
    h = smphdr.Header(
        op=smphdr.OP.WRITE_RSP,
        version=smphdr.Version.V1,
        flags=smphdr.Flag(0),
        length=len(d),
        group_id=smphdr.GroupId.TRANSPORT_MANAGEMENT,
        sequence=0,
        command_id=smphdr.CommandId.TransportManagement.DISCONNECT,
    )

    e = smptrans.TransportManagementErrorV1.loads(h.BYTES + d)

    assert e.rc == 3
    assert e.rsn == "no such transport"


@pytest.mark.parametrize("command_id", list(smphdr.CommandId.TransportManagement))
def test_header_accepts_every_command_id(
    command_id: smphdr.CommandId.TransportManagement,
) -> None:
    h = smphdr.Header(
        op=smphdr.OP.READ,
        version=smphdr.Version.V2,
        flags=smphdr.Flag(0),
        length=0,
        group_id=smphdr.GroupId.TRANSPORT_MANAGEMENT,
        sequence=0,
        command_id=command_id,
    )

    assert h == smphdr.Header.loads(h.BYTES)


@pytest.mark.parametrize("command_id", [3, 4, 5, 9, 255])
def test_header_rejects_reserved_and_unassigned_command_ids(command_id: int) -> None:
    """Command IDs 3 to 5 are reserved, and 9 onwards are unassigned."""

    with pytest.raises(ValueError):
        smphdr.Header(
            op=smphdr.OP.READ,
            version=smphdr.Version.V2,
            flags=smphdr.Flag(0),
            length=0,
            group_id=smphdr.GroupId.TRANSPORT_MANAGEMENT,
            sequence=0,
            command_id=command_id,
        )


def test_Mode_rejects_a_false_flag() -> None:
    """A flag the protocol only ever emits as true is not a `bool`."""

    with pytest.raises(ValidationError):
        smptrans.Mode(id=0, description="UART", incoming=False)  # type: ignore[arg-type]

    with pytest.raises(ValidationError):
        smptrans.Mode(id=0, description="UART", outgoing=False)  # type: ignore[arg-type]


def test_ConfigDetail_rejects_a_false_required() -> None:
    with pytest.raises(ValidationError):
        smptrans.ConfigDetail(
            name="port",
            type=smptrans.ConfigType.STRING,
            required=False,  # type: ignore[arg-type]
        )
