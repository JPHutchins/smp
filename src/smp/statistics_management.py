"""The Simple Management Protocol (SMP) Statistics Management group."""

from enum import IntEnum, unique

import smp.error as smperr
import smp.header as smphdr
import smp.message as smpmsg


@unique
class STAT_MGMT_ERR(IntEnum):
    """Return codes for the statistics management group."""

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


class StatisticsManagementErrorV1(smperr.ErrorV1, frozen=True):
    """Error response to a statistics management command."""

    _GROUP_ID = smphdr.GroupId.STATISTICS_MANAGEMENT


class StatisticsManagementErrorV2(smperr.ErrorV2[STAT_MGMT_ERR], frozen=True):
    """Error response to a statistics management command."""

    _GROUP_ID = smphdr.GroupId.STATISTICS_MANAGEMENT


class _StatisticsGroupBase:
    _ErrorV1 = StatisticsManagementErrorV1
    _ErrorV2 = StatisticsManagementErrorV2


class GroupDataResponse(smpmsg.ReadResponse, frozen=True):
    """Statistics group data response."""

    _GROUP_ID = smphdr.GroupId.STATISTICS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.StatisticsManagement.GROUP_DATA

    name: str
    fields: dict[str, int]


class GroupDataRequest(smpmsg.ReadRequest, _StatisticsGroupBase, frozen=True):
    """Read the statistics group data."""

    _GROUP_ID = smphdr.GroupId.STATISTICS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.StatisticsManagement.GROUP_DATA
    _Response = GroupDataResponse

    name: str


class ListOfGroupsResponse(smpmsg.ReadResponse, frozen=True):
    """List of available statistics groups."""

    _GROUP_ID = smphdr.GroupId.STATISTICS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.StatisticsManagement.LIST_OF_GROUPS

    stat_list: tuple[str, ...]


class ListOfGroupsRequest(smpmsg.ReadRequest, _StatisticsGroupBase, frozen=True):
    """List the available statistics groups."""

    _GROUP_ID = smphdr.GroupId.STATISTICS_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.StatisticsManagement.LIST_OF_GROUPS
    _Response = ListOfGroupsResponse
