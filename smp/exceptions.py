"""Simple Management Protocol (SMP) runtime Python `Exception`s."""


class SMPException(Exception):
    """Common base class for all `smp` module exceptions."""


class SMPDecodeError(SMPException):
    """Common base class for `smp` `decode` exceptions."""


class SMPBadStartDelimiter(SMPDecodeError):
    """The packet begins an SMP frame but does not have the SMP start delimiter."""


class SMPBadContinueDelimiter(SMPDecodeError):
    """The packet continues an SMP frame but does not have the SMP continue delimiter."""


class SMPBadCRC(SMPDecodeError):
    """The decoded frame failed CRC."""


class SMPDeserializationError(SMPException):
    """Common base class for `smp` deserialization exceptions."""


class SMPMismatchedGroupId(SMPDeserializationError):
    """The deserialized `GroupId` does not match the `GroupId` of the type."""
