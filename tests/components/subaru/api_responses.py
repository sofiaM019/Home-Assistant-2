"""Sample API response data for tests."""

from homeassistant.components.subaru.const import (
    API_GEN_1,
    API_GEN_2,
    VEHICLE_API_GEN,
    VEHICLE_HAS_EV,
    VEHICLE_HAS_REMOTE_SERVICE,
    VEHICLE_HAS_REMOTE_START,
    VEHICLE_HAS_SAFETY_SERVICE,
    VEHICLE_NAME,
    VEHICLE_VIN,
)

TEST_VIN_1_G1 = "JF2ABCDE6L0000001"
TEST_VIN_2_EV = "JF2ABCDE6L0000002"
TEST_VIN_3_G2 = "JF2ABCDE6L0000003"

VEHICLE_DATA = {
    TEST_VIN_1_G1: {
        VEHICLE_VIN: TEST_VIN_1_G1,
        VEHICLE_NAME: "test_vehicle_1",
        VEHICLE_HAS_EV: False,
        VEHICLE_API_GEN: API_GEN_1,
        VEHICLE_HAS_REMOTE_START: True,
        VEHICLE_HAS_REMOTE_SERVICE: True,
        VEHICLE_HAS_SAFETY_SERVICE: False,
    },
    TEST_VIN_2_EV: {
        VEHICLE_VIN: TEST_VIN_2_EV,
        VEHICLE_NAME: "test_vehicle_2",
        VEHICLE_HAS_EV: True,
        VEHICLE_API_GEN: API_GEN_2,
        VEHICLE_HAS_REMOTE_START: True,
        VEHICLE_HAS_REMOTE_SERVICE: True,
        VEHICLE_HAS_SAFETY_SERVICE: True,
    },
    TEST_VIN_3_G2: {
        VEHICLE_VIN: TEST_VIN_3_G2,
        VEHICLE_NAME: "test_vehicle_3",
        VEHICLE_HAS_EV: False,
        VEHICLE_API_GEN: API_GEN_2,
        VEHICLE_HAS_REMOTE_START: True,
        VEHICLE_HAS_REMOTE_SERVICE: True,
        VEHICLE_HAS_SAFETY_SERVICE: True,
    },
}

VEHICLE_STATUS_EV = {
    "status": {
        "AVG_FUEL_CONSUMPTION": 2.3,
        "BATTERY_VOLTAGE": "12.0",
        "DISTANCE_TO_EMPTY_FUEL": 707,
        "DOOR_BOOT_LOCK_STATUS": "UNKNOWN",
        "DOOR_BOOT_POSITION": "CLOSED",
        "DOOR_ENGINE_HOOD_LOCK_STATUS": "UNKNOWN",
        "DOOR_ENGINE_HOOD_POSITION": "CLOSED",
        "DOOR_FRONT_LEFT_LOCK_STATUS": "UNKNOWN",
        "DOOR_FRONT_LEFT_POSITION": "CLOSED",
        "DOOR_FRONT_RIGHT_LOCK_STATUS": "UNKNOWN",
        "DOOR_FRONT_RIGHT_POSITION": "CLOSED",
        "DOOR_REAR_LEFT_LOCK_STATUS": "UNKNOWN",
        "DOOR_REAR_LEFT_POSITION": "CLOSED",
        "DOOR_REAR_RIGHT_LOCK_STATUS": "UNKNOWN",
        "DOOR_REAR_RIGHT_POSITION": "CLOSED",
        "EV_CHARGER_STATE_TYPE": "CHARGING_STOPPED",
        "EV_CHARGE_SETTING_AMPERE_TYPE": "MAXIMUM",
        "EV_CHARGE_VOLT_TYPE": "CHARGE_LEVEL_1",
        "EV_DISTANCE_TO_EMPTY": 17,
        "EV_IS_PLUGGED_IN": "UNLOCKED_CONNECTED",
        "EV_STATE_OF_CHARGE_MODE": "EV_MODE",
        "EV_STATE_OF_CHARGE_PERCENT": "100",
        "EV_TIME_TO_FULLY_CHARGED": "65535",
        "EV_VEHICLE_TIME_DAYOFWEEK": "6",
        "EV_VEHICLE_TIME_HOUR": "14",
        "EV_VEHICLE_TIME_MINUTE": "20",
        "EV_VEHICLE_TIME_SECOND": "39",
        "EXT_EXTERNAL_TEMP": "21.5",
        "ODOMETER": 1234,
        "POSITION_HEADING_DEGREE": "150",
        "POSITION_SPEED_KMPH": "0",
        "POSITION_TIMESTAMP": 1595560000.0,
        "SEAT_BELT_STATUS_FRONT_LEFT": "BELTED",
        "SEAT_BELT_STATUS_FRONT_MIDDLE": "NOT_EQUIPPED",
        "SEAT_BELT_STATUS_FRONT_RIGHT": "BELTED",
        "SEAT_BELT_STATUS_SECOND_LEFT": "UNKNOWN",
        "SEAT_BELT_STATUS_SECOND_MIDDLE": "UNKNOWN",
        "SEAT_BELT_STATUS_SECOND_RIGHT": "UNKNOWN",
        "SEAT_BELT_STATUS_THIRD_LEFT": "UNKNOWN",
        "SEAT_BELT_STATUS_THIRD_MIDDLE": "UNKNOWN",
        "SEAT_BELT_STATUS_THIRD_RIGHT": "UNKNOWN",
        "SEAT_OCCUPATION_STATUS_FRONT_LEFT": "UNKNOWN",
        "SEAT_OCCUPATION_STATUS_FRONT_MIDDLE": "NOT_EQUIPPED",
        "SEAT_OCCUPATION_STATUS_FRONT_RIGHT": "UNKNOWN",
        "SEAT_OCCUPATION_STATUS_SECOND_LEFT": "UNKNOWN",
        "SEAT_OCCUPATION_STATUS_SECOND_MIDDLE": "UNKNOWN",
        "SEAT_OCCUPATION_STATUS_SECOND_RIGHT": "UNKNOWN",
        "SEAT_OCCUPATION_STATUS_THIRD_LEFT": "UNKNOWN",
        "SEAT_OCCUPATION_STATUS_THIRD_MIDDLE": "UNKNOWN",
        "SEAT_OCCUPATION_STATUS_THIRD_RIGHT": "UNKNOWN",
        "TIMESTAMP": 1595560000.0,
        "TRANSMISSION_MODE": "UNKNOWN",
        "TYRE_PRESSURE_FRONT_LEFT": 2550,
        "TYRE_PRESSURE_FRONT_RIGHT": 2550,
        "TYRE_PRESSURE_REAR_LEFT": 2450,
        "TYRE_PRESSURE_REAR_RIGHT": 2350,
        "TYRE_STATUS_FRONT_LEFT": "UNKNOWN",
        "TYRE_STATUS_FRONT_RIGHT": "UNKNOWN",
        "TYRE_STATUS_REAR_LEFT": "UNKNOWN",
        "TYRE_STATUS_REAR_RIGHT": "UNKNOWN",
        "VEHICLE_STATE_TYPE": "IGNITION_OFF",
        "WINDOW_BACK_STATUS": "UNKNOWN",
        "WINDOW_FRONT_LEFT_STATUS": "VENTED",
        "WINDOW_FRONT_RIGHT_STATUS": "VENTED",
        "WINDOW_REAR_LEFT_STATUS": "UNKNOWN",
        "WINDOW_REAR_RIGHT_STATUS": "UNKNOWN",
        "WINDOW_SUNROOF_STATUS": "UNKNOWN",
        "heading": 170,
        "latitude": 40.0,
        "longitude": -100.0,
    }
}

VEHICLE_STATUS_G2 = {
    "status": {
        "AVG_FUEL_CONSUMPTION": 2.3,
        "BATTERY_VOLTAGE": "12.0",
        "DISTANCE_TO_EMPTY_FUEL": 707,
        "DOOR_BOOT_LOCK_STATUS": "UNKNOWN",
        "DOOR_BOOT_POSITION": "CLOSED",
        "DOOR_ENGINE_HOOD_LOCK_STATUS": "UNKNOWN",
        "DOOR_ENGINE_HOOD_POSITION": "CLOSED",
        "DOOR_FRONT_LEFT_LOCK_STATUS": "UNKNOWN",
        "DOOR_FRONT_LEFT_POSITION": "CLOSED",
        "DOOR_FRONT_RIGHT_LOCK_STATUS": "UNKNOWN",
        "DOOR_FRONT_RIGHT_POSITION": "CLOSED",
        "DOOR_REAR_LEFT_LOCK_STATUS": "UNKNOWN",
        "DOOR_REAR_LEFT_POSITION": "CLOSED",
        "DOOR_REAR_RIGHT_LOCK_STATUS": "UNKNOWN",
        "DOOR_REAR_RIGHT_POSITION": "CLOSED",
        "EXT_EXTERNAL_TEMP": "21.5",
        "ODOMETER": 1234,
        "POSITION_HEADING_DEGREE": "150",
        "POSITION_SPEED_KMPH": "0",
        "POSITION_TIMESTAMP": 1595560000.0,
        "SEAT_BELT_STATUS_FRONT_LEFT": "BELTED",
        "SEAT_BELT_STATUS_FRONT_MIDDLE": "NOT_EQUIPPED",
        "SEAT_BELT_STATUS_FRONT_RIGHT": "BELTED",
        "SEAT_BELT_STATUS_SECOND_LEFT": "UNKNOWN",
        "SEAT_BELT_STATUS_SECOND_MIDDLE": "UNKNOWN",
        "SEAT_BELT_STATUS_SECOND_RIGHT": "UNKNOWN",
        "SEAT_BELT_STATUS_THIRD_LEFT": "UNKNOWN",
        "SEAT_BELT_STATUS_THIRD_MIDDLE": "UNKNOWN",
        "SEAT_BELT_STATUS_THIRD_RIGHT": "UNKNOWN",
        "SEAT_OCCUPATION_STATUS_FRONT_LEFT": "UNKNOWN",
        "SEAT_OCCUPATION_STATUS_FRONT_MIDDLE": "NOT_EQUIPPED",
        "SEAT_OCCUPATION_STATUS_FRONT_RIGHT": "UNKNOWN",
        "SEAT_OCCUPATION_STATUS_SECOND_LEFT": "UNKNOWN",
        "SEAT_OCCUPATION_STATUS_SECOND_MIDDLE": "UNKNOWN",
        "SEAT_OCCUPATION_STATUS_SECOND_RIGHT": "UNKNOWN",
        "SEAT_OCCUPATION_STATUS_THIRD_LEFT": "UNKNOWN",
        "SEAT_OCCUPATION_STATUS_THIRD_MIDDLE": "UNKNOWN",
        "SEAT_OCCUPATION_STATUS_THIRD_RIGHT": "UNKNOWN",
        "TIMESTAMP": 1595560000.0,
        "TRANSMISSION_MODE": "UNKNOWN",
        "TYRE_PRESSURE_FRONT_LEFT": 2550,
        "TYRE_PRESSURE_FRONT_RIGHT": 2550,
        "TYRE_PRESSURE_REAR_LEFT": 2450,
        "TYRE_PRESSURE_REAR_RIGHT": 2350,
        "TYRE_STATUS_FRONT_LEFT": "UNKNOWN",
        "TYRE_STATUS_FRONT_RIGHT": "UNKNOWN",
        "TYRE_STATUS_REAR_LEFT": "UNKNOWN",
        "TYRE_STATUS_REAR_RIGHT": "UNKNOWN",
        "VEHICLE_STATE_TYPE": "IGNITION_OFF",
        "WINDOW_BACK_STATUS": "UNKNOWN",
        "WINDOW_FRONT_LEFT_STATUS": "VENTED",
        "WINDOW_FRONT_RIGHT_STATUS": "VENTED",
        "WINDOW_REAR_LEFT_STATUS": "UNKNOWN",
        "WINDOW_REAR_RIGHT_STATUS": "UNKNOWN",
        "WINDOW_SUNROOF_STATUS": "UNKNOWN",
        "heading": 170,
        "latitude": 40.0,
        "longitude": -100.0,
    }
}

EXPECTED_STATE_EV_IMPERIAL = {
    "AVG_FUEL_CONSUMPTION": "102.3",
    "BATTERY_VOLTAGE": "12.0",
    "DISTANCE_TO_EMPTY_FUEL": "439.3",
    "EV_CHARGER_STATE_TYPE": "CHARGING_STOPPED",
    "EV_CHARGE_SETTING_AMPERE_TYPE": "MAXIMUM",
    "EV_CHARGE_VOLT_TYPE": "CHARGE_LEVEL_1",
    "EV_DISTANCE_TO_EMPTY": "17",
    "EV_IS_PLUGGED_IN": "UNLOCKED_CONNECTED",
    "EV_STATE_OF_CHARGE_MODE": "EV_MODE",
    "EV_STATE_OF_CHARGE_PERCENT": "100",
    "EV_TIME_TO_FULLY_CHARGED": "unknown",
    "EV_VEHICLE_TIME_DAYOFWEEK": "6",
    "EV_VEHICLE_TIME_HOUR": "14",
    "EV_VEHICLE_TIME_MINUTE": "20",
    "EV_VEHICLE_TIME_SECOND": "39",
    "EXT_EXTERNAL_TEMP": "70.7",
    "ODOMETER": "766.8",
    "POSITION_HEADING_DEGREE": "150",
    "POSITION_SPEED_KMPH": "0",
    "POSITION_TIMESTAMP": 1595560000.0,
    "TIMESTAMP": 1595560000.0,
    "TRANSMISSION_MODE": "UNKNOWN",
    "TYRE_PRESSURE_FRONT_LEFT": "37.0",
    "TYRE_PRESSURE_FRONT_RIGHT": "37.0",
    "TYRE_PRESSURE_REAR_LEFT": "35.5",
    "TYRE_PRESSURE_REAR_RIGHT": "34.1",
    "VEHICLE_STATE_TYPE": "IGNITION_OFF",
    "heading": 170,
    "latitude": 40.0,
    "longitude": -100.0,
}

EXPECTED_STATE_EV_METRIC = {
    "AVG_FUEL_CONSUMPTION": "2.3",
    "BATTERY_VOLTAGE": "12.0",
    "DISTANCE_TO_EMPTY_FUEL": "707",
    "EV_CHARGER_STATE_TYPE": "CHARGING_STOPPED",
    "EV_CHARGE_SETTING_AMPERE_TYPE": "MAXIMUM",
    "EV_CHARGE_VOLT_TYPE": "CHARGE_LEVEL_1",
    "EV_DISTANCE_TO_EMPTY": "27.4",
    "EV_IS_PLUGGED_IN": "UNLOCKED_CONNECTED",
    "EV_STATE_OF_CHARGE_MODE": "EV_MODE",
    "EV_STATE_OF_CHARGE_PERCENT": "100",
    "EV_TIME_TO_FULLY_CHARGED": "unknown",
    "EV_VEHICLE_TIME_DAYOFWEEK": "6",
    "EV_VEHICLE_TIME_HOUR": "14",
    "EV_VEHICLE_TIME_MINUTE": "20",
    "EV_VEHICLE_TIME_SECOND": "39",
    "EXT_EXTERNAL_TEMP": "21.5",
    "ODOMETER": "1234",
    "POSITION_HEADING_DEGREE": "150",
    "POSITION_SPEED_KMPH": "0",
    "POSITION_TIMESTAMP": 1595560000.0,
    "TIMESTAMP": 1595560000.0,
    "TRANSMISSION_MODE": "UNKNOWN",
    "TYRE_PRESSURE_FRONT_LEFT": "2550",
    "TYRE_PRESSURE_FRONT_RIGHT": "2550",
    "TYRE_PRESSURE_REAR_LEFT": "2450",
    "TYRE_PRESSURE_REAR_RIGHT": "2350",
    "VEHICLE_STATE_TYPE": "IGNITION_OFF",
    "heading": 170,
    "latitude": 40.0,
    "longitude": -100.0,
}

EXPECTED_STATE_EV_UNAVAILABLE = {
    "AVG_FUEL_CONSUMPTION": "unavailable",
    "BATTERY_VOLTAGE": "unavailable",
    "DISTANCE_TO_EMPTY_FUEL": "unavailable",
    "EV_CHARGER_STATE_TYPE": "unavailable",
    "EV_CHARGE_SETTING_AMPERE_TYPE": "unavailable",
    "EV_CHARGE_VOLT_TYPE": "unavailable",
    "EV_DISTANCE_TO_EMPTY": "unavailable",
    "EV_IS_PLUGGED_IN": "unavailable",
    "EV_STATE_OF_CHARGE_MODE": "unavailable",
    "EV_STATE_OF_CHARGE_PERCENT": "unavailable",
    "EV_TIME_TO_FULLY_CHARGED": "unavailable",
    "EV_VEHICLE_TIME_DAYOFWEEK": "unavailable",
    "EV_VEHICLE_TIME_HOUR": "unavailable",
    "EV_VEHICLE_TIME_MINUTE": "unavailable",
    "EV_VEHICLE_TIME_SECOND": "unavailable",
    "EXT_EXTERNAL_TEMP": "unavailable",
    "ODOMETER": "unavailable",
    "POSITION_HEADING_DEGREE": "unavailable",
    "POSITION_SPEED_KMPH": "unavailable",
    "POSITION_TIMESTAMP": "unavailable",
    "TIMESTAMP": "unavailable",
    "TRANSMISSION_MODE": "unavailable",
    "TYRE_PRESSURE_FRONT_LEFT": "unavailable",
    "TYRE_PRESSURE_FRONT_RIGHT": "unavailable",
    "TYRE_PRESSURE_REAR_LEFT": "unavailable",
    "TYRE_PRESSURE_REAR_RIGHT": "unavailable",
    "VEHICLE_STATE_TYPE": "unavailable",
    "heading": "unavailable",
    "latitude": "unavailable",
    "longitude": "unavailable",
}
