"""Matter light."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import partial
from typing import Any

from chip.clusters import Objects as clusters
from matter_server.common.models import device_types

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    ATTR_XY_COLOR,
    ColorMode,
    LightEntity,
    LightEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import LOGGER
from .entity import MatterEntity, MatterEntityDescriptionBaseClass
from .helpers import get_matter
from .util import renormalize

XY_COLOR_FACTOR = 65536


class MatterColorMode(Enum):
    """Matter color mode."""

    HS = 0
    XY = 1
    COLOR_TEMP = 2


COLOR_MODE_MAP = {
    MatterColorMode.HS: ColorMode.HS,
    MatterColorMode.XY: ColorMode.XY,
    MatterColorMode.COLOR_TEMP: ColorMode.COLOR_TEMP,
}


class MatterColorControlFeatures(Enum):
    """Matter color control features."""

    HS = 0  # Hue and saturation (Optional if device is color capable)
    EHUE = 1  # Enhanced hue and saturation (Optional if device is color capable)
    COLOR_LOOP = 2  # Color loop (Optional if device is color capable)
    XY = 3  # XY (Mandatory if device is color capable)
    COLOR_TEMP = 4  # Color temperature (Mandatory if device is color capable)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Matter Light from Config Entry."""
    matter = get_matter(hass)
    matter.register_platform_handler(Platform.LIGHT, async_add_entities)


class MatterLight(MatterEntity, LightEntity):
    """Representation of a Matter light."""

    entity_description: MatterLightEntityDescription

    def _supports_feature(
        self, feature_map: int, feature: MatterColorControlFeatures
    ) -> bool:
        """Return if device supports given feature."""

        return (feature_map & (1 << feature.value)) != 0

    def _supports_color_mode(self, color_feature: MatterColorControlFeatures) -> bool:
        """Return if device supports given color mode."""

        if not self._supports_color():
            return False

        feature_map = self._device_type_instance.node.get_attribute(
            self._device_type_instance.endpoint,
            clusters.ColorControl,
            clusters.ColorControl.Attributes.FeatureMap,
        )

        assert isinstance(feature_map.value, int)

        return self._supports_feature(int(feature_map.value), color_feature)

    def _supports_hs_color(self) -> bool:
        """Return if device supports hs color."""

        return self._supports_color_mode(MatterColorControlFeatures.HS)

    def _supports_xy_color(self) -> bool:
        """Return if device supports xy color."""

        return self._supports_color_mode(MatterColorControlFeatures.XY)

    def _supports_color_loop(self) -> bool:
        """Return if device supports color loop."""

        return self._supports_color_mode(MatterColorControlFeatures.COLOR_LOOP)

    def _supports_color_temperature(self) -> bool:
        """Return if device supports color temperature."""

        return self._supports_color_mode(MatterColorControlFeatures.COLOR_TEMP)

    def _supports_brightness(self) -> bool:
        """Return if device supports brightness."""

        return (
            clusters.LevelControl.Attributes.CurrentLevel
            in self.entity_description.subscribe_attributes
        )

    def _supports_color(self) -> bool:
        """Return if device supports color."""

        return (
            clusters.ColorControl.Attributes.ColorMode
            in self.entity_description.subscribe_attributes
        )

    async def _set_xy_color(self, xy_color: tuple[float, float]) -> None:
        """Set xy color."""

        LOGGER.debug("Setting xy color to %s", (xy_color))
        await self.send_device_command(
            clusters.ColorControl.Commands.MoveToColor(
                colorX=int(xy_color[0] * XY_COLOR_FACTOR),
                colorY=int(xy_color[1] * XY_COLOR_FACTOR),
                # It's required in TLV. We don't implement transition time yet.
                transitionTime=0,
            )
        )

    async def _set_hs_color(self, hs_color: tuple[float, float]) -> None:
        """Set hs color."""

        hue = int(hs_color[0] / 360 * 254)
        saturation = int(renormalize(hs_color[1], (0, 100), (0, 254)))

        LOGGER.debug("Setting hs color to %s", (hue, saturation))

        await self.send_device_command(
            clusters.ColorControl.Commands.MoveToHueAndSaturation(
                hue=hue,
                saturation=saturation,
                # It's required in TLV. We don't implement transition time yet.
                transitionTime=0,
            )
        )

    async def _set_color_temp(self, color_temp: int) -> None:
        """Set color temperature."""

        LOGGER.debug("Setting color temperature to %s", color_temp)
        await self.send_device_command(
            clusters.ColorControl.Commands.MoveToColorTemperature(
                colorTemperature=color_temp,
                # It's required in TLV. We don't implement transition time yet.
                transitionTime=0,
            )
        )

    async def _set_brightness(self, brightness: int) -> None:
        """Set brightness."""

        LOGGER.debug("Setting brightness to %s", brightness)
        level_control = self._device_type_instance.get_cluster(clusters.LevelControl)

        assert level_control is not None

        level = round(
            renormalize(
                brightness,
                (0, 255),
                (level_control.minLevel, level_control.maxLevel),
            )
        )

        await self.send_device_command(
            clusters.LevelControl.Commands.MoveToLevelWithOnOff(
                level=level,
                # It's required in TLV. We don't implement transition time yet.
                transitionTime=0,
            )
        )

    def _get_xy_color(self) -> tuple[float, float]:
        """Get xy color from matter."""

        x_color = self.get_matter_attribute(clusters.ColorControl.Attributes.CurrentX)
        y_color = self.get_matter_attribute(clusters.ColorControl.Attributes.CurrentY)

        assert x_color is not None
        assert y_color is not None

        xy_color = (
            x_color.value / XY_COLOR_FACTOR,
            y_color.value / XY_COLOR_FACTOR,
        )

        LOGGER.debug(
            "Got xy color %s for %s",
            xy_color,
            self._device_type_instance,
        )

        return xy_color

    def _get_hs_color(self) -> tuple[float, float]:
        """Get hs color from matter."""

        hue = self.get_matter_attribute(clusters.ColorControl.Attributes.CurrentHue)

        saturation = self.get_matter_attribute(
            clusters.ColorControl.Attributes.CurrentSaturation
        )

        assert hue is not None
        assert saturation is not None

        hue_saturation = (
            int(hue.value * 360 / 254),
            int(renormalize(saturation.value, (0, 254), (0, 100))),
        )

        LOGGER.debug(
            "Got hs color %s for %s",
            hue_saturation,
            self._device_type_instance,
        )

        return hue_saturation

    def _get_color_temperature(self) -> int:
        """Get color temperature from matter."""

        color_temp = self.get_matter_attribute(
            clusters.ColorControl.Attributes.ColorTemperatureMireds
        )

        assert color_temp is not None

        LOGGER.debug(
            "Got color temperature %s for %s",
            color_temp.value,
            self._device_type_instance,
        )

        return int(color_temp.value)

    def _get_color_mode(self) -> ColorMode:
        """Get color mode from matter."""

        color_mode = self.get_matter_attribute(
            clusters.ColorControl.Attributes.ColorMode
        )

        assert color_mode is not None

        ha_color_mode = COLOR_MODE_MAP.get(MatterColorMode(color_mode.value))

        if ha_color_mode is None:
            LOGGER.warning("Unknown color mode %s", color_mode.value)
            ha_color_mode = ColorMode.UNKNOWN

        LOGGER.debug(
            "Got color mode (%s) for %s", ha_color_mode, self._device_type_instance
        )

        return ha_color_mode

    async def send_device_command(self, command: Any) -> None:
        """Send device command."""
        await self.matter_client.send_device_command(
            node_id=self._device_type_instance.node.node_id,
            endpoint=self._device_type_instance.endpoint,
            command=command,
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn light on."""

        hs_color = kwargs.get(ATTR_HS_COLOR)
        xy_color = kwargs.get(ATTR_XY_COLOR)
        color_temp = kwargs.get(ATTR_COLOR_TEMP)
        brightness = kwargs.get(ATTR_BRIGHTNESS)

        if hs_color is not None and self._supports_hs_color():
            await self._set_hs_color(hs_color)
        elif xy_color is not None and self._supports_xy_color():
            await self._set_xy_color(xy_color)
        elif color_temp is not None and self._supports_color_temperature():
            await self._set_color_temp(color_temp)

        if brightness is not None and self._supports_brightness():
            await self._set_brightness(brightness)
            return

        await self.send_device_command(
            clusters.OnOff.Commands.On(),
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn light off."""
        await self.send_device_command(
            clusters.OnOff.Commands.Off(),
        )

    @callback
    def _update_from_device(self) -> None:
        """Update from device."""

        supports_color = self._supports_color()

        if self._attr_supported_color_modes is None and supports_color:
            self._attr_supported_color_modes = {
                ColorMode.XY,
                ColorMode.COLOR_TEMP,
                ColorMode.BRIGHTNESS,
            }

            if self._supports_hs_color():
                LOGGER.debug(
                    "Adding (HS) color mode for %s", self._device_type_instance
                )
                self._attr_supported_color_modes.add(ColorMode.HS)

        supports_color_temperature = self._supports_color_temperature()

        if self._attr_supported_color_modes is None and supports_color_temperature:
            self._attr_supported_color_modes = {
                ColorMode.COLOR_TEMP,
                ColorMode.BRIGHTNESS,
            }

        supports_brightness = self._supports_brightness()

        if self._attr_supported_color_modes is None and supports_brightness:
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}

        LOGGER.debug(
            "Supported color modes: %s for %s",
            self._attr_supported_color_modes,
            self._device_type_instance,
        )

        if supports_color:
            self._attr_color_mode = self._get_color_mode()
            if self._attr_color_mode == ColorMode.HS:
                self._attr_hs_color = self._get_hs_color()
            else:
                self._attr_xy_color = self._get_xy_color()

        if supports_color_temperature:
            self._attr_color_temp = self._get_color_temperature()

        if attr := self.get_matter_attribute(clusters.OnOff.Attributes.OnOff):
            self._attr_is_on = attr.value

        if supports_brightness:
            level_control = self._device_type_instance.get_cluster(
                clusters.LevelControl
            )
            # We check above that the device supports brightness, ie level control.
            assert level_control is not None

            # Convert brightness to Home Assistant = 0..255
            self._attr_brightness = round(
                renormalize(
                    level_control.currentLevel,
                    (level_control.minLevel, level_control.maxLevel),
                    (0, 255),
                )
            )


@dataclass
class MatterLightEntityDescription(
    LightEntityDescription,
    MatterEntityDescriptionBaseClass,
):
    """Matter light entity description."""


# You can't set default values on inherited data classes
MatterLightEntityDescriptionFactory = partial(
    MatterLightEntityDescription, entity_cls=MatterLight
)

# Mapping of a Matter Device type to Light Entity Description.
# A Matter device type (instance) can consist of multiple attributes.
# For example a Color Light which has an attribute to control brightness
# but also for color.

DEVICE_ENTITY: dict[
    type[device_types.DeviceType],
    MatterEntityDescriptionBaseClass | list[MatterEntityDescriptionBaseClass],
] = {
    device_types.OnOffLight: MatterLightEntityDescriptionFactory(
        key=device_types.OnOffLight,
        subscribe_attributes=(clusters.OnOff.Attributes.OnOff,),
    ),
    device_types.DimmableLight: MatterLightEntityDescriptionFactory(
        key=device_types.DimmableLight,
        subscribe_attributes=(
            clusters.OnOff.Attributes.OnOff,
            clusters.LevelControl.Attributes.CurrentLevel,
        ),
    ),
    device_types.DimmablePlugInUnit: MatterLightEntityDescriptionFactory(
        key=device_types.DimmablePlugInUnit,
        subscribe_attributes=(
            clusters.OnOff.Attributes.OnOff,
            clusters.LevelControl.Attributes.CurrentLevel,
        ),
    ),
    device_types.ColorTemperatureLight: MatterLightEntityDescriptionFactory(
        key=device_types.ColorTemperatureLight,
        subscribe_attributes=(
            clusters.OnOff.Attributes.OnOff,
            clusters.LevelControl.Attributes.CurrentLevel,
            clusters.ColorControl.Attributes.ColorTemperatureMireds,
        ),
    ),
    device_types.ExtendedColorLight: MatterLightEntityDescriptionFactory(
        key=device_types.ExtendedColorLight,
        subscribe_attributes=(
            clusters.OnOff.Attributes.OnOff,
            clusters.LevelControl.Attributes.CurrentLevel,
            clusters.ColorControl.Attributes.ColorMode,
            clusters.ColorControl.Attributes.CurrentHue,
            clusters.ColorControl.Attributes.CurrentSaturation,
            clusters.ColorControl.Attributes.CurrentX,
            clusters.ColorControl.Attributes.CurrentY,
            clusters.ColorControl.Attributes.ColorTemperatureMireds,
        ),
    ),
}
