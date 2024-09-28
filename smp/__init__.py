# flake8: noqa

"""The Simple Management Protocol (SMP) for remotely managing MCU firmware.

This package implements de/serialization of SMP messages allowing for their use
on the transport of your choice.

The SMP specification can be found [here](https://docs.zephyrproject.org/latest/services/device_mgmt/smp_protocol.html).

## Usage

SMP messages are represented as Pydantic models.  Each SMP Request and
Response contains a `header` attribute that is an instance of
`smp.header.Header`.  Other attributes are specific to the message type.

For example, to create a `smp.os_management.EchoWriteRequest`:

```python
from smp.os_management import EchoWriteRequest

request = EchoWriteRequest(d="Hello world!")
print(bytes(request))
```

Prints the serialized SMP Frame:
```python
b'\\n\\x00\\x00\\x10\\x00\\x00\\x00\\x00\\xa1adlHello world!'
```

All messages can be deserialized and validated using the `loads()` method.  To 
load a `smp.os_management.EchoWriteResponse`:

```python
from smp.os_management import EchoWriteResponse

data = bytes.fromhex("0b00000700008c00a1617263486921")  # data from the transport
response = EchoWriteResponse.loads(data)
print(response)
```

Prints the deserialized SMP message representation:
```
header=Header(op=<OP.WRITE_RSP: 3>, version=<Version.V2: 1>, flags=<Flag: 0>,
length=7, group_id=0, sequence=140, command_id=0) version=<Version.V2: 1>
sequence=140 smp_data=b'\\x0b\\x00\\x00\\x07\\x00\\x00\\x8c\\x00\\xa1arcHi!' r='Hi!'
```
Generally, the `header` can be ignored and the message-specific attributes are
what you are interested in.
```
# print(response.r)
Hi!
```
All models and their attributes are statically typed and validated; enforced by
mypy linting and by Pydantic at runtime.

## Serialization

There are a few optional arguments that are common to all SMP messages when they
are created.

-   `header` is the SMP header.  Typically this can be left as `None` and will be
    so that the header is created automatically.
-   `version` is the SMP version.  This defaults to `smp.header.Version.V2`.
-   `sequence` is the sequence number of the message.  If not provided, it will
    be automatically generated using an incrementing counter.

Take a look at `smp.message` for more information on the base classes.

## Deserialization

If you are writing an SMP client, then you already know the type of the
incoming message because it must be a Response to your Request, or an
`smp.error.ErrorV1` or `smp.error.ErrorV2`.  You can use the
`smp.message._MessageBase.loads()` method that is common to all SMP
messages to deserialize and validate the message.

If you are writing an SMP server, then Python and SMP are odd choices!  Yet, you
can narrow the type by first loading the header with `smp.header.Header.loads()`.

## Encoding & Decoding

The USB and serial transports defined by Zephyr use a base64 encoding and
framing.  The encoding/fragmentation and decoding/reassembly is provided by 
`smp.packet.encode()` and `smp.packet.decode()`.

More information is at the [Zephyr docs](https://docs.zephyrproject.org/latest/services/device_mgmt/smp_transport.html#uart-serial-and-console)

## Typing

This package is meticulously typed and is intended to be used with mypy.

## Validation

All models are validated in order to detect transport and SMP server errors.  It
is impossible to create an invalid SMP message or deserialize an invalid SMP
message.  If you find a way, please open an issue.
"""
