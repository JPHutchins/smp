"""Test the SMP Zephyr Management group."""

from __future__ import annotations

from smp import header as smphdr
from smp import zephyr_management as smpz
from tests.helpers import make_do_test

zephyrcmd = smphdr.CommandId.ZephyrManagement


_do_test = make_do_test(smphdr.GroupId.ZEPHYR_MANAGEMENT)


def test_EraseStorageRequest() -> None:
    _do_test(
        smpz.EraseStorageRequest,
        smphdr.OP.WRITE,
        zephyrcmd.ERASE_STORAGE,
        {},
    )


def test_EraseStorageResponse() -> None:
    _do_test(
        smpz.EraseStorageResponse,
        smphdr.OP.WRITE_RSP,
        zephyrcmd.ERASE_STORAGE,
        {},
    )
