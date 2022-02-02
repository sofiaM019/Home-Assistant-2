"""Constants for ebus component."""
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    ENERGY_KILO_WATT_HOUR,
    PERCENTAGE,
    PRESSURE_BAR,
    TEMP_CELSIUS,
    TIME_SECONDS,
)

DOMAIN = "ebusd"

#  SensorTypes from ebusdpy module :
#  0='decimal', 1='time-schedule', 2='switch', 3='string', 4='value;status'

SENSOR_TYPES = {
    "700": {
        "ActualFlowTemperatureDesired": [
            "Hc1ActualFlowTempDesired",
            TEMP_CELSIUS,
            None,
            0,
            SensorDeviceClass.TEMPERATURE,
        ],
        "MaxFlowTemperatureDesired": [
            "Hc1MaxFlowTempDesired",
            TEMP_CELSIUS,
            None,
            0,
            SensorDeviceClass.TEMPERATURE,
        ],
        "MinFlowTemperatureDesired": [
            "Hc1MinFlowTempDesired",
            TEMP_CELSIUS,
            None,
            0,
            SensorDeviceClass.TEMPERATURE,
        ],
        "PumpStatus": ["Hc1PumpStatus", None, "mdi:toggle-switch", 2, None],
        "HCSummerTemperatureLimit": [
            "Hc1SummerTempLimit",
            TEMP_CELSIUS,
            "mdi:weather-sunny",
            0,
            SensorDeviceClass.TEMPERATURE,
        ],
        "HolidayTemperature": [
            "HolidayTemp",
            TEMP_CELSIUS,
            None,
            0,
            SensorDeviceClass.TEMPERATURE,
        ],
        "HWTemperatureDesired": [
            "HwcTempDesired",
            TEMP_CELSIUS,
            None,
            0,
            SensorDeviceClass.TEMPERATURE,
        ],
        "HWActualTemperature": [
            "HwcStorageTemp",
            TEMP_CELSIUS,
            None,
            0,
            SensorDeviceClass.TEMPERATURE,
        ],
        "HWTimerMonday": ["hwcTimer.Monday", None, "mdi:timer-outline", 1, None],
        "HWTimerTuesday": ["hwcTimer.Tuesday", None, "mdi:timer-outline", 1, None],
        "HWTimerWednesday": ["hwcTimer.Wednesday", None, "mdi:timer-outline", 1, None],
        "HWTimerThursday": ["hwcTimer.Thursday", None, "mdi:timer-outline", 1, None],
        "HWTimerFriday": ["hwcTimer.Friday", None, "mdi:timer-outline", 1, None],
        "HWTimerSaturday": ["hwcTimer.Saturday", None, "mdi:timer-outline", 1, None],
        "HWTimerSunday": ["hwcTimer.Sunday", None, "mdi:timer-outline", 1, None],
        "HWOperativeMode": ["HwcOpMode", None, "mdi:math-compass", 3, None],
        "WaterPressure": ["WaterPressure", PRESSURE_BAR, "mdi:water-pump", 0, None],
        "Zone1RoomZoneMapping": ["z1RoomZoneMapping", None, "mdi:label", 0, None],
        "Zone1NightTemperature": [
            "z1NightTemp",
            TEMP_CELSIUS,
            "mdi:weather-night",
            0,
            SensorDeviceClass.TEMPERATURE,
        ],
        "Zone1DayTemperature": [
            "z1DayTemp",
            TEMP_CELSIUS,
            "mdi:weather-sunny",
            0,
            SensorDeviceClass.TEMPERATURE,
        ],
        "Zone1HolidayTemperature": [
            "z1HolidayTemp",
            TEMP_CELSIUS,
            None,
            0,
            SensorDeviceClass.TEMPERATURE,
        ],
        "Zone1RoomTemperature": [
            "z1RoomTemp",
            TEMP_CELSIUS,
            None,
            0,
            SensorDeviceClass.TEMPERATURE,
        ],
        "Zone1ActualRoomTemperatureDesired": [
            "z1ActualRoomTempDesired",
            TEMP_CELSIUS,
            None,
            0,
            SensorDeviceClass.TEMPERATURE,
        ],
        "Zone1TimerMonday": ["z1Timer.Monday", None, "mdi:timer-outline", 1, None],
        "Zone1TimerTuesday": ["z1Timer.Tuesday", None, "mdi:timer-outline", 1, None],
        "Zone1TimerWednesday": [
            "z1Timer.Wednesday",
            None,
            "mdi:timer-outline",
            1,
            None,
        ],
        "Zone1TimerThursday": ["z1Timer.Thursday", None, "mdi:timer-outline", 1, None],
        "Zone1TimerFriday": ["z1Timer.Friday", None, "mdi:timer-outline", 1, None],
        "Zone1TimerSaturday": ["z1Timer.Saturday", None, "mdi:timer-outline", 1, None],
        "Zone1TimerSunday": ["z1Timer.Sunday", None, "mdi:timer-outline", 1, None],
        "Zone1OperativeMode": ["z1OpMode", None, "mdi:math-compass", 3, None],
        "ContinuosHeating": [
            "ContinuosHeating",
            TEMP_CELSIUS,
            "mdi:weather-snowy",
            0,
            SensorDeviceClass.TEMPERATURE,
        ],
        "PowerEnergyConsumptionLastMonth": [
            "PrEnergySumHcLastMonth",
            ENERGY_KILO_WATT_HOUR,
            "mdi:flash",
            0,
            None,
        ],
        "PowerEnergyConsumptionThisMonth": [
            "PrEnergySumHcThisMonth",
            ENERGY_KILO_WATT_HOUR,
            "mdi:flash",
            0,
            None,
        ],
    },
    "ehp": {
        "HWTemperature": [
            "HwcTemp",
            TEMP_CELSIUS,
            None,
            4,
            SensorDeviceClass.TEMPERATURE,
        ],
        "OutsideTemp": [
            "OutsideTemp",
            TEMP_CELSIUS,
            None,
            4,
            SensorDeviceClass.TEMPERATURE,
        ],
    },
    "bai": {
        "HotWaterTemperature": [
            "HwcTemp",
            TEMP_CELSIUS,
            None,
            4,
            SensorDeviceClass.TEMPERATURE,
        ],
        "StorageTemperature": [
            "StorageTemp",
            TEMP_CELSIUS,
            None,
            4,
            SensorDeviceClass.TEMPERATURE,
        ],
        "DesiredStorageTemperature": [
            "StorageTempDesired",
            TEMP_CELSIUS,
            None,
            0,
            SensorDeviceClass.TEMPERATURE,
        ],
        "OutdoorsTemperature": [
            "OutdoorstempSensor",
            TEMP_CELSIUS,
            None,
            4,
            SensorDeviceClass.TEMPERATURE,
        ],
        "WaterPreasure": ["WaterPressure", PRESSURE_BAR, "mdi:pipe", 4, None],
        "AverageIgnitionTime": [
            "averageIgnitiontime",
            TIME_SECONDS,
            "mdi:av-timer",
            0,
            None,
        ],
        "MaximumIgnitionTime": [
            "maxIgnitiontime",
            TIME_SECONDS,
            "mdi:av-timer",
            0,
            None,
        ],
        "MinimumIgnitionTime": [
            "minIgnitiontime",
            TIME_SECONDS,
            "mdi:av-timer",
            0,
            None,
        ],
        "ReturnTemperature": [
            "ReturnTemp",
            TEMP_CELSIUS,
            None,
            4,
            SensorDeviceClass.TEMPERATURE,
        ],
        "CentralHeatingPump": ["WP", None, "mdi:toggle-switch", 2, None],
        "HeatingSwitch": ["HeatingSwitch", None, "mdi:toggle-switch", 2, None],
        "DesiredFlowTemperature": [
            "FlowTempDesired",
            TEMP_CELSIUS,
            None,
            0,
            SensorDeviceClass.TEMPERATURE,
        ],
        "FlowTemperature": [
            "FlowTemp",
            TEMP_CELSIUS,
            None,
            4,
            SensorDeviceClass.TEMPERATURE,
        ],
        "Flame": ["Flame", None, "mdi:toggle-switch", 2, None],
        "PowerEnergyConsumptionHeatingCircuit": [
            "PrEnergySumHc1",
            ENERGY_KILO_WATT_HOUR,
            "mdi:flash",
            0,
            None,
        ],
        "PowerEnergyConsumptionHotWaterCircuit": [
            "PrEnergySumHwc1",
            ENERGY_KILO_WATT_HOUR,
            "mdi:flash",
            0,
            None,
        ],
        "RoomThermostat": ["DCRoomthermostat", None, "mdi:toggle-switch", 2, None],
        "HeatingPartLoad": [
            "PartloadHcKW",
            ENERGY_KILO_WATT_HOUR,
            "mdi:flash",
            0,
            None,
        ],
        "StateNumber": ["StateNumber", None, "mdi:fire", 3, None],
        "ModulationPercentage": [
            "ModulationTempDesired",
            PERCENTAGE,
            "mdi:percent",
            0,
            None,
        ],
    },
}
