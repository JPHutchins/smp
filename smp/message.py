"""The Simple Management Protocol (SMP) Message base class."""

from __future__ import annotations

import itertools
import logging
from abc import ABC
from enum import IntEnum, unique
from typing import ClassVar, Type, TypeVar, cast

import cbor2
from pydantic import BaseModel, ConfigDict

from smp import header as smpheader
from smp.exceptions import SMPMalformed, SMPMismatchedGroupId

T = TypeVar("T", bound='_MessageBase')


_counter = itertools.count()
logger = logging.getLogger(__name__)


class _MessageBase(ABC, BaseModel):
    """The base class for SMP messages."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    _OP: ClassVar[smpheader.OP]
    _FLAGS: ClassVar[smpheader.Flag] = smpheader.Flag(0)
    _GROUP_ID: ClassVar[smpheader.GroupId | smpheader.UserGroupId | smpheader.AnyGroupId]
    _COMMAND_ID: ClassVar[
        smpheader.AnyCommandId
        | smpheader.CommandId.ImageManagement
        | smpheader.CommandId.OSManagement
        | smpheader.CommandId.ShellManagement
        | smpheader.CommandId.Intercreate
        | smpheader.CommandId.FileManagement
    ]

    # This is is a dummy header that will be replaced in model_post_init
    header: smpheader.Header = None  # type: ignore
    version: smpheader.Version = smpheader.Version.V2
    sequence: int = None  # type: ignore
    smp_data: bytes = None  # type: ignore

    def __bytes__(self) -> bytes:
        return self.smp_data

    @property
    def BYTES(self) -> bytes:
        return self.smp_data

    @classmethod
    def loads(cls: Type[T], data: bytes) -> T:
        """Deserialize the SMP message."""
        message = cls(
            header=smpheader.Header.loads(data[: smpheader.Header.SIZE]),
            **cast(dict, cbor2.loads(data[smpheader.Header.SIZE :])),
            smp_data=data,
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

    def model_post_init(self, _: None) -> None:
        data_bytes = cbor2.dumps(
            self.model_dump(
                exclude_unset=True,
                exclude={'header', 'version', 'sequence', 'smp_data'},
                exclude_none=True,
            ),
            canonical=True,
        )
        if self.header is None:  # create the header
            object.__setattr__(
                self,
                'header',
                smpheader.Header(
                    op=self._OP,
                    version=self.version,
                    flags=smpheader.Flag(self._FLAGS),
                    length=len(data_bytes),
                    group_id=self._GROUP_ID,
                    sequence=next(_counter) % 0xFF if self.sequence is None else self.sequence,
                    command_id=self._COMMAND_ID,
                ),
            )
            object.__setattr__(self, 'sequence', self.header.sequence)
        else:  # validate the header and update version & sequence
            if self.smp_data is None and self.header.length != len(data_bytes):
                raise SMPMalformed(
                    f"header.length {self.header.length} != len(data_bytes) {len(data_bytes)}"
                )
            if self.sequence is not None:  # pragma: no cover
                raise ValueError(
                    f"{self.sequence=} {self.header.sequence=} "
                    "Do not use the sequence attribute when the header is provided."
                )
            object.__setattr__(self, 'sequence', self.header.sequence)
            if self.version != self.header.version:
                logger.warning(
                    f"Overriding {self.version=} with {self.header.version=} "
                    "from the provided header."
                )
            object.__setattr__(self, 'version', self.header.version)
        if self.smp_data is None:
            object.__setattr__(self, 'smp_data', bytes(self.header) + data_bytes)

    # # Uncomment this to create a record for a de/serialization regression lock
    #     self._log_serialized_bytes()

    # def _log_serialized_bytes(self) -> None:
    #     import json
    #     import os

    #     from smp.image_management import HashBytes

    #     kwargs = self.model_dump(
    #         exclude_unset=True,
    #         exclude={'header', 'version', 'sequence', 'smp_data'},
    #         exclude_none=True,
    #     )

    #     message = f"{self.__class__.__module__}.{self.__class__.__qualname__}"

    #     log_dir = "serialization_logs"
    #     os.makedirs(log_dir, exist_ok=True)
    #     log_file = os.path.join(log_dir, f"{message}.json")

    #     def convert_bytes(obj: dict) -> dict:
    #         if isinstance(obj, dict):
    #             return {k: convert_bytes(v) for k, v in obj.items()}
    #         elif isinstance(obj, list):
    #             return [convert_bytes(i) for i in obj]
    #         elif isinstance(obj, tuple):
    #             return tuple(convert_bytes(i) for i in obj)
    #         elif isinstance(obj, bytes) or isinstance(obj, HashBytes):
    #             return obj.hex()
    #         else:
    #             return obj

    #     log_data = {
    #         "message": message,
    #         "version": self.version,
    #         "sequence": self.sequence,
    #         "kwargs": convert_bytes(kwargs),
    #         "bytes": self.BYTES.hex(),
    #     }

    #     try:
    #         with open(log_file, "a") as f:
    #             f.write(json.dumps(log_data) + "\n")
    #     except OSError as e:
    #         print(f"Failed to write to {log_file}: {e}")


class Request(_MessageBase, ABC):
    """Base class for SMP Requests."""


@unique
class ResponseType(IntEnum):
    """An SMP `Response` to an SMP `Request` must be `SUCCESS`, `ERROR_V1`, or `ERROR_V2`."""

    SUCCESS = 0
    ERROR_V1 = 1
    ERROR_V2 = 2


class Response(_MessageBase, ABC):
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
