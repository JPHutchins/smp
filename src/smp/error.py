"""The Simple Management Protocol (SMP) error responses."""

from __future__ import annotations

from enum import IntEnum, unique
from typing import Any, Generic, TypeVar, get_args, get_origin

import msgspec

from smp import header, message

T = TypeVar("T", bound=IntEnum)


@unique
class MGMT_ERR(IntEnum):
    """General error codes for the Simple Management Protocol (SMP)."""

    EOK = 0
    """No error (success)."""

    EUNKNOWN = 1
    """Unknown error."""

    ENOMEM = 2
    """Insufficient memory (likely not enough space for CBOR object)."""

    EINVAL = 3
    """Error in input value."""

    ETIMEOUT = 4
    """Operation timed out."""

    ENOENT = 5
    """No such file/entry."""

    EBADSTATE = 6
    """Current state disallows command."""

    EMSGSIZE = 7
    """Response too large."""

    ENOTSUP = 8
    """Command not supported."""

    ECORRUPT = 9
    """Corrupt."""

    EBUSY = 10
    """Command blocked by processing of other command."""

    EACCESSDENIED = 11
    """Access to specific function, command or resource denied."""

    UNSUPPORTED_TOO_OLD = 12
    """Requested SMP MCUmgr protocol version is not supported (too old)."""

    UNSUPPORTED_TOO_NEW = 13
    """Requested SMP MCUmgr protocol version is not supported (too new)."""

    EPERUSER = 256
    """User errors defined from 256 onwards"""


class ErrorV1(message.Response, frozen=True):
    """SMP error response version 1."""

    RESPONSE_TYPE = message.ResponseType.ERROR_V1

    rc: MGMT_ERR
    """Error code."""

    rsn: str | None = None
    """Error reason."""


class Err(msgspec.Struct, Generic[T], frozen=True, omit_defaults=True, forbid_unknown_fields=True):
    """SMP error response version 2 `err` map."""

    group: header.GroupIdField
    rc: T


class _ErrWire(msgspec.Struct, frozen=True, omit_defaults=True, forbid_unknown_fields=True):
    group: int
    rc: int


class ErrorV2(message.Response, Generic[T], frozen=True):
    """SMP error response version 2."""

    RESPONSE_TYPE = message.ResponseType.ERROR_V2

    err: Err[T]

    @classmethod
    def _rc_type(cls) -> Any:
        for base in getattr(cls, "__orig_bases__", ()):
            if get_origin(base) is ErrorV2:
                return get_args(base)[0]
        raise TypeError(f"{cls.__name__} does not parametrize {ErrorV2.__name__}")

    @classmethod
    def _convert_mapping(cls, data: dict[str, Any]) -> ErrorV2[T]:
        cls._validate_mapping(data)
        wire = msgspec.convert(data["err"], type=_ErrWire)
        return cls(
            err=Err(
                group=header.resolve_group_id(wire.group),
                rc=msgspec.convert(wire.rc, type=cls._rc_type()),
            )
        )
