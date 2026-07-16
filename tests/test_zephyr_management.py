"""Test the SMP Zephyr Management group."""

from __future__ import annotations

from smp import header as smphdr
from smp import zephyr_management as smpz
from tests.helpers import assert_frame

zephyrcmd = smphdr.CommandId.ZephyrManagement


def test_EraseStorageRequest() -> None:
    assert_frame(
        smpz.EraseStorageRequest(),
        op=smphdr.OP.WRITE,
        group_id=smphdr.GroupId.ZEPHYR_MANAGEMENT,
        command_id=zephyrcmd.ERASE_STORAGE,
    )


def test_EraseStorageResponse() -> None:
    assert_frame(
        smpz.EraseStorageResponse(),
        op=smphdr.OP.WRITE_RSP,
        group_id=smphdr.GroupId.ZEPHYR_MANAGEMENT,
        command_id=zephyrcmd.ERASE_STORAGE,
    )
