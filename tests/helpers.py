from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Protocol, Type

import cbor2
from pydantic import BaseModel

import smp.header as smphdr
import smp.message as smpmsg


def make_assert_header(
    group_id: smphdr.GroupId | smphdr.UserGroupId,
    op: smphdr.OP,
    command_id: smphdr.AnyCommandId,
    length: int | None,
) -> Callable[[smpmsg.Frame], None]:
    """Return an `assert_header` function."""

    def f(
        f: smpmsg.Frame,
    ) -> None:
        h = f.header
        assert op == h.op
        assert smphdr.Version.V2 == h.version
        assert 0 == h.flags
        if length is not None:
            assert length == h.length
        else:
            assert 0 <= h.length <= 0xFFFF
        assert group_id == h.group_id
        assert 0 <= h.sequence <= 0xFF
        assert command_id == h.command_id

    return f


def _do_test(
    msg: Type[smpmsg.T],
    op: smphdr.OP,
    command_id: Any,
    data: Dict[str, Any],
    nested_model: Type[BaseModel] | None = None,
    group_id: smphdr.GroupId = None,  # type: ignore[assignment]
) -> smpmsg.T:
    cbor = cbor2.dumps(data, canonical=True)
    assert_header = make_assert_header(group_id, op, command_id, len(cbor))

    def _assert_common(r: smpmsg.SMPData) -> None:
        for k, v in data.items():
            actual = getattr(r, k)
            if type(v) is tuple and nested_model is not None:
                for v2, actual2 in zip(v, actual):
                    assert v2 == nested_model(**v2).model_dump()
            elif isinstance(v, dict) and nested_model is not None and isinstance(actual, dict):
                for subk, subv in v.items():
                    assert subv == actual[subk].model_dump()
            else:
                assert v == actual
        assert cbor == bytes(r)

    r = msg(**data)

    _assert_common(r)  # serialize
    f = msg.loads(bytes(r.to_frame()))
    assert_header(f)
    _assert_common(f.smp_data)  # deserialize

    return r


class DoTestProtocol(Protocol):
    def __call__(
        self,
        msg: Type[smpmsg.T],
        op: smphdr.OP,
        command_id: Any,
        data: Dict[str, Any],
        nested_model: Optional[Type[BaseModel]] = ...,
    ) -> smpmsg.T:
        ...


def make_do_test(
    group_id: smphdr.GroupId,
) -> DoTestProtocol:
    """Return a `_do_test` function with a fixed `group_id`."""

    def do_test(
        msg: Type[smpmsg.T],
        op: smphdr.OP,
        command_id: Any,
        data: Dict[str, Any],
        nested_model: Optional[Type[BaseModel]] = None,
    ) -> smpmsg.T:
        return _do_test(
            msg,
            op,
            command_id,
            data,
            nested_model=nested_model,
            group_id=group_id,
        )

    return do_test
