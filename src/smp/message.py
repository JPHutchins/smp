"""The Simple Management Protocol (SMP) message base classes.

An SMP message is a `Frame`: an SMP `Header` and its CBOR payload `Data`.
"""

from __future__ import annotations

from enum import IntEnum, unique
from typing import Any, ClassVar, Generic, TypeVar

import msgspec
import msgspec_cbor

from smp import header as smpheader
from smp.exceptions import SMPMalformed, SMPMismatchedGroupId

T = TypeVar("T", bound="Data")


class Data(msgspec.Struct, frozen=True, omit_defaults=True, forbid_unknown_fields=True):
    """The CBOR payload of an SMP `Frame`."""

    _OP: ClassVar[smpheader.OP]
    _FLAGS: ClassVar[smpheader.Flag] = smpheader.Flag(0)
    _GROUP_ID: ClassVar[smpheader.GroupIdField]
    _COMMAND_ID: ClassVar[
        smpheader.AnyCommandId
        | smpheader.CommandId.ImageManagement
        | smpheader.CommandId.OSManagement
        | smpheader.CommandId.ShellManagement
        | smpheader.CommandId.Intercreate
        | smpheader.CommandId.FileManagement
    ]

    def __bytes__(self) -> bytes:
        return msgspec_cbor.encode(self, order="canonical")

    def to_frame(
        self: T,
        sequence: int,
        version: smpheader.Version = smpheader.Version.V2,
        flags: smpheader.Flag | None = None,
    ) -> Frame[T]:
        """Wrap this `Data` in a `Frame`, synthesizing the SMP `Header`."""
        payload = bytes(self)
        return Frame(
            smpheader.Header(
                op=self._OP,
                version=version,
                flags=smpheader.Flag(self._FLAGS if flags is None else flags),
                length=len(payload),
                group_id=self._GROUP_ID,
                sequence=sequence,
                command_id=self._COMMAND_ID,
            ),
            self,
        )

    @classmethod
    def _validate_mapping(cls, data: dict[str, Any]) -> None:
        fields = msgspec.structs.fields(cls)
        known = frozenset(f.encode_name for f in fields)
        for key in data:
            if key not in known:
                raise msgspec.ValidationError(f"Object contains unknown field `{key}`")
        for field in fields:
            if field.required and field.encode_name not in data:
                raise msgspec.ValidationError(
                    f"Object missing required field `{field.encode_name}`"
                )

    @classmethod
    def _convert_mapping(cls: type[T], data: dict[str, Any]) -> T:
        return msgspec.convert(data, type=cls)

    @classmethod
    def _decode_payload(cls: type[T], payload: bytes) -> T:
        # Direct decode unless a subclass overrides _convert_mapping to discriminate
        # an int-like union or a bare dynamic map that msgspec cannot decode directly.
        if cls._convert_mapping.__func__ is Data._convert_mapping.__func__:  # type: ignore[attr-defined]
            return msgspec_cbor.decode(payload, type=cls)
        return cls._convert_mapping(msgspec_cbor.decode(payload, type=dict))

    @classmethod
    def loads(cls: type[T], frame: bytes) -> Frame[T]:
        """Deserialize an SMP `Frame` (header followed by CBOR payload)."""
        header = smpheader.Header.loads(frame[: smpheader.Header.SIZE])
        if header.length != len(frame) - smpheader.Header.SIZE:
            raise SMPMalformed(
                f"header.length {header.length} != payload length "
                f"{len(frame) - smpheader.Header.SIZE}"
            )
        if header.group_id != cls._GROUP_ID:
            raise SMPMismatchedGroupId(
                f"{cls.__name__} has {cls._GROUP_ID}, header has {header.group_id}"
            )
        return Frame(header, cls._decode_payload(frame[smpheader.Header.SIZE :]))

    @classmethod
    def load(cls: type[T], header: smpheader.Header, data: dict[str, Any]) -> Frame[T]:
        """Build a `Frame` from an SMP header and a decoded CBOR mapping."""
        if header.group_id != cls._GROUP_ID:
            raise SMPMismatchedGroupId(
                f"{cls.__name__} has {cls._GROUP_ID}, header has {header.group_id}"
            )
        return Frame(header, cls._convert_mapping(data))


class Frame(msgspec.Struct, Generic[T], frozen=True):
    """An SMP message: an SMP `Header` and its `Data` payload."""

    header: smpheader.Header
    data: T

    def __bytes__(self) -> bytes:
        return bytes(self.header) + bytes(self.data)


class Request(Data, frozen=True):
    """Base class for SMP Requests."""


@unique
class ResponseType(IntEnum):
    """An SMP `Response` to an SMP `Request` must be `SUCCESS`, `ERROR_V1`, or `ERROR_V2`."""

    SUCCESS = 0
    ERROR_V1 = 1
    ERROR_V2 = 2


class Response(Data, frozen=True):
    """Base class for SMP Responses."""

    RESPONSE_TYPE: ClassVar[ResponseType]


class ReadRequest(Request, frozen=True):
    """A read request from an SMP client to an SMP server."""

    _OP = smpheader.OP.READ


class ReadResponse(Response, frozen=True):
    """A response from an SMP server to an SMP client read request."""

    RESPONSE_TYPE = ResponseType.SUCCESS
    _OP = smpheader.OP.READ_RSP


class WriteRequest(Request, frozen=True):
    """A write request from an SMP client to an SMP server."""

    _OP = smpheader.OP.WRITE


class WriteResponse(Response, frozen=True):
    """A response from an SMP server to an SMP client write request."""

    RESPONSE_TYPE = ResponseType.SUCCESS
    _OP = smpheader.OP.WRITE_RSP
