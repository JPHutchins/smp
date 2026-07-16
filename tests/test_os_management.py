"""Test the SMP OS Management group."""

from __future__ import annotations

import msgspec
import pytest

from smp import header as smphdr
from smp import os_management as smpos
from tests.helpers import assert_frame

oscmd = smphdr.CommandId.OSManagement
OS = smphdr.GroupId.OS_MANAGEMENT


def test_EchoWriteRequest() -> None:
    assert_frame(
        smpos.EchoWriteRequest(d="Hello world!"),
        op=smphdr.OP.WRITE,
        group_id=OS,
        command_id=oscmd.ECHO,
    )


def test_EchoWriteResponse() -> None:
    assert_frame(
        smpos.EchoWriteResponse(r="Hi!"), op=smphdr.OP.WRITE_RSP, group_id=OS, command_id=oscmd.ECHO
    )


def test_ResetWriteRequest() -> None:
    assert_frame(
        smpos.ResetWriteRequest(), op=smphdr.OP.WRITE, group_id=OS, command_id=oscmd.RESET, length=1
    )


def test_ResetWriteResponse() -> None:
    assert_frame(
        smpos.ResetWriteResponse(),
        op=smphdr.OP.WRITE_RSP,
        group_id=OS,
        command_id=oscmd.RESET,
        length=1,
    )


def test_ResetWriteRequest_boot_mode_normal() -> None:
    frame = assert_frame(
        smpos.ResetWriteRequest(boot_mode=0),
        op=smphdr.OP.WRITE,
        group_id=OS,
        command_id=oscmd.RESET,
    )
    assert frame.data.boot_mode is smpos.BootMode.NORMAL


def test_ResetWriteRequest_boot_mode_bootloader() -> None:
    frame = assert_frame(
        smpos.ResetWriteRequest(boot_mode=1),
        op=smphdr.OP.WRITE,
        group_id=OS,
        command_id=oscmd.RESET,
    )
    assert frame.data.boot_mode is smpos.BootMode.BOOTLOADER


def test_ResetWriteRequest_boot_mode_passes_through_unknown_int() -> None:
    """A wire-valid but unrecognized boot mode stays a plain int."""
    frame = assert_frame(
        smpos.ResetWriteRequest(boot_mode=5),
        op=smphdr.OP.WRITE,
        group_id=OS,
        command_id=oscmd.RESET,
    )
    assert frame.data.boot_mode == 5
    assert type(frame.data.boot_mode) is int


def test_ResetWriteRequest_force_and_boot_mode() -> None:
    frame = assert_frame(
        smpos.ResetWriteRequest(force=1, boot_mode=1),
        op=smphdr.OP.WRITE,
        group_id=OS,
        command_id=oscmd.RESET,
    )
    assert frame.data.force == 1
    assert frame.data.boot_mode is smpos.BootMode.BOOTLOADER


def test_ResetWriteRequest_boot_mode_accepts_enum_member() -> None:
    """Constructing with a BootMode member serializes identically to its int value."""
    from_enum = smpos.ResetWriteRequest(boot_mode=smpos.BootMode.BOOTLOADER)
    from_int = smpos.ResetWriteRequest(boot_mode=1)
    assert bytes(from_enum.to_frame(sequence=0))[8:] == bytes(from_int.to_frame(sequence=0))[8:]
    assert from_enum.boot_mode is smpos.BootMode.BOOTLOADER


@pytest.mark.parametrize("boot_mode", [-1, 256])
def test_ResetWriteRequest_boot_mode_rejects_out_of_range(boot_mode: int) -> None:
    """boot_mode is a uint8_t on the wire; values outside [0, 255] are invalid."""
    with pytest.raises(ValueError):
        smpos.ResetWriteRequest(boot_mode=boot_mode)


def test_TaskStatisticsReadRequest() -> None:
    assert_frame(
        smpos.TaskStatisticsReadRequest(),
        op=smphdr.OP.READ,
        group_id=OS,
        command_id=oscmd.TASK_STATS,
        length=1,
    )


def test_TaskStatisticsReadResponse() -> None:
    frame = assert_frame(
        smpos.TaskStatisticsReadResponse(
            tasks={
                "task_1": smpos.TaskStatistics(
                    prio=1,
                    tid=2,
                    state=3,
                    stkuse=4,
                    stksiz=5,
                    cswcnt=6,
                    runtime=7,
                    last_checkin=0,
                    next_checkin=0,
                ),
                "task_2": smpos.TaskStatistics(
                    prio=8,
                    tid=9,
                    state=10,
                    stkuse=11,
                    stksiz=12,
                    cswcnt=13,
                    runtime=14,
                    last_checkin=0,
                    next_checkin=0,
                ),
            }
        ),
        op=smphdr.OP.READ_RSP,
        group_id=OS,
        command_id=oscmd.TASK_STATS,
    )
    assert frame.data.tasks["task_1"].prio == 1
    assert frame.data.tasks["task_2"].prio == 8
    assert frame.data.tasks["task_1"].tid == 2
    assert frame.data.tasks["task_2"].tid == 9


def test_MemoryPoolStatisticsReadRequest() -> None:
    assert_frame(
        smpos.MemoryPoolStatisticsReadRequest(),
        op=smphdr.OP.READ,
        group_id=OS,
        command_id=oscmd.MEMORY_POOL_STATS,
        length=1,
    )


def test_MemoryPoolStatisticsReadResponse() -> None:
    frame = assert_frame(
        smpos.MemoryPoolStatisticsReadResponse(
            pools={
                "mem_pool_1": smpos.MemoryPoolStatistics(blksize=1, nblks=2, nfree=3, min=4),
                "mem_pool_2": smpos.MemoryPoolStatistics(blksize=5, nblks=6, nfree=7, min=8),
            }
        ),
        op=smphdr.OP.READ_RSP,
        group_id=OS,
        command_id=oscmd.MEMORY_POOL_STATS,
    )
    assert frame.data.pools["mem_pool_1"].blksize == 1
    assert frame.data.pools["mem_pool_2"].min == 8


def test_DatetimeReadRequest() -> None:
    assert_frame(
        smpos.DateTimeReadRequest(),
        op=smphdr.OP.READ,
        group_id=OS,
        command_id=oscmd.DATETIME_STRING,
        length=1,
    )


def test_DatetimeReadResponse() -> None:
    assert_frame(
        smpos.DateTimeReadResponse(datetime="2024-01-01T00:00:00Z"),
        op=smphdr.OP.READ_RSP,
        group_id=OS,
        command_id=oscmd.DATETIME_STRING,
    )


def test_DateTimeWriteRequest() -> None:
    assert_frame(
        smpos.DateTimeWriteRequest(datetime="2024-01-01T00:00:00Z"),
        op=smphdr.OP.WRITE,
        group_id=OS,
        command_id=oscmd.DATETIME_STRING,
    )


def test_DateTimeWriteResponse() -> None:
    assert_frame(
        smpos.DateTimeWriteResponse(),
        op=smphdr.OP.WRITE_RSP,
        group_id=OS,
        command_id=oscmd.DATETIME_STRING,
        length=1,
    )


def test_MCUMgrParametersReadRequest() -> None:
    assert_frame(
        smpos.MCUMgrParametersReadRequest(),
        op=smphdr.OP.READ,
        group_id=OS,
        command_id=oscmd.MCUMGR_PARAMETERS,
        length=1,
    )


def test_MCUMgrParametersReadResponse() -> None:
    frame = assert_frame(
        smpos.MCUMgrParametersReadResponse(buf_size=1, buf_count=2),
        op=smphdr.OP.READ_RSP,
        group_id=OS,
        command_id=oscmd.MCUMGR_PARAMETERS,
    )
    assert frame.data.buf_size == 1
    assert frame.data.buf_count == 2


def test_OSApplicationInfoReadRequest() -> None:
    assert_frame(
        smpos.OSApplicationInfoReadRequest(),
        op=smphdr.OP.READ,
        group_id=OS,
        command_id=oscmd.OS_APPLICATION_INFO,
        length=1,
    )
    assert_frame(
        smpos.OSApplicationInfoReadRequest(format="snrvbmpioa"),
        op=smphdr.OP.READ,
        group_id=OS,
        command_id=oscmd.OS_APPLICATION_INFO,
    )


def test_OSApplicationInfoReadResponse() -> None:
    assert_frame(
        smpos.OSApplicationInfoReadResponse(output="the requested output string"),
        op=smphdr.OP.READ_RSP,
        group_id=OS,
        command_id=oscmd.OS_APPLICATION_INFO,
    )


def test_BootloaderInformationReadRequest() -> None:
    assert_frame(
        smpos.BootloaderInformationReadRequest(),
        op=smphdr.OP.READ,
        group_id=OS,
        command_id=oscmd.BOOTLOADER_INFO,
        length=1,
    )
    assert_frame(
        smpos.BootloaderInformationReadRequest(query="MCUbootMode"),
        op=smphdr.OP.READ,
        group_id=OS,
        command_id=oscmd.BOOTLOADER_INFO,
    )


def test_BootloaderInformationReadResponse() -> None:
    frame = assert_frame(
        smpos.BootloaderInformationReadResponse(
            bootloader="MCUboot",
            response=smpos.MCUbootModeQueryResponse(
                mode=smpos.MCUbootMode.SWAP_WITHOUT_SCRATCH, no_downgrade=True
            ),
        ),
        op=smphdr.OP.READ_RSP,
        group_id=OS,
        command_id=oscmd.BOOTLOADER_INFO,
    )
    assert frame.data.bootloader == "MCUboot"
    assert type(frame.data.response) is smpos.MCUbootModeQueryResponse
    assert frame.data.response.mode is smpos.MCUbootMode.SWAP_WITHOUT_SCRATCH
    assert frame.data.response.no_downgrade is True


def test_TaskStatisticsReadResponse_all_fields() -> None:
    """Test TaskStatistics with all fields present."""
    frame = assert_frame(
        smpos.TaskStatisticsReadResponse(
            tasks={
                "task": smpos.TaskStatistics(
                    prio=1,
                    tid=2,
                    state=3,
                    stkuse=4,
                    stksiz=5,
                    cswcnt=6,
                    runtime=7,
                    last_checkin=0,
                    next_checkin=0,
                )
            }
        ),
        op=smphdr.OP.READ_RSP,
        group_id=OS,
        command_id=oscmd.TASK_STATS,
    )
    task = frame.data.tasks["task"]
    assert isinstance(task, smpos.TaskStatistics)
    assert task.prio == 1
    assert task.tid == 2
    assert task.state == 3
    assert task.stkuse == 4
    assert task.stksiz == 5
    assert task.cswcnt == 6
    assert task.runtime == 7
    assert task.last_checkin == 0
    assert task.next_checkin == 0


def test_TaskStatisticsZephyrReadResponse_only_required() -> None:
    """Test TaskStatisticsZephyr with only required fields (prio, tid, state)."""
    frame = assert_frame(
        smpos.TaskStatisticsReadResponse(
            tasks={"zephyr_task": smpos.TaskStatisticsZephyr(prio=10, tid=20, state=30)}
        ),
        op=smphdr.OP.READ_RSP,
        group_id=OS,
        command_id=oscmd.TASK_STATS,
    )
    task = frame.data.tasks["zephyr_task"]
    assert isinstance(task, smpos.TaskStatisticsZephyr)
    assert task.prio == 10
    assert task.tid == 20
    assert task.state == 30
    assert task.stkuse is None
    assert task.stksiz is None
    assert task.cswcnt is None
    assert task.runtime is None
    assert task.last_checkin is None
    assert task.next_checkin is None


def test_TaskStatisticsZephyrReadResponse_partial_fields() -> None:
    """Test TaskStatisticsZephyr with some optional fields present."""
    frame = assert_frame(
        smpos.TaskStatisticsReadResponse(
            tasks={
                "partial_task": smpos.TaskStatisticsZephyr(
                    prio=5, tid=15, state=25, stksiz=100, stkuse=50
                )
            }
        ),
        op=smphdr.OP.READ_RSP,
        group_id=OS,
        command_id=oscmd.TASK_STATS,
    )
    task = frame.data.tasks["partial_task"]
    assert isinstance(task, smpos.TaskStatisticsZephyr)
    assert task.prio == 5
    assert task.tid == 15
    assert task.state == 25
    assert task.stksiz == 100
    assert task.stkuse == 50
    assert task.cswcnt is None
    assert task.runtime is None
    assert task.last_checkin is None
    assert task.next_checkin is None


def _os_header(command_id: smphdr.CommandId.OSManagement, op: smphdr.OP) -> smphdr.Header:
    return smphdr.Header(
        op=op,
        version=smphdr.Version.V2,
        flags=smphdr.Flag(0),
        length=0,
        group_id=OS,
        sequence=0,
        command_id=command_id,
    )


def test_TaskStatisticsReadResponse_rejects_missing_tasks() -> None:
    with pytest.raises(msgspec.ValidationError):
        smpos.TaskStatisticsReadResponse.load(_os_header(oscmd.TASK_STATS, smphdr.OP.READ_RSP), {})


def test_TaskStatisticsReadResponse_rejects_non_map_tasks() -> None:
    with pytest.raises(msgspec.ValidationError):
        smpos.TaskStatisticsReadResponse.load(
            _os_header(oscmd.TASK_STATS, smphdr.OP.READ_RSP), {"tasks": 5}
        )


def test_ResetWriteRequest_rejects_unknown_field() -> None:
    with pytest.raises(msgspec.ValidationError):
        smpos.ResetWriteRequest.load(_os_header(oscmd.RESET, smphdr.OP.WRITE), {"bogus": 1})
