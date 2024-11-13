"""Test the SMP Enumeration Management group."""

from __future__ import annotations

from typing import Any, Dict, Type, TypeVar

import cbor2
import pytest
from pydantic import BaseModel

from smp import enumeration_management as smpenum
from smp import header as smphdr
from smp import message as smpmsg
from tests.helpers import make_assert_header

T = TypeVar("T", bound=smpmsg._MessageBase)


def _do_test(
    msg: Type[T],
    op: smphdr.OP,
    command_id: smphdr.CommandId.EnumManagement,
    data: Dict[str, Any],
    nested_model: Type[BaseModel] | None = None,
) -> T:
    cbor = cbor2.dumps(data, canonical=True)
    assert_header = make_assert_header(smphdr.GroupId.ENUM_MANAGEMENT, op, command_id, len(cbor))

    def _assert_common(r: smpmsg._MessageBase) -> None:
        assert_header(r)
        for k, v in data.items():
            if type(v) is tuple and nested_model is not None:
                for v2 in v:
                    assert v2 == nested_model(**v2).model_dump()
            else:
                assert v == getattr(r, k)
        assert cbor == r.BYTES[8:]

    r = msg(**data)

    _assert_common(r)  # serialize
    _assert_common(msg.loads(r.BYTES))  # deserialize

    return r


def test_GroupCountRequest() -> None:
    _do_test(
        smpenum.GroupCountRequest,
        smphdr.OP.READ,
        smphdr.CommandId.EnumManagement.GROUP_COUNT,
        {},
    )


def test_GroupCountResponse() -> None:
    r = _do_test(
        smpenum.GroupCountResponse,
        smphdr.OP.READ_RSP,
        smphdr.CommandId.EnumManagement.GROUP_COUNT,
        {"count": 2},
    )
    assert r.count == 2


def test_ListOfGroupsRequest() -> None:
    _do_test(
        smpenum.ListOfGroupsRequest,
        smphdr.OP.READ,
        smphdr.CommandId.EnumManagement.LIST_OF_GROUPS,
        {},
    )


def test_ListOfGroupsResponse() -> None:
    r = _do_test(
        smpenum.ListOfGroupsResponse,
        smphdr.OP.READ_RSP,
        smphdr.CommandId.EnumManagement.LIST_OF_GROUPS,
        {"groups": (2, smphdr.GroupId.RUNTIME_TESTS, 15, 64)},
    )
    assert r.groups == (2, 5, 15, 64)

    assert type(r.groups[0]) is smphdr.GroupId
    assert r.groups[0] == smphdr.GroupId.STATISTICS_MANAGEMENT

    assert type(r.groups[1]) is smphdr.GroupId
    assert r.groups[1] == smphdr.GroupId.RUNTIME_TESTS

    assert type(r.groups[2]) is int
    assert r.groups[2] == 15

    assert type(r.groups[3]) is smphdr.UserGroupId
    assert r.groups[3] == smphdr.UserGroupId.INTERCREATE


@pytest.mark.parametrize("index", [0, 1, None])
def test_GroupIdRequest(index: int | None) -> None:
    _do_test(
        smpenum.GroupIdRequest,
        smphdr.OP.READ,
        smphdr.CommandId.EnumManagement.GROUP_ID,
        {"index": index} if index is not None else {},
    )


def test_GroupIdResponse() -> None:
    r = _do_test(
        smpenum.GroupIdResponse,
        smphdr.OP.READ_RSP,
        smphdr.CommandId.EnumManagement.GROUP_ID,
        {"group": 2},
    )
    assert r.group == smphdr.GroupId.STATISTICS_MANAGEMENT
    assert type(r.group) is smphdr.GroupId
    assert not r.end


def test_GroupDetailsRequest() -> None:
    _do_test(
        smpenum.GroupDetailsRequest,
        smphdr.OP.READ,
        smphdr.CommandId.EnumManagement.GROUP_DETAILS,
        {"groups": (smphdr.GroupId.STATISTICS_MANAGEMENT, smphdr.GroupId.RUNTIME_TESTS, 15)},
    )


def test_GroupDetailsResponse() -> None:
    r = _do_test(
        smpenum.GroupDetailsResponse,
        smphdr.OP.READ_RSP,
        smphdr.CommandId.EnumManagement.GROUP_DETAILS,
        {
            "groups": (
                {"id": 2, "name": "group2", "handlers": 2},
                {"id": 5, "name": "group5", "handlers": 5},
                {"id": 15, "name": "group15", "handlers": 15},
                {"id": 64, "name": "group64", "handlers": 64},
            )
        },
        nested_model=smpenum.GroupDetails,
    )
    assert r.groups == (
        smpenum.GroupDetails(id=2, name="group2", handlers=2),
        smpenum.GroupDetails(id=5, name="group5", handlers=5),
        smpenum.GroupDetails(id=15, name="group15", handlers=15),
        smpenum.GroupDetails(id=64, name="group64", handlers=64),
    )
    assert type(r.groups[0].id) is smphdr.GroupId
    assert type(r.groups[1].id) is smphdr.GroupId
    assert type(r.groups[2].id) is int
    assert type(r.groups[3].id) is smphdr.UserGroupId
