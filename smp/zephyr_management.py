"""The Simple Management Protocol (SMP) Zephyr Management group."""


from enum import IntEnum, unique

import smp.error as smperr
import smp.header as smphdr
import smp.message as smpmsg


class EraseStorageRequest(smpmsg.WriteRequest):
    """Erase the storage area."""

    _GROUP_ID = smphdr.GroupId.ZEPHYR_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.ZephyrManagement.ERASE_STORAGE


class EraseStorageResponse(smpmsg.WriteResponse):
    """Success response to a storage area erase."""

    _GROUP_ID = smphdr.GroupId.ZEPHYR_MANAGEMENT
    _COMMAND_ID = smphdr.CommandId.ZephyrManagement.ERASE_STORAGE


@unique
class ZEPHYRBASIC_MGMT_ERR(IntEnum):
    """Return codes for the Zephyr Management group."""

    OK = 0
    """No error, this is implied if there is no ret value in the response"""

    UNKNOWN = 1
    """Unknown error occurred."""

    FLASH_OPEN_FAILED = 2
    """Opening of the flash area has failed."""

    FLASH_CONFIG_QUERY_FAIL = 3
    """Querying the flash area parameters has failed."""

    FLASH_ERASE_FAILED = 4
    """Erasing the flash area has failed."""


class ZephyrManagementErrorV1(smperr.ErrorV1):
    """Error response to a Zephyr Management command."""

    _GROUP_ID = smphdr.GroupId.ZEPHYR_MANAGEMENT


class ZephyrManagementErrorV2(smperr.ErrorV2[ZEPHYRBASIC_MGMT_ERR]):
    """Error response to a Zephyr Management command."""

    _GROUP_ID = smphdr.GroupId.ZEPHYR_MANAGEMENT
