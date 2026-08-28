"""Test the SMP Statistics Management group."""

from __future__ import annotations

from smp import header as smphdr
from smp import statistics_management as smpstat
from tests.helpers import assert_frame

statcmd = smphdr.CommandId.StatisticsManagement


def test_GroupDataRequest() -> None:
    frame = assert_frame(
        smpstat.GroupDataRequest(name="example"),
        op=smphdr.OP.READ,
        group_id=smphdr.GroupId.STATISTICS_MANAGEMENT,
        command_id=statcmd.GROUP_DATA,
    )
    assert frame.data.name == "example"


def test_GroupDataResponse() -> None:
    frame = assert_frame(
        smpstat.GroupDataResponse(name="example", fields={"field1": 1, "field2": 2}),
        op=smphdr.OP.READ_RSP,
        group_id=smphdr.GroupId.STATISTICS_MANAGEMENT,
        command_id=statcmd.GROUP_DATA,
    )
    assert frame.data.name == "example"
    assert frame.data.fields == {"field1": 1, "field2": 2}


def test_ListOfGroupsRequest() -> None:
    assert_frame(
        smpstat.ListOfGroupsRequest(),
        op=smphdr.OP.READ,
        group_id=smphdr.GroupId.STATISTICS_MANAGEMENT,
        command_id=statcmd.LIST_OF_GROUPS,
    )


def test_ListOfGroupsResponse() -> None:
    frame = assert_frame(
        smpstat.ListOfGroupsResponse(stat_list=("example1", "example2")),
        op=smphdr.OP.READ_RSP,
        group_id=smphdr.GroupId.STATISTICS_MANAGEMENT,
        command_id=statcmd.LIST_OF_GROUPS,
    )
    assert frame.data.stat_list == ("example1", "example2")
