"""Z-Wave Constants."""

ATTR_NODE_ID = "node_id"
ATTR_TARGET_NODE_ID = "target_node_id"
ATTR_ASSOCIATION = "association"
ATTR_INSTANCE = "instance"
ATTR_GROUP = "group"
ATTR_VALUE_ID = "value_id"
ATTR_OBJECT_ID = "object_id"
ATTR_NAME = "name"
ATTR_SCENE_ID = "scene_id"
ATTR_BASIC_LEVEL = "basic_level"
ATTR_CONFIG_PARAMETER = "parameter"
ATTR_CONFIG_SIZE = "size"
ATTR_CONFIG_VALUE = "value"
NETWORK_READY_WAIT_SECS = 30

DISCOVERY_DEVICE = 'device'

SERVICE_CHANGE_ASSOCIATION = "change_association"
SERVICE_ADD_NODE = "add_node"
SERVICE_ADD_NODE_SECURE = "add_node_secure"
SERVICE_REMOVE_NODE = "remove_node"
SERVICE_CANCEL_COMMAND = "cancel_command"
SERVICE_HEAL_NETWORK = "heal_network"
SERVICE_SOFT_RESET = "soft_reset"
SERVICE_TEST_NETWORK = "test_network"
SERVICE_SET_CONFIG_PARAMETER = "set_config_parameter"
SERVICE_PRINT_CONFIG_PARAMETER = "print_config_parameter"
SERVICE_PRINT_NODE = "print_node"
SERVICE_REMOVE_FAILED_NODE = "remove_failed_node"
SERVICE_REPLACE_FAILED_NODE = "replace_failed_node"
SERVICE_SET_WAKEUP = "set_wakeup"
SERVICE_STOP_NETWORK = "stop_network"
SERVICE_START_NETWORK = "start_network"
SERVICE_RENAME_NODE = "rename_node"

EVENT_SCENE_ACTIVATED = "zwave.scene_activated"
EVENT_NODE_EVENT = "zwave.node_event"
EVENT_NETWORK_READY = "zwave.network_ready"
EVENT_NETWORK_COMPLETE = "zwave.network_complete"
EVENT_NETWORK_START = "zwave.network_start"
EVENT_NETWORK_STOP = "zwave.network_stop"

COMMAND_CLASS_ALARM = 113
COMMAND_CLASS_ANTITHEFT = 93
COMMAND_CLASS_APPLICATION_CAPABILITY = 87
COMMAND_CLASS_APPLICATION_STATUS = 34
COMMAND_CLASS_ASSOCIATION = 133
COMMAND_CLASS_ASSOCIATION_COMMAND_CONFIGURATION = 155
COMMAND_CLASS_ASSOCIATION_GRP_INFO = 89
COMMAND_CLASS_BARRIER_OPERATOR = 102
COMMAND_CLASS_BASIC = 32
COMMAND_CLASS_BASIC_TARIFF_INFO = 54
COMMAND_CLASS_BASIC_WINDOW_COVERING = 80
COMMAND_CLASS_BATTERY = 128
COMMAND_CLASS_CENTRAL_SCENE = 91
COMMAND_CLASS_CLIMATE_CONTROL_SCHEDULE = 70
COMMAND_CLASS_CLOCK = 129
COMMAND_CLASS_CONFIGURATION = 112
COMMAND_CLASS_CONTROLLER_REPLICATION = 33
COMMAND_CLASS_CRC_16_ENCAP = 86
COMMAND_CLASS_DCP_CONFIG = 58
COMMAND_CLASS_DCP_MONITOR = 59
COMMAND_CLASS_DEVICE_RESET_LOCALLY = 90
COMMAND_CLASS_DOOR_LOCK = 98
COMMAND_CLASS_DOOR_LOCK_LOGGING = 76
COMMAND_CLASS_ENERGY_PRODUCTION = 144
COMMAND_CLASS_ENTRY_CONTROL = 111
COMMAND_CLASS_FIRMWARE_UPDATE_MD = 122
COMMAND_CLASS_GEOGRAPHIC_LOCATION = 140
COMMAND_CLASS_GROUPING_NAME = 123
COMMAND_CLASS_HAIL = 130
COMMAND_CLASS_HRV_CONTROL = 57
COMMAND_CLASS_HRV_STATUS = 55
COMMAND_CLASS_HUMIDITY_CONTROL_MODE = 109
COMMAND_CLASS_HUMIDITY_CONTROL_OPERATING_STATE = 110
COMMAND_CLASS_HUMIDITY_CONTROL_SETPOINT = 100
COMMAND_CLASS_INDICATOR = 135
COMMAND_CLASS_IP_ASSOCIATION = 92
COMMAND_CLASS_IP_CONFIGURATION = 14
COMMAND_CLASS_IRRIGATION = 107
COMMAND_CLASS_LANGUAGE = 137
COMMAND_CLASS_LOCK = 118
COMMAND_CLASS_MAILBOX = 105
COMMAND_CLASS_MANUFACTURER_PROPRIETARY = 145
COMMAND_CLASS_MANUFACTURER_SPECIFIC = 114
COMMAND_CLASS_MARK = 239
COMMAND_CLASS_METER = 50
COMMAND_CLASS_METER_PULSE = 53
COMMAND_CLASS_METER_TBL_CONFIG = 60
COMMAND_CLASS_METER_TBL_MONITOR = 61
COMMAND_CLASS_METER_TBL_PUSH = 62
COMMAND_CLASS_MTP_WINDOW_COVERING = 81
COMMAND_CLASS_MULTI_CHANNEL = 96
COMMAND_CLASS_MULTI_CHANNEL_ASSOCIATION = 142
COMMAND_CLASS_MULTI_COMMAND = 143
COMMAND_CLASS_NETWORK_MANAGEMENT_BASIC = 77
COMMAND_CLASS_NETWORK_MANAGEMENT_INCLUSION = 52
COMMAND_CLASS_NETWORK_MANAGEMENT_PRIMARY = 84
COMMAND_CLASS_NETWORK_MANAGEMENT_PROXY = 82
COMMAND_CLASS_NO_OPERATION = 0
COMMAND_CLASS_NODE_NAMING = 119
COMMAND_CLASS_NON_INTEROPERABLE = 240
COMMAND_CLASS_NOTIFICATION = 113
COMMAND_CLASS_POWERLEVEL = 115
COMMAND_CLASS_PREPAYMENT = 63
COMMAND_CLASS_PREPAYMENT_ENCAPSULATION = 65
COMMAND_CLASS_PROPRIETARY = 136
COMMAND_CLASS_PROTECTION = 117
COMMAND_CLASS_RATE_TBL_CONFIG = 72
COMMAND_CLASS_RATE_TBL_MONITOR = 73
COMMAND_CLASS_REMOTE_ASSOCIATION_ACTIVATE = 124
COMMAND_CLASS_REMOTE_ASSOCIATION = 125
COMMAND_CLASS_SCENE_ACTIVATION = 43
COMMAND_CLASS_SCENE_ACTUATOR_CONF = 44
COMMAND_CLASS_SCENE_CONTROLLER_CONF = 45
COMMAND_CLASS_SCHEDULE = 83
COMMAND_CLASS_SCHEDULE_ENTRY_LOCK = 78
COMMAND_CLASS_SCREEN_ATTRIBUTES = 147
COMMAND_CLASS_SCREEN_MD = 146
COMMAND_CLASS_SECURITY = 152
COMMAND_CLASS_SECURITY_SCHEME0_MARK = 61696
COMMAND_CLASS_SENSOR_ALARM = 156
COMMAND_CLASS_SENSOR_BINARY = 48
COMMAND_CLASS_SENSOR_CONFIGURATION = 158
COMMAND_CLASS_SENSOR_MULTILEVEL = 49
COMMAND_CLASS_SILENCE_ALARM = 157
COMMAND_CLASS_SIMPLE_AV_CONTROL = 148
COMMAND_CLASS_SUPERVISION = 108
COMMAND_CLASS_SWITCH_ALL = 39
COMMAND_CLASS_SWITCH_BINARY = 37
COMMAND_CLASS_SWITCH_COLOR = 51
COMMAND_CLASS_SWITCH_MULTILEVEL = 38
COMMAND_CLASS_SWITCH_TOGGLE_BINARY = 40
COMMAND_CLASS_SWITCH_TOGGLE_MULTILEVEL = 41
COMMAND_CLASS_TARIFF_TBL_CONFIG = 74
COMMAND_CLASS_TARIFF_TBL_MONITOR = 75
COMMAND_CLASS_THERMOSTAT_FAN_MODE = 68
COMMAND_CLASS_THERMOSTAT_FAN_STATE = 69
COMMAND_CLASS_THERMOSTAT_MODE = 64
COMMAND_CLASS_THERMOSTAT_OPERATING_STATE = 66
COMMAND_CLASS_THERMOSTAT_SETBACK = 71
COMMAND_CLASS_THERMOSTAT_SETPOINT = 67
COMMAND_CLASS_TIME = 138
COMMAND_CLASS_TIME_PARAMETERS = 139
COMMAND_CLASS_TRANSPORT_SERVICE = 85
COMMAND_CLASS_USER_CODE = 99
COMMAND_CLASS_VERSION = 134
COMMAND_CLASS_WAKE_UP = 132
COMMAND_CLASS_ZIP = 35
COMMAND_CLASS_ZIP_NAMING = 104
COMMAND_CLASS_ZIP_ND = 88
COMMAND_CLASS_ZIP_6LOWPAN = 79
COMMAND_CLASS_ZIP_GATEWAY = 95
COMMAND_CLASS_ZIP_PORTAL = 97
COMMAND_CLASS_ZWAVEPLUS_INFO = 94
COMMAND_CLASS_WHATEVER = None  # Match ALL
COMMAND_CLASS_WINDOW_COVERING = 106

GENERIC_TYPE_WHATEVER = None  # Match ALL
SPECIFIC_TYPE_WHATEVER = None  # Match ALL
SPECIFIC_TYPE_NOT_USED = 0  # Available in all Generic types

GENERIC_TYPE_AV_CONTROL_POINT = 3
SPECIFIC_TYPE_DOORBELL = 18
SPECIFIC_TYPE_SATELLITE_RECIEVER = 4
SPECIFIC_TYPE_SATELLITE_RECIEVER_V2 = 17

GENERIC_TYPE_DISPLAY = 4
SPECIFIC_TYPE_SIMPLE_DISPLAY = 1

GENERIC_TYPE_ENTRY_CONTROL = 64
SPECIFIC_TYPE_DOOR_LOCK = 1
SPECIFIC_TYPE_ADVANCED_DOOR_LOCK = 2
SPECIFIC_TYPE_SECURE_KEYPAD_DOOR_LOCK = 3
SPECIFIC_TYPE_SECURE_KEYPAD_DOOR_LOCK_DEADBOLT = 4
SPECIFIC_TYPE_SECURE_DOOR = 5
SPECIFIC_TYPE_SECURE_GATE = 6
SPECIFIC_TYPE_SECURE_BARRIER_ADDON = 7
SPECIFIC_TYPE_SECURE_BARRIER_OPEN_ONLY = 8
SPECIFIC_TYPE_SECURE_BARRIER_CLOSE_ONLY = 9
SPECIFIC_TYPE_SECURE_LOCKBOX = 10
SPECIFIC_TYPE_SECURE_KEYPAD = 11

GENERIC_TYPE_GENERIC_CONTROLLER = 1
SPECIFIC_TYPE_PORTABLE_CONTROLLER = 1
SPECIFIC_TYPE_PORTABLE_SCENE_CONTROLLER = 2
SPECIFIC_TYPE_PORTABLE_INSTALLER_TOOL = 3
SPECIFIC_TYPE_REMOTE_CONTROL_AV = 4
SPECIFIC_TYPE_REMOTE_CONTROL_SIMPLE = 6

GENERIC_TYPE_METER = 49
SPECIFIC_TYPE_SIMPLE_METER = 1
SPECIFIC_TYPE_ADV_ENERGY_CONTROL = 2
SPECIFIC_TYPE_WHOLE_HOME_METER_SIMPLE = 3

GENERIC_TYPE_METER_PULSE = 48

GENERIC_TYPE_NON_INTEROPERABLE = 255

GENERIC_TYPE_REPEATER_SLAVE = 15
SPECIFIC_TYPE_REPEATER_SLAVE = 1
SPECIFIC_TYPE_VIRTUAL_NODE = 2

GENERIC_TYPE_SECURITY_PANEL = 23
SPECIFIC_TYPE_ZONED_SECURITY_PANEL = 1

GENERIC_TYPE_SEMI_INTEROPERABLE = 80
SPECIFIC_TYPE_ENERGY_PRODUCTION = 1

GENERIC_TYPE_SENSOR_ALARM = 161
SPECIFIC_TYPE_ADV_ZENSOR_NET_ALARM_SENSOR = 5
SPECIFIC_TYPE_ADV_ZENSOR_NET_SMOKE_SENSOR = 10
SPECIFIC_TYPE_BASIC_ROUTING_ALARM_SENSOR = 1
SPECIFIC_TYPE_BASIC_ROUTING_SMOKE_SENSOR = 6
SPECIFIC_TYPE_BASIC_ZENSOR_NET_ALARM_SENSOR = 3
SPECIFIC_TYPE_BASIC_ZENSOR_NET_SMOKE_SENSOR = 8
SPECIFIC_TYPE_ROUTING_ALARM_SENSOR = 2
SPECIFIC_TYPE_ROUTING_SMOKE_SENSOR = 7
SPECIFIC_TYPE_ZENSOR_NET_ALARM_SENSOR = 4
SPECIFIC_TYPE_ZENSOR_NET_SMOKE_SENSOR = 9
SPECIFIC_TYPE_ALARM_SENSOR = 11

GENERIC_TYPE_SENSOR_BINARY = 32
SPECIFIC_TYPE_ROUTING_SENSOR_BINARY = 1

GENERIC_TYPE_SENSOR_MULTILEVEL = 33
SPECIFIC_TYPE_ROUTING_SENSOR_MULTILEVEL = 1
SPECIFIC_TYPE_CHIMNEY_FAN = 2

GENERIC_TYPE_STATIC_CONTROLLER = 2
SPECIFIC_TYPE_PC_CONTROLLER = 1
SPECIFIC_TYPE_SCENE_CONTROLLER = 2
SPECIFIC_TYPE_STATIC_INSTALLER_TOOL = 3
SPECIFIC_TYPE_SET_TOP_BOX = 4
SPECIFIC_TYPE_SUB_SYSTEM_CONTROLLER = 5
SPECIFIC_TYPE_TV = 6
SPECIFIC_TYPE_GATEWAY = 7

GENERIC_TYPE_SWITCH_BINARY = 16
SPECIFIC_TYPE_POWER_SWITCH_BINARY = 1
SPECIFIC_TYPE_SCENE_SWITCH_BINARY = 3
SPECIFIC_TYPE_POWER_STRIP = 4
SPECIFIC_TYPE_SIREN = 5
SPECIFIC_TYPE_VALVE_OPEN_CLOSE = 6
SPECIFIC_TYPE_COLOR_TUNABLE_BINARY = 2
SPECIFIC_TYPE_IRRIGATION_CONTROLLER = 7

GENERIC_TYPE_SWITCH_MULTILEVEL = 17
SPECIFIC_TYPE_CLASS_A_MOTOR_CONTROL = 5
SPECIFIC_TYPE_CLASS_B_MOTOR_CONTROL = 6
SPECIFIC_TYPE_CLASS_C_MOTOR_CONTROL = 7
SPECIFIC_TYPE_MOTOR_MULTIPOSITION = 3
SPECIFIC_TYPE_POWER_SWITCH_MULTILEVEL = 1
SPECIFIC_TYPE_SCENE_SWITCH_MULTILEVEL = 4
SPECIFIC_TYPE_FAN_SWITCH = 8
SPECIFIC_TYPE_COLOR_TUNABLE_MULTILEVEL = 2

GENERIC_TYPE_SWITCH_REMOTE = 18
SPECIFIC_TYPE_REMOTE_BINARY = 1
SPECIFIC_TYPE_REMOTE_MULTILEVEL = 2
SPECIFIC_TYPE_REMOTE_TOGGLE_BINARY = 3
SPECIFIC_TYPE_REMOTE_TOGGLE_MULTILEVEL = 4

GENERIC_TYPE_SWITCH_TOGGLE = 19
SPECIFIC_TYPE_SWITCH_TOGGLE_BINARY = 1
SPECIFIC_TYPE_SWITCH_TOGGLE_MULTILEVEL = 2

GENERIC_TYPE_THERMOSTAT = 8
SPECIFIC_TYPE_SETBACK_SCHEDULE_THERMOSTAT = 3
SPECIFIC_TYPE_SETBACK_THERMOSTAT = 5
SPECIFIC_TYPE_SETPOINT_THERMOSTAT = 4
SPECIFIC_TYPE_THERMOSTAT_GENERAL = 2
SPECIFIC_TYPE_THERMOSTAT_GENERAL_V2 = 6
SPECIFIC_TYPE_THERMOSTAT_HEATING = 1

GENERIC_TYPE_VENTILATION = 22
SPECIFIC_TYPE_RESIDENTIAL_HRV = 1

GENERIC_TYPE_WINDOWS_COVERING = 9
SPECIFIC_TYPE_SIMPLE_WINDOW_COVERING = 1

GENERIC_TYPE_ZIP_NODE = 21
SPECIFIC_TYPE_ZIP_ADV_NODE = 2
SPECIFIC_TYPE_ZIP_TUN_NODE = 1

GENERIC_TYPE_WALL_CONTROLLER = 24
SPECIFIC_TYPE_BASIC_WALL_CONTROLLER = 1

GENERIC_TYPE_NETWORK_EXTENDER = 5
SPECIFIC_TYPE_SECURE_EXTENDER = 1

GENERIC_TYPE_APPLIANCE = 6
SPECIFIC_TYPE_GENERAL_APPLIANCE = 1
SPECIFIC_TYPE_KITCHEN_APPLIANCE = 2
SPECIFIC_TYPE_LAUNDRY_APPLIANCE = 3

GENERIC_TYPE_SENSOR_NOTIFICATION = 7
SPECIFIC_TYPE_NOTIFICATION_SENSOR = 1

GENRE_WHATEVER = None
GENRE_USER = "User"
GENRE_SYSTEM = "System"

TYPE_WHATEVER = None
TYPE_BYTE = "Byte"
TYPE_BOOL = "Bool"
TYPE_DECIMAL = "Decimal"
TYPE_INT = "Int"
TYPE_LIST = "List"
