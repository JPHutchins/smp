"""The Simple Management Protocol (SMP) Enumeration Management group."""

from __future__ import annotations

from enum import IntEnum, unique
from typing import Tuple, Union

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Annotated

import smp.error as smperr
import smp.header as smphdr
import smp.message as smpmsg

# We can't 'or' types until a later python
GroupIdField = Annotated[
    Union[smphdr.GroupId, smphdr.UserGroupId, int], Field(union_mode="left_to_right")
]


class GroupCountRequest(smpmsg.ReadRequest):
    """Read the number of SMP server groups."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.EnumManagement.GROUP_COUNT


class GroupCountResponse(smpmsg.ReadResponse):
    """SMP group count response."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.EnumManagement.GROUP_COUNT

    count: int


class ListOfGroupsRequest(smpmsg.ReadRequest):
    """List the available SMP groups."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.EnumManagement.LIST_OF_GROUPS


class ListOfGroupsResponse(smpmsg.ReadResponse):
    """SMP group list response."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.EnumManagement.LIST_OF_GROUPS

    groups: Tuple[GroupIdField, ...]


class GroupIdRequest(smpmsg.ReadRequest):
    """List a SMP group by index."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.EnumManagement.GROUP_ID

    index: int | None = None


class GroupIdResponse(smpmsg.ReadResponse):
    """SMP group at index response."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.EnumManagement.GROUP_ID

    group: GroupIdField
    end: bool | None = None


class GroupDetailsRequest(smpmsg.ReadRequest):
    """List a SMP group by index."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.EnumManagement.GROUP_DETAILS

    groups: Tuple[GroupIdField, ...]


class GroupDetails(BaseModel):
    """Group Details"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: GroupIdField
    name: str | None = None
    handlers: int | None = None


class GroupDetailsResponse(smpmsg.ReadResponse):
    """SMP group details response."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.EnumManagement.GROUP_DETAILS

    groups: Tuple[GroupDetails, ...]


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


class EnumManagementErrorV1(smperr.ErrorV1):
    """Error response to a enumeration management command."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT


class EnumManagementErrorV2(smperr.ErrorV2[ENUM_MGMT_ERR]):
    """Error response to a enumeration management command."""

    _GROUP_ID = smphdr.GroupId.ENUM_MANAGEMENT
