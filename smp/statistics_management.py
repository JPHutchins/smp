"""The Simple Management Protocol (SMP) Statistics Management group."""


from enum import IntEnum, unique
from typing import Dict, Tuple

import smp.error as smperr
import smp.header as smphdr
import smp.message as smpmsg


class GroupDataRequest(smpmsg.ReadRequest):
    _GROUP_ID = smphdr.GroupId.STATISTICS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.StatisticsManagement.GROUP_DATA

    name: str


class GroupDataResponse(smpmsg.ReadResponse):
    _GROUP_ID = smphdr.GroupId.STATISTICS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.StatisticsManagement.GROUP_DATA

    name: str
    fields: Dict[str, int]


class ListOfGroupsRequest(smpmsg.ReadRequest):
    _GROUP_ID = smphdr.GroupId.STATISTICS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.StatisticsManagement.LIST_OF_GROUPS


class ListOfGroupsResponse(smpmsg.ReadResponse):
    _GROUP_ID = smphdr.GroupId.STATISTICS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.StatisticsManagement.LIST_OF_GROUPS

    stat_list: Tuple[str, ...]


@unique
class STAT_MGMT_ERR(IntEnum):
    OK = 0
    """No error, this is implied if there is no ret value in the response."""

    UNKNOWN = 1
    """Unknown error occurred."""

    ERR_INVALID_GROUP = 2
    """The provided statistic group name was not found."""

    ERR_INVALID_STAT_NAME = 3
    """The provided statistic name was not found."""

    ERR_INVALID_STAT_SIZE = 4
    """The size of the statistic cannot be handled."""

    ERR_WALK_ABORTED = 5
    """Walk through of statistics was aborted."""


class StatisticsManagementErrorV1(smperr.ErrorV1):
    _GROUP_ID = smphdr.GroupId.STATISTICS_MANAGEMENT


class StatisticsManagementErrorV2(smperr.ErrorV2[STAT_MGMT_ERR]):
    _GROUP_ID = smphdr.GroupId.STATISTICS_MANAGEMENT
