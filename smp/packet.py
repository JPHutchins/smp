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


def encode(request: bytes, line_length: int = 8192) -> Generator[bytes, None, None]:
    """Iteratively pack an SMP bytes to packets of `line_length` size."""

    logger.debug(f"Serializing {request=}")

    crc16 = CRC16_STRUCT.pack(crc16_func(request))
    frame_length = FRAME_LENGTH_STRUCT.pack(len(request) + CRC16_STRUCT.size)

    total_size = FRAME_LENGTH_STRUCT.size + len(request) + CRC16_STRUCT.size
    logger.debug(f"Total size of request is {total_size}B")

    packet_size = ((line_length - LINE_LENGTH_SUBTRACTOR) // 4) * 4

    complete_b64 = b64encode(frame_length + request + crc16)
    logger.debug(f"Total size of b64 encoded request is {len(complete_b64)}B")

    # send the start delimiter, as many bytes as possible, and newline
    yield SIXTY_NINE + complete_b64[:packet_size] + CR

    remaining = complete_b64[packet_size:]

    while len(remaining) > 0:
        # send the continue delimiter, as many bytes as possible, and newline
        yield FOUR_TWENTY + remaining[:packet_size] + CR
        remaining = remaining[packet_size:]


def decode() -> Generator[None, bytes, bytes]:
    """Iteratively unpack a series of SMP packets to bytes."""

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
