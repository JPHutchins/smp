"""Test the SMP Image Management group."""

from __future__ import annotations

from smp import header as smphdr
from smp import os_management as smpos
from tests.helpers import make_do_test

oscmd = smphdr.CommandId.OSManagement


_do_test = make_do_test(smphdr.GroupId.OS_MANAGEMENT)


def test_EchoWriteRequest() -> None:
    _do_test(
        smpos.EchoWriteRequest,
        smphdr.OP.WRITE,
        oscmd.ECHO,
        {"d": "Hello world!"},
    )


def test_EchoWriteResponse() -> None:
    _do_test(
        smpos.EchoWriteResponse,
        smphdr.OP.WRITE_RSP,
        oscmd.ECHO,
        {"r": "Hi!"},
    )


def test_ResetWriteRequest() -> None:
    _do_test(smpos.ResetWriteRequest, smphdr.OP.WRITE, oscmd.RESET, {})


def test_ResetWriteResponse() -> None:
    _do_test(smpos.ResetWriteResponse, smphdr.OP.WRITE_RSP, oscmd.RESET, {})


def test_TaskStatisticsReadRequest() -> None:
    _do_test(smpos.TaskStatisticsReadRequest, smphdr.OP.READ, oscmd.TASK_STATS, {})


def test_TaskStatisticsReadResponse() -> None:
    m = _do_test(
        smpos.TaskStatisticsReadResponse,
        smphdr.OP.READ_RSP,
        oscmd.TASK_STATS,
        {
            "tasks": {
                "task_1": {
                    "prio": 1,
                    "tid": 2,
                    "state": 3,
                    "stkuse": 4,
                    "stksize": 5,
                    "cswcnt": 6,
                    "runtime": 7,
                    "last_checkin": 0,
                    "next_checkin": 0,
                },
                "task_2": {
                    "prio": 8,
                    "tid": 9,
                    "state": 10,
                    "stkuse": 11,
                    "stksize": 12,
                    "cswcnt": 13,
                    "runtime": 14,
                    "last_checkin": 0,
                    "next_checkin": 0,
                },
            }
        },
        nested_model=smpos.TaskStatistics,
    )

    assert m.tasks["task_1"].prio == 1
    assert m.tasks["task_2"].prio == 8
    assert m.tasks["task_1"].tid == 2
    assert m.tasks["task_2"].tid == 9


def test_MemoryPoolStatisticsReadRequest() -> None:
    _do_test(smpos.MemoryPoolStatisticsReadRequest, smphdr.OP.READ, oscmd.MEMORY_POOL_STATS, {})


def test_MemoryPoolStatisticsReadResponse() -> None:
    _do_test(
        smpos.MemoryPoolStatisticsReadResponse,
        smphdr.OP.READ_RSP,
        oscmd.MEMORY_POOL_STATS,
        {
            "mem_pool_1": {"blksize": 1, "nblks": 2, "nfree": 3, "min": 4},
            "mem_pool_2": {"blksize": 5, "nblks": 6, "nfree": 7, "min": 8},
        },
    )


def test_DatetimeReadRequest() -> None:
    _do_test(smpos.DateTimeReadRequest, smphdr.OP.READ, oscmd.DATETIME_STRING, {})


def test_DatetimeReadResponse() -> None:
    _do_test(
        smpos.DateTimeReadResponse,
        smphdr.OP.READ_RSP,
        oscmd.DATETIME_STRING,
        {"datetime": "2024-01-01T00:00:00Z"},
    )


def test_DateTimeWriteRequest() -> None:
    _do_test(
        smpos.DateTimeWriteRequest,
        smphdr.OP.WRITE,
        oscmd.DATETIME_STRING,
        {"datetime": "2024-01-01T00:00:00Z"},
    )


def test_DateTimeWriteResponse() -> None:
    _do_test(
        smpos.DateTimeWriteResponse,
        smphdr.OP.WRITE_RSP,
        oscmd.DATETIME_STRING,
        {},
    )


def test_MCUMgrParametersReadRequest() -> None:
    _do_test(smpos.MCUMgrParametersReadRequest, smphdr.OP.READ, oscmd.MCUMGR_PARAMETERS, {})


def test_MCUMgrParametersReadResponse() -> None:
    _do_test(
        smpos.MCUMgrParametersReadResponse,
        smphdr.OP.READ_RSP,
        oscmd.MCUMGR_PARAMETERS,
        {"buf_size": 1, "buf_count": 2},
    )


def test_OSApplicationInfoReadRequest() -> None:
    _do_test(smpos.OSApplicationInfoReadRequest, smphdr.OP.READ, oscmd.OS_APPLICATION_INFO, {})
    _do_test(
        smpos.OSApplicationInfoReadRequest,
        smphdr.OP.READ,
        oscmd.OS_APPLICATION_INFO,
        {"format": "snrvbmpioa"},
    )


def test_OSApplicationInfoReadResponse() -> None:
    _do_test(
        smpos.OSApplicationInfoReadResponse,
        smphdr.OP.READ_RSP,
        oscmd.OS_APPLICATION_INFO,
        {"output": "the requested output string"},
    )


def test_BootloaderInformationReadRequest() -> None:
    _do_test(smpos.BootloaderInformationReadRequest, smphdr.OP.READ, oscmd.BOOTLOADER_INFO, {})
    _do_test(
        smpos.BootloaderInformationReadRequest,
        smphdr.OP.READ,
        oscmd.BOOTLOADER_INFO,
        {"query": "MCUbootMode"},
    )


def test_BootloaderInformationReadResponse() -> None:
    r = _do_test(
        smpos.BootloaderInformationReadResponse,
        smphdr.OP.READ_RSP,
        oscmd.BOOTLOADER_INFO,
        {"bootloader": "MCUboot", "response": {"mode": 3, "no-downgrade": True}},
    )

    assert r.bootloader == "MCUboot"
    assert type(r.response) is dict
    assert r.response["mode"] == smpos.MCUbootMode.SWAP_WITHOUT_SCRATCH
    assert r.response["no-downgrade"] is True
