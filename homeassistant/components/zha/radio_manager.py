"""Config flow for ZHA."""
from __future__ import annotations

import asyncio
import contextlib
import copy
import logging
import os
from typing import Any

import voluptuous as vol
from zigpy.application import ControllerApplication
import zigpy.backups
from zigpy.config import CONF_DEVICE, CONF_DEVICE_PATH
from zigpy.exceptions import NetworkNotFormed

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .core.const import (
    CONF_DATABASE,
    CONF_RADIO_TYPE,
    CONF_ZIGPY,
    DATA_ZHA,
    DATA_ZHA_CONFIG,
    DEFAULT_DATABASE_NAME,
    EZSP_OVERWRITE_EUI64,
    RadioType,
)

# Only the common radio types will be autoprobed, ordered by new device popularity.
# XBee takes too long to probe since it scans through all possible bauds and likely has
# very few users to begin with.
AUTOPROBE_RADIOS = (
    RadioType.ezsp,
    RadioType.znp,
    RadioType.deconz,
    RadioType.zigate,
)

CONNECT_DELAY_S = 1.0

MIGRATION_RETRIES = 10

HARDWARE_DISCOVERY_SCHEMA = vol.Schema(
    {
        vol.Required("name"): str,
        vol.Required("port"): dict,
        vol.Required("radio_type"): str,
    }
)

HARDWARE_MIGRATION_SCHEMA = vol.Schema(
    {
        vol.Required("new_discovery_info"): HARDWARE_DISCOVERY_SCHEMA,
        vol.Required("old_discovery_info"): HARDWARE_DISCOVERY_SCHEMA,
    }
)

_LOGGER = logging.getLogger(__name__)


def _allow_overwrite_ezsp_ieee(
    backup: zigpy.backups.NetworkBackup,
) -> zigpy.backups.NetworkBackup:
    """Return a new backup with the flag to allow overwriting the EZSP EUI64."""
    new_stack_specific = copy.deepcopy(backup.network_info.stack_specific)
    new_stack_specific.setdefault("ezsp", {})[EZSP_OVERWRITE_EUI64] = True

    return backup.replace(
        network_info=backup.network_info.replace(stack_specific=new_stack_specific)
    )


def _prevent_overwrite_ezsp_ieee(
    backup: zigpy.backups.NetworkBackup,
) -> zigpy.backups.NetworkBackup:
    """Return a new backup without the flag to allow overwriting the EZSP EUI64."""
    if "ezsp" not in backup.network_info.stack_specific:
        return backup

    new_stack_specific = copy.deepcopy(backup.network_info.stack_specific)
    new_stack_specific.setdefault("ezsp", {}).pop(EZSP_OVERWRITE_EUI64, None)

    return backup.replace(
        network_info=backup.network_info.replace(stack_specific=new_stack_specific)
    )


class ZhaRadioManager:
    """Helper class with radio related functionality."""

    hass: HomeAssistant

    def __init__(self) -> None:
        """Initialize ZhaRadioManager instance."""
        self.device_path: str | None = None
        self.device_settings: dict[str, Any] | None = None
        self.radio_type: RadioType | None = None
        self.current_settings: zigpy.backups.NetworkBackup | None = None
        self.backups: list[zigpy.backups.NetworkBackup] = []
        self.chosen_backup: zigpy.backups.NetworkBackup | None = None

    @contextlib.asynccontextmanager
    async def _connect_zigpy_app(self) -> ControllerApplication:
        """Connect to the radio with the current config and then clean up."""
        assert self.radio_type is not None

        config = self.hass.data.get(DATA_ZHA, {}).get(DATA_ZHA_CONFIG, {})
        app_config = config.get(CONF_ZIGPY, {}).copy()

        database_path = config.get(
            CONF_DATABASE,
            self.hass.config.path(DEFAULT_DATABASE_NAME),
        )

        # Don't create `zigbee.db` if it doesn't already exist
        if not await self.hass.async_add_executor_job(os.path.exists, database_path):
            database_path = None

        app_config[CONF_DATABASE] = database_path
        app_config[CONF_DEVICE] = self.device_settings
        app_config = self.radio_type.controller.SCHEMA(app_config)

        app = await self.radio_type.controller.new(
            app_config, auto_form=False, start_radio=False
        )

        try:
            await app.connect()
            yield app
        finally:
            await app.disconnect()
            await asyncio.sleep(CONNECT_DELAY_S)

    async def restore_backup(
        self, backup: zigpy.backups.NetworkBackup, **kwargs: Any
    ) -> None:
        """Restore the provided network backup, passing through kwargs."""
        if self.current_settings is not None and self.current_settings.supersedes(
            self.chosen_backup
        ):
            return

        async with self._connect_zigpy_app() as app:
            await app.backups.restore_backup(backup, **kwargs)

    def parse_radio_type(self, radio_type: str) -> RadioType:
        """Parse a radio type name, accounting for past aliases."""
        if radio_type == "efr32":
            return RadioType.ezsp

        return RadioType[radio_type]

    async def detect_radio_type(self) -> bool:
        """Probe all radio types on the current port."""
        for radio in AUTOPROBE_RADIOS:
            _LOGGER.debug("Attempting to probe radio type %s", radio)

            dev_config = radio.controller.SCHEMA_DEVICE(
                {CONF_DEVICE_PATH: self.device_path}
            )
            probe_result = await radio.controller.probe(dev_config)

            if not probe_result:
                continue

            # Radio library probing can succeed and return new device settings
            if isinstance(probe_result, dict):
                dev_config = probe_result

            self.radio_type = radio
            self.device_settings = dev_config

            return True

        return False

    async def async_load_network_settings(self, create_backup: bool = False) -> None:
        """Connect to the radio and load its current network settings."""
        async with self._connect_zigpy_app() as app:
            # Check if the stick has any settings and load them
            try:
                await app.load_network_info()
            except NetworkNotFormed:
                pass
            else:
                self.current_settings = zigpy.backups.NetworkBackup(
                    network_info=app.state.network_info,
                    node_info=app.state.node_info,
                )

                if create_backup:
                    await app.backups.create_backup()

            # The list of backups will always exist
            self.backups = app.backups.backups.copy()

    async def async_form_network(self) -> None:
        """Form a brand new network."""
        async with self._connect_zigpy_app() as app:
            await app.form_network()

    async def async_reset_adapter(self) -> None:
        """Reset the current adapter."""
        async with self._connect_zigpy_app() as app:
            await app.reset_network_info()

    async def async_restore_backup_step_1(self) -> bool:
        """Prepare restoring backup.

        Returns True if async_restore_backup_step_2 should be called.
        """
        assert self.chosen_backup is not None

        if self.radio_type != RadioType.ezsp:
            await self.restore_backup(self.chosen_backup)
            return False

        # We have no way to partially load network settings if no network is formed
        if self.current_settings is None:
            # Since we are going to be restoring the backup anyways, write it to the
            # radio without overwriting the IEEE but don't take a backup with these
            # temporary settings
            temp_backup = _prevent_overwrite_ezsp_ieee(self.chosen_backup)
            await self.restore_backup(temp_backup, create_new=False)
            await self.async_load_network_settings()

            assert self.current_settings is not None

        if (
            self.current_settings.node_info.ieee == self.chosen_backup.node_info.ieee
            or not self.current_settings.network_info.metadata["ezsp"][
                "can_write_custom_eui64"
            ]
        ):
            # No point in prompting the user if the backup doesn't have a new IEEE
            # address or if there is no way to overwrite the IEEE address a second time
            await self.restore_backup(self.chosen_backup)

            return False

        return True

    async def async_restore_backup_step_2(self, overwrite_ieee: bool) -> None:
        """Restore backup and optionally overwrite IEEE."""
        assert self.chosen_backup is not None

        backup = self.chosen_backup

        if overwrite_ieee:
            backup = _allow_overwrite_ezsp_ieee(backup)

        # If the user declined to overwrite the IEEE *and* we wrote the backup to
        # their empty radio above, restoring it again would be redundant.
        await self.restore_backup(backup)


class ZhaMigrationHelper:
    """Helper class for automatic migration."""

    def __init__(
        self, hass: HomeAssistant, config_entry: config_entries.ConfigEntry
    ) -> None:
        """Initialize MigrationHelper instance."""
        self._config_entry = config_entry
        self._hass = hass
        self._radio_mgr = ZhaRadioManager()
        self._radio_mgr.hass = hass

    async def async_prepare_yellow_migration(self, data: dict[str, Any]) -> bool:
        """Prepare ZHA migration."""
        migration_data = HARDWARE_MIGRATION_SCHEMA(data)

        name = migration_data["new_discovery_info"]["name"]
        new_radio_type = self._radio_mgr.parse_radio_type(
            migration_data["new_discovery_info"]["radio_type"]
        )
        old_radio_type = self._radio_mgr.parse_radio_type(
            migration_data["old_discovery_info"]["radio_type"]
        )

        new_device_settings = new_radio_type.controller.SCHEMA_DEVICE(
            migration_data["new_discovery_info"]["port"]
        )
        old_device_settings = old_radio_type.controller.SCHEMA_DEVICE(
            migration_data["old_discovery_info"]["port"]
        )

        if (
            self._config_entry.data[CONF_DEVICE][CONF_DEVICE_PATH]
            != old_device_settings[CONF_DEVICE_PATH]
        ):
            # ZHA is using another radio, do nothing
            return False

        try:
            await self._hass.config_entries.async_unload(self._config_entry.entry_id)
        except config_entries.OperationNotAllowed:
            # ZHA is not running
            pass

        # Load our current network settings
        await self._radio_mgr.async_load_network_settings(create_backup=True)
        self._radio_mgr.chosen_backup = self._radio_mgr.backups[0]

        self._radio_mgr.radio_type = new_radio_type
        self._radio_mgr.device_path = new_device_settings[CONF_DEVICE_PATH]
        self._radio_mgr.device_settings = new_device_settings
        device_settings = self._radio_mgr.device_settings.copy()  # type: ignore[union-attr]

        # Update the config entry settings
        self._hass.config_entries.async_update_entry(
            entry=self._config_entry,
            data={
                CONF_DEVICE: device_settings,
                CONF_RADIO_TYPE: self._radio_mgr.radio_type.name,
            },
            options=self._config_entry.options,
            title=name,
        )
        return True

    async def async_finish_yellow_migration(self) -> bool:
        """Finish ZHA migration."""
        # Restore the backup, permanently overwriting the device IEEE address
        for retry in range(MIGRATION_RETRIES):
            try:
                if await self._radio_mgr.async_restore_backup_step_1():
                    await self._radio_mgr.async_restore_backup_step_2(True)
                _LOGGER.debug("Restored backup after %s retries", retry)
                return True
            except OSError as err:
                _LOGGER.debug(
                    "Failed to restore backup %s, retrying in %s seconds",
                    err,
                    CONNECT_DELAY_S,
                )

            await asyncio.sleep(CONNECT_DELAY_S)

        return False
