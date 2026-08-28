"""Test the SMP Settings Management group."""

from __future__ import annotations

from smp import header as smphdr
from smp import settings_management as smpset
from tests.helpers import assert_frame

setcmd = smphdr.CommandId.SettingsManagement


def test_ReadSettingRequest() -> None:
    frame = assert_frame(
        smpset.ReadSettingRequest(name="example"),
        op=smphdr.OP.READ,
        group_id=smphdr.GroupId.SETTINGS_MANAGEMENT,
        command_id=setcmd.READ_WRITE_SETTING,
    )
    assert frame.data.name == "example"
    assert frame.data.max_size is None

    frame = assert_frame(
        smpset.ReadSettingRequest(name="example", max_size=256),
        op=smphdr.OP.READ,
        group_id=smphdr.GroupId.SETTINGS_MANAGEMENT,
        command_id=setcmd.READ_WRITE_SETTING,
    )
    assert frame.data.name == "example"
    assert frame.data.max_size == 256


def test_ReadSettingResponse() -> None:
    frame = assert_frame(
        smpset.ReadSettingResponse(val=b"example"),
        op=smphdr.OP.READ_RSP,
        group_id=smphdr.GroupId.SETTINGS_MANAGEMENT,
        command_id=setcmd.READ_WRITE_SETTING,
    )
    assert frame.data.val == b"example"
    assert frame.data.max_size is None

    frame = assert_frame(
        smpset.ReadSettingResponse(val=b"example", max_size=256),
        op=smphdr.OP.READ_RSP,
        group_id=smphdr.GroupId.SETTINGS_MANAGEMENT,
        command_id=setcmd.READ_WRITE_SETTING,
    )
    assert frame.data.val == b"example"
    assert frame.data.max_size == 256


def test_WriteSettingRequest() -> None:
    frame = assert_frame(
        smpset.WriteSettingRequest(name="example", val=b"example"),
        op=smphdr.OP.WRITE,
        group_id=smphdr.GroupId.SETTINGS_MANAGEMENT,
        command_id=setcmd.READ_WRITE_SETTING,
    )
    assert frame.data.name == "example"
    assert frame.data.val == b"example"


def test_WriteSettingResponse() -> None:
    assert_frame(
        smpset.WriteSettingResponse(),
        op=smphdr.OP.WRITE_RSP,
        group_id=smphdr.GroupId.SETTINGS_MANAGEMENT,
        command_id=setcmd.READ_WRITE_SETTING,
    )


def test_DeleteSettingRequest() -> None:
    frame = assert_frame(
        smpset.DeleteSettingRequest(name="example"),
        op=smphdr.OP.WRITE,
        group_id=smphdr.GroupId.SETTINGS_MANAGEMENT,
        command_id=setcmd.DELETE_SETTING,
    )
    assert frame.data.name == "example"


def test_DeleteSettingResponse() -> None:
    assert_frame(
        smpset.DeleteSettingResponse(),
        op=smphdr.OP.WRITE_RSP,
        group_id=smphdr.GroupId.SETTINGS_MANAGEMENT,
        command_id=setcmd.DELETE_SETTING,
    )


def test_CommitSettingsRequest() -> None:
    assert_frame(
        smpset.CommitSettingsRequest(),
        op=smphdr.OP.WRITE,
        group_id=smphdr.GroupId.SETTINGS_MANAGEMENT,
        command_id=setcmd.COMMIT_SETTINGS,
    )


def test_CommitSettingsResponse() -> None:
    assert_frame(
        smpset.CommitSettingsResponse(),
        op=smphdr.OP.WRITE_RSP,
        group_id=smphdr.GroupId.SETTINGS_MANAGEMENT,
        command_id=setcmd.COMMIT_SETTINGS,
    )


def test_LoadSettingsRequest() -> None:
    assert_frame(
        smpset.LoadSettingsRequest(),
        op=smphdr.OP.READ,
        group_id=smphdr.GroupId.SETTINGS_MANAGEMENT,
        command_id=setcmd.LOAD_SAVE_SETTINGS,
    )


def test_LoadSettingsResponse() -> None:
    assert_frame(
        smpset.LoadSettingsResponse(),
        op=smphdr.OP.READ_RSP,
        group_id=smphdr.GroupId.SETTINGS_MANAGEMENT,
        command_id=setcmd.LOAD_SAVE_SETTINGS,
    )


def test_SaveSettingsRequest() -> None:
    assert_frame(
        smpset.SaveSettingsRequest(),
        op=smphdr.OP.WRITE,
        group_id=smphdr.GroupId.SETTINGS_MANAGEMENT,
        command_id=setcmd.LOAD_SAVE_SETTINGS,
    )


def test_SaveSettingsResponse() -> None:
    assert_frame(
        smpset.SaveSettingsResponse(),
        op=smphdr.OP.WRITE_RSP,
        group_id=smphdr.GroupId.SETTINGS_MANAGEMENT,
        command_id=setcmd.LOAD_SAVE_SETTINGS,
    )
