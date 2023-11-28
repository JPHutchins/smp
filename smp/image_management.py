"""The Simple Management Protocol (SMP) Image Management group."""

from enum import IntEnum, auto, unique
from typing import Generator, List

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

from smp import error, header, message


class _ImageManagementGroup:
    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT


class _HashBytes(bytes):  # pragma: no cover
    """Only to print something useful to the console.

    @private
    """

    def __rich_repr__(self) -> Generator[str, None, None]:
        yield self.hex().upper()


class ImageState(BaseModel):
    """Representation of an image on."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)
    """@private"""

    slot: int
    """Partition within the image, e.g. `0` -> `slot0_partition` or `image-0`."""

    version: str
    """String representing image version, as set with `imgtool`."""

    image: int | None = None
    """Semi-optional image number.
      
    The field is not required when only one image is supported by the running application.
    """

    hash: _HashBytes | bytes | None = None
    """SHA256 hash of the image header and body.

    Note that this will not be the same as the SHA256 of the whole file, it is the field in the
    MCUboot TLV section that contains a hash of the data which is used for signature verification
    purposes. This field is optional but only optional when using MCUboot's serial recovery feature
    with one pair of image slots, Kconfig `CONFIG_BOOT_SERIAL_IMG_GRP_HASH` can be disabled to
    remove support for hashes in this configuration. MCUmgr in applications must support sending
    hashes.
    
    """

    bootable: bool | None = None
    """`True` if image has `bootable` flag set; does not have to be present if `False`."""

    pending: bool | None = None
    """`True` if image is set for next swap; does not have to be present if `False`."""

    confirmed: bool | None = None
    """`True` if image has been confirmed; does not have to be present if `False`."""

    active: bool | None = None
    """`True` if image is currently active application; does not have to be present if `False`."""

    permanent: bool | None = None
    """`True` if image is to stay in primary slot after the next boot; does not have to be present
    if `False`.
    """

    @field_validator("hash")
    @classmethod
    def _cast_bytes(cls, v: bytes | None, _: ValidationInfo) -> _HashBytes | None:
        """Cast `hash` to a `bytes` subclass with good rich repr.  @private"""
        if v is None:
            return None
        return _HashBytes(v)


class ImageStatesReadRequest(_ImageManagementGroup, message.ReadRequest):
    """Request the state of images."""

    _COMMAND_ID = header.CommandId.ImageManagement.STATE


class ImageStatesReadResponse(_ImageManagementGroup, message.ReadResponse):
    """Successful response to an `ImageStatesReadRequest`."""

    _COMMAND_ID = header.CommandId.ImageManagement.STATE

    images: List[ImageState]
    splitStatus: int | None = None
    """States whether loader of split image is compatible with application part."""


class ImageStatesWriteRequest(_ImageManagementGroup, message.WriteRequest):
    _COMMAND_ID = header.CommandId.ImageManagement.STATE

    hash: bytes
    confirm: bool = False


class ImageStatesWriteResponse(ImageStatesReadResponse):
    ...


class ImageUploadWriteRequest(_ImageManagementGroup, message.WriteRequest):
    _COMMAND_ID = header.CommandId.ImageManagement.UPLOAD

    off: int
    data: bytes
    image: int | None = None  # 'required' when off == 0
    len: int | None = None  # required when off == 0
    sha: bytes | None = None  # should be sent when off == 0
    upgrade: bool | None = None  # allowed when off == 0


class ImageUploadProgressWriteResponse(_ImageManagementGroup, message.WriteResponse):
    _COMMAND_ID = header.CommandId.ImageManagement.UPLOAD

    rc: int | None = None
    off: int | None = None


class ImageUploadFinalWriteResponse(_ImageManagementGroup, message.WriteResponse):
    _COMMAND_ID = header.CommandId.ImageManagement.UPLOAD

    off: int | None = None
    match: bool | None = None


@unique
class IMG_MGMT_ERR(IntEnum):
    """Image Management Group error response enumeration."""

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


class ImageManagementError1(error.ErrorV0[IMG_MGMT_ERR]):
    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT


class ImageManagementError2(error.ErrorV1[IMG_MGMT_ERR]):
    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
