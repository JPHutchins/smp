"""The Simple Management Protocol (SMP) File Management group."""

from __future__ import annotations

from enum import IntEnum, auto, unique
from typing import Dict

from pydantic import BaseModel, ConfigDict

from smp import error, header, message


class FileDownloadRequest(message.ReadRequest):
    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_DOWNLOAD_UPLOAD

    off: int
    name: str


class FileDownloadResponse(message.ReadResponse):
    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_DOWNLOAD_UPLOAD

    off: int
    data: bytes
    len: int | None = None  # only mandatory when “off” is 0.


class FileUploadRequest(message.WriteRequest):
    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_DOWNLOAD_UPLOAD

    off: int
    data: bytes
    name: str
    len: int | None = None  # this field is only mandatory when “off” is 0


class FileUploadResponse(message.WriteResponse):
    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_DOWNLOAD_UPLOAD

    off: int


class FileStatusRequest(message.ReadRequest):
    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_STATUS

    name: str


class FileStatusResponse(message.ReadResponse):
    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_STATUS

    len: int


class FileHashChecksumRequest(message.ReadRequest):
    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_HASH_CHECKSUM

    name: str
    type: str | None = None  # omit to use default.
    off: int | None = None  # 0 if not provided
    len: int | None = None  # full size if not provided


class FileHashChecksumResponse(message.ReadResponse):
    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_HASH_CHECKSUM

    type: str
    off: int | None = None  # only present if not 0
    len: int
    output: int | bytes


class SupportedFileHashChecksumTypesRequest(message.ReadRequest):
    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.SUPPORTED_FILE_HASH_CHECKSUM_TYPES


class HashChecksumType(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    format: int
    size: int


class SupportedFileHashChecksumTypesResponse(message.ReadResponse):
    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.SUPPORTED_FILE_HASH_CHECKSUM_TYPES

    types: Dict[str, HashChecksumType]


class FileCloseRequest(message.WriteRequest):
    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_CLOSE


class FileCloseResponse(message.WriteResponse):
    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_CLOSE


@unique
class FS_MGMT_ERR(IntEnum):
    OK = 0
    """No error (success)."""

    UNKNOWN = auto()
    """ Unknown error. """

    FILE_INVALID_NAME = auto()
    """The specified file name is not valid."""

    FILE_NOT_FOUND = auto()
    """The specified file does not exist."""

    FILE_IS_DIRECTORY = auto()
    """The specified file is a directory, not a file. """

    FILE_OPEN_FAILED = auto()
    """Error occurred whilst attempting to open a file."""

    FILE_SEEK_FAILED = auto()
    """Error occurred whilst attempting to seek to an offset in a file. """

    FILE_READ_FAILED = auto()
    """Error occurred whilst attempting to read data from a file."""

    FILE_TRUNCATE_FAILED = auto()
    """Error occurred whilst trying to truncate file."""

    FILE_DELETE_FAILED = auto()
    """Error occurred whilst trying to delete file."""

    FILE_WRITE_FAILED = auto()
    """Error occurred whilst attempting to write data to a file."""

    FILE_OFFSET_NOT_VALID = auto()
    """The specified data offset is not valid, this could indicate that the file on the device has
    changed since the previous command. The length of the current file on the device is returned as
    "len", the user application needs to decide how to handle this (e.g. the hash of the file could
    be requested and compared with the hash of the length of the file being uploaded to see if they
    match or not)."""

    FILE_OFFSET_LARGER_THAN_FILE = auto()
    """The requested offset is larger than the size of the file on the device."""

    CHECKSUM_HASH_NOT_FOUND = auto()
    """The requested checksum or hash type was not found or is not supported by this build."""

    MOUNT_POINT_NOT_FOUND = auto()
    """The specified mount point was not found or is not mounted."""

    READ_ONLY_FILESYSTEM = auto()
    """The specified mount point is that of a read-only filesystem."""

    FILE_EMPTY = auto()
    """The operation cannot be performed because the file is empty with no contents. """


class FileSystemManagementErrorV1(error.ErrorV1):
    _GROUP_ID = header.GroupId.FILE_MANAGEMENT


class FileSystemManagementErrorV2(error.ErrorV2[FS_MGMT_ERR]):
    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
