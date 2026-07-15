"""Simple Management Protocol (SMP) runtime Python `Exception`s."""


class SMPException(Exception):
    """Base class for SMP exceptions."""


class SMPDecodeError(SMPException):
    """An error occurred while decoding an SMP message."""


class SMPBadStartDelimiter(SMPDecodeError):
    """The start delimiter of the SMP message is invalid."""


class SMPBadContinueDelimiter(SMPDecodeError):
    """The continue delimiter of the SMP message is invalid."""


class SMPBadCRC(SMPDecodeError):
    """The CRC of the SMP message failed."""


class SMPDeserializationError(SMPException):
    """Failed to deserialize an SMP message."""


class SMPMismatchedGroupId(SMPDeserializationError):
    """Group ID in the SMP message does not match the expected group."""


class SMPMalformed(SMPException):
    """The SMP message is malformed."""
