"""Test the SMP File Management group."""

from __future__ import annotations

from typing import Any, Dict, Type, TypeVar

import cbor2
from pydantic import BaseModel

from smp import file_management as smpfs
from smp import header as smphdr
from smp import message as smpmsg
from tests.helpers import make_assert_header

T = TypeVar("T", bound=smpmsg._MessageBase)

fscmd = smphdr.CommandId.FileManagement


def _do_test(
    msg: Type[T],
    op: smphdr.OP,
    command_id: smphdr.CommandId.FileManagement,
    data: Dict[str, Any],
    nested_model: Type[BaseModel] | None = None,
) -> T:
    cbor = cbor2.dumps(data, canonical=True)
    assert_header = make_assert_header(smphdr.GroupId.FILE_MANAGEMENT, op, command_id, len(cbor))

    def _assert_common(r: smpmsg._MessageBase) -> None:
        assert_header(r)
        for k, v in data.items():
            if type(v) is dict and nested_model is not None:
                for k2, v2 in v.items():
                    one_deep = getattr(r, k)
                    assert isinstance(one_deep[k2], nested_model)
                    assert v2 == one_deep[k2].model_dump()
            else:
                assert v == getattr(r, k)
        assert cbor == r.BYTES[8:]

    r = msg(**data)

    _assert_common(r)  # serialize
    _assert_common(msg.loads(r.BYTES))  # deserialize

    return r


def test_FileDownloadRequest() -> None:
    r = _do_test(
        smpfs.FileDownloadRequest,
        smphdr.OP.READ,
        fscmd.FILE_DOWNLOAD_UPLOAD,
        {"off": 0, "name": "test_file.txt"},
    )
    assert r.off == 0
    assert r.name == "test_file.txt"


def test_FileDownloadResponse() -> None:
    r = _do_test(
        smpfs.FileDownloadResponse,
        smphdr.OP.READ_RSP,
        fscmd.FILE_DOWNLOAD_UPLOAD,
        {"off": 0, "data": b"test", "len": 100},
    )
    assert r.off == 0
    assert r.data == b"test"
    assert r.len == 100


def test_FileUploadRequest() -> None:
    r = _do_test(
        smpfs.FileUploadRequest,
        smphdr.OP.WRITE,
        fscmd.FILE_DOWNLOAD_UPLOAD,
        {"off": 0, "data": b"test", "name": "test.txt", "len": 1000},
    )
    assert r.off == 0
    assert r.data == b"test"
    assert r.name == "test.txt"
    assert r.len == 1000


def test_FileUploadResponse() -> None:
    r = _do_test(
        smpfs.FileUploadResponse,
        smphdr.OP.WRITE_RSP,
        fscmd.FILE_DOWNLOAD_UPLOAD,
        {"off": 0},
    )
    assert r.off == 0


def test_FileStatusRequest() -> None:
    r = _do_test(
        smpfs.FileStatusRequest,
        smphdr.OP.READ,
        fscmd.FILE_STATUS,
        {"name": "test.txt"},
    )
    assert r.name == "test.txt"


def test_FileStatusResponse() -> None:
    r = _do_test(
        smpfs.FileStatusResponse,
        smphdr.OP.READ_RSP,
        fscmd.FILE_STATUS,
        {"len": 100},
    )
    assert r.len == 100


def test_FileHashChecksumRequest() -> None:
    r = _do_test(
        smpfs.FileHashChecksumRequest,
        smphdr.OP.READ,
        fscmd.FILE_HASH_CHECKSUM,
        {"name": "test.txt", "type": "crc32", "off": 0, "len": 100},
    )
    assert r.name == "test.txt"
    assert r.type == "crc32"
    assert r.off == 0
    assert r.len == 100


def test_FileHashChecksumResponse_bytes() -> None:
    r = _do_test(
        smpfs.FileHashChecksumResponse,
        smphdr.OP.READ_RSP,
        fscmd.FILE_HASH_CHECKSUM,
        {"type": "crc32", "off": 0, "len": 100, "output": b"test"},
    )
    assert r.type == "crc32"
    assert r.off == 0
    assert r.len == 100
    assert r.output == b"test"


def test_FileHashChecksumResponse_int() -> None:
    r = _do_test(
        smpfs.FileHashChecksumResponse,
        smphdr.OP.READ_RSP,
        fscmd.FILE_HASH_CHECKSUM,
        {"type": "crc32", "off": 0, "len": 100, "output": 1000000},
    )
    assert r.type == "crc32"
    assert r.off == 0
    assert r.len == 100
    assert r.output == 1000000


def test_SupportedFileHashChecksumTypesRequest() -> None:
    _do_test(
        smpfs.SupportedFileHashChecksumTypesRequest,
        smphdr.OP.READ,
        fscmd.SUPPORTED_FILE_HASH_CHECKSUM_TYPES,
        {},
    )


def test_SupportedFileHashChecksumTypesResponse() -> None:
    r = _do_test(
        smpfs.SupportedFileHashChecksumTypesResponse,
        smphdr.OP.READ_RSP,
        fscmd.SUPPORTED_FILE_HASH_CHECKSUM_TYPES,
        {"types": {"crc32": {"format": 1, "size": 4}, "sha256": {"format": 0, "size": 32}}},
        nested_model=smpfs.HashChecksumType,
    )
    assert r.types["crc32"].format == 1
    assert r.types["crc32"].size == 4
    assert r.types["sha256"].format == 0
    assert r.types["sha256"].size == 32


def test_FileCloseRequest() -> None:
    _do_test(
        smpfs.FileCloseRequest,
        smphdr.OP.WRITE,
        fscmd.FILE_CLOSE,
        {},
    )


def test_FileCloseResponse() -> None:
    _do_test(
        smpfs.FileCloseResponse,
        smphdr.OP.WRITE_RSP,
        fscmd.FILE_CLOSE,
        {},
    )
