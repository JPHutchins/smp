"""The Simple Management Protocol (SMP) message base classes.

An SMP message is a `Frame`: an SMP `Header` and its CBOR payload `Data`.
"""

from __future__ import annotations

import datetime
import decimal
import itertools
import uuid
from enum import IntEnum, unique
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar

import cbor2
import msgspec
import msgspec_cbor

from smp import header as smpheader
from smp.exceptions import SMPMismatchedGroupId

if TYPE_CHECKING:
    from collections.abc import Iterator

_counter = itertools.count()

# KLUDGE: duplicates msgspec_cbor._BUILTIN_TYPES. Only here because msgspec_cbor.encode()
# does not expose cbor2's length-first `canonical=True` ordering (it offers msgspec's
# lexicographic order= instead), so the encode path can't go through msgspec_cbor and
# reimplements its to_builtins()+cbor2 step. Real fix: add canonical ordering to
# msgspec_cbor.encode(), then this whole block collapses to `msgspec_cbor.encode(obj, ...)`.
_CBOR_NATIVE = (bytes, bytearray, datetime.datetime, datetime.date, decimal.Decimal, uuid.UUID)

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
        return cbor2.dumps(msgspec.to_builtins(self, builtin_types=_CBOR_NATIVE), canonical=True)

    def to_frame(
        self: T,
        *,
        version: smpheader.Version = smpheader.Version.V2,
        flags: smpheader.Flag | None = None,
        sequence: int | None = None,
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
                sequence=next(_counter) % 0xFF if sequence is None else sequence,
                command_id=self._COMMAND_ID,
            ),
            self,
        )

    @classmethod
    def loads(cls: type[T], frame: bytes) -> Frame[T]:
        """Deserialize an SMP `Frame` (header followed by CBOR payload)."""
        header = smpheader.Header.loads(frame[: smpheader.Header.SIZE])
        if header.group_id != cls._GROUP_ID:
            raise SMPMismatchedGroupId(
                f"{cls.__name__} has {cls._GROUP_ID}, header has {header.group_id}"
            )
        return Frame(header, msgspec_cbor.decode(frame[smpheader.Header.SIZE :], type=cls))

    @classmethod
    def load(cls: type[T], header: smpheader.Header, data: dict[str, Any]) -> Frame[T]:
        """Build a `Frame` from an SMP header and a decoded CBOR mapping."""
        if header.group_id != cls._GROUP_ID:
            raise SMPMismatchedGroupId(
                f"{cls.__name__} has {cls._GROUP_ID}, header has {header.group_id}"
            )
        return Frame(header, msgspec.convert(data, type=cls))


class Frame(msgspec.Struct, Generic[T], frozen=True):
    """An SMP message: an SMP `Header` and its `Data` payload."""

    header: smpheader.Header
    data: T

    def __bytes__(self) -> bytes:
        return bytes(self.header) + bytes(self.data)

    def __iter__(self) -> Iterator[Any]:
        return iter((self.header, self.data))


class Request(Data):
    """Base class for SMP Requests."""


@unique
class ResponseType(IntEnum):
    """An SMP `Response` to an SMP `Request` must be `SUCCESS`, `ERROR_V1`, or `ERROR_V2`."""

    SUCCESS = 0
    ERROR_V1 = 1
    ERROR_V2 = 2


class Response(Data):
    """Base class for SMP Responses."""

    RESPONSE_TYPE: ClassVar[ResponseType]


class ReadRequest(Request):
    """A read request from an SMP client to an SMP server."""

    _OP = smpheader.OP.READ


class ReadResponse(Response):
    """A response from an SMP server to an SMP client read request."""

    RESPONSE_TYPE = ResponseType.SUCCESS
    _OP = smpheader.OP.READ_RSP


class WriteRequest(Request):
    """A write request from an SMP client to an SMP server."""

    _OP = smpheader.OP.WRITE


class WriteResponse(Response):
    """A response from an SMP server to an SMP client write request."""

    RESPONSE_TYPE = ResponseType.SUCCESS
    _OP = smpheader.OP.WRITE_RSP
