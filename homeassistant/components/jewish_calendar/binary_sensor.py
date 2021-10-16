"""Support for Jewish Calendar binary sensors."""
from __future__ import annotations

import datetime as dt

import hdate

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.components.jewish_calendar.erev_shabbt_hag_binary_sensor import (
    ErevShabbtHagBinarySensor,
)
from homeassistant.components.jewish_calendar.motzei_shabbt_hag_binary_sensor import (
    MotzeiShabbtHagBinarySensor,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import event
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import homeassistant.util.dt as dt_util

from . import DOMAIN

BINARY_SENSOR = BinarySensorEntityDescription(
    key="issur_melacha_in_effect",
    name="Issur Melacha in Effect",
    icon="mdi:power-plug-off",
)

MOTZEI_BINARY_SENSOR = BinarySensorEntityDescription(
    key="motzei_shabbat_hat_in_effect",
    name="Motzei Shabbat/Hag in Effect",
    icon="mdi:power-plug-off",
)

EREV_BINARY_SENSOR = BinarySensorEntityDescription(
    key="erev_shabbat_hat_in_effect",
    name="Erev Shabbat/Hag in Effect",
    icon="mdi:power-plug-off",
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
):
    """Set up the Jewish Calendar binary sensor devices."""
    if discovery_info is None:
        return

    async_add_entities([JewishCalendarBinarySensor(hass.data[DOMAIN], BINARY_SENSOR)])
    async_add_entities(
        [MotzeiShabbtHagBinarySensor(hass.data[DOMAIN], MOTZEI_BINARY_SENSOR)]
    )
    async_add_entities(
        [ErevShabbtHagBinarySensor(hass.data[DOMAIN], EREV_BINARY_SENSOR)]
    )


class JewishCalendarBinarySensor(BinarySensorEntity):
    """Representation of an Jewish Calendar binary sensor."""

    _attr_should_poll = False

    def __init__(self, data, description: BinarySensorEntityDescription) -> None:
        """Initialize the binary sensor."""
        self._attr_name = f"{data['name']} {description.name}"
        self._attr_unique_id = f"{data['prefix']}_{description.key}"
        self._location = data["location"]
        self._hebrew = data["language"] == "hebrew"
        self._candle_lighting_offset = data["candle_lighting_offset"]
        self._havdalah_offset = data["havdalah_offset"]
        self._update_unsub = None

    @property
    def is_on(self) -> bool:
        """Return true if sensor is on."""
        return self._get_zmanim().issur_melacha_in_effect

    def _get_zmanim(self):
        """Return the Zmanim object for now()."""
        return hdate.Zmanim(
            date=dt_util.now(),
            location=self._location,
            candle_lighting_offset=self._candle_lighting_offset,
            havdalah_offset=self._havdalah_offset,
            hebrew=self._hebrew,
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        self._schedule_update()

    @callback
    def _update(self, now=None):
        """Update the state of the sensor."""
        self._update_unsub = None
        self._schedule_update()
        self.async_write_ha_state()

    def _schedule_update(self):
        """Schedule the next update of the sensor."""
        now = dt_util.now()
        zmanim = self._get_zmanim()
        update = zmanim.zmanim["sunrise"] + dt.timedelta(days=1)
        candle_lighting = zmanim.candle_lighting
        if candle_lighting is not None and now < candle_lighting < update:
            update = candle_lighting
        havdalah = zmanim.havdalah
        if havdalah is not None and now < havdalah < update:
            update = havdalah
        if self._update_unsub:
            self._update_unsub()
        self._update_unsub = event.async_track_point_in_time(
            self.hass, self._update, update
        )
