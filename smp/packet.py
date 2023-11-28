"""Generators for encoding and decoding Simple Management Protocol (SMP) packets."""

import logging
import struct
from base64 import b64decode, b64encode
from typing import Final, Generator

from crcmod.predefined import mkPredefinedCrcFun  # type: ignore

from smp.exceptions import SMPBadContinueDelimiter, SMPBadCRC, SMPBadStartDelimiter

SIXTY_NINE: Final = struct.pack("!BB", 6, 9)
FOUR_TWENTY: Final = struct.pack("!BB", 4, 20)
DELIMITER_SIZE: Final = len(SIXTY_NINE)
assert len(SIXTY_NINE) == len(FOUR_TWENTY) and len(FOUR_TWENTY) == DELIMITER_SIZE
CR: Final = b"\n"
LINE_LENGTH_SUBTRACTOR: Final = 4  # you'd think it's 3, len(delimiter) + len(CR)
FRAME_LENGTH_STRUCT: Final = struct.Struct("!H")
CRC16_STRUCT: Final = struct.Struct("!H")

crc16_func: Final = mkPredefinedCrcFun("xmodem")


logger: Final = logging.getLogger(__name__)


def encode(smp_bytes: bytes, mtu: int = 128) -> Generator[bytes, None, None]:
    """Iteratively pack SMP bytes to packets of `mtu` size.

    `smp_bytes` is a serialized SMP `Request` or `Response`.

    `mtu` should conform to the Maximum Transmission Unit requirements of the SMP server and
    transport.  128 is selected as a conservative default that matches legacy MCUMgr
    implementations.

    Typical usage example:
    ```python
    my_transport = SMPTransport()  # e.g. PySerial, bleak, etc.
    my_request = ImageStatesReadRequest()

    for packet in encode(bytes(my_request)):  # SMP messages implement __bytes__
        await my_transport.send(packet)
    ```
    """

    crc16 = CRC16_STRUCT.pack(crc16_func(smp_bytes))
    frame_length = FRAME_LENGTH_STRUCT.pack(len(smp_bytes) + CRC16_STRUCT.size)

    total_size = FRAME_LENGTH_STRUCT.size + len(smp_bytes) + CRC16_STRUCT.size
    logger.debug(f"Total size of smp_bytes is {total_size}B")

    packet_size = ((mtu - LINE_LENGTH_SUBTRACTOR) // 4) * 4

    complete_b64 = b64encode(frame_length + smp_bytes + crc16)
    logger.debug(f"Total size of b64 encoded request is {len(complete_b64)}B")

    # send the start delimiter, as many bytes as possible, and newline
    yield SIXTY_NINE + complete_b64[:packet_size] + CR

    remaining = complete_b64[packet_size:]

    while len(remaining) > 0:
        # send the continue delimiter, as many bytes as possible, and newline
        yield FOUR_TWENTY + remaining[:packet_size] + CR
        remaining = remaining[packet_size:]


def decode() -> Generator[None, bytes, bytes]:
    """Iteratively unpack a series of SMP packets to bytes.

    After creating an instance of this generator, it must be "primed" by calling `next` once:
    ```python
    decoder = decode()
    next(decoder)
    ```

    Typical usage example:
    ```python
    my_transport = SMPTransport()  # e.g. PySerial, bleak, etc.

    decoder = decode()
    next(decoder)

    while True:
        try:
            raw_bytes = await my_transport.receive()
            decoder.send(raw_bytes)  # send the bytes to the decoder
        except StopIteration as e:
            # when the decoder has constructed a complete frame, it raises `StopIteration`
            frame = e.value
            break

    # deserialize the decoded frame
    my_response = ImageStatesReadResponse.loads(frame)
    ```
    """

    packet = yield

    if packet[:DELIMITER_SIZE] != SIXTY_NINE:
        raise SMPBadStartDelimiter(f"Bad start delimiter {packet[:DELIMITER_SIZE].hex()}")

    length_and_frame = b64decode(packet[DELIMITER_SIZE : -len(CR)])
    frame_length = FRAME_LENGTH_STRUCT.unpack(length_and_frame[: FRAME_LENGTH_STRUCT.size])[0]
    logger.debug(f"Response {length_and_frame=}")

    frame = bytearray(length_and_frame[FRAME_LENGTH_STRUCT.size :])
    logger.debug(f"length of frame: {len(frame)}")
    while len(frame) < frame_length:
        packet = yield

        if packet[:DELIMITER_SIZE] != FOUR_TWENTY:
            raise SMPBadContinueDelimiter(f"Bad continue delimiter {packet[:DELIMITER_SIZE].hex()}")

        frame.extend(b64decode(packet[DELIMITER_SIZE : -len(CR)]))

    complete_frame = frame[: -CRC16_STRUCT.size]
    packet_crc16 = CRC16_STRUCT.unpack(frame[-CRC16_STRUCT.size :])[0]
    calculated_crc16 = crc16_func(complete_frame)

    if packet_crc16 != calculated_crc16:
        raise SMPBadCRC(f"Packet CRC {hex(packet_crc16)} != calculated CRC {hex(calculated_crc16)}")

    return complete_frame
