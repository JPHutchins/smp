"""Generators for encoding and decoding Simple Management Protocol (SMP) packets."""

import logging
import struct
from base64 import b64decode, b64encode
from typing import Final, Generator

from crcmod.predefined import mkPredefinedCrcFun  # type: ignore

from smp.exceptions import SMPBadContinueDelimiter, SMPBadCRC, SMPBadStartDelimiter

SIXTY_NINE: Final = struct.pack("!BB", 6, 9)
START_DELIMITER: Final = SIXTY_NINE
FOUR_TWENTY: Final = struct.pack("!BB", 4, 20)
CONTINUE_DELIMITER: Final = FOUR_TWENTY
DELIMITER_SIZE: Final = len(SIXTY_NINE)
assert len(SIXTY_NINE) == len(FOUR_TWENTY) and len(FOUR_TWENTY) == DELIMITER_SIZE
LF: Final = b"\n"
END_DELIMITER: Final = LF
LINE_LENGTH_SUBTRACTOR: Final = 4  # you'd think it's 3, len(delimiter) + len(CR)
FRAME_LENGTH_STRUCT: Final = struct.Struct("!H")
CRC16_STRUCT: Final = struct.Struct("!H")

crc16_func: Final = mkPredefinedCrcFun("xmodem")


logger: Final = logging.getLogger(__name__)


def encode(request: bytes, line_length: int = 8192) -> Generator[bytes, None, None]:
    """Iteratively pack an SMP bytes to packets of `line_length` size.

    Note: only the USB/serial transport uses this encoding and fragmentation.
    The BLE and UDP transports can simply send the SMP frames as they are.

    Params:
    - request: The bytes to be encoded.
    - line_length: The maximum length of each packet.

    Example:

    Encode arbitrary bytes to SMP packets:

    ```python
    from smp.packet import encode

    for packet in encode(b"Hello, world!"):
        print(packet)
    ```
    prints:
    ```
    b'\\x06\\tAA9IZWxsbywgd29ybGQhet4=\\n'
    ```

    Set a smaller packet size to fragment:

    ```python
    from smp.packet import encode

    for packet in encode(b"Hello, world!", line_length=8):
        print(packet)
    ```
    prints:
    ```
    b'\\x06\\tAA9I\\n'
    b'\\x04\\x14ZWxs\\n'
    b'\\x04\\x14bywg\\n'
    b'\\x04\\x14d29y\\n'
    b'\\x04\\x14bGQh\\n'
    b'\\x04\\x14et4=\\n'
    ```

    The packet size should be set according to the buffer sizes of the SMP
    server, and larger buffers will be more efficient.  It is not necessary to
    use multiple buffers.
    """

    logger.debug(f"Serializing {request=}")

    crc16 = CRC16_STRUCT.pack(crc16_func(request))
    frame_length = FRAME_LENGTH_STRUCT.pack(len(request) + CRC16_STRUCT.size)

    total_size = FRAME_LENGTH_STRUCT.size + len(request) + CRC16_STRUCT.size
    logger.debug(f"Total size of request is {total_size}B")

    packet_size = ((line_length - LINE_LENGTH_SUBTRACTOR) // 4) * 4

    complete_b64 = b64encode(frame_length + request + crc16)
    logger.debug(f"Total size of b64 encoded request is {len(complete_b64)}B")

    # send the start delimiter, as many bytes as possible, and newline
    yield START_DELIMITER + complete_b64[:packet_size] + END_DELIMITER

    remaining = complete_b64[packet_size:]

    while len(remaining) > 0:
        # send the continue delimiter, as many bytes as possible, and newline
        yield CONTINUE_DELIMITER + remaining[:packet_size] + END_DELIMITER
        remaining = remaining[packet_size:]


def decode() -> Generator[None, bytes, bytes]:
    """Iteratively unpack a series of SMP packets to SMP frame bytes.

    Example:

    ```python
    from smp.packet import decode
    from smp.image_management import ImageUploadWriteRequest

    # Example encoded SMP packets
    packets = (
        bytes.fromhex("06094148344b41414230414147610a"),
        bytes.fromhex("041441615a6a6247567544574e760a"),
        bytes.fromhex("04145a6d59594b6d4e7a6147464d0a"),
        bytes.fromhex("041464484a3163335167625755670a"),
        bytes.fromhex("0414596e4a765a475268644746590a"),
        bytes.fromhex("04145141414241674d45425159480a"),
        bytes.fromhex("041443416b4b4377774e446738510a"),
        bytes.fromhex("041445524954464255574678675a0a"),
        bytes.fromhex("04144768736348523466494345690a"),
        bytes.fromhex("04144979516c4a69636f4b536f720a"),
        bytes.fromhex("04144c4330754c7a41784d6a4d300a"),
        bytes.fromhex("04144e5459334f446b364f7a77390a"),
        bytes.fromhex("0414506a396c615731685a3255410a"),
        bytes.fromhex("04145a3356775a334a685a4758300a"),
        bytes.fromhex("04147134673d0a"),
    )

    decoder = decode()
    next(decoder)

    for packet in packets:
        try:
            decoder.send(packet)
        except StopIteration as e:
            frame = e.value
            break

    print(frame)
    print(ImageUploadWriteRequest.loads(frame))
    ```
    prints:
    ```
    bytearray(b'\\n\\x00\\x00t\\x00\\x01\\x9a\\x01\\xa6clen\\rcoff\\x18*cshaLtrust me broddataX@\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f\\x10\\x11\\x12\\x13\\x14\\x15\\x16\\x17\\x18\\x19\\x1a\\x1b\\x1c\\x1d\\x1e\\x1f !"#$%&\\'()*+,-./0123456789:;<=>?eimage\\x00gupgrade\\xf4')  # noqa: E501
    ```
    and
    ```
    header=Header(op=<OP.WRITE: 2>, version=<Version.V2: 1>, flags=<Flag: 0>,
    length=116, group_id=1, sequence=154, command_id=1) version=<Version.V2: 1>
    sequence=154 smp_data=b'\\n\\x00\\x00t\\x00\\x01\\x9a\\x01\\xa6clen\\rcoff\\x18*cshaL
    trust me broddataX@\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e
    \\x0f\\x10\\x11\\x12\\x13\\x14\\x15\\x16\\x17\\x18\\x19\\x1a\\x1b\\x1c\\x1d\\x1e\\x1f !"#$%&
    \\'()*+,-./0123456789:;<=>?eimage\\x00gupgrade\\xf4' off=42 data=b'\\x00\\x01\\x02
    \\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f\\x10\\x11\\x12\\x13\\x14\\x15\\x16
    \\x17\\x18\\x19\\x1a\\x1b\\x1c\\x1d\\x1e\\x1f !"#$%&\\'()*+,-./0123456789:;<=>?'
    image=0 len=13 sha=b'trust me bro' upgrade=False
    ```
    """

    packet = yield

    if packet[:DELIMITER_SIZE] != START_DELIMITER:
        raise SMPBadStartDelimiter(f"Bad start delimiter {packet[:DELIMITER_SIZE].hex()}")

    length_and_frame = b64decode(packet[DELIMITER_SIZE : -len(END_DELIMITER)])
    frame_length = FRAME_LENGTH_STRUCT.unpack(length_and_frame[: FRAME_LENGTH_STRUCT.size])[0]
    logger.debug(f"Response {length_and_frame=}")

    frame = bytearray(length_and_frame[FRAME_LENGTH_STRUCT.size :])
    logger.debug(f"length of frame: {len(frame)}")
    while len(frame) < frame_length:
        packet = yield

        if packet[:DELIMITER_SIZE] != CONTINUE_DELIMITER:
            raise SMPBadContinueDelimiter(f"Bad continue delimiter {packet[:DELIMITER_SIZE].hex()}")

        frame.extend(b64decode(packet[DELIMITER_SIZE : -len(END_DELIMITER)]))

    complete_frame = frame[: -CRC16_STRUCT.size]
    packet_crc16 = CRC16_STRUCT.unpack(frame[-CRC16_STRUCT.size :])[0]
    calculated_crc16 = crc16_func(complete_frame)

    if packet_crc16 != calculated_crc16:
        raise SMPBadCRC(f"Packet CRC {hex(packet_crc16)} != calculated CRC {hex(calculated_crc16)}")

    return complete_frame
