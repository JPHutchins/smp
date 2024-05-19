"""The Simple Management Protocol (SMP) Message base class."""

from __future__ import annotations

import itertools
from abc import ABC
from enum import IntEnum, unique
from typing import ClassVar, Type, TypeVar, cast

import cbor2
from pydantic import BaseModel, ConfigDict

from smp import header as smpheader
from smp.exceptions import SMPMalformed, SMPMismatchedGroupId

T = TypeVar("T", bound='_MessageBase')


_counter = itertools.count()


class _MessageBase(ABC, BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    _OP: ClassVar[smpheader.OP]
    _VERSION: ClassVar[smpheader.Version] = smpheader.Version.V0
    _FLAGS: ClassVar[smpheader.Flag] = smpheader.Flag(0)
    _GROUP_ID: ClassVar[smpheader.GroupId | smpheader.UserGroupId | smpheader.AnyGroupId]
    _COMMAND_ID: ClassVar[
        smpheader.AnyCommandId
        | smpheader.CommandId.ImageManagement
        | smpheader.CommandId.OSManagement
        | smpheader.CommandId.ShellManagement
        | smpheader.CommandId.Intercreate
    ]

    header: smpheader.Header | None = None

    def __bytes__(self) -> bytes:
        return self._bytes  # type: ignore

    @property
    def BYTES(self) -> bytes:
        return self._bytes  # type: ignore

    @classmethod
    def loads(cls: Type[T], data: bytes) -> T:
        """Deserialize the SMP message."""
        message = cls(
            header=smpheader.Header.loads(data[: smpheader.Header.SIZE]),
            **cast(dict, cbor2.loads(data[smpheader.Header.SIZE :])),
        )
        if message.header is None:  # pragma: no cover
            raise ValueError
        if message.header.group_id != cls._GROUP_ID:  # pragma: no cover
            raise SMPMismatchedGroupId(
                f"{cls.__name__} has {cls._GROUP_ID}, header has {message.header.group_id}"
            )
        return message

    @classmethod
    def load(cls: Type[T], header: smpheader.Header, data: dict) -> T:
        """Load an SMP header and CBOR dict."""
        if header.group_id != cls._GROUP_ID:  # pragma: no cover
            raise SMPMismatchedGroupId(
                f"{cls.__name__} has {cls._GROUP_ID}, header has {header.group_id}"
            )
        return cls(header=header, **data)


class Request(_MessageBase, ABC):
    def model_post_init(self, _: None) -> None:
        data_bytes = cbor2.dumps(
            self.model_dump(exclude_unset=True, exclude={'header'}, exclude_none=True)
        )
        if self.header is None:
            object.__setattr__(
                self,
                'header',
                smpheader.Header(
                    op=self._OP,
                    version=self._VERSION,
                    flags=smpheader.Flag(self._FLAGS),
                    length=len(data_bytes),
                    group_id=self._GROUP_ID,
                    sequence=next(_counter) % 0xFF,
                    command_id=self._COMMAND_ID,
                ),
            )
        elif self.header.length != len(data_bytes):
            raise SMPMalformed(
                f"header.length {self.header.length} != len(data_bytes) {len(data_bytes)}"
            )
        self._bytes = cast(smpheader.Header, self.header).BYTES + data_bytes


@unique
class ResponseType(IntEnum):
    """An SMP `Response` to an SMP `Request` must be `SUCCESS`, `ERROR_V0`, or `ERROR_V1`."""

    SUCCESS = 0
    ERROR_V0 = 1
    ERROR_V1 = 2


class Response(_MessageBase, ABC):
    sequence: int = 0

    RESPONSE_TYPE: ClassVar[ResponseType]

    def model_post_init(self, _: None) -> None:
        data_bytes = cbor2.dumps(
            self.model_dump(exclude_unset=True, exclude={'header', 'sequence'}, exclude_none=True)
        )
        if self.header is None:
            object.__setattr__(
                self,
                'header',
                smpheader.Header(
                    op=self._OP,
                    version=self._VERSION,
                    flags=smpheader.Flag(self._FLAGS),
                    length=len(data_bytes),
                    group_id=self._GROUP_ID,
                    sequence=self.sequence,
                    command_id=self._COMMAND_ID,
                ),
            )
        self._bytes = cast(smpheader.Header, self.header).BYTES + data_bytes


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
