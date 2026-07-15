"""Test the SMP Image Management group."""

from __future__ import annotations

from typing import Any, TypeVar

import cbor2
import pytest
from pydantic import BaseModel, ValidationError

from smp import header as smphdr
from smp import message as smpmsg
from smp import os_management as smpos
from tests.helpers import make_assert_header

oscmd = smphdr.CommandId.OSManagement


T = TypeVar("T", bound=smpmsg._MessageBase)


def _do_test(
    msg: type[T],
    op: smphdr.OP,
    command_id: smphdr.CommandId.OSManagement,
    data: dict[str, Any],
    nested_model: type[BaseModel] | None = None,
) -> T:
    cbor = cbor2.dumps(data, canonical=True)
    assert_header = make_assert_header(smphdr.GroupId.OS_MANAGEMENT, op, command_id, len(cbor))

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


def test_ResetWriteRequest_boot_mode_normal() -> None:
    r = _do_test(smpos.ResetWriteRequest, smphdr.OP.WRITE, oscmd.RESET, {"boot_mode": 0})
    assert r.boot_mode is smpos.BootMode.NORMAL


def test_ResetWriteRequest_boot_mode_bootloader() -> None:
    r = _do_test(smpos.ResetWriteRequest, smphdr.OP.WRITE, oscmd.RESET, {"boot_mode": 1})
    assert r.boot_mode is smpos.BootMode.BOOTLOADER


def test_ResetWriteRequest_boot_mode_passes_through_unknown_int() -> None:
    """A wire-valid but unrecognized boot mode stays a plain int."""
    r = _do_test(smpos.ResetWriteRequest, smphdr.OP.WRITE, oscmd.RESET, {"boot_mode": 5})
    assert r.boot_mode == 5
    assert type(r.boot_mode) is int


def test_ResetWriteRequest_force_and_boot_mode() -> None:
    r = _do_test(
        smpos.ResetWriteRequest,
        smphdr.OP.WRITE,
        oscmd.RESET,
        {"force": 1, "boot_mode": 1},
    )
    assert r.force == 1
    assert r.boot_mode is smpos.BootMode.BOOTLOADER


def test_ResetWriteRequest_boot_mode_accepts_enum_member() -> None:
    """Constructing with a BootMode member serializes identically to its int value."""
    from_enum = smpos.ResetWriteRequest(boot_mode=smpos.BootMode.BOOTLOADER)
    from_int = smpos.ResetWriteRequest(boot_mode=1)
    assert from_enum.BYTES[8:] == from_int.BYTES[8:]
    assert from_enum.boot_mode is smpos.BootMode.BOOTLOADER


@pytest.mark.parametrize("boot_mode", [-1, 256])
def test_ResetWriteRequest_boot_mode_rejects_out_of_range(boot_mode: int) -> None:
    """boot_mode is a uint8_t on the wire; values outside [0, 255] are invalid."""
    with pytest.raises(ValidationError):
        smpos.ResetWriteRequest(boot_mode=boot_mode)


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
                    "stksiz": 5,
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
                    "stksiz": 12,
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


def test_TaskStatisticsReadResponse_all_fields() -> None:
    """Test TaskStatistics with all fields present."""
    data: dict[str, Any] = {
        "tasks": {
            "task": {
                "prio": 1,
                "tid": 2,
                "state": 3,
                "stkuse": 4,
                "stksiz": 5,
                "cswcnt": 6,
                "runtime": 7,
                "last_checkin": 0,
                "next_checkin": 0,
            }
        }
    }
    cbor = cbor2.dumps(data, canonical=True)
    assert_header = make_assert_header(
        smphdr.GroupId.OS_MANAGEMENT, smphdr.OP.READ_RSP, oscmd.TASK_STATS, len(cbor)
    )

    m = smpos.TaskStatisticsReadResponse(**data)
    assert_header(m)
    assert isinstance(m.tasks["task"], smpos.TaskStatistics)
    assert m.tasks["task"].prio == 1
    assert m.tasks["task"].tid == 2
    assert m.tasks["task"].state == 3
    assert m.tasks["task"].stkuse == 4
    assert m.tasks["task"].stksiz == 5
    assert m.tasks["task"].cswcnt == 6
    assert m.tasks["task"].runtime == 7
    assert m.tasks["task"].last_checkin == 0
    assert m.tasks["task"].next_checkin == 0
    assert cbor == m.BYTES[8:]

    # Test deserialization
    m2 = smpos.TaskStatisticsReadResponse.loads(m.BYTES)
    assert_header(m2)
    assert isinstance(m2.tasks["task"], smpos.TaskStatistics)


def test_TaskStatisticsZephyrReadResponse_only_required() -> None:
    """Test TaskStatisticsZephyr with only required fields (prio, tid, state)."""
    data: dict[str, Any] = {
        "tasks": {
            "zephyr_task": {
                "prio": 10,
                "tid": 20,
                "state": 30,
            }
        }
    }
    cbor = cbor2.dumps(data, canonical=True)
    assert_header = make_assert_header(
        smphdr.GroupId.OS_MANAGEMENT, smphdr.OP.READ_RSP, oscmd.TASK_STATS, len(cbor)
    )

    m = smpos.TaskStatisticsReadResponse(**data)
    assert_header(m)
    assert isinstance(m.tasks["zephyr_task"], smpos.TaskStatisticsZephyr)
    assert m.tasks["zephyr_task"].prio == 10
    assert m.tasks["zephyr_task"].tid == 20
    assert m.tasks["zephyr_task"].state == 30
    assert m.tasks["zephyr_task"].stkuse is None
    assert m.tasks["zephyr_task"].stksiz is None
    assert m.tasks["zephyr_task"].cswcnt is None
    assert m.tasks["zephyr_task"].runtime is None
    assert m.tasks["zephyr_task"].last_checkin is None
    assert m.tasks["zephyr_task"].next_checkin is None
    assert cbor == m.BYTES[8:]

    # Test deserialization
    m2 = smpos.TaskStatisticsReadResponse.loads(m.BYTES)
    assert_header(m2)
    assert isinstance(m2.tasks["zephyr_task"], smpos.TaskStatisticsZephyr)


def test_TaskStatisticsZephyrReadResponse_partial_fields() -> None:
    """Test TaskStatisticsZephyr with some optional fields present."""
    data: dict[str, Any] = {
        "tasks": {
            "partial_task": {
                "prio": 5,
                "tid": 15,
                "state": 25,
                "stksiz": 100,
                "stkuse": 50,
            }
        }
    }
    cbor = cbor2.dumps(data, canonical=True)
    assert_header = make_assert_header(
        smphdr.GroupId.OS_MANAGEMENT, smphdr.OP.READ_RSP, oscmd.TASK_STATS, len(cbor)
    )

    m = smpos.TaskStatisticsReadResponse(**data)
    assert_header(m)
    assert isinstance(m.tasks["partial_task"], smpos.TaskStatisticsZephyr)
    assert m.tasks["partial_task"].prio == 5
    assert m.tasks["partial_task"].tid == 15
    assert m.tasks["partial_task"].state == 25
    assert m.tasks["partial_task"].stksiz == 100
    assert m.tasks["partial_task"].stkuse == 50
    assert m.tasks["partial_task"].cswcnt is None
    assert m.tasks["partial_task"].runtime is None
    assert m.tasks["partial_task"].last_checkin is None
    assert m.tasks["partial_task"].next_checkin is None
    assert cbor == m.BYTES[8:]

    # Test deserialization
    m2 = smpos.TaskStatisticsReadResponse.loads(m.BYTES)
    assert_header(m2)
    assert isinstance(m2.tasks["partial_task"], smpos.TaskStatisticsZephyr)
