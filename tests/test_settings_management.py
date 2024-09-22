"""Test the SMP Settings Management group."""

from __future__ import annotations

from typing import Any, Dict, Type, TypeVar

import cbor2

from smp import header as smphdr
from smp import message as smpmsg
from smp import settings_management as smpset
from tests.helpers import make_assert_header

T = TypeVar("T", bound=smpmsg._MessageBase)


def _do_test(
    msg: Type[T],
    op: smphdr.OP,
    command_id: smphdr.CommandId.SettingsManagement,
    data: Dict[str, Any],
) -> T:
    cbor = cbor2.dumps(data, canonical=True)
    assert_header = make_assert_header(
        smphdr.GroupId.SETTINGS_MANAGEMENT, op, command_id, len(cbor)
    )

    def _assert_common(r: smpmsg._MessageBase) -> None:
        assert_header(r)
        for k, v in data.items():
            assert v == getattr(r, k)
        assert cbor == r.BYTES[8:]

    r = msg(**data)

    _assert_common(r)  # serialize
    _assert_common(msg.loads(r.BYTES))  # deserialize

    return r


def test_ReadSettingRequest() -> None:
    r = _do_test(
        smpset.ReadSettingRequest,
        smphdr.OP.READ,
        smphdr.CommandId.SettingsManagement.READ_WRITE_SETTING,
        {"name": "example"},
    )
    assert r.name == "example"
    assert r.max_size is None

    r = _do_test(
        smpset.ReadSettingRequest,
        smphdr.OP.READ,
        smphdr.CommandId.SettingsManagement.READ_WRITE_SETTING,
        {"name": "example", "max_size": 256},
    )
    assert r.name == "example"
    assert r.max_size == 256


def test_ReadSettingResponse() -> None:
    r = _do_test(
        smpset.ReadSettingResponse,
        smphdr.OP.READ_RSP,
        smphdr.CommandId.SettingsManagement.READ_WRITE_SETTING,
        {"val": b"example"},
    )
    assert r.val == b"example"
    assert r.max_size is None

    r = _do_test(
        smpset.ReadSettingResponse,
        smphdr.OP.READ_RSP,
        smphdr.CommandId.SettingsManagement.READ_WRITE_SETTING,
        {"val": b"example", "max_size": 256},
    )
    assert r.val == b"example"
    assert r.max_size == 256


def test_WriteSettingRequest() -> None:
    r = _do_test(
        smpset.WriteSettingRequest,
        smphdr.OP.WRITE,
        smphdr.CommandId.SettingsManagement.READ_WRITE_SETTING,
        {"name": "example", "val": b"example"},
    )
    assert r.name == "example"
    assert r.val == b"example"


def test_WriteSettingResponse() -> None:
    _do_test(
        smpset.WriteSettingResponse,
        smphdr.OP.WRITE_RSP,
        smphdr.CommandId.SettingsManagement.READ_WRITE_SETTING,
        {},
    )


def test_DeleteSettingRequest() -> None:
    r = _do_test(
        smpset.DeleteSettingRequest,
        smphdr.OP.WRITE,
        smphdr.CommandId.SettingsManagement.DELETE_SETTING,
        {"name": "example"},
    )
    assert r.name == "example"


def test_DeleteSettingResponse() -> None:
    _do_test(
        smpset.DeleteSettingResponse,
        smphdr.OP.WRITE_RSP,
        smphdr.CommandId.SettingsManagement.DELETE_SETTING,
        {},
    )


def test_CommitSettingsRequest() -> None:
    _do_test(
        smpset.CommitSettingsRequest,
        smphdr.OP.WRITE,
        smphdr.CommandId.SettingsManagement.COMMIT_SETTINGS,
        {},
    )


def test_CommitSettingsResponse() -> None:
    _do_test(
        smpset.CommitSettingsResponse,
        smphdr.OP.WRITE_RSP,
        smphdr.CommandId.SettingsManagement.COMMIT_SETTINGS,
        {},
    )


def test_LoadSettingsRequest() -> None:
    _do_test(
        smpset.LoadSettingsRequest,
        smphdr.OP.READ,
        smphdr.CommandId.SettingsManagement.LOAD_SAVE_SETTINGS,
        {},
    )


def test_LoadSettingsResponse() -> None:
    _do_test(
        smpset.LoadSettingsResponse,
        smphdr.OP.READ_RSP,
        smphdr.CommandId.SettingsManagement.LOAD_SAVE_SETTINGS,
        {},
    )


def test_SaveSettingsRequest() -> None:
    _do_test(
        smpset.SaveSettingsRequest,
        smphdr.OP.WRITE,
        smphdr.CommandId.SettingsManagement.LOAD_SAVE_SETTINGS,
        {},
    )


def test_SaveSettingsResponse() -> None:
    _do_test(
        smpset.SaveSettingsResponse,
        smphdr.OP.WRITE_RSP,
        smphdr.CommandId.SettingsManagement.LOAD_SAVE_SETTINGS,
        {},
    )
