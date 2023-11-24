"""Test the SMP Image Management group."""

import cbor2

from smp import header as smpheader
from smp.os_management import (
    EchoWriteRequest,
    EchoWriteResponse,
    ResetWriteRequest,
    ResetWriteResponse,
)
from tests.helpers import make_assert_header


def test_EchoWriteRequest() -> None:
    data = cbor2.dumps({"d": "Hello world!"})

    assert_header = make_assert_header(
        smpheader.GroupId.OS_MANAGEMENT,
        smpheader.OP.WRITE,
        smpheader.CommandId.OSManagement.ECHO,
        len(data),
    )
    r = EchoWriteRequest(d="Hello world!")

    assert_header(r)
    assert "Hello world!" == r.d
    assert data == r.BYTES[8:]

    r = EchoWriteRequest.loads(r.BYTES)
    assert_header(r)
    assert "Hello world!" == r.d
    assert data == r.BYTES[8:]


def test_EchoWriteResponse() -> None:
    data = cbor2.dumps({"r": "Hi!"})
    assert_header = make_assert_header(
        smpheader.GroupId.OS_MANAGEMENT,
        smpheader.OP.WRITE_RSP,
        smpheader.CommandId.OSManagement.ECHO,
        len(data),
    )

    server_response = EchoWriteResponse(sequence=0, r="Hi!")
    assert_header(server_response)
    assert "Hi!" == server_response.r
    assert data == server_response.BYTES[8:]

    r = EchoWriteResponse.loads(server_response.BYTES)
    assert_header(r)
    assert "Hi!" == r.r
    assert data == r.BYTES[8:]


def test_ResetWriteRequest() -> None:
    data = cbor2.dumps({})

    assert_header = make_assert_header(
        smpheader.GroupId.OS_MANAGEMENT,
        smpheader.OP.WRITE,
        smpheader.CommandId.OSManagement.RESET,
        len(data),
    )
    r = ResetWriteRequest()

    assert_header(r)
    assert data == r.BYTES[8:]

    r = ResetWriteRequest.loads(r.BYTES)
    assert_header(r)
    assert data == r.BYTES[8:]


def test_ResetWriteResponse() -> None:
    data = cbor2.dumps({})

    assert_header = make_assert_header(
        smpheader.GroupId.OS_MANAGEMENT,
        smpheader.OP.WRITE_RSP,
        smpheader.CommandId.OSManagement.RESET,
        len(data),
    )
    r = ResetWriteResponse()

    assert_header(r)
    assert data == r.BYTES[8:]

    r = ResetWriteResponse.loads(r.BYTES)
    assert_header(r)
    assert data == r.BYTES[8:]
