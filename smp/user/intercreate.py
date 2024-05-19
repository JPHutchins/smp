"""The Simple Management Protocol (SMP) Intercreate Management group."""

from __future__ import annotations

from enum import IntEnum, auto, unique

from smp import error, header, message


class ImageUploadWriteRequest(message.WriteRequest):
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
    _GROUP_ID = header.UserGroupId.INTERCREATE
    _COMMAND_ID = header.CommandId.Intercreate.UPLOAD

    off: int
    """The offset in the image after the request was written."""


@unique
class IC_MGMT_ERR(IntEnum):
    OK = 0
    """No error."""

    INVALID_IMAGE = auto()
    """No image matched the image provided."""


class ErrorV0(error.ErrorV0[IC_MGMT_ERR]):
    _GROUP_ID = header.UserGroupId.INTERCREATE


class ErrorV1(error.ErrorV1[IC_MGMT_ERR]):
    _GROUP_ID = header.UserGroupId.INTERCREATE
