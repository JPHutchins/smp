"""The Simple Management Protocol (SMP) error responses."""

from __future__ import annotations

from enum import IntEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

from smp import message
from smp.header import GroupId

T = TypeVar("T", bound=IntEnum)


class ErrorV0(message.Response, Generic[T]):
    RESPONSE_TYPE = message.ResponseType.ERROR_V0

    rc: T
    rsn: str | None = None


class Err(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    group: GroupId
    rc: T


class ErrorV1(message.Response, Generic[T]):
    RESPONSE_TYPE = message.ResponseType.ERROR_V1

    err: Err[T]
