"""The Simple Management Protocol (SMP) Message base class."""

from __future__ import annotations

import itertools
import logging
from abc import ABC
from enum import IntEnum, unique
from typing import ClassVar, Final, Generic, NamedTuple, Type, TypeVar, cast

import cbor2
from pydantic import BaseModel, ConfigDict

from smp import header as smpheader
from smp.exceptions import SMPMalformed, SMPMismatchedGroupId

T = TypeVar("T", bound='SMPData')


_counter = itertools.count()
logger = logging.getLogger(__name__)


class SMPData(ABC, BaseModel):
    """Base class for SMP data."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    # metadata for generating a matching header - provided by implementations
    _OP: ClassVar[smpheader.OP]
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
        """Serialize the SMP data to bytes."""
        return cbor2.dumps(self.model_dump(exclude_unset=True, exclude_none=True), canonical=True)

    def to_frame(
        self: T,
        version: smpheader.Version = smpheader.Version.V2,
        flags: smpheader.Flag = smpheader.Flag(0),
        sequence: int | None = None,
    ) -> Frame[T]:
        """Create the SMP Frame.

        Params:
        - version: The SMP version. Defaults to `smp.header.Version.V2`.
        - flags: The SMP flags. Defaults to `smp.header.Flag(0)`.
        - sequence: The sequence number of the message. If not provided, it will
            be automatically generated using a global counter.

        """
        smp_data: Final = bytes(self)

        return Frame(
            header=smpheader.Header(
                op=self._OP,
                version=version,
                flags=flags,
                length=len(smp_data),
                group_id=self._GROUP_ID,
                sequence=next(_counter) % 0xFF if sequence is None else sequence,
                command_id=self._COMMAND_ID,
            ),
            smp_data=self,
        )

    @classmethod
    def loads(cls: Type[T], frame: bytes) -> Frame[T]:
        """Deserialize the SMP message."""
        header = smpheader.Header.loads(frame[: smpheader.Header.SIZE])

        if header.group_id != cls._GROUP_ID:  # pragma: no cover
            raise SMPMismatchedGroupId(
                f"{cls.__name__} has {cls._GROUP_ID}, header has {header.group_id}"
            )

        if header.length != len(frame) - smpheader.Header.SIZE:  # pragma: no cover
            raise SMPMalformed(
                f"header.length {header.length} != len(frame) {len(frame) - smpheader.Header.SIZE}"
            )

        return Frame(
            header=header, smp_data=cls(**cast(dict, cbor2.loads(frame[smpheader.Header.SIZE :])))
        )

    @classmethod
    def load(cls: Type[T], header: smpheader.Header, data: dict) -> Frame[T]:
        """Load an SMP header and CBOR dict into a Frame."""
        if header.group_id != cls._GROUP_ID:  # pragma: no cover
            raise SMPMismatchedGroupId(
                f"{cls.__name__} has {cls._GROUP_ID}, header has {header.group_id}"
            )
        if header.command_id != cls._COMMAND_ID:  # pragma: no cover
            raise SMPMalformed(
                f"{cls.__name__} has {cls._COMMAND_ID}, header has {header.command_id}"
            )
        return Frame(header=header, smp_data=cls(**data))


class Frame(NamedTuple, Generic[T]):
    """A deserialized SMP message frame."""

    header: smpheader.Header
    smp_data: T

    def __bytes__(self) -> bytes:
        """Serialize the SMP message frame to bytes."""
        return bytes(self.header) + bytes(self.smp_data)


class Request(SMPData, ABC):
    """Base class for SMP Requests."""


@unique
class ResponseType(IntEnum):
    """An SMP `Response` to an SMP `Request` must be `SUCCESS`, `ERROR_V1`, or `ERROR_V2`."""

    SUCCESS = 0
    ERROR_V1 = 1
    ERROR_V2 = 2


class Response(SMPData, ABC):
    """Base class for SMP Responses."""

    RESPONSE_TYPE: ClassVar[ResponseType]


class ReadRequest(Request, ABC):
    """A read request from an SMP client to an SMP server."""

    _OP = smpheader.OP.READ


class ReadResponse(Response, ABC):
    """A response from an SMP server to an SMP client read request."""

    RESPONSE_TYPE = ResponseType.SUCCESS
    _OP = smpheader.OP.READ_RSP


class WriteRequest(Request, ABC):
    """A write request from an SMP client to an SMP server."""

    _OP = smpheader.OP.WRITE


class WriteResponse(Response, ABC):
    """A response from an SMP server to an SMP client write request."""

    RESPONSE_TYPE = ResponseType.SUCCESS
    _OP = smpheader.OP.WRITE_RSP
