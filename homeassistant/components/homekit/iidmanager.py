"""
Manage allocation of instance ID's.

HomeKit needs to allocate unique numbers to each accessory. These need to
be stable between reboots and upgrades.

This module generates and stores them in a HA storage.
"""
from __future__ import annotations

from uuid import UUID

from pyhap.util import uuid_to_hap_type

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from .util import get_iid_storage_filename_for_entry_id

AID_MANAGER_STORAGE_VERSION = 1
AID_MANAGER_SAVE_DELAY = 2

ALLOCATIONS_KEY = "allocations"

IID_MIN = 1
IID_MAX = 18446744073709551615


class AccessoryIIDStorage:
    """
    Provide stable allocation of IIDs for the lifetime of an accessory.

    Will generate new ID's, ensure they are unique and store them to make sure they
    persist over reboots.
    """

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Create a new iid store."""
        self._hass = hass
        self._allocations: dict[str, int] = {}
        self._allocated_iids: list[int] = []
        self._entry_id = entry_id
        self._store: Store | None = None

    async def async_initialize(self) -> None:
        """Load the latest IID data."""
        iid_store = get_iid_storage_filename_for_entry_id(self._entry_id)
        self._store = Store(self._hass, AID_MANAGER_STORAGE_VERSION, iid_store)

        if not (raw_storage := await self._store.async_load()):
            # There is no data about iid allocations yet
            return

        assert isinstance(raw_storage, dict)
        self._allocations = raw_storage.get(ALLOCATIONS_KEY, {})
        self._allocated_iids = sorted(self._allocations.values())

    def get_or_allocate_iid(
        self,
        aid: int,
        service_uuid: UUID,
        char_uuid: UUID | None,
        unique_id: str | None,
    ) -> int:
        """Generate a stable iid."""
        service_hap_type: str = uuid_to_hap_type(service_uuid)
        char_hap_type: str | None = uuid_to_hap_type(char_uuid) if char_uuid else None
        # Allocation key must be a string since we are saving it to JSON
        allocation_key = (
            f'{aid}_{service_hap_type}_{char_hap_type or ""}_{unique_id or ""}'
        )
        if allocation_key in self._allocations:
            return self._allocations[allocation_key]
        next_iid = self._allocated_iids[-1] + 1 if self._allocated_iids else 1
        self._allocations[allocation_key] = next_iid
        self._allocated_iids.append(next_iid)
        self._async_schedule_save()
        return next_iid

    @callback
    def _async_schedule_save(self) -> None:
        """Schedule saving the iid allocations."""
        assert self._store is not None
        self._store.async_delay_save(self._data_to_save, AID_MANAGER_SAVE_DELAY)

    async def async_save(self) -> None:
        """Save the iid allocations."""
        assert self._store is not None
        return await self._store.async_save(self._data_to_save())

    @callback
    def _data_to_save(self) -> dict:
        """Return data of entity map to store in a file."""
        return {ALLOCATIONS_KEY: self._allocations}
