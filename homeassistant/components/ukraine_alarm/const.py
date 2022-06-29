"""Consts for the Ukraine Alarm."""
from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "ukraine_alarm"
ATTRIBUTION = "Data provided by Ukraine Alarm"
MANUFACTURER = "Ukraine Alarm"
ALERT_TYPE_UNKNOWN = "UNKNOWN"
ALERT_TYPE_AIR = "AIR"
ALERT_TYPE_ARTILLERY = "ARTILLERY"
ALERT_TYPE_URBAN_FIGHTS = "URBAN_FIGHTS"
ALERT_TYPES = {
    ALERT_TYPE_UNKNOWN,
    ALERT_TYPE_AIR,
    ALERT_TYPE_ARTILLERY,
    ALERT_TYPE_URBAN_FIGHTS,
}
PLATFORMS = [Platform.BINARY_SENSOR]
