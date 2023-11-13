"""Number for ViCare."""
from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
import logging

from PyViCare.PyViCareDevice import Device as PyViCareDevice
from PyViCare.PyViCareDeviceConfig import PyViCareDeviceConfig
from PyViCare.PyViCareHeatingDevice import (
    HeatingDeviceWithComponent as PyViCareHeatingDeviceWithComponent,
)
from PyViCare.PyViCareUtils import (
    PyViCareInvalidDataError,
    PyViCareNotSupportedFeatureError,
    PyViCareRateLimitError,
)
import requests

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ViCareRequiredKeysMixin
from .const import DOMAIN, VICARE_API, VICARE_DEVICE_CONFIG
from .entity import ViCareEntity
from .utils import is_supported

_LOGGER = logging.getLogger(__name__)


@dataclass
class ViCareNumberEntityDescription(NumberEntityDescription, ViCareRequiredKeysMixin):
    """Describes ViCare number entity."""

    value_setter: Callable[[PyViCareDevice, float], str | None] | None = None


CIRCUIT_SENSORS: tuple[ViCareNumberEntityDescription, ...] = (
    ViCareNumberEntityDescription(
        key="heating curve shift",
        name="Heating curve shift",
        icon="mdi:plus-minus-variant",
        entity_category=EntityCategory.CONFIG,
        value_getter=lambda api: api.getHeatingCurveShift(),
        value_setter=lambda api, shift: api.setHeatingCurve(
            shift, api.getHeatingCurveSlope()
        ),
        native_min_value=-13,
        native_max_value=40,
        native_step=1,
    ),
    ViCareNumberEntityDescription(
        key="heating curve slope",
        name="Heating curve slope",
        icon="mdi:slope-uphill",
        entity_category=EntityCategory.CONFIG,
        value_getter=lambda api: api.getHeatingCurveSlope(),
        value_setter=lambda api, slope: api.setHeatingCurve(
            api.getHeatingCurveShift(), slope
        ),
        native_min_value=0.2,
        native_max_value=3.5,
        native_step=0.1,
    ),
)


def _build_entity(
    name: str,
    vicare_api: PyViCareHeatingDeviceWithComponent,
    device_config: PyViCareDeviceConfig,
    entity_description: ViCareNumberEntityDescription,
    hass: HomeAssistant,
) -> ViCareNumber | None:
    """Create a ViCare number entity."""
    _LOGGER.debug("Found device %s", name)
    if is_supported(name, entity_description, vicare_api):
        return ViCareNumber(
            name,
            vicare_api,
            device_config,
            entity_description,
            hass,
        )
    return None


async def _entities_from_descriptions(
    hass: HomeAssistant,
    entities: list[ViCareNumber],
    sensor_descriptions: tuple[ViCareNumberEntityDescription, ...],
    iterables: list[PyViCareHeatingDeviceWithComponent],
    config_entry: ConfigEntry,
) -> None:
    """Create entities from descriptions and list of burners/circuits."""
    for description in sensor_descriptions:
        for current in iterables:
            suffix = ""
            if len(iterables) > 1:
                suffix = f" {current.id}"
            entity = await hass.async_add_executor_job(
                _build_entity,
                f"{description.name}{suffix}",
                current,
                hass.data[DOMAIN][config_entry.entry_id][VICARE_DEVICE_CONFIG],
                description,
                hass,
            )
            if entity is not None:
                entities.append(entity)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the ViCare sensor devices."""
    api = hass.data[DOMAIN][config_entry.entry_id][VICARE_API]

    entities: list[ViCareNumber] = []
    try:
        await _entities_from_descriptions(
            hass, entities, CIRCUIT_SENSORS, api.circuits, config_entry
        )
    except PyViCareNotSupportedFeatureError:
        _LOGGER.debug("No circuits found")

    async_add_entities(entities)


class ViCareNumber(ViCareEntity, NumberEntity):
    """Representation of a ViCare sensor."""

    entity_description: ViCareNumberEntityDescription

    def __init__(
        self,
        name: str,
        api: PyViCareHeatingDeviceWithComponent,
        device_config: PyViCareDeviceConfig,
        description: ViCareNumberEntityDescription,
        hass: HomeAssistant,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(device_config)
        self.entity_description = description
        self._attr_name = name
        self._api = api
        self._device_config = device_config
        self._hass = hass

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._attr_native_value is not None

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        tmp_id = (
            f"{self._device_config.getConfig().serial}-{self.entity_description.key}"
        )
        if hasattr(self._api, "id"):
            return f"{tmp_id}-{self._api.id}"
        return tmp_id

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        if self.entity_description.value_setter:
            await self._hass.async_add_executor_job(
                self.entity_description.value_setter, self._api, value
            )
        self.async_write_ha_state()

    def update(self) -> None:
        """Update state of sensor."""
        try:
            with suppress(PyViCareNotSupportedFeatureError):
                self._attr_native_value = self.entity_description.value_getter(
                    self._api
                )
        except requests.exceptions.ConnectionError:
            _LOGGER.error("Unable to retrieve data from ViCare server")
        except ValueError:
            _LOGGER.error("Unable to decode data from ViCare server")
        except PyViCareRateLimitError as limit_exception:
            _LOGGER.error("Vicare API rate limit exceeded: %s", limit_exception)
        except PyViCareInvalidDataError as invalid_data_exception:
            _LOGGER.error("Invalid data from Vicare server: %s", invalid_data_exception)
