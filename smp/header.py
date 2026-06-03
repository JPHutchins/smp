"""The Simple Management Protocol (SMP) header."""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from enum import IntEnum, IntFlag, unique
from typing import ClassVar, Dict, List, Type, Union

from pydantic import Field
from typing_extensions import Annotated, TypeAlias


class CommandId:
    @unique
    class OSManagement(IntEnum):
        ECHO = 0
        ECHO_CONTROL = 1
        TASK_STATS = 2
        MEMORY_POOL_STATS = 3
        DATETIME_STRING = 4
        RESET = 5
        MCUMGR_PARAMETERS = 6
        OS_APPLICATION_INFO = 7
        BOOTLOADER_INFO = 8

    @unique
    class ImageManagement(IntEnum):
        STATE = 0
        UPLOAD = 1
        FILE = 2
        CORELIST = 3
        CORELOAD = 4
        ERASE = 5

    @unique
    class StatisticsManagement(IntEnum):
        GROUP_DATA = 0
        LIST_OF_GROUPS = 1

    @unique
    class SettingsManagement(IntEnum):
        READ_WRITE_SETTING = 0
        DELETE_SETTING = 1
        COMMIT_SETTINGS = 2
        LOAD_SAVE_SETTINGS = 3

    @unique
    class ShellManagement(IntEnum):
        EXECUTE = 0

    @unique
    class FileManagement(IntEnum):
        FILE_DOWNLOAD_UPLOAD = 0
        FILE_STATUS = 1
        FILE_HASH_CHECKSUM = 2
        SUPPORTED_FILE_HASH_CHECKSUM_TYPES = 3
        FILE_CLOSE = 4

    @unique
    class EnumManagement(IntEnum):
        GROUP_COUNT = 0
        LIST_OF_GROUPS = 1
        GROUP_ID = 2
        GROUP_DETAILS = 3

    @unique
    class ZephyrManagement(IntEnum):
        ERASE_STORAGE = 0

    @unique
    class Intercreate(IntEnum):
        UPLOAD = 1


AnyCommandId: TypeAlias = Union[IntEnum, int]


@unique
class GroupId(IntEnum):
    OS_MANAGEMENT = 0
    IMAGE_MANAGEMENT = 1
    STATISTICS_MANAGEMENT = 2
    SETTINGS_MANAGEMENT = 3
    LOG_MANAGEMENT = 4
    RUNTIME_TESTS = 5
    SPLIT_IMAGE_MANAGEMENT = 6
    TEST_CRASH = 7
    FILE_MANAGEMENT = 8
    SHELL_MANAGEMENT = 9
    ENUM_MANAGEMENT = 10
    ZEPHYR_MANAGEMENT = 63


class UserGroupId(IntEnum):
    """Users may define their own Group IDs starting at 64.

    It is optional to register them here."""

    INTERCREATE = 64


GroupIdField = Annotated[Union[GroupId, UserGroupId, int], Field(union_mode="left_to_right")]


@unique
class OP(IntEnum):
    READ = 0
    READ_RSP = 1
    WRITE = 2
    WRITE_RSP = 3


class _OP_BIT:
    MASK = 0b111
    SHIFT = 0


@unique
class Version(IntEnum):
    V1 = 0
    V2 = 1


class _VERSION_BIT:
    MASK = 0b11
    SHIFT = 3


@unique
class Flag(IntFlag):
    UNUSED = 0
    FORWARD_TREE = 0x80


@dataclass(frozen=True)
class Header:
    op: OP
    version: Version
    flags: Flag
    length: int
    group_id: GroupIdField
    sequence: int
    command_id: Union[
        AnyCommandId,
        CommandId.OSManagement,
        CommandId.ImageManagement,
        CommandId.ShellManagement,
        CommandId.Intercreate,
        CommandId.FileManagement,
    ]

    _MAP_GROUP_ID_TO_COMMAND_ID_ENUM: ClassVar[Dict[int, Type[IntEnum]]] = {
        GroupId.OS_MANAGEMENT: CommandId.OSManagement,
        GroupId.IMAGE_MANAGEMENT: CommandId.ImageManagement,
        GroupId.SHELL_MANAGEMENT: CommandId.ShellManagement,
        GroupId.FILE_MANAGEMENT: CommandId.FileManagement,
    }
    _STRUCT: ClassVar[struct.Struct] = struct.Struct("!BBHHBB")
    SIZE: ClassVar[int] = _STRUCT.size

    @staticmethod
    def _pack_op(op: OP) -> int:
        """The value to be packed into the byte."""
        return op << _OP_BIT.SHIFT

    @staticmethod
    def _unpack_op(res_ver_op_byte: int) -> OP:
        """The value unpacked from the byte."""
        return OP((res_ver_op_byte & _OP_BIT.MASK) >> _OP_BIT.SHIFT)

    @staticmethod
    def _pack_version(version: Version) -> int:
        """The value to be packed into the byte."""
        return version << _VERSION_BIT.SHIFT

    @staticmethod
    def _unpack_version(res_ver_op_byte: int) -> Version:
        """The value unpacked from the byte."""
        return Version((res_ver_op_byte >> _VERSION_BIT.SHIFT) & _VERSION_BIT.MASK)

    @staticmethod
    def _pack_op_and_version(op: OP, version: Version) -> int:
        """The op and version packed into one byte."""
        return Header._pack_op(op) | Header._pack_version(version)

    @staticmethod
    def _validate_command_id(group_id: int, command_id: int) -> None:
        """Validate the command_id if the GroupId is known."""

        if command_id_t := Header._MAP_GROUP_ID_TO_COMMAND_ID_ENUM.get(group_id):
            try:
                command_id_t(command_id)
            except ValueError:
                raise ValueError(
                    f"Command ID {command_id} is not valid for Group ID {group_id}"
                    f" ({GroupId(group_id).name})"
                )

    def __post_init__(self) -> None:
        Header._validate_command_id(self.group_id, self.command_id)

        self._bytes: bytes
        object.__setattr__(
            self,
            '_bytes',
            self._STRUCT.pack(
                self._pack_op_and_version(self.op, self.version),
                Flag(self.flags),
                self.length,
                self.group_id,
                self.sequence,
                self.command_id,
            ),
        )

    def __bytes__(self) -> bytes:
        return self._bytes

    @property
    def BYTES(self) -> bytes:
        return self._bytes

    @staticmethod
    def loads(header: bytes) -> 'Header':
        """Deserialize the header bytes to a `Header`."""
        assert len(header) == 8, "The header is specified as 8 bytes"

        res_ver_op_byte, flags, length, group_id, sequence, command_id = Header._STRUCT.unpack(
            header
        )

        Header._validate_command_id(group_id, command_id)

        return Header(
            Header._unpack_op(res_ver_op_byte),
            Header._unpack_version(res_ver_op_byte),
            Flag(flags),
            length,
            group_id,
            sequence,
            command_id,
        )


@dataclass
class ForwardTree:
    ft: List[int] = field(default_factory=list)

    _STRUCT: ClassVar[struct.Struct] = struct.Struct(">Q")
    SIZE: ClassVar[int] = _STRUCT.size

    @staticmethod
    def _get_int(nimbles: List[int]) -> int:
        """Get the 64-bits data from the 16 nibbles"""
        hops = nimbles[0]
        if hops > 15:
            raise ValueError("ForwardTree max hops is 15")

        data = ForwardTree._set_nibble(15, 0, hops)
        for i in range(hops):
            data = ForwardTree._set_nibble(hops - i - 1, data, nimbles[i + 1])

        return data

    @staticmethod
    def _get_nibbles(value: int) -> List[int]:
        """Get all 16 nibbles"""
        nibbles = []
        for i in range(16):
            nibbles.append(ForwardTree._get_nibble(i, value))
        return nibbles

    @staticmethod
    def _get_nibble(index: int, value: int) -> int:
        """Get specific nibble (0-15)"""
        if not 0 <= index < 16:
            raise IndexError("Nibble index must be 0-15")
        return (value >> ((15 - index) * 4)) & 0xF

    @staticmethod
    def _set_nibble(index: int, data: int, value: int) -> int:
        """Set specific nibble (0-15)"""
        if not 0 <= index < 16:
            raise IndexError("Nibble index must be 0-15")
        if not 0 <= value <= 15:
            raise ValueError("Nibble value must be 0-15")

        # Clear the target nibble
        mask = ~(0xF << (index * 4))
        data &= mask
        # Set the new value
        data |= (value & 0xF) << (index * 4)
        return data

    def __post_init__(self) -> None:
        self._bytes: bytes
        object.__setattr__(
            self,
            '_bytes',
            self._STRUCT.pack(ForwardTree._get_int(self.ft)),
        )

    def __bytes__(self) -> bytes:
        return self._bytes

    @property
    def BYTES(self) -> bytes:
        return self._bytes

    @staticmethod
    def loads(forward: bytes) -> 'ForwardTree':
        """Deserialize the payload bytes to a `ForwardTree`."""
        assert len(forward) == 8, "The ForwardTree is specified as 8 bytes"

        data64 = ForwardTree._STRUCT.unpack(forward)
        nimbles = ForwardTree._get_nibbles(data64)

        return ForwardTree(nimbles)
