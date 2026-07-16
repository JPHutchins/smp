"""Test the SMP Enumeration Management group."""

from __future__ import annotations

from functools import partial

import msgspec
import pytest

from smp import enumeration_management as smpenum
from smp import header as smphdr
from tests.helpers import assert_frame

enumcmd = smphdr.CommandId.EnumManagement

make_header = partial(
    smphdr.Header,
    op=smphdr.OP.READ_RSP,
    version=smphdr.Version.V2,
    flags=smphdr.Flag(0),
    length=0,
    group_id=smphdr.GroupId.ENUM_MANAGEMENT,
    sequence=0,
    command_id=enumcmd.LIST_OF_GROUPS,
)


def test_GroupCountRequest() -> None:
    assert_frame(
        smpenum.GroupCountRequest(),
        op=smphdr.OP.READ,
        group_id=smphdr.GroupId.ENUM_MANAGEMENT,
        command_id=enumcmd.GROUP_COUNT,
        length=1,
    )


def test_GroupCountResponse() -> None:
    frame = assert_frame(
        smpenum.GroupCountResponse(count=2),
        op=smphdr.OP.READ_RSP,
        group_id=smphdr.GroupId.ENUM_MANAGEMENT,
        command_id=enumcmd.GROUP_COUNT,
    )
    assert frame.data.count == 2


def test_ListOfGroupsRequest() -> None:
    assert_frame(
        smpenum.ListOfGroupsRequest(),
        op=smphdr.OP.READ,
        group_id=smphdr.GroupId.ENUM_MANAGEMENT,
        command_id=enumcmd.LIST_OF_GROUPS,
        length=1,
    )


def test_ListOfGroupsResponse() -> None:
    frame = assert_frame(
        smpenum.ListOfGroupsResponse(groups=(2, smphdr.GroupId.RUNTIME_TESTS, 15, 64)),
        op=smphdr.OP.READ_RSP,
        group_id=smphdr.GroupId.ENUM_MANAGEMENT,
        command_id=enumcmd.LIST_OF_GROUPS,
    )
    groups = frame.data.groups
    assert groups == (2, 5, 15, 64)

    assert type(groups[0]) is smphdr.GroupId
    assert groups[0] == smphdr.GroupId.STATISTICS_MANAGEMENT
    assert type(groups[1]) is smphdr.GroupId
    assert groups[1] == smphdr.GroupId.RUNTIME_TESTS
    assert type(groups[2]) is int
    assert groups[2] == 15
    assert type(groups[3]) is smphdr.UserGroupId
    assert groups[3] == smphdr.UserGroupId.INTERCREATE


@pytest.mark.parametrize("index", [0, 1, None])
def test_GroupIdRequest(index: int | None) -> None:
    assert_frame(
        smpenum.GroupIdRequest(index=index),
        op=smphdr.OP.READ,
        group_id=smphdr.GroupId.ENUM_MANAGEMENT,
        command_id=enumcmd.GROUP_ID,
    )


def test_GroupIdResponse() -> None:
    frame = assert_frame(
        smpenum.GroupIdResponse(group=2),
        op=smphdr.OP.READ_RSP,
        group_id=smphdr.GroupId.ENUM_MANAGEMENT,
        command_id=enumcmd.GROUP_ID,
    )
    assert frame.data.group == smphdr.GroupId.STATISTICS_MANAGEMENT
    assert type(frame.data.group) is smphdr.GroupId
    assert not frame.data.end


def test_GroupDetailsRequest() -> None:
    assert_frame(
        smpenum.GroupDetailsRequest(
            groups=(smphdr.GroupId.STATISTICS_MANAGEMENT, smphdr.GroupId.RUNTIME_TESTS, 15)
        ),
        op=smphdr.OP.READ,
        group_id=smphdr.GroupId.ENUM_MANAGEMENT,
        command_id=enumcmd.GROUP_DETAILS,
    )
    assert_frame(
        smpenum.GroupDetailsRequest(),
        op=smphdr.OP.READ,
        group_id=smphdr.GroupId.ENUM_MANAGEMENT,
        command_id=enumcmd.GROUP_DETAILS,
        length=1,
    )


def test_GroupDetailsResponse() -> None:
    frame = assert_frame(
        smpenum.GroupDetailsResponse(
            groups=(
                smpenum.GroupDetails(group=2, name="group2", handlers=2),
                smpenum.GroupDetails(group=5, name="group5", handlers=5),
                smpenum.GroupDetails(group=15, name="group15", handlers=15),
                smpenum.GroupDetails(group=64, name="group64", handlers=64),
            )
        ),
        op=smphdr.OP.READ_RSP,
        group_id=smphdr.GroupId.ENUM_MANAGEMENT,
        command_id=enumcmd.GROUP_DETAILS,
    )
    groups = frame.data.groups
    assert groups == (
        smpenum.GroupDetails(group=2, name="group2", handlers=2),
        smpenum.GroupDetails(group=5, name="group5", handlers=5),
        smpenum.GroupDetails(group=15, name="group15", handlers=15),
        smpenum.GroupDetails(group=64, name="group64", handlers=64),
    )
    assert type(groups[0].group) is smphdr.GroupId
    assert type(groups[1].group) is smphdr.GroupId
    assert type(groups[2].group) is int
    assert type(groups[3].group) is smphdr.UserGroupId


def test_ListOfGroupsResponse_rejects_missing_groups() -> None:
    with pytest.raises(msgspec.ValidationError):
        smpenum.ListOfGroupsResponse.load(make_header(command_id=enumcmd.LIST_OF_GROUPS), {})


def test_GroupIdResponse_rejects_missing_group() -> None:
    with pytest.raises(msgspec.ValidationError):
        smpenum.GroupIdResponse.load(make_header(command_id=enumcmd.GROUP_ID), {"end": True})


def test_GroupIdResponse_rejects_unknown_field() -> None:
    with pytest.raises(msgspec.ValidationError):
        smpenum.GroupIdResponse.load(
            make_header(command_id=enumcmd.GROUP_ID), {"group": 2, "bogus": 1}
        )


def test_GroupDetailsResponse_rejects_missing_group_in_element() -> None:
    with pytest.raises(msgspec.ValidationError):
        smpenum.GroupDetailsResponse.load(
            make_header(command_id=enumcmd.GROUP_DETAILS), {"groups": [{"name": "x"}]}
        )
