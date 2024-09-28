"""The Simple Management Protocol (SMP) Image Management group.

## Notion of "slots" and "images" in Zephyr

The “slot” and “image” definition comes from mcuboot where “image” would consist
of two “slots”, further named “primary” and “secondary”; the application is
supposed to run from the “primary slot” and update is supposed to be uploaded to
the “secondary slot”; the mcuboot is responsible in swapping slots on boot. This
means that pair of slots is dedicated to single upgradable application. In case
of Zephyr this gets a little bit confusing because DTS will use
“slot0_partition” and “slot1_partition”, as label of fixed-partition dedicated
to single application, but will name them as “image-0” and “image-1”
respectively.

Currently Zephyr supports at most two images, in which case mapping is as
follows:

| Image | Slot labels | Slot Names |
|-------|-------------|------------|
| 0     | “slot0_partition” “slot1_partition” | “image-0” “image-1” |
| 1     | “slot2_partition” “slot3_partition” | “image-2” “image-3” |

"""

from __future__ import annotations

from enum import IntEnum, unique
from typing import Generator, List

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

from smp import error, header, message


class HashBytes(bytes):  # pragma: no cover
    """Only to print something useful to the `rich` console."""

    def __rich_repr__(self) -> Generator[str, None, None]:
        yield self.hex().upper()


class ImageState(BaseModel):
    """The state of an image in a slot."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    slot: int
    """Slot number within “image”.

    Each image has two slots:
    - primary (running one) = 0
    - secondary (for DFU dual-bank purposes) = 1.
    """
    version: str
    """Version of the image."""
    image: int | None = None
    """Semi-optional image number.

    The field is not required when only one image is supported by the running
    application.
    """
    hash: HashBytes | bytes | None = None
    """SHA256 hash of the image header and body.

    Note that this will not be the same as the SHA256 of the whole file, it is
    the field in the MCUboot TLV section that contains a hash of the data which
    is used for signature verification purposes. This field is optional but only
    optional when using MCUboot's serial recovery feature with one pair of image
    slots, `CONFIG_BOOT_SERIAL_IMG_GRP_HASH` can be disabled to remove
    support for hashes in this configuration. SMP server in applications must
    support sending hashes.
    """
    bootable: bool | None = None
    """True if image has bootable flag set.

    This field does not have to be present if false.
    """
    pending: bool | None = None
    """True if image is set for next swap.

    This field does not have to be present if false.
    """
    confirmed: bool | None = None
    """True if image has been confirmed.

    This field does not have to be present if false.
    """
    active: bool | None = None
    """True if image is currently active application

    This field does not have to be present if false.
    """
    permanent: bool | None = None
    """True if image is to stay in primary slot after the next boot.

    This does not have to be present if false.
    """

    @field_validator("hash")
    @classmethod
    def cast_bytes(cls, v: bytes | None, _: ValidationInfo) -> HashBytes | None:
        if v is None:
            return None
        return HashBytes(v)


class ImageStatesReadRequest(message.ReadRequest):
    """Obtain list of images with their current state."""

    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
    _COMMAND_ID = header.CommandId.ImageManagement.STATE


class ImageStatesReadResponse(message.ReadResponse):
    """Response to an image state request."""

    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
    _COMMAND_ID = header.CommandId.ImageManagement.STATE

    images: List[ImageState]
    """List of images with their current state."""
    splitStatus: int | None = None
    """States whether loader of split image is compatible with application part.

    This is unused by Zephyr.
    """


class ImageStatesWriteRequest(message.WriteRequest):
    """Set the state of an image.

    If “confirm” is false or not provided, an image with the “hash” will be set
    for test, which means that it will not be marked as permanent and upon hard
    reset the previous application will be restored to the primary slot. In case
    when “confirm” is true, the “hash” is optional as the currently running
    application will be assumed as target for confirmation.
    """

    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
    _COMMAND_ID = header.CommandId.ImageManagement.STATE

    hash: bytes | None = None
    """SHA256 hash of the image header and body."""
    confirm: bool = False
    """Confirm the image given by hash.

    CAUTION: it is dangerous to confirm the image before it has been booted!

    Setting this to true will mark the image as confirmed before it has been
    booted, which can brick the device.  Zephyr provides hooks for confirming
    the image from within the application, so this is not necessary for normal
    operation.
    """


class ImageStatesWriteResponse(ImageStatesReadResponse):
    """Success response to an image state write request."""


class ImageUploadWriteRequest(message.WriteRequest):
    """Upload an image to the device.

    The image is uploaded in chunks, with each chunk being sent in a separate
    request. The first request must include the image's length and image number.
    """

    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
    _COMMAND_ID = header.CommandId.ImageManagement.UPLOAD

    off: int
    """The offset of the data chunk in this request."""
    data: bytes
    """The data chunk to write."""
    image: int | None = None
    """Image number.

    It does not have to appear in request at all, in which case it is assumed to
    be 0. Should only be present when `off` is 0.
    """
    len: int | None = None
    """The length of the image.

    Required when `off` is 0, otherwise ignored.
    """
    sha: bytes | None = None
    """SHA256 hash of the image.

    This is used to identify an upload session (e.g. to allow to continue
    a broken session), and for image verification purposes. This must be a full
    SHA256 hash of the whole image being uploaded, or not included if the hash
    is not available (in which case, upload session continuation and image
    verification functionality will be unavailable). Should only be present when
    “off” is 0.
    """
    upgrade: bool | None = None
    """Optional flag that states that only upgrade should be allowed.

    If the version of uploaded software is not higher then already on a device,
    the image upload will be rejected. Zephyr compares major, minor and
    revision (x.y.z) by default unless `CONFIG_MCUMGR_GRP_IMG_VERSION_CMP_USE_BUILD_NUMBER`
    is set, whereby it will compare build numbers too. Should only be present
    when “off” is 0.
    """


class ImageUploadWriteResponse(message.WriteResponse):
    """Success response to an image upload request."""

    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
    _COMMAND_ID = header.CommandId.ImageManagement.UPLOAD

    off: int | None = None
    """The portion of the upload that has been completed, in 8-bit bytes.

    This is the offset of the next byte to be written. If the offset is equal to
    the length of the image, the upload is complete.
    """

    match: bool | None = None
    """Indicates if the uploaded data successfully matches the provided SHA256.

    Only sent in the final packet if CONFIG_IMG_ENABLE_IMAGE_CHECK is enabled.
    """

    rc: int | None = None
    """Legacy field that contains a return code; possibly `MGMT_ERR`.

    This field may be present on old SMP server implementations or new SMP
    server implementations that have set
    `CONFIG_MCUMGR_SMP_LEGACY_RC_BEHAVIOUR=y` for backwards compatibility with
    old SMP clients.

    Note that we are not validating this field because we don't necessarily
    trust the server to send us valid values. If this value is present, then it
    indicates use of an SMP server that is out of spec and interpretation of the
    value should be done with reference to that server's source code, rather
    that the SMP specification.

    Zephyr source code reference: https://github.com/zephyrproject-rtos/zephyr/blob/91a1e706535b2f99433280513c5bc66dfb918506/subsys/mgmt/mcumgr/grp/img_mgmt/src/img_mgmt.c#L397-L400
    """  # noqa: E501


class ImageEraseRequest(message.WriteRequest):
    """Erase an image from a slot."""

    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
    _COMMAND_ID = header.CommandId.ImageManagement.ERASE

    slot: int | None = None
    """The slot to erase. If not provided, slot 1 will be erased."""


class ImageEraseResponse(message.WriteResponse):
    """Success response to an image erase request."""

    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
    _COMMAND_ID = header.CommandId.ImageManagement.ERASE


@unique
class IMG_MGMT_ERR(IntEnum):
    """Image management error codes."""

    OK = 0
    """No error, this is implied if there is no ret value in the response"""

    UNKNOWN = 1
    """Unknown error occurred."""

    FLASH_CONFIG_QUERY_FAIL = 2
    """Failed to query flash area configuration."""

    NO_IMAGE = 3
    """There is no image in the slot."""

    NO_TLVS = 4
    """The image in the slot has no TLVs (tag, length, value)."""

    INVALID_TLV = 5
    """The image in the slot has an invalid TLV type and/or length."""

    TLV_MULTIPLE_HASHES_FOUND = 6
    """The image in the slot has multiple hash TLVs, which is invalid."""

    TLV_INVALID_SIZE = 7
    """The image in the slot has an invalid TLV size."""

    HASH_NOT_FOUND = 8
    """The image in the slot does not have a hash TLV, which is required."""

    NO_FREE_SLOT = 9
    """There is no free slot to place the image."""

    FLASH_OPEN_FAILED = 10
    """Flash area opening failed."""

    FLASH_READ_FAILED = 11
    """Flash area reading failed."""

    FLASH_WRITE_FAILED = 12
    """Flash area writing failed."""

    FLASH_ERASE_FAILED = 13
    """Flash area erase failed."""

    INVALID_SLOT = 14
    """The provided slot is not valid."""

    NO_FREE_MEMORY = 15
    """Insufficient heap memory (malloc failed)."""

    FLASH_CONTEXT_ALREADY_SET = 16
    """The flash context is already set."""

    FLASH_CONTEXT_NOT_SET = 17
    """The flash context is not set."""

    FLASH_AREA_DEVICE_NULL = 18
    """The device for the flash area is NULL."""

    INVALID_PAGE_OFFSET = 19
    """The offset for a page number is invalid."""

    INVALID_OFFSET = 20
    """The offset parameter was not provided and is required."""

    INVALID_LENGTH = 21
    """The length parameter was not provided and is required."""

    INVALID_IMAGE_HEADER = 22
    """The image length is smaller than the size of an image header."""

    INVALID_IMAGE_HEADER_MAGIC = 23
    """The image header magic value does not match the expected value."""

    INVALID_HASH = 24
    """The hash parameter provided is not valid."""

    INVALID_FLASH_ADDRESS = 25
    """The image load address does not match the address of the flash area."""

    VERSION_GET_FAILED = 26
    """Failed to get version of currently running application."""

    CURRENT_VERSION_IS_NEWER = 27
    """The currently running application is newer than the version being uploaded."""

    IMAGE_ALREADY_PENDING = 28
    """There is already an image operating pending."""

    INVALID_IMAGE_VECTOR_TABLE = 29
    """The image vector table is invalid."""

    INVALID_IMAGE_TOO_LARGE = 30
    """The image it too large to fit."""

    INVALID_IMAGE_DATA_OVERRUN = 31
    """The amount of data sent is larger than the provided image size."""

    IMAGE_CONFIRMATION_DENIED = 32
    """Confirmation of image has been denied"""

    IMAGE_SETTING_TEST_TO_ACTIVE_DENIED = 33
    """Setting test to active slot is not allowed"""


class ImageManagementErrorV1(error.ErrorV1):
    """Image Management error response."""

    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT


class ImageManagementErrorV2(error.ErrorV2[IMG_MGMT_ERR]):
    """Image Management error response."""

    _GROUP_ID = header.GroupId.IMAGE_MANAGEMENT
