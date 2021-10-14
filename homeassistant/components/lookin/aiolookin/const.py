"""The lookin integration constants."""
from __future__ import annotations

import logging
from typing import Final

INFO_URL: Final = "http://{host}/device"
METEO_SENSOR_URL: Final = "http://{host}/sensors/meteo"
DEVICES_INFO_URL: Final = "http://{host}/data"
DEVICE_INFO_URL: Final = "http://{host}/data/{uuid}"
UPDATE_CLIMATE_URL: Final = "http://{host}/commands/ir/ac/{extra}{status}"
SEND_IR_COMMAND: Final = "http://{host}/commands/ir/localremote/{uuid}{command}{signal}"

LOGGER = logging.getLogger(__name__)

IR_SENSOR_ID = "87"

DEVICE_TO_CODE: Final = {
    "tv": "1",
    "media": "2",
    "light": "3",
    "humidifier": "4",
    "air_purifier": "5",
    "vacuum": "6",
    "fan": "7",
    "climate_control": "EF",
}

CODE_TO_NAME: Final = {v: k for k, v in DEVICE_TO_CODE.items()}

COMMAND_TO_CODE: Final = {
    "power": "01",
    "poweron": "02",
    "poweroff": "03",
    "mode": "04",
    "mute": "05",
    "volup": "06",
    "voldown": "07",
    "chup": "08",
    "chdown": "09",
    "swing": "0A",
    "speed": "0B",
    "cursor": "0C",
    "menu": "0D",
}

POWER_CMD: Final = "power"
POWER_ON_CMD: Final = "power_on"
POWER_OFF_CMD: Final = "power_off"
