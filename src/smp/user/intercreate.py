"""The Simple Management Protocol (SMP) Intercreate Management group."""

from __future__ import annotations

from enum import IntEnum, unique

from smp import error, header, message


class ImageUploadWriteRequest(message.WriteRequest):
    """Upload an image to an application-defined location like a secondary MCU."""

    _GROUP_ID = header.UserGroupId.INTERCREATE
    _COMMAND_ID = header.CommandId.Intercreate.UPLOAD

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


class ImageUploadWriteResponse(message.WriteResponse):
    """Success response to an image upload request."""

    _GROUP_ID = header.UserGroupId.INTERCREATE
    _COMMAND_ID = header.CommandId.Intercreate.UPLOAD

    off: int
    """The offset in the image after the request was written."""


@unique
class IC_MGMT_ERR(IntEnum):
    """Intercreate Management error codes."""

    OK = 0
    """No error."""

    INVALID_IMAGE = 1
    """No image matched the image provided."""


class ErrorV1(error.ErrorV1):
    """Intercreate Management error response."""

    _GROUP_ID = header.UserGroupId.INTERCREATE


class ErrorV2(error.ErrorV2[IC_MGMT_ERR]):
    """Intercreate Management error response."""

    _GROUP_ID = header.UserGroupId.INTERCREATE
