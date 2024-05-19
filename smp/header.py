"""The Simple Management Protocol (SMP) header."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum, IntFlag, auto, unique
from typing import ClassVar, Dict, Type, Union

from typing_extensions import TypeAlias


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
    class ShellManagement(IntEnum):
        EXECUTE = 0

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
    ZEPHYR = 63


class UserGroupId(IntEnum):
    """Users may define their own Group IDs starting at 64.

    It is optional to register them here."""

    INTERCREATE = 64


AnyGroupId: TypeAlias = Union[IntEnum, int]


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
    V0 = 0
    V1 = 1


class _VERSION_BIT:
    MASK = 0b11
    SHIFT = 3


@unique
class Flag(IntFlag):
    UNUSED = auto()


@dataclass(frozen=True)
class Header:
    op: OP
    version: Version
    flags: Flag
    length: int
    group_id: Union[AnyGroupId, GroupId, UserGroupId]
    sequence: int
    command_id: Union[
        AnyCommandId,
        CommandId.OSManagement,
        CommandId.ImageManagement,
        CommandId.ShellManagement,
        CommandId.Intercreate,
    ]

    _MAP_GROUP_ID_TO_COMMAND_ID_ENUM: ClassVar[Dict[int, Type[IntEnum]]] = {
        GroupId.OS_MANAGEMENT: CommandId.OSManagement,
        GroupId.IMAGE_MANAGEMENT: CommandId.ImageManagement,
        GroupId.SHELL_MANAGEMENT: CommandId.ShellManagement,
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
        return self._bytes  # type: ignore

    @property
    def BYTES(self) -> bytes:
        return self._bytes  # type: ignore

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
