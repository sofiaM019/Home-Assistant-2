"""Constants used by the Withings component."""
import homeassistant.const as const

SOURCE_USER = 'user'

BASE_URL = 'base_url'
CLIENT_ID = 'client_id'
CLIENT_SECRET = 'client_secret'
CODE = 'code'
CONFIG = 'config'
CREDENTIALS = 'credentials'
DOMAIN = 'withings'
LOG_NAMESPACE = 'homeassistant.components.withings'
MEASURES = 'measures'
PROFILE = 'profile'
PROFILES = 'profiles'

AUTH_CALLBACK_PATH = '/api/withings/callback'
AUTH_CALLBACK_NAME = 'api:withings:callback'

THROTTLE_INTERVAL = 60

STATE_UNKNOWN = const.STATE_UNKNOWN
STATE_AWAKE = 'awake'
STATE_DEEP = 'deep'
STATE_LIGHT = 'light'
STATE_REM = 'rem'

MEASURE_TYPE_BODY_TEMP = 71
MEASURE_TYPE_BONE_MASS = 88
MEASURE_TYPE_DIASTOLIC_BP = 9
MEASURE_TYPE_FAT_MASS = 8
MEASURE_TYPE_FAT_MASS_FREE = 5
MEASURE_TYPE_FAT_RATIO = 6
MEASURE_TYPE_HEART_PULSE = 11
MEASURE_TYPE_HEIGHT = 4
MEASURE_TYPE_HYDRATION = 77
MEASURE_TYPE_MUSCLE_MASS = 76
MEASURE_TYPE_PWV = 91
MEASURE_TYPE_SKIN_TEMP = 73
MEASURE_TYPE_SLEEP_DEEP_DURATION = 'deepsleepduration'
MEASURE_TYPE_SLEEP_HEART_RATE_AVERAGE = 'hr_average'
MEASURE_TYPE_SLEEP_HEART_RATE_MAX = 'hr_max'
MEASURE_TYPE_SLEEP_HEART_RATE_MIN = 'hr_min'
MEASURE_TYPE_SLEEP_LIGHT_DURATION = 'lightsleepduration'
MEASURE_TYPE_SLEEP_REM_DURATION = 'remsleepduration'
MEASURE_TYPE_SLEEP_RESPIRATORY_RATE_AVERAGE = 'rr_average'
MEASURE_TYPE_SLEEP_RESPIRATORY_RATE_MAX = 'rr_max'
MEASURE_TYPE_SLEEP_RESPIRATORY_RATE_MIN = 'rr_min'
MEASURE_TYPE_SLEEP_STATE_AWAKE = 0
MEASURE_TYPE_SLEEP_STATE_DEEP = 2
MEASURE_TYPE_SLEEP_STATE_LIGHT = 1
MEASURE_TYPE_SLEEP_STATE_REM = 3
MEASURE_TYPE_SLEEP_TOSLEEP_DURATION = 'durationtosleep'
MEASURE_TYPE_SLEEP_TOWAKEUP_DURATION = 'durationtowakeup'
MEASURE_TYPE_SLEEP_WAKEUP_DURATION = 'wakeupduration'
MEASURE_TYPE_SLEEP_WAKUP_COUNT = 'wakeupcount'
MEASURE_TYPE_SPO2 = 54
MEASURE_TYPE_SYSTOLIC_BP = 10
MEASURE_TYPE_TEMP = 12
MEASURE_TYPE_WEIGHT = 1

MEAS_BODY_TEMP_AUTO = 'body_temperature_auto'
MEAS_BODY_TEMP_C = 'body_temperature_c'
MEAS_BODY_TEMP_F = 'body_temperature_f'
MEAS_BONE_MASS_KG = 'bone_mass_kg'
MEAS_BONE_MASS_LB = 'bone_mass_lb'
MEAS_BONE_MASS_STONE = 'bone_mass_st'
MEAS_DIASTOLIC_MMHG = 'diastolic_blood_pressure_mmhg'
MEAS_FAT_FREE_MASS_KG = 'fat_free_mass_kg'
MEAS_FAT_FREE_MASS_LB = 'fat_free_mass_lb'
MEAS_FAT_FREE_MASS_STONE = 'fat_free_mass_st'
MEAS_FAT_MASS_KG = 'fat_mass_kg'
MEAS_FAT_MASS_LB = 'fat_mass_lb'
MEAS_FAT_MASS_STONE = 'fat_mass_st'
MEAS_FAT_RATIO_PCT = 'fat_ratio_pct'
MEAS_HEART_PULSE_BPM = 'heart_pulse_bpm'
MEAS_HEIGHT_CM = 'height_cm'
MEAS_HEIGHT_IMP = 'height_imp'
MEAS_HEIGHT_IN = 'height_in'
MEAS_HEIGHT_M = 'height_m'
MEAS_HYDRATION = 'hydration'
MEAS_MUSCLE_MASS_KG = 'muscle_mass_kg'
MEAS_MUSCLE_MASS_LB = 'muscle_mass_lb'
MEAS_MUSCLE_MASS_STONE = 'muscle_mass_st'
MEAS_PWV = 'pulse_wave_velocity'
MEAS_SKIN_TEMP_AUTO = 'skin_temperature_auto'
MEAS_SKIN_TEMP_C = 'skin_temperature_c'
MEAS_SKIN_TEMP_F = 'skin_temperature_f'
MEAS_SLEEP_DEEP_DURATION_HOURS = 'sleep_deep_duration_hours'
MEAS_SLEEP_DEEP_DURATION_MINUTES = 'sleep_deep_duration_minutes'
MEAS_SLEEP_HEART_RATE_AVERAGE = 'sleep_heart_rate_average_bpm'
MEAS_SLEEP_HEART_RATE_MAX = 'sleep_heart_rate_max_bpm'
MEAS_SLEEP_HEART_RATE_MIN = 'sleep_heart_rate_min_bpm'
MEAS_SLEEP_LIGHT_DURATION_HOURS = 'sleep_light_duration_hours'
MEAS_SLEEP_LIGHT_DURATION_MINUTES = 'sleep_light_duration_minutes'
MEAS_SLEEP_REM_DURATION_HOURS = 'sleep_rem_duration_hours'
MEAS_SLEEP_REM_DURATION_MINUTES = 'sleep_rem_duration_minutes'
MEAS_SLEEP_RESPIRATORY_RATE_AVERAGE = 'sleep_respiratory_average_bpm'
MEAS_SLEEP_RESPIRATORY_RATE_MAX = 'sleep_respiratory_max_bpm'
MEAS_SLEEP_RESPIRATORY_RATE_MIN = 'sleep_respiratory_min_bpm'
MEAS_SLEEP_STATE = 'sleep_state'
MEAS_SLEEP_TOSLEEP_DURATION_HOURS = 'sleep_tosleep_duration_hours'
MEAS_SLEEP_TOSLEEP_DURATION_MINUTES = 'sleep_tosleep_duration_minutes'
MEAS_SLEEP_TOWAKEUP_DURATION_HOURS = 'sleep_towakeup_duration_hours'
MEAS_SLEEP_TOWAKEUP_DURATION_MINUTES = 'sleep_towakeup_duration_minutes'
MEAS_SLEEP_WAKEUP_COUNT = 'sleep_wakeup_count'
MEAS_SLEEP_WAKEUP_DURATION_HOURS = 'sleep_wakeup_duration_hours'
MEAS_SLEEP_WAKEUP_DURATION_MINUTES = 'sleep_wakeup_duration_minutes'
MEAS_SPO2_PCT = 'spo2_pct'
MEAS_SYSTOLIC_MMGH = 'systolic_blood_pressure_mmhg'
MEAS_TEMP_AUTO = 'temperature_auto'
MEAS_TEMP_C = 'temperature_c'
MEAS_TEMP_F = 'temperature_f'
MEAS_WEIGHT_KG = 'weight_kg'
MEAS_WEIGHT_LB = 'weight_lb'
MEAS_WEIGHT_STONE = 'weight_st'

UOM_BEATS_PER_MINUTE = 'bpm'
UOM_BREATHS_PER_MINUTE = 'br/m'
UOM_FREQUENCY = 'times'
UOM_HOURS = 'hrs'
UOM_IMPERIAL_HEIGHT = 'height'
UOM_METERS_PER_SECOND = 'm/s'
UOM_MINUTES = 'mins'
UOM_MMHG = 'mmhg'
UOM_PERCENT = '%'
UOM_MASS_STONE = 'st'
UOM_LENGTH_CM = const.LENGTH_CENTIMETERS
UOM_LENGTH_IN = const.LENGTH_INCHES
UOM_LENGTH_M = const.LENGTH_METERS
UOM_MASS_KG = const.MASS_KILOGRAMS
UOM_MASS_LB = const.MASS_POUNDS
UOM_TEMP_C = const.TEMP_CELSIUS
UOM_TEMP_F = const.TEMP_FAHRENHEIT
