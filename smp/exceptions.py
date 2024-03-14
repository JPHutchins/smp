"""Simple Management Protocol (SMP) runtime Python `Exception`s."""


class SMPException(Exception):
    ...


class SMPDecodeError(SMPException):
    ...


class SMPBadStartDelimiter(SMPDecodeError):
    ...


class SMPBadContinueDelimiter(SMPDecodeError):
    ...


class SMPBadCRC(SMPDecodeError):
    ...


class SMPDeserializationError(SMPException):
    ...


class SMPMismatchedGroupId(SMPDeserializationError):
    ...


class SMPMalformed(SMPException):
    ...
