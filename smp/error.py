"""The Simple Management Protocol (SMP) error responses."""

from __future__ import annotations

from enum import IntEnum, unique
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

from smp import message
from smp.header import GroupId

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


class ErrorV1(message.Response):
    """SMP error response version 1."""

    RESPONSE_TYPE = message.ResponseType.ERROR_V1

    rc: MGMT_ERR
    """Error code."""

    rsn: str | None = None
    """Error reason."""


class Err(BaseModel, Generic[T]):
    """SMP error response version 2 `err` map."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    group: GroupId
    rc: T


class ErrorV2(message.Response, Generic[T]):
    """SMP error response version 2."""

    RESPONSE_TYPE = message.ResponseType.ERROR_V2

    err: Err[T]
