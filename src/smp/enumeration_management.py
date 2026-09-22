"""The Simple Management Protocol (SMP) Enumeration Management group."""

from __future__ import annotations

from enum import IntEnum, unique

import msgspec

import smp.error as smperr
import smp.header as smphdr
import smp.message as smpmsg


@unique
class ENUM_MGMT_ERR(IntEnum):
    """Return codes for the enumeration management group."""

    OK = 0
    """No error, this is implied if there is no ret value in the response."""

    UNKNOWN = 1
    """Unknown error occurred."""

    ERR_TOO_MANY_GROUP_ENTRIES = 2
    """Too many entries were provided."""

    ERR_INSUFFICIENT_HEAP_FOR_ENTRIES = 3
    """Insufficient heap memory to store entry data."""

    ENUM_MGMT_ERR_INDEX_TOO_LARGE = 4
    """Provided index is larger than the number of supported groups."""


class EnumManagementErrorV1(smperr.ErrorV1, frozen=True):
    """Error response to a enumeration management command."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT


class EnumManagementErrorV2(smperr.ErrorV2[ENUM_MGMT_ERR], frozen=True):
    """Error response to a enumeration management command."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT


class _EnumGroupBase:
    _ErrorV1 = EnumManagementErrorV1
    _ErrorV2 = EnumManagementErrorV2


class GroupCountResponse(smpmsg.ReadResponse, frozen=True):
    """SMP group count response."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.EnumManagement.GROUP_COUNT

    count: int
    """Contains the total number of supported SMP groups on the device."""


class GroupCountRequest(smpmsg.ReadRequest, _EnumGroupBase, frozen=True):
    """Read the number of SMP server groups.

    Count of supported groups returns the total number of SMP command groups
    that a device supports.
    """

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.EnumManagement.GROUP_COUNT
    _Response = GroupCountResponse


class ListOfGroupsResponse(smpmsg.ReadResponse, frozen=True):
    """SMP group list response."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.EnumManagement.LIST_OF_GROUPS

    groups: tuple[smphdr.GroupId, ...]
    """Contains a list of the supported SMP group IDs on the device."""


class ListOfGroupsRequest(smpmsg.ReadRequest, _EnumGroupBase, frozen=True):
    """List the available SMP groups."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.EnumManagement.LIST_OF_GROUPS
    _Response = ListOfGroupsResponse


class GroupIdResponse(smpmsg.ReadResponse, frozen=True):
    """SMP group at index response."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.EnumManagement.GROUP_ID

    group: smphdr.GroupId
    """The Group ID at the requested index."""
    end: bool | None = None
    """Will be set to true if the listed group is the final supported group on
    the device, otherwise will be omitted.
    """


class GroupIdRequest(smpmsg.ReadRequest, _EnumGroupBase, frozen=True):
    """List a SMP group by index.

    Fetch single group ID command allows listing the group IDs of supported SMP
    groups on the device, one by one.
    """

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.EnumManagement.GROUP_ID
    _Response = GroupIdResponse

    index: int | None = None
    """Contains the (0-based) index of the group to return information on, can
    be omitted to return the first group's details.
"""


class GroupDetails(msgspec.Struct, frozen=True, omit_defaults=True, forbid_unknown_fields=True):
    """Group Details"""

    group: smphdr.GroupId
    """The group ID of the SMP command group."""
    name: str | None = None
    """The name of the SMP command group."""
    handlers: int | None = None
    """The number of handlers that the SMP command group supports."""


class GroupDetailsResponse(smpmsg.ReadResponse, frozen=True):
    """SMP group details response."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.EnumManagement.GROUP_DETAILS

    groups: tuple[GroupDetails, ...]
    """Contains a list of the requested SMP group details."""


class GroupDetailsRequest(smpmsg.ReadRequest, _EnumGroupBase, frozen=True):
    """Request the details of the supported SMP groups.

    Details on supported groups command allows fetching details on each
    supported SMP group, such as the name and number of handlers. A device can
    specify an allow list of groups to return details on or details on all
    groups can be returned.

    This command is optional, it can be enabled using
    `CONFIG_MCUMGR_GRP_ENUM_DETAILS`. The optional name and number of handlers
    can be enabled/disabled with `CONFIG_MCUMGR_GRP_ENUM_DETAILS_NAME` and
    `CONFIG_MCUMGR_GRP_ENUM_DETAILS_HANDLERS`.
    """

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.EnumManagement.GROUP_DETAILS
    _Response = GroupDetailsResponse

    groups: tuple[smphdr.GroupId, ...] | None = None
    """Contains a list of the SMP group IDs to fetch details on.

    If omitted, details on all supported groups will be returned.
    """
