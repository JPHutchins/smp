"""The Simple Management Protocol (SMP) Intercreate Management group."""

from __future__ import annotations

from enum import IntEnum, unique

from smp import error, header, message


@unique
class IC_MGMT_ERR(IntEnum):
    """Intercreate Management error codes."""

    OK = 0
    """No error."""

    INVALID_IMAGE = 1
    """No image matched the image provided."""


class ErrorV1(error.ErrorV1, frozen=True):
    """Intercreate Management error response."""

    _GROUP_ID = header.UserGroupId.INTERCREATE


class ErrorV2(error.ErrorV2[IC_MGMT_ERR], frozen=True):
    """Intercreate Management error response."""

    _GROUP_ID = header.UserGroupId.INTERCREATE


class _IntercreateGroupBase:
    _ErrorV1 = ErrorV1
    _ErrorV2 = ErrorV2


class ImageUploadWriteResponse(message.WriteResponse, frozen=True):
    """Success response to an image upload request."""

    _GROUP_ID = header.UserGroupId.INTERCREATE
    _COMMAND_ID = header.CommandId.Intercreate.UPLOAD

    off: int
    """The offset in the image after the request was written."""


class ImageUploadWriteRequest(message.WriteRequest, _IntercreateGroupBase, frozen=True):
    """Upload an image to an application-defined location like a secondary MCU."""

    _GROUP_ID = header.UserGroupId.INTERCREATE
    _COMMAND_ID = header.CommandId.Intercreate.UPLOAD
    _Response = ImageUploadWriteResponse

    off: int
    """The offset in the image to write to."""

    data: bytes
    """The data to write to the image."""

    image: int | None = None
    """The image to write to; required when off == 0."""

    len: int | None = None
    """The length of the data to write; required when off == 0."""

    sha: bytes | None = None
    """The SHA-256 hash of the image; optional when off == 0, else ignored."""
