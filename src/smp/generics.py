"""Generics and type narrowing for SMP requests and their responses.

An `SMPRequest` binds a `Request` to the `Response`, `ErrorV1`, and `ErrorV2`
it may provoke, so that a request/response round trip is exhaustively typed:

```python
response = client.request(SomeRequest())
if success(response):
    ...  # narrowed to the request's Response
elif error_v1(response):
    ...  # narrowed to the request's ErrorV1
elif error_v2(response):
    ...  # narrowed to the request's ErrorV2
else:
    assert_never(response)
```
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeVar

from smp import message as smpmessage

if TYPE_CHECKING:
    from typing_extensions import TypeIs

    from smp import error as smperror

TRep = TypeVar("TRep", bound="smpmessage.ReadResponse | smpmessage.WriteResponse")
TEr1 = TypeVar("TEr1", bound="smperror.ErrorV1")
TEr2 = TypeVar("TEr2", bound="smperror.ErrorV2")

_TRep_co = TypeVar(
    "_TRep_co", bound="smpmessage.ReadResponse | smpmessage.WriteResponse", covariant=True
)
_TEr1_co = TypeVar("_TEr1_co", bound="smperror.ErrorV1", covariant=True)
_TEr2_co = TypeVar("_TEr2_co", bound="smperror.ErrorV2", covariant=True)


class SMPRequest(Protocol[_TRep_co, _TEr1_co, _TEr2_co]):
    """A `Request` bound to its expected `Response`, `ErrorV1`, and `ErrorV2`."""

    @property
    def _Response(self) -> type[_TRep_co]: ...
    @property
    def _ErrorV1(self) -> type[_TEr1_co]: ...
    @property
    def _ErrorV2(self) -> type[_TEr2_co]: ...
    def to_frame(self) -> smpmessage.Frame[Any]: ...


def success(
    response: smpmessage.Response,
) -> TypeIs[smpmessage.ReadResponse | smpmessage.WriteResponse]:
    return response.RESPONSE_TYPE == smpmessage.ResponseType.SUCCESS


def error_v1(response: smpmessage.Response) -> TypeIs[smperror.ErrorV1]:
    return response.RESPONSE_TYPE == smpmessage.ResponseType.ERROR_V1


def error_v2(response: smpmessage.Response) -> TypeIs[smperror.ErrorV2[Any]]:
    return response.RESPONSE_TYPE == smpmessage.ResponseType.ERROR_V2


def error(response: smpmessage.Response) -> TypeIs[smperror.ErrorV1 | smperror.ErrorV2[Any]]:
    return error_v1(response) or error_v2(response)
