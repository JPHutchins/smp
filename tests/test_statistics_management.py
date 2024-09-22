"""Test the SMP Shell Management group."""

from __future__ import annotations

from typing import Any, Dict, Type, TypeVar

import cbor2

from smp import header as smphdr
from smp import message as smpmsg
from smp import statistics_management as smpstat
from tests.helpers import make_assert_header

T = TypeVar("T", bound=smpmsg._MessageBase)


def _do_test(
    msg: Type[T],
    op: smphdr.OP,
    command_id: smphdr.CommandId.StatisticsManagement,
    data: Dict[str, Any],
) -> T:
    cbor = cbor2.dumps(data, canonical=True)
    assert_header = make_assert_header(
        smphdr.GroupId.STATISTICS_MANAGEMENT, op, command_id, len(cbor)
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
