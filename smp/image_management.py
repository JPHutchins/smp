"""The Simple Management Protocol (SMP) Image Management group."""

from __future__ import annotations

from enum import IntEnum, auto, unique
from typing import Generator, List

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

from smp import error, header, message


class HashBytes(bytes):  # pragma: no cover
    """Only to print something useful to the console."""

    def __rich_repr__(self) -> Generator[str, None, None]:
        yield self.hex().upper()


class ImageState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    slot: int
    version: str
    image: int | None = None
    hash: HashBytes | bytes | None = None
    bootable: bool | None = None
    pending: bool | None = None
    confirmed: bool | None = None
    active: bool | None = None
    permanent: bool | None = None

    @field_validator("hash")
    @classmethod
    def cast_bytes(cls, v: bytes | None, _: ValidationInfo) -> HashBytes | None:
        if v is None:
            return None
        return HashBytes(v)


class ImageStatesReadRequest(message.ReadRequest):
    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
    _COMMAND_ID = header.CommandId.ImageManagement.STATE


class ImageStatesReadResponse(message.ReadResponse):
    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
    _COMMAND_ID = header.CommandId.ImageManagement.STATE

    images: List[ImageState]
    splitStatus: int | None = None


class ImageStatesWriteRequest(message.WriteRequest):
    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
    _COMMAND_ID = header.CommandId.ImageManagement.STATE

    hash: bytes
    confirm: bool = False


class ImageStatesWriteResponse(ImageStatesReadResponse):
    pass


class ImageUploadWriteRequest(message.WriteRequest):
    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
    _COMMAND_ID = header.CommandId.ImageManagement.UPLOAD

    off: int
    data: bytes
    image: int | None = None  # 'required' when off == 0
    len: int | None = None  # required when off == 0
    sha: bytes | None = None  # should be sent when off == 0
    upgrade: bool | None = None  # allowed when off == 0


class ImageUploadProgressWriteResponse(message.WriteResponse):
    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
    _COMMAND_ID = header.CommandId.ImageManagement.UPLOAD

    rc: int | None = None
    off: int | None = None


class ImageUploadFinalWriteResponse(message.WriteResponse):
    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
    _COMMAND_ID = header.CommandId.ImageManagement.UPLOAD

    off: int | None = None
    match: bool | None = None


class ImageEraseRequest(message.WriteRequest):
    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
    _COMMAND_ID = header.CommandId.ImageManagement.ERASE

    slot: int | None = None
    """The slot to erase. If not provided, slot 1 will be erased."""


class ImageEraseResponse(message.WriteResponse):
    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
    _COMMAND_ID = header.CommandId.ImageManagement.ERASE


@unique
class IMG_MGMT_ERR(IntEnum):
    OK = 0
    """No error, this is implied if there is no ret value in the response"""

    UNKNOWN = auto()
    """Unknown error occurred."""

    FLASH_CONFIG_QUERY_FAIL = auto()
    """Failed to query flash area configuration."""

    NO_IMAGE = auto()
    """There is no image in the slot."""

    NO_TLVS = auto()
    """The image in the slot has no TLVs (tag, length, value)."""

    INVALID_TLV = auto()
    """The image in the slot has an invalid TLV type and/or length."""

    TLV_MULTIPLE_HASHES_FOUND = auto()
    """The image in the slot has multiple hash TLVs, which is invalid."""

    TLV_INVALID_SIZE = auto()
    """The image in the slot has an invalid TLV size."""

    HASH_NOT_FOUND = auto()
    """The image in the slot does not have a hash TLV, which is required."""

    NO_FREE_SLOT = auto()
    """There is no free slot to place the image."""

    FLASH_OPEN_FAILED = auto()
    """Flash area opening failed."""

    FLASH_READ_FAILED = auto()
    """Flash area reading failed."""

    FLASH_WRITE_FAILED = auto()
    """Flash area writing failed."""

    FLASH_ERASE_FAILED = auto()
    """Flash area erase failed."""

    INVALID_SLOT = auto()
    """The provided slot is not valid."""

    NO_FREE_MEMORY = auto()
    """Insufficient heap memory (malloc failed)."""

    FLASH_CONTEXT_ALREADY_SET = auto()
    """The flash context is already set."""

    FLASH_CONTEXT_NOT_SET = auto()
    """The flash context is not set."""

    FLASH_AREA_DEVICE_NULL = auto()
    """The device for the flash area is NULL."""

    INVALID_PAGE_OFFSET = auto()
    """The offset for a page number is invalid."""

    INVALID_OFFSET = auto()
    """The offset parameter was not provided and is required."""

    INVALID_LENGTH = auto()
    """The length parameter was not provided and is required."""

    INVALID_IMAGE_HEADER = auto()
    """The image length is smaller than the size of an image header."""

    INVALID_IMAGE_HEADER_MAGIC = auto()
    """The image header magic value does not match the expected value."""

    INVALID_HASH = auto()
    """The hash parameter provided is not valid."""

    INVALID_FLASH_ADDRESS = auto()
    """The image load address does not match the address of the flash area."""

    VERSION_GET_FAILED = auto()
    """Failed to get version of currently running application."""

    CURRENT_VERSION_IS_NEWER = auto()
    """The currently running application is newer than the version being uploaded."""

    IMAGE_ALREADY_PENDING = auto()
    """There is already an image operating pending."""

    INVALID_IMAGE_VECTOR_TABLE = auto()
    """The image vector table is invalid."""

    INVALID_IMAGE_TOO_LARGE = auto()
    """The image it too large to fit."""

    INVALID_IMAGE_DATA_OVERRUN = auto()
    """The amount of data sent is larger than the provided image size."""

    IMAGE_CONFIRMATION_DENIED = auto()
    """Confirmation of image has been denied"""

    IMAGE_SETTING_TEST_TO_ACTIVE_DENIED = auto()
    """Setting test to active slot is not allowed"""


class ImageManagementErrorV0(error.ErrorV0[IMG_MGMT_ERR]):
    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT


class ImageManagementErrorV1(error.ErrorV1[IMG_MGMT_ERR]):
    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
