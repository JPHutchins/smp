"""Test the SMP Shell Management group."""

from __future__ import annotations

from smp import header as smphdr
from smp import statistics_management as smpstat
from tests.helpers import make_do_test

_do_test = make_do_test(smphdr.GroupId.STATISTICS_MANAGEMENT)


def test_GroupDataRequest() -> None:
    r = _do_test(
        smpstat.GroupDataRequest,
        smphdr.OP.READ,
        smphdr.CommandId.StatisticsManagement.GROUP_DATA,
        {"name": "example"},
    )
    assert r.name == "example"


def test_GroupDataResponse() -> None:
    r = _do_test(
        smpstat.GroupDataResponse,
        smphdr.OP.READ_RSP,
        smphdr.CommandId.StatisticsManagement.GROUP_DATA,
        {"name": "example", "fields": {"field1": 1, "field2": 2}},
    )
    assert r.name == "example"
    assert r.fields == {"field1": 1, "field2": 2}


def test_ListOfGroupsRequest() -> None:
    _do_test(
        smpstat.ListOfGroupsRequest,
        smphdr.OP.READ,
        smphdr.CommandId.StatisticsManagement.LIST_OF_GROUPS,
        {},
    )


def test_ListOfGroupsResponse() -> None:
    r = _do_test(
        smpstat.ListOfGroupsResponse,
        smphdr.OP.READ_RSP,
        smphdr.CommandId.StatisticsManagement.LIST_OF_GROUPS,
        {"stat_list": ("example1", "example2")},
    )
    assert r.stat_list == ("example1", "example2")
