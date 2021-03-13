"""Support for Verisure locks."""
from __future__ import annotations

import asyncio
from typing import Callable

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_CODE, STATE_LOCKED, STATE_UNLOCKED
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_LOCK_CODE_DIGITS,
    CONF_LOCK_DEFAULT_CODE,
    DEFAULT_LOCK_CODE_DIGITS,
    DOMAIN,
    LOGGER,
)
from .coordinator import VerisureDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable[[list[VerisureDoorlock]], None],
) -> None:
    """Set up Verisure alarm control panel from a config entry."""
    coordinator: VerisureDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            VerisureDoorlock(coordinator, serial_number)
            for serial_number in coordinator.data["locks"]
        ]
    )


class VerisureDoorlock(CoordinatorEntity, LockEntity):
    """Representation of a Verisure doorlock."""

    coordinator: VerisureDataUpdateCoordinator

    def __init__(
        self, coordinator: VerisureDataUpdateCoordinator, serial_number: str
    ) -> None:
        """Initialize the Verisure lock."""
        super().__init__(coordinator)
        self.serial_number = serial_number
        self._state = None
        self._digits = coordinator.entry.options.get(
            CONF_LOCK_CODE_DIGITS, DEFAULT_LOCK_CODE_DIGITS
        )
        self._default_lock_code = coordinator.entry.options.get(CONF_LOCK_DEFAULT_CODE)

    @property
    def name(self) -> str:
        """Return the name of the lock."""
        return self.coordinator.data["locks"][self.serial_number]["area"]

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available and self.serial_number in self.coordinator.data["locks"]
        )

    @property
    def changed_by(self) -> str | None:
        """Last change triggered by."""
        return self.coordinator.data["locks"][self.serial_number].get("userString")

    @property
    def code_format(self) -> str:
        """Return the required six digit code."""
        return "^\\d{%s}$" % self._digits

    @property
    def is_locked(self) -> bool:
        """Return true if lock is locked."""
        return (
            self.coordinator.data["locks"][self.serial_number]["lockedState"]
            == "LOCKED"
        )

    async def async_unlock(self, **kwargs) -> None:
        """Send unlock command."""
        code = kwargs.get(ATTR_CODE, self._default_lock_code)
        if code is None:
            LOGGER.error("Code required but none provided")
            return

        await self.async_set_lock_state(code, STATE_UNLOCKED)

    async def async_lock(self, **kwargs) -> None:
        """Send lock command."""
        code = kwargs.get(ATTR_CODE, self._default_lock_code)
        if code is None:
            LOGGER.error("Code required but none provided")
            return

        await self.async_set_lock_state(code, STATE_LOCKED)

    async def async_set_lock_state(self, code: str, state: str) -> None:
        """Send set lock state command."""
        target_state = "lock" if state == STATE_LOCKED else "unlock"
        lock_state = await self.hass.async_add_executor_job(
            self.coordinator.verisure.set_lock_state,
            code,
            self.serial_number,
            target_state,
        )

        LOGGER.debug("Verisure doorlock %s", state)
        transaction = {}
        attempts = 0
        while "result" not in transaction:
            transaction = await self.hass.async_add_executor_job(
                self.coordinator.verisure.get_lock_state_transaction,
                lock_state["doorLockStateChangeTransactionId"],
            )
            attempts += 1
            if attempts == 30:
                break
            if attempts > 1:
                await asyncio.sleep(0.5)
        if transaction["result"] == "OK":
            self._state = state
