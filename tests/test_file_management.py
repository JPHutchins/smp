"""Test the SMP File Management group."""

from __future__ import annotations

from smp import file_management as smpfs
from smp import header as smphdr
from tests.helpers import assert_frame

fscmd = smphdr.CommandId.FileManagement


def test_FileDownloadRequest() -> None:
    frame = assert_frame(
        smpfs.FileDownloadRequest(off=0, name="test_file.txt"),
        op=smphdr.OP.READ,
        group_id=smphdr.GroupId.FILE_MANAGEMENT,
        command_id=fscmd.FILE_DOWNLOAD_UPLOAD,
    )
    assert frame.data.off == 0
    assert frame.data.name == "test_file.txt"


def test_FileDownloadResponse() -> None:
    frame = assert_frame(
        smpfs.FileDownloadResponse(off=0, data=b"test", len=100),
        op=smphdr.OP.READ_RSP,
        group_id=smphdr.GroupId.FILE_MANAGEMENT,
        command_id=fscmd.FILE_DOWNLOAD_UPLOAD,
    )
    assert frame.data.off == 0
    assert frame.data.data == b"test"
    assert frame.data.len == 100


def test_FileUploadRequest() -> None:
    frame = assert_frame(
        smpfs.FileUploadRequest(off=0, data=b"test", name="test.txt", len=1000),
        op=smphdr.OP.WRITE,
        group_id=smphdr.GroupId.FILE_MANAGEMENT,
        command_id=fscmd.FILE_DOWNLOAD_UPLOAD,
    )
    assert frame.data.off == 0
    assert frame.data.data == b"test"
    assert frame.data.name == "test.txt"
    assert frame.data.len == 1000


def test_FileUploadResponse() -> None:
    frame = assert_frame(
        smpfs.FileUploadResponse(off=0),
        op=smphdr.OP.WRITE_RSP,
        group_id=smphdr.GroupId.FILE_MANAGEMENT,
        command_id=fscmd.FILE_DOWNLOAD_UPLOAD,
    )
    assert frame.data.off == 0


def test_FileStatusRequest() -> None:
    frame = assert_frame(
        smpfs.FileStatusRequest(name="test.txt"),
        op=smphdr.OP.READ,
        group_id=smphdr.GroupId.FILE_MANAGEMENT,
        command_id=fscmd.FILE_STATUS,
    )
    assert frame.data.name == "test.txt"


def test_FileStatusResponse() -> None:
    frame = assert_frame(
        smpfs.FileStatusResponse(len=100),
        op=smphdr.OP.READ_RSP,
        group_id=smphdr.GroupId.FILE_MANAGEMENT,
        command_id=fscmd.FILE_STATUS,
    )
    assert frame.data.len == 100


def test_FileHashChecksumRequest() -> None:
    frame = assert_frame(
        smpfs.FileHashChecksumRequest(name="test.txt", type="crc32", off=0, len=100),
        op=smphdr.OP.READ,
        group_id=smphdr.GroupId.FILE_MANAGEMENT,
        command_id=fscmd.FILE_HASH_CHECKSUM,
    )
    assert frame.data.name == "test.txt"
    assert frame.data.type == "crc32"
    assert frame.data.off == 0
    assert frame.data.len == 100


def test_FileHashChecksumResponse_bytes() -> None:
    frame = assert_frame(
        smpfs.FileHashChecksumResponse(type="crc32", off=0, len=100, output=b"test"),
        op=smphdr.OP.READ_RSP,
        group_id=smphdr.GroupId.FILE_MANAGEMENT,
        command_id=fscmd.FILE_HASH_CHECKSUM,
    )
    assert frame.data.type == "crc32"
    assert frame.data.off == 0
    assert frame.data.len == 100
    assert frame.data.output == b"test"


def test_FileHashChecksumResponse_int() -> None:
    frame = assert_frame(
        smpfs.FileHashChecksumResponse(type="crc32", off=0, len=100, output=1000000),
        op=smphdr.OP.READ_RSP,
        group_id=smphdr.GroupId.FILE_MANAGEMENT,
        command_id=fscmd.FILE_HASH_CHECKSUM,
    )
    assert frame.data.type == "crc32"
    assert frame.data.off == 0
    assert frame.data.len == 100
    assert frame.data.output == 1000000


def test_SupportedFileHashChecksumTypesRequest() -> None:
    assert_frame(
        smpfs.SupportedFileHashChecksumTypesRequest(),
        op=smphdr.OP.READ,
        group_id=smphdr.GroupId.FILE_MANAGEMENT,
        command_id=fscmd.SUPPORTED_FILE_HASH_CHECKSUM_TYPES,
        length=1,
    )


def test_SupportedFileHashChecksumTypesResponse() -> None:
    frame = assert_frame(
        smpfs.SupportedFileHashChecksumTypesResponse(
            types={
                "crc32": smpfs.HashChecksumType(format=smpfs.HashChecksumFormat.BYTE_ARRAY, size=4),
                "sha256": smpfs.HashChecksumType(
                    format=smpfs.HashChecksumFormat.NUMERICAL, size=32
                ),
            }
        ),
        op=smphdr.OP.READ_RSP,
        group_id=smphdr.GroupId.FILE_MANAGEMENT,
        command_id=fscmd.SUPPORTED_FILE_HASH_CHECKSUM_TYPES,
    )
    assert frame.data.types["crc32"].format == smpfs.HashChecksumFormat.BYTE_ARRAY
    assert frame.data.types["crc32"].size == 4
    assert frame.data.types["sha256"].format == smpfs.HashChecksumFormat.NUMERICAL
    assert frame.data.types["sha256"].size == 32


def test_FileCloseRequest() -> None:
    assert_frame(
        smpfs.FileCloseRequest(),
        op=smphdr.OP.WRITE,
        group_id=smphdr.GroupId.FILE_MANAGEMENT,
        command_id=fscmd.FILE_CLOSE,
        length=1,
    )


def test_FileCloseResponse() -> None:
    assert_frame(
        smpfs.FileCloseResponse(),
        op=smphdr.OP.WRITE_RSP,
        group_id=smphdr.GroupId.FILE_MANAGEMENT,
        command_id=fscmd.FILE_CLOSE,
        length=1,
    )
