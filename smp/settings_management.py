"""The Simple Management Protocol (SMP) Settings Management group."""

from __future__ import annotations

from enum import IntEnum, unique

import smp.error as smperr
import smp.header as smphdr
import smp.message as smpmsg


class ReadSettingRequest(smpmsg.ReadRequest):
    """Read setting."""

    _GROUP_ID = smphdr.GroupId.SETTINGS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.SettingsManagement.READ_WRITE_SETTING

    name: str
    """The name of the setting to read."""

    max_size: int | None = None
    """The maximum size of the data to read."""


class ReadSettingResponse(smpmsg.ReadResponse):
    """Read setting success response."""

    _GROUP_ID = smphdr.GroupId.SETTINGS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.SettingsManagement.READ_WRITE_SETTING

    val: bytes
    """Binary string of the returned data.

    Note that the underlying data type cannot be specified through this and must
    be known by the client.
    """

    max_size: int | None = None
    """The SMP server supports a smaller size than requested.

    Will be set if the maximum supported data size is smaller than the maximum
    requested data size, and contains the maximum data size which the device
    supports, equivalent to `CONFIG_MCUMGR_GRP_SETTINGS_NAME_LEN`.
    """


class WriteSettingRequest(smpmsg.WriteRequest):
    """Write setting."""

    _GROUP_ID = smphdr.GroupId.SETTINGS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.SettingsManagement.READ_WRITE_SETTING

    name: str
    """The name of the setting to write."""

    val: bytes
    """Binary data to write."""


class WriteSettingResponse(smpmsg.WriteResponse):
    """Write setting success response."""

    _GROUP_ID = smphdr.GroupId.SETTINGS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.SettingsManagement.READ_WRITE_SETTING


class DeleteSettingRequest(smpmsg.WriteRequest):
    """Delete setting."""

    _GROUP_ID = smphdr.GroupId.SETTINGS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.SettingsManagement.DELETE_SETTING

    name: str
    """The name of the setting to delete."""


class DeleteSettingResponse(smpmsg.WriteResponse):
    """Delete setting success response."""

    _GROUP_ID = smphdr.GroupId.SETTINGS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.SettingsManagement.DELETE_SETTING


class CommitSettingsRequest(smpmsg.WriteRequest):
    """Commit pending settings.

    Commit settings command allows committing all settings that have been set
    but not yet applied on a device.
    """

    _GROUP_ID = smphdr.GroupId.SETTINGS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.SettingsManagement.COMMIT_SETTINGS


class CommitSettingsResponse(smpmsg.WriteResponse):
    """Commit pending settings success response."""

    _GROUP_ID = smphdr.GroupId.SETTINGS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.SettingsManagement.COMMIT_SETTINGS


class LoadSettingsRequest(smpmsg.ReadRequest):
    """Load settings from persistent storage."""

    _GROUP_ID = smphdr.GroupId.SETTINGS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.SettingsManagement.LOAD_SAVE_SETTINGS


class LoadSettingsResponse(smpmsg.ReadResponse):
    """Load settings from persistent storage success response."""

    _GROUP_ID = smphdr.GroupId.SETTINGS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.SettingsManagement.LOAD_SAVE_SETTINGS


class SaveSettingsRequest(smpmsg.WriteRequest):
    """Save settings to persistent storage."""

    _GROUP_ID = smphdr.GroupId.SETTINGS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.SettingsManagement.LOAD_SAVE_SETTINGS


class SaveSettingsResponse(smpmsg.WriteResponse):
    """Save settings to persistent storage success response."""

    _GROUP_ID = smphdr.GroupId.SETTINGS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.SettingsManagement.LOAD_SAVE_SETTINGS


@unique
class SETTINGS_MGMT_ERR(IntEnum):
    """Return codes for the settings management group."""

    OK = 0
    """No error, this is implied if there is no ret value in the response."""

    UNKNOWN = 1
    """Unknown error occurred."""

    KEY_TOO_LONG = 2
    """The provided key name is too long to be used."""

    KEY_NOT_FOUND = 3
    """The provided key name does not exist."""

    READ_NOT_SUPPORTED = 4
    """The provided key name does not support being read."""

    ROOT_KEY_NOT_FOUND = 5
    """The provided root key name does not exist."""

    WRITE_NOT_SUPPORTED = 6
    """The provided key name does not support being written."""

    DELETE_NOT_SUPPORTED = 7
    """The provided key name does not support being deleted."""


class SettingsManagementErrorV1(smperr.ErrorV1):
    """Error response to a settings management command."""

    _GROUP_ID = smphdr.GroupId.SETTINGS_MANAGEMENT


class SettingsManagementErrorV2(smperr.ErrorV2[SETTINGS_MGMT_ERR]):
    """Error response to a settings management command."""

    _GROUP_ID = smphdr.GroupId.SETTINGS_MANAGEMENT
