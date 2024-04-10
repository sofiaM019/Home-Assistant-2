"""Config flow for the Home Assistant SkyConnect integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from universal_silabs_flasher.const import ApplicationType

from homeassistant.components import usb
from homeassistant.components.hassio import (
    AddonError,
    AddonInfo,
    AddonManager,
    AddonState,
    is_hassio,
)
from homeassistant.components.homeassistant_hardware import silabs_multiprotocol_addon
from homeassistant.components.homeassistant_hardware.silabs_multiprotocol_addon import (
    WaitingAddonManager,
)
from homeassistant.components.zha import DOMAIN as ZHA_DOMAIN
from homeassistant.components.zha.repairs.wrong_silabs_firmware import (
    probe_silabs_firmware_type,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigEntryBaseFlow,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    OptionsFlowWithConfigEntry,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.helpers.singleton import singleton

from .const import DOMAIN, HardwareVariant
from .util import get_hardware_variant, get_usb_service_info

_LOGGER = logging.getLogger(__name__)

DATA_OTBR_ADDON_MANAGER = "openthread_border_router"
DATA_ZIGBEE_FLASHER_ADDON_MANAGER = "silabs_flasher"

OTBR_ADDON_SLUG = "core_openthread_border_router"
ZIGBEE_FLASHER_ADDON_SLUG = "core_silabs_flasher"

STEP_PICK_FIRMWARE_THREAD = "pick_firmware_thread"
STEP_PICK_FIRMWARE_ZIGBEE = "pick_firmware_zigbee"


@singleton(DATA_OTBR_ADDON_MANAGER)
@callback
def get_otbr_addon_manager(hass: HomeAssistant) -> WaitingAddonManager:
    """Get the OTBR add-on manager."""
    return WaitingAddonManager(
        hass,
        _LOGGER,
        "OpenThread Border Router",
        OTBR_ADDON_SLUG,
    )


@singleton(DATA_ZIGBEE_FLASHER_ADDON_MANAGER)
@callback
def get_zigbee_flasher_addon_manager(hass: HomeAssistant) -> WaitingAddonManager:
    """Get the flasher add-on manager."""
    return WaitingAddonManager(
        hass,
        _LOGGER,
        "Silicon Labs Flasher",
        ZIGBEE_FLASHER_ADDON_SLUG,
    )


class BaseFirmwareInstallFlow(ConfigEntryBaseFlow):
    """Base flow to install firmware."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Instantiate base flow."""
        super().__init__(*args, **kwargs)

        self._current_firmware_type: ApplicationType | None = None
        self._usb_info: usb.UsbServiceInfo | None = None
        self._hw_variant: HardwareVariant | None = None

        self.install_task: asyncio.Task | None = None
        self.start_task: asyncio.Task | None = None
        self.stop_task: asyncio.Task | None = None

    def _get_translation_placeholders(self) -> dict[str, str]:
        """Shared translation placeholders."""
        placeholders = {
            "model": (
                self._hw_variant.full_name
                if self._hw_variant is not None
                else "unknown"
            ),
            "firmware_type": (
                self._current_firmware_type
                if self._current_firmware_type is not None
                else "unknown"
            ),
            "docs_web_flasher_url": "https://skyconnect.home-assistant.io/firmware-update/",
        }

        self.context["title_placeholders"] = placeholders

        return placeholders

    async def _async_set_addon_config(
        self, config: dict, addon_manager: AddonManager
    ) -> None:
        """Set add-on config."""
        try:
            await addon_manager.async_set_addon_options(config)
        except AddonError as err:
            _LOGGER.error(err)
            raise AbortFlow("addon_set_config_failed") from err

    async def _async_get_addon_info(self, addon_manager: AddonManager) -> AddonInfo:
        """Return add-on info."""
        try:
            addon_info: AddonInfo = await addon_manager.async_get_addon_info()
        except AddonError as err:
            _LOGGER.error(err)
            raise AbortFlow(
                "addon_info_failed",
                description_placeholders={"addon_name": addon_manager.addon_name},
            ) from err

        return addon_info

    async def async_step_pick_firmware(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick Thread or Zigbee firmware."""
        assert self._usb_info is not None

        self._current_firmware_type = await probe_silabs_firmware_type(
            self._usb_info.device,
            probe_methods=(
                # We probe in order of frequency: Zigbee, Thread, then multi-PAN
                ApplicationType.GECKO_BOOTLOADER,
                ApplicationType.EZSP,
                ApplicationType.SPINEL,
                ApplicationType.CPC,
            ),
        )

        if self._current_firmware_type not in (
            ApplicationType.EZSP,
            ApplicationType.SPINEL,
            ApplicationType.CPC,
        ):
            return self.async_abort(
                reason="unsupported_firmware",
                description_placeholders=self._get_translation_placeholders(),
            )

        return self.async_show_menu(
            step_id="pick_firmware",
            menu_options=[
                STEP_PICK_FIRMWARE_THREAD,
                STEP_PICK_FIRMWARE_ZIGBEE,
            ],
            description_placeholders=self._get_translation_placeholders(),
        )

    async def async_step_pick_firmware_zigbee(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick Zigbee firmware."""
        if self._current_firmware_type == ApplicationType.EZSP:
            return await self.async_step_confirm_zigbee()

        if not is_hassio(self.hass):
            return self.async_abort(
                reason="not_hassio",
                description_placeholders=self._get_translation_placeholders(),
            )

        # Only flash new firmware if we need to
        fw_flasher_manager = get_zigbee_flasher_addon_manager(self.hass)
        addon_info = await self._async_get_addon_info(fw_flasher_manager)

        if addon_info.state == AddonState.NOT_INSTALLED:
            return await self.async_step_install_zigbee_flasher_addon()

        if addon_info.state == AddonState.NOT_RUNNING:
            return await self.async_step_run_zigbee_flasher_addon()

        # If the addon is already installed and running, fail
        return self.async_abort(
            reason="addon_already_running",
            description_placeholders={
                **self._get_translation_placeholders(),
                "addon_name": fw_flasher_manager.addon_name,
            },
        )

    async def async_step_install_zigbee_flasher_addon(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show progress dialog for installing the Zigbee flasher addon."""
        fw_flasher_manager = get_zigbee_flasher_addon_manager(self.hass)
        addon_info = await self._async_get_addon_info(fw_flasher_manager)

        _LOGGER.debug("Flasher addon state: %s", addon_info)

        if not self.install_task:
            self.install_task = self.hass.async_create_task(
                fw_flasher_manager.async_install_addon_waiting(),
                "SiLabs Flasher addon install",
            )

        if not self.install_task.done():
            return self.async_show_progress(
                step_id="install_zigbee_flasher_addon",
                progress_action="install_addon",
                description_placeholders={
                    **self._get_translation_placeholders(),
                    "addon_name": fw_flasher_manager.addon_name,
                },
                progress_task=self.install_task,
            )

        try:
            await self.install_task
        except AddonError as err:
            _LOGGER.error(err)
            return self.async_show_progress_done(next_step_id="install_failed")
        finally:
            self.install_task = None

        return self.async_show_progress_done(next_step_id="run_zigbee_flasher_addon")

    async def async_step_run_zigbee_flasher_addon(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure the flasher addon to point to the SkyConnect."""
        fw_flasher_manager = get_zigbee_flasher_addon_manager(self.hass)
        addon_info = await self._async_get_addon_info(fw_flasher_manager)

        assert self._usb_info is not None
        new_addon_config = {
            **addon_info.options,
            "device": self._usb_info.device,
            "baudrate": 115200,
            "flow_control": True,
        }

        _LOGGER.debug("Reconfiguring flasher addon with %s", new_addon_config)
        await self._async_set_addon_config(new_addon_config, fw_flasher_manager)

        if not self.start_task:

            async def start_and_wait_until_done() -> None:
                await fw_flasher_manager.async_start_addon_waiting()
                # Now that the addon is running, wait for it to finish
                await fw_flasher_manager.async_wait_until_addon_state(
                    AddonState.NOT_RUNNING
                )

            self.start_task = self.hass.async_create_task(start_and_wait_until_done())

        if not self.start_task.done():
            return self.async_show_progress(
                step_id="start_zigbee_flasher_addon",
                progress_action="start_zigbee_flasher_addon",
                description_placeholders={
                    **self._get_translation_placeholders(),
                    "addon_name": fw_flasher_manager.addon_name,
                },
                progress_task=self.start_task,
            )

        try:
            await self.start_task
        except (AddonError, AbortFlow) as err:
            _LOGGER.error(err)
            return self.async_show_progress_done(next_step_id="zigbee_flasher_failed")
        finally:
            self.start_task = None

        return self.async_show_progress_done(next_step_id="zigbee_flashing_complete")

    async def async_step_zigbee_flasher_failed(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Flasher add-on start failed."""
        fw_flasher_manager = get_zigbee_flasher_addon_manager(self.hass)
        return self.async_abort(
            reason="addon_start_failed",
            description_placeholders={
                **self._get_translation_placeholders(),
                "addon_name": fw_flasher_manager.addon_name,
            },
        )

    async def async_step_zigbee_flashing_complete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show completion dialog for flashing Zigbee firmware."""
        fw_flasher_manager = get_zigbee_flasher_addon_manager(self.hass)
        await fw_flasher_manager.async_uninstall_addon_waiting()

        return self.async_show_progress_done(next_step_id="confirm_zigbee")

    async def async_step_confirm_zigbee(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm Zigbee setup."""
        assert self._usb_info is not None
        assert self._hw_variant is not None

        if user_input is not None:
            await self.hass.config_entries.flow.async_init(
                ZHA_DOMAIN,
                context={"source": "hardware"},
                data={
                    "name": self._hw_variant.full_name,
                    "port": {
                        "path": self._usb_info.device,
                        "baudrate": 115200,
                        "flow_control": "hardware",
                    },
                    "radio_type": "ezsp",
                },
            )

            return self._async_flow_finished()

        return self.async_show_form(
            step_id="confirm_zigbee",
            description_placeholders=self._get_translation_placeholders(),
        )

    async def async_step_pick_firmware_thread(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick Thread firmware."""
        # We install the OTBR addon no matter what, since it is required to use Thread
        if not is_hassio(self.hass):
            return self.async_abort(
                reason="not_hassio_thread",
                description_placeholders=self._get_translation_placeholders(),
            )

        otbr_manager = get_otbr_addon_manager(self.hass)
        addon_info = await self._async_get_addon_info(otbr_manager)

        if addon_info.state == AddonState.NOT_INSTALLED:
            return await self.async_step_install_otbr_addon()

        if addon_info.state == AddonState.NOT_RUNNING:
            return await self.async_step_start_otbr_addon()

        # If the addon is already installed and running, fail
        return self.async_abort(
            reason="otbr_addon_already_running",
            description_placeholders={
                **self._get_translation_placeholders(),
                "addon_name": otbr_manager.addon_name,
            },
        )

    async def async_step_install_otbr_addon(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show progress dialog for installing the OTBR addon."""
        otbr_manager = get_otbr_addon_manager(self.hass)
        addon_info = await self._async_get_addon_info(otbr_manager)

        _LOGGER.debug("Flasher addon state: %s", addon_info)

        if not self.install_task:
            self.install_task = self.hass.async_create_task(
                otbr_manager.async_install_addon_waiting(),
                "SiLabs Flasher addon install",
            )

        if not self.install_task.done():
            return self.async_show_progress(
                step_id="install_otbr_addon",
                progress_action="install_addon",
                description_placeholders={
                    **self._get_translation_placeholders(),
                    "addon_name": otbr_manager.addon_name,
                },
                progress_task=self.install_task,
            )

        try:
            await self.install_task
        except AddonError as err:
            _LOGGER.error(err)
            return self.async_show_progress_done(next_step_id="install_failed")
        finally:
            self.install_task = None

        return self.async_show_progress_done(next_step_id="start_otbr_addon")

    async def async_step_start_otbr_addon(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure OTBR to point to the SkyConnect and run the addon."""
        otbr_manager = get_otbr_addon_manager(self.hass)
        addon_info = await self._async_get_addon_info(otbr_manager)

        assert self._usb_info is not None
        new_addon_config = {
            **addon_info.options,
            "device": self._usb_info.device,
            "baudrate": 460800,
            "flow_control": True,
            "autoflash_firmware": True,
        }

        _LOGGER.debug("Reconfiguring OTBR addon with %s", new_addon_config)
        await self._async_set_addon_config(new_addon_config, otbr_manager)

        if not self.start_task:
            self.start_task = self.hass.async_create_task(
                otbr_manager.async_start_addon_waiting()
            )

        if not self.start_task.done():
            return self.async_show_progress(
                step_id="start_otbr_addon",
                progress_action="start_otbr_addon",
                description_placeholders={
                    **self._get_translation_placeholders(),
                    "addon_name": otbr_manager.addon_name,
                },
                progress_task=self.start_task,
            )

        try:
            await self.start_task
        except (AddonError, AbortFlow) as err:
            _LOGGER.error(err)
            return self.async_show_progress_done(next_step_id="otbr_failed")
        finally:
            self.start_task = None

        return self.async_show_progress_done(next_step_id="otbr_complete")

    async def async_step_otbr_failed(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """OTBR add-on start failed."""
        otbr_manager = get_otbr_addon_manager(self.hass)
        return self.async_abort(
            reason="addon_start_failed",
            description_placeholders={
                **self._get_translation_placeholders(),
                "addon_name": otbr_manager.addon_name,
            },
        )

    async def async_step_otbr_complete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show completion dialog for OTBR."""
        self._current_firmware_type = ApplicationType.SPINEL
        return self.async_show_progress_done(next_step_id="confirm_otbr")

    async def async_step_confirm_otbr(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm OTBR setup."""
        assert self._usb_info is not None
        assert self._hw_variant is not None
        assert self._current_firmware_type is not None

        if user_input is not None:
            # OTBR discovery is done automatically via hassio
            return self._async_flow_finished()

        return self.async_show_form(
            step_id="confirm_otbr",
            description_placeholders=self._get_translation_placeholders(),
        )

    def _async_flow_finished(self) -> ConfigFlowResult:
        """Finish the flow."""
        raise NotImplementedError


class HomeAssistantSkyConnectConfigFlow(
    BaseFirmwareInstallFlow, ConfigFlow, domain=DOMAIN
):
    """Handle a config flow for Home Assistant SkyConnect."""

    VERSION = 2
    MINOR_VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Return the options flow."""
        firmware_type = ApplicationType(config_entry.data["firmware"])

        if firmware_type == ApplicationType.CPC:
            return HomeAssistantSkyConnectMultiPanOptionsFlowHandler(config_entry)

        return HomeAssistantSkyConnectOptionsFlowHandler(config_entry)

    async def async_step_usb(
        self, discovery_info: usb.UsbServiceInfo
    ) -> ConfigFlowResult:
        """Handle usb discovery."""
        device = discovery_info.device
        vid = discovery_info.vid
        pid = discovery_info.pid
        serial_number = discovery_info.serial_number
        manufacturer = discovery_info.manufacturer
        description = discovery_info.description
        unique_id = f"{vid}:{pid}_{serial_number}_{manufacturer}_{description}"

        if await self.async_set_unique_id(unique_id):
            self._abort_if_unique_id_configured(updates={"device": device})

        discovery_info.device = await self.hass.async_add_executor_job(
            usb.get_serial_by_id, discovery_info.device
        )

        self._usb_info = discovery_info

        assert description is not None
        self._hw_variant = HardwareVariant.from_usb_product_name(description)

        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm a discovery."""
        self._set_confirm_only()

        # Without confirmation, discovery can automatically progress into parts of the
        # config flow logic that interacts with hardware.
        if user_input is not None:
            return await self.async_step_pick_firmware()

        return self.async_show_form(
            step_id="confirm",
            description_placeholders=self._get_translation_placeholders(),
        )

    def _async_flow_finished(self) -> ConfigFlowResult:
        """Create the config entry."""
        assert self._usb_info is not None
        assert self._hw_variant is not None
        assert self._current_firmware_type is not None

        return self.async_create_entry(
            title=self._hw_variant.full_name,
            data={
                "vid": self._usb_info.vid,
                "pid": self._usb_info.pid,
                "serial_number": self._usb_info.serial_number,
                "manufacturer": self._usb_info.manufacturer,
                "product": self._usb_info.description,
                "device": self._usb_info.device,
                "firmware": self._current_firmware_type.lower(),
            },
        )


class HomeAssistantSkyConnectMultiPanOptionsFlowHandler(
    silabs_multiprotocol_addon.OptionsFlowHandler
):
    """Multi-PAN options flow for Home Assistant SkyConnect."""

    async def _async_serial_port_settings(
        self,
    ) -> silabs_multiprotocol_addon.SerialPortSettings:
        """Return the radio serial port settings."""
        usb_dev = self.config_entry.data["device"]
        # The call to get_serial_by_id can be removed in HA Core 2024.1
        dev_path = await self.hass.async_add_executor_job(usb.get_serial_by_id, usb_dev)
        return silabs_multiprotocol_addon.SerialPortSettings(
            device=dev_path,
            baudrate="115200",
            flow_control=True,
        )

    async def _async_zha_physical_discovery(self) -> dict[str, Any]:
        """Return ZHA discovery data when multiprotocol FW is not used.

        Passed to ZHA do determine if the ZHA config entry is connected to the radio
        being migrated.
        """
        return {"usb": get_usb_service_info(self.config_entry)}

    @property
    def _hw_variant(self) -> HardwareVariant:
        """Return the hardware variant."""
        return get_hardware_variant(self.config_entry)

    def _zha_name(self) -> str:
        """Return the ZHA name."""
        return f"{self._hw_variant.short_name} Multiprotocol"

    def _hardware_name(self) -> str:
        """Return the name of the hardware."""
        return self._hw_variant.full_name


class HomeAssistantSkyConnectOptionsFlowHandler(
    BaseFirmwareInstallFlow, OptionsFlowWithConfigEntry
):
    """Zigbee and Thread options flow handlers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Instantiate options flow."""
        super().__init__(*args, **kwargs)

        self._usb_info = usb.UsbServiceInfo(
            device=self.config_entry.data["device"],
            vid=self.config_entry.data["vid"],
            pid=self.config_entry.data["pid"],
            serial_number=self.config_entry.data["serial_number"],
            manufacturer=self.config_entry.data["manufacturer"],
            description=self.config_entry.data["product"],
        )
        self._current_firmware_type = ApplicationType(
            self.config_entry.data["firmware"]
        )
        self._hw_variant = HardwareVariant.from_usb_product_name(
            self.config_entry.data["product"]
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options flow."""
        return await self.async_step_pick_firmware()

    def _async_flow_finished(self) -> ConfigFlowResult:
        """Create the config entry."""
        assert self._usb_info is not None
        assert self._hw_variant is not None
        assert self._current_firmware_type is not None

        self.hass.config_entries.async_update_entry(
            entry=self.config_entry,
            data={
                **self.config_entry.data,
                "firmware": self._current_firmware_type,
            },
            options=self.config_entry.options,
        )

        return self.async_create_entry(title="", data={})
