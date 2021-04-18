"""Constants for the Somfy TaHoma integration."""
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR
from homeassistant.components.cover import DOMAIN as COVER
from homeassistant.components.light import DOMAIN as LIGHT
from homeassistant.components.lock import DOMAIN as LOCK
from homeassistant.components.sensor import DOMAIN as SENSOR

DOMAIN = "tahoma"

CONF_HUB = "hub"
DEFAULT_HUB = "Somfy (Europe)"

MIN_UPDATE_INTERVAL = 30
DEFAULT_UPDATE_INTERVAL = 30

SUPPORTED_ENDPOINTS = {
    "Cozytouch": "https://ha110-1.overkiz.com/enduser-mobile-web/enduserAPI/",
    "eedomus": "https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
    "Hi Kumo": "https://ha117-1.overkiz.com/enduser-mobile-web/enduserAPI/",
    "Rexel Energeasy Connect": "https://ha112-1.overkiz.com/enduser-mobile-web/enduserAPI/",
    "Somfy (Australia)": "https://ha201-1.overkiz.com/enduser-mobile-web/enduserAPI/",
    "Somfy (Europe)": "https://tahomalink.com/enduser-mobile-web/enduserAPI/",
    "Somfy (North America)": "https://ha401-1.overkiz.com/enduser-mobile-web/enduserAPI/",
}

IGNORED_TAHOMA_DEVICES = [
    "ProtocolGateway",
    "Pod",
]

# Used to map the Somfy widget and ui_class to the Home Assistant platform
TAHOMA_DEVICE_TO_PLATFORM = {
    "AdjustableSlatsRollerShutter": COVER,
    "AirFlowSensor": BINARY_SENSOR,  # widgetName, uiClass is AirSensor (sensor)
    "AirSensor": SENSOR,
    "Awning": COVER,
    "CarButtonSensor": BINARY_SENSOR,
    "ConsumptionSensor": SENSOR,
    "ContactSensor": BINARY_SENSOR,
    "Curtain": COVER,
    "DoorLock": LOCK,
    "ElectricitySensor": SENSOR,
    "ExteriorScreen": COVER,
    "ExteriorVenetianBlind": COVER,
    "GarageDoor": COVER,
    "GasSensor": SENSOR,
    "Gate": COVER,
    "GenericSensor": SENSOR,
    "HumiditySensor": SENSOR,
    "Light": LIGHT,
    "LightSensor": SENSOR,
    "MotionSensor": BINARY_SENSOR,
    "MyFoxSecurityCamera": COVER,  # widgetName, uiClass is Camera (not supported)
    "OccupancySensor": BINARY_SENSOR,
    "Pergola": COVER,
    "RainSensor": BINARY_SENSOR,
    "RollerShutter": COVER,
    "Screen": COVER,
    "Shutter": COVER,
    "SirenStatus": BINARY_SENSOR,  # widgetName, uiClass is Siren (switch)
    "SmokeSensor": BINARY_SENSOR,
    "SunIntensitySensor": SENSOR,
    "SunSensor": SENSOR,
    "SwingingShutter": COVER,
    "TemperatureSensor": SENSOR,
    "ThermalEnergySensor": SENSOR,
    "VenetianBlind": COVER,
    "WaterDetectionSensor": BINARY_SENSOR,  # widgetName, uiClass is HumiditySensor (sensor)
    "WaterSensor": SENSOR,
    "WeatherSensor": SENSOR,
    "WindSensor": SENSOR,
    "Window": COVER,
    "WindowHandle": BINARY_SENSOR,
}

CORE_ON_OFF_STATE = "core:OnOffState"

COMMAND_OFF = "off"
COMMAND_ON = "on"

CONF_UPDATE_INTERVAL = "update_interval"
