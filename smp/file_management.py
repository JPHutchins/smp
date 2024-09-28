"""The Simple Management Protocol (SMP) File Management group."""

from __future__ import annotations

from enum import IntEnum, unique
from typing import Dict, Literal

from pydantic import BaseModel, ConfigDict

from smp import error, header, message


class FileDownloadRequest(message.ReadRequest):
    """Download contents of an existing file from specified path.

    Client applications must keep track of data they have already downloaded and
    where their position in the file is, and issue subsequent requests, with
    modified offset, to gather the entire file.

    Request does not carry size of requested chunk, the size is specified by
    application itself. Note that file handles will remain open for consecutive
    requests (as long as an idle timeout has not been reached and another
    transport does not make use of uploading/downloading files using fs_mgmt),
    but files are not exclusively owned by SMP, for the time of download
    session, and may change between requests or even be removed.
    """

    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_DOWNLOAD_UPLOAD

    off: int
    """Offset in the file to read from."""
    name: str
    """Name of the file to download."""


class FileDownloadResponse(message.ReadResponse):
    """Success response to a file download request."""

    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_DOWNLOAD_UPLOAD

    off: int
    """Offset that this response is for."""
    data: bytes
    """Data read from the file."""
    len: int | None = None
    """The length of the file, only mandatory if “off” is 0."""


class FileUploadRequest(message.WriteRequest):
    """Upload a file to a specified location.

    Command will automatically overwrite existing file or create a new one if it
    does not exist at specified path. The protocol supports stateless upload
    where each requests carries different chunk of a file and it is client side
    responsibility to track progress of upload.

    Note that file handles will remain open for consecutive requests (as long as
    an idle timeout has not been reached, but files are not exclusively owned by
    SMP, for the time of download session, and may change between requests or
    even be removed. Note that file handles will remain open for consecutive
    requests (as long as an idle timeout has not been reached and another
    transport does not make use of uploading/downloading files using fs_mgmt),
    but files are not exclusively owned by MCUmgr, for the time of download
    session, and may change between requests or even be removed.
    """

    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_DOWNLOAD_UPLOAD

    off: int
    """Offset to start/continue writing to."""
    data: bytes
    """Data to write to the file."""
    name: str
    """Name of the file to upload."""
    len: int | None = None
    """The length of the file, only mandatory if “off” is 0."""


class FileUploadResponse(message.WriteResponse):
    """Success response to a file upload request."""

    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_DOWNLOAD_UPLOAD

    off: int
    """Offset of the file."""


class FileStatusRequest(message.ReadRequest):
    """Retrieve status of an existing file from specified path of a target device."""

    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_STATUS

    name: str


class FileStatusResponse(message.ReadResponse):
    """Success response to a file status request."""

    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_STATUS

    len: int


class FileHashChecksumRequest(message.ReadRequest):
    """Generate a hash/checksum of an existing file at a specified path on a target device.

    Note that kernel heap memory is required for buffers to be allocated for
    this to function, and large stack memory buffers are required for generation
    of the output hash/checksum. Requires `CONFIG_MCUMGR_GRP_FS_CHECKSUM_HASH` to
    be enabled for the base functionality, supported hash/checksum are opt-in
    with `CONFIG_MCUMGR_GRP_FS_CHECKSUM_IEEE_CRC32` or
    `CONFIG_MCUMGR_GRP_FS_HASH_SHA256`.
    """

    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_HASH_CHECKSUM

    name: str
    """Absolute path to the file to generate hash/checksum for."""
    type: Literal["crc32", "sha256"] | None = None
    """Type of hash/checksum to generate, if not provided, default is used."""
    off: int | None = None
    """Offset to start hash/checksum generation from, default 0."""
    len: int | None = None
    """Maximum length of the file to generate hash/checksum for, default is entire file."""


class FileHashChecksumResponse(message.ReadResponse):
    """Success response to a file hash/checksum request."""

    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_HASH_CHECKSUM

    type: Literal["crc32", "sha256"]
    off: int | None = None
    """Only present if not 0."""
    len: int
    """Length of input data used to generate hash/checksum."""
    output: int | bytes
    """Output hash/checksum, depending on the type requested."""


class SupportedFileHashChecksumTypesRequest(message.ReadRequest):
    """List the hash and checksum types are available on a device.

    Requires Kconfig `CONFIG_MCUMGR_GRP_FS_CHECKSUM_HASH_SUPPORTED_CMD` to be enabled.
    """

    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.SUPPORTED_FILE_HASH_CHECKSUM_TYPES


class HashChecksumFormat(IntEnum):
    """Format that the hash/checksum returns where 0 is for numerical and 1 is for byte array."""

    NUMERICAL = 0
    BYTE_ARRAY = 1


class HashChecksumType(BaseModel):
    """Hash and checksum type supported by the device."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    format: HashChecksumFormat
    """Format that the hash/checksum returns where 0 is for numerical and 1 is for byte array."""
    size: int
    """Size of the hash/checksum in bytes."""


class SupportedFileHashChecksumTypesResponse(message.ReadResponse):
    """Success response to a supported file hash/checksum types request."""

    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.SUPPORTED_FILE_HASH_CHECKSUM_TYPES

    types: Dict[Literal["crc32", "sha256"], HashChecksumType]
    """The map of supported hash/checksum types."""


class FileCloseRequest(message.WriteRequest):
    """Close all open file handles held by fs_mgmt upload/download requests."""

    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_CLOSE


class FileCloseResponse(message.WriteResponse):
    """Success response to a file close request."""

    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
    _COMMAND_ID = header.CommandId.FileManagement.FILE_CLOSE


@unique
class FS_MGMT_ERR(IntEnum):
    """File System Management error codes."""

    OK = 0
    """No error (success)."""

    UNKNOWN = 1
    """ Unknown error. """

    FILE_INVALID_NAME = 2
    """The specified file name is not valid."""

    FILE_NOT_FOUND = 3
    """The specified file does not exist."""

    FILE_IS_DIRECTORY = 4
    """The specified file is a directory, not a file. """

    FILE_OPEN_FAILED = 5
    """Error occurred whilst attempting to open a file."""

    FILE_SEEK_FAILED = 6
    """Error occurred whilst attempting to seek to an offset in a file. """

    FILE_READ_FAILED = 7
    """Error occurred whilst attempting to read data from a file."""

    FILE_TRUNCATE_FAILED = 8
    """Error occurred whilst trying to truncate file."""

    FILE_DELETE_FAILED = 9
    """Error occurred whilst trying to delete file."""

    FILE_WRITE_FAILED = 10
    """Error occurred whilst attempting to write data to a file."""

    FILE_OFFSET_NOT_VALID = 11
    """The specified data offset is not valid, this could indicate that the file on the device has
    changed since the previous command. The length of the current file on the device is returned as
    "len", the user application needs to decide how to handle this (e.g. the hash of the file could
    be requested and compared with the hash of the length of the file being uploaded to see if they
    match or not)."""

    FILE_OFFSET_LARGER_THAN_FILE = 12
    """The requested offset is larger than the size of the file on the device."""

    CHECKSUM_HASH_NOT_FOUND = 13
    """The requested checksum or hash type was not found or is not supported by this build."""

    MOUNT_POINT_NOT_FOUND = 14
    """The specified mount point was not found or is not mounted."""

    READ_ONLY_FILESYSTEM = 15
    """The specified mount point is that of a read-only filesystem."""

    FILE_EMPTY = 16
    """The operation cannot be performed because the file is empty with no contents. """


class FileSystemManagementErrorV1(error.ErrorV1):
    """File System Management error response."""

    _GROUP_ID = header.GroupId.FILE_MANAGEMENT


class FileSystemManagementErrorV2(error.ErrorV2[FS_MGMT_ERR]):
    """File System Management error response."""

    _GROUP_ID = header.GroupId.FILE_MANAGEMENT
