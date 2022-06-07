"""Common stuff for Fritz!Tools tests."""
from homeassistant.components import ssdp
from homeassistant.components.fritz.const import DOMAIN
from homeassistant.components.ssdp import ATTR_UPNP_FRIENDLY_NAME, ATTR_UPNP_UDN
from homeassistant.const import (
    CONF_DEVICES,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)

ATTR_HOST = "host"
ATTR_NEW_SERIAL_NUMBER = "NewSerialNumber"

MOCK_CONFIG = {
    DOMAIN: {
        CONF_DEVICES: [
            {
                CONF_HOST: "fake_host",
                CONF_PORT: "1234",
                CONF_PASSWORD: "fake_pass",
                CONF_USERNAME: "fake_user",
            }
        ]
    }
}
MOCK_HOST = "fake_host"
MOCK_IPS = {"fritz.box": "192.168.178.1", "printer": "192.168.178.2"}
MOCK_MODELNAME = "FRITZ!Box 7530 AX"
MOCK_FIRMWARE = "256.07.29"
MOCK_FIRMWARE_AVAILABLE = "256.07.50"
MOCK_FIRMWARE_RELEASE_URL = (
    "http://download.avm.de/fritzbox/fritzbox-7530-ax/deutschland/fritz.os/info_de.txt"
)
MOCK_SERIAL_NUMBER = "fake_serial_number"
MOCK_FIRMWARE_INFO = [True, "1.1.1", "some-release-url"]
MOCK_MESH_SSID = "TestSSID"
MOCK_MESH_MASTER_MAC = "1C:ED:6F:12:34:11"
MOCK_MESH_MASTER_WIFI1_MAC = "1C:ED:6F:12:34:12"
MOCK_MESH_SLAVE_MAC = "1C:ED:6F:12:34:21"
MOCK_MESH_SLAVE_WIFI1_MAC = "1C:ED:6F:12:34:22"

MOCK_FB_SERVICES: dict[str, dict] = {
    "DeviceInfo1": {
        "GetInfo": {
            "NewSerialNumber": MOCK_MESH_MASTER_MAC,
            "NewName": "TheName",
            "NewModelName": MOCK_MODELNAME,
            "NewSoftwareVersion": MOCK_FIRMWARE,
            "NewUpTime": 2518179,
        },
    },
    "Hosts1": {
        "GetGenericHostEntry": [
            {
                "NewIPAddress": MOCK_IPS["fritz.box"],
                "NewAddressSource": "Static",
                "NewLeaseTimeRemaining": 0,
                "NewMACAddress": MOCK_MESH_MASTER_MAC,
                "NewInterfaceType": "",
                "NewActive": True,
                "NewHostName": "fritz.box",
            },
            {
                "NewIPAddress": MOCK_IPS["printer"],
                "NewAddressSource": "DHCP",
                "NewLeaseTimeRemaining": 0,
                "NewMACAddress": "AA:BB:CC:00:11:22",
                "NewInterfaceType": "Ethernet",
                "NewActive": True,
                "NewHostName": "printer",
            },
        ],
        "X_AVM-DE_GetMeshListPath": {},
    },
    "LANEthernetInterfaceConfig1": {
        "GetStatistics": {
            "NewBytesSent": 23004321,
            "NewBytesReceived": 12045,
        },
    },
    "Layer3Forwarding1": {
        "GetDefaultConnectionService": {
            "NewDefaultConnectionService": "1.WANPPPConnection.1"
        }
    },
    "UserInterface1": {
        "GetInfo": {},
    },
    "WANCommonIFC1": {
        "GetCommonLinkProperties": {
            "NewLayer1DownstreamMaxBitRate": 10087000,
            "NewLayer1UpstreamMaxBitRate": 2105000,
            "NewPhysicalLinkStatus": "Up",
        },
        "GetAddonInfos": {
            "NewByteSendRate": 3438,
            "NewByteReceiveRate": 67649,
            "NewTotalBytesSent": 1712232562,
            "NewTotalBytesReceived": 5221019883,
            "NewX_AVM_DE_TotalBytesSent64": 1712232562,
            "NeWX_AVM_DE_TotalBytesReceived64": 5221019883,
        },
        "GetTotalBytesSent": {"NewTotalBytesSent": 1712232562},
        "GetTotalBytesReceived": {"NewTotalBytesReceived": 5221019883},
    },
    "WANCommonInterfaceConfig1": {
        "GetCommonLinkProperties": {
            "NewWANAccessType": "DSL",
            "NewLayer1UpstreamMaxBitRate": 51805000,
            "NewLayer1DownstreamMaxBitRate": 318557000,
            "NewPhysicalLinkStatus": "Up",
        }
    },
    "WANDSLInterfaceConfig1": {
        "GetInfo": {
            "NewEnable": True,
            "NewStatus": "Up",
            "NewDataPath": "Interleaved",
            "NewUpstreamCurrRate": 46720,
            "NewDownstreamCurrRate": 292030,
            "NewUpstreamMaxRate": 51348,
            "NewDownstreamMaxRate": 315978,
            "NewUpstreamNoiseMargin": 90,
            "NewDownstreamNoiseMargin": 80,
            "NewUpstreamAttenuation": 70,
            "NewDownstreamAttenuation": 120,
            "NewATURVendor": "41564d00",
            "NewATURCountry": "0400",
            "NewUpstreamPower": 500,
            "NewDownstreamPower": 500,
        }
    },
    "WANIPConn1": {
        "GetStatusInfo": {
            "NewConnectionStatus": "Connected",
            "NewUptime": 35307,
        },
        "GetExternalIPAddress": {"NewExternalIPAddress": "1.2.3.4"},
    },
    "WANPPPConnection1": {
        "GetInfo": {
            "NewEnable": True,
            "NewConnectionStatus": "Connected",
            "NewUptime": 57199,
            "NewUpstreamMaxBitRate": 46531924,
            "NewDownstreamMaxBitRate": 43430530,
            "NewExternalIPAddress": "1.2.3.4",
        },
        "GetPortMappingNumberOfEntries": {},
    },
    "X_AVM-DE_Homeauto1": {
        "GetGenericDeviceInfos": [
            {
                "NewSwitchIsValid": "VALID",
                "NewMultimeterIsValid": "VALID",
                "NewTemperatureIsValid": "VALID",
                "NewDeviceId": 16,
                "NewAIN": "08761 0114116",
                "NewDeviceName": "FRITZ!DECT 200 #1",
                "NewTemperatureOffset": "0",
                "NewSwitchLock": "0",
                "NewProductName": "FRITZ!DECT 200",
                "NewPresent": "CONNECTED",
                "NewMultimeterPower": 1673,
                "NewHkrComfortTemperature": "0",
                "NewSwitchMode": "AUTO",
                "NewManufacturer": "AVM",
                "NewMultimeterIsEnabled": "ENABLED",
                "NewHkrIsTemperature": "0",
                "NewFunctionBitMask": 2944,
                "NewTemperatureIsEnabled": "ENABLED",
                "NewSwitchState": "ON",
                "NewSwitchIsEnabled": "ENABLED",
                "NewFirmwareVersion": "03.87",
                "NewHkrSetVentilStatus": "CLOSED",
                "NewMultimeterEnergy": 5182,
                "NewHkrComfortVentilStatus": "CLOSED",
                "NewHkrReduceTemperature": "0",
                "NewHkrReduceVentilStatus": "CLOSED",
                "NewHkrIsEnabled": "DISABLED",
                "NewHkrSetTemperature": "0",
                "NewTemperatureCelsius": "225",
                "NewHkrIsValid": "INVALID",
            },
            {},
        ],
    },
    "X_AVM-DE_HostFilter1": {
        "GetWANAccessByIP": {
            MOCK_IPS["printer"]: {"NewDisallow": False, "NewWANAccess": "granted"}
        }
    },
}

MOCK_MESH_DATA = {
    "schema_version": "1.9",
    "nodes": [
        {
            "uid": "n-1",
            "device_name": "fritz.box",
            "device_model": "FRITZ!Box 7530 AX",
            "device_manufacturer": "AVM",
            "device_firmware_version": "256.07.29",
            "device_mac_address": MOCK_MESH_MASTER_MAC,
            "is_meshed": True,
            "mesh_role": "master",
            "meshd_version": "3.13",
            "node_interfaces": [
                {
                    "uid": "ni-5",
                    "name": "LANBridge",
                    "type": "LAN",
                    "mac_address": MOCK_MESH_MASTER_MAC,
                    "blocking_state": "NOT_BLOCKED",
                    "node_links": [],
                },
                {
                    "uid": "ni-30",
                    "name": "LAN:2",
                    "type": "LAN",
                    "mac_address": MOCK_MESH_MASTER_MAC,
                    "blocking_state": "NOT_BLOCKED",
                    "node_links": [],
                },
                {
                    "uid": "ni-32",
                    "name": "LAN:3",
                    "type": "LAN",
                    "mac_address": MOCK_MESH_MASTER_MAC,
                    "blocking_state": "NOT_BLOCKED",
                    "node_links": [],
                },
                {
                    "uid": "ni-31",
                    "name": "LAN:1",
                    "type": "LAN",
                    "mac_address": MOCK_MESH_MASTER_MAC,
                    "blocking_state": "NOT_BLOCKED",
                    "node_links": [
                        {
                            "uid": "nl-78",
                            "type": "LAN",
                            "state": "CONNECTED",
                            "last_connected": 1642872967,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-76",
                            "node_interface_1_uid": "ni-31",
                            "node_interface_2_uid": "ni-77",
                            "max_data_rate_rx": 1000000,
                            "max_data_rate_tx": 1000000,
                            "cur_data_rate_rx": 0,
                            "cur_data_rate_tx": 0,
                            "cur_availability_rx": 99,
                            "cur_availability_tx": 99,
                        }
                    ],
                },
                {
                    "uid": "ni-33",
                    "name": "LAN:4",
                    "type": "LAN",
                    "mac_address": MOCK_MESH_MASTER_MAC,
                    "blocking_state": "NOT_BLOCKED",
                    "node_links": [],
                },
                {
                    "uid": "ni-230",
                    "name": "AP:2G:0",
                    "type": "WLAN",
                    "mac_address": MOCK_MESH_MASTER_WIFI1_MAC,
                    "blocking_state": "UNKNOWN",
                    "node_links": [
                        {
                            "uid": "nl-219",
                            "type": "WLAN",
                            "state": "CONNECTED",
                            "last_connected": 1644618820,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-89",
                            "node_interface_1_uid": "ni-230",
                            "node_interface_2_uid": "ni-90",
                            "max_data_rate_rx": 72200,
                            "max_data_rate_tx": 72200,
                            "cur_data_rate_rx": 54000,
                            "cur_data_rate_tx": 65000,
                            "cur_availability_rx": 100,
                            "cur_availability_tx": 100,
                            "rx_rsni": 51,
                            "tx_rsni": 255,
                            "rx_rcpi": -38,
                            "tx_rcpi": 255,
                        },
                        {
                            "uid": "nl-168",
                            "type": "WLAN",
                            "state": "CONNECTED",
                            "last_connected": 1645162418,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-118",
                            "node_interface_1_uid": "ni-230",
                            "node_interface_2_uid": "ni-119",
                            "max_data_rate_rx": 144400,
                            "max_data_rate_tx": 144400,
                            "cur_data_rate_rx": 144400,
                            "cur_data_rate_tx": 130000,
                            "cur_availability_rx": 100,
                            "cur_availability_tx": 100,
                            "rx_rsni": 37,
                            "tx_rsni": 255,
                            "rx_rcpi": -52,
                            "tx_rcpi": 255,
                        },
                        {
                            "uid": "nl-185",
                            "type": "WLAN",
                            "state": "CONNECTED",
                            "last_connected": 1645273363,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-100",
                            "node_interface_1_uid": "ni-230",
                            "node_interface_2_uid": "ni-99",
                            "max_data_rate_rx": 72200,
                            "max_data_rate_tx": 72200,
                            "cur_data_rate_rx": 1000,
                            "cur_data_rate_tx": 1000,
                            "cur_availability_rx": 100,
                            "cur_availability_tx": 100,
                            "rx_rsni": 35,
                            "tx_rsni": 255,
                            "rx_rcpi": -54,
                            "tx_rcpi": 255,
                        },
                        {
                            "uid": "nl-166",
                            "type": "WLAN",
                            "state": "CONNECTED",
                            "last_connected": 1644618912,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-16",
                            "node_interface_1_uid": "ni-230",
                            "node_interface_2_uid": "ni-15",
                            "max_data_rate_rx": 72200,
                            "max_data_rate_tx": 72200,
                            "cur_data_rate_rx": 54000,
                            "cur_data_rate_tx": 65000,
                            "cur_availability_rx": 100,
                            "cur_availability_tx": 100,
                            "rx_rsni": 41,
                            "tx_rsni": 255,
                            "rx_rcpi": -48,
                            "tx_rcpi": 255,
                        },
                        {
                            "uid": "nl-239",
                            "type": "WLAN",
                            "state": "CONNECTED",
                            "last_connected": 1644618828,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-59",
                            "node_interface_1_uid": "ni-230",
                            "node_interface_2_uid": "ni-58",
                            "max_data_rate_rx": 72200,
                            "max_data_rate_tx": 72200,
                            "cur_data_rate_rx": 54000,
                            "cur_data_rate_tx": 65000,
                            "cur_availability_rx": 100,
                            "cur_availability_tx": 100,
                            "rx_rsni": 43,
                            "tx_rsni": 255,
                            "rx_rcpi": -46,
                            "tx_rcpi": 255,
                        },
                        {
                            "uid": "nl-173",
                            "type": "WLAN",
                            "state": "CONNECTED",
                            "last_connected": 1645331764,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-137",
                            "node_interface_1_uid": "ni-230",
                            "node_interface_2_uid": "ni-138",
                            "max_data_rate_rx": 72200,
                            "max_data_rate_tx": 72200,
                            "cur_data_rate_rx": 72200,
                            "cur_data_rate_tx": 65000,
                            "cur_availability_rx": 100,
                            "cur_availability_tx": 100,
                            "rx_rsni": 38,
                            "tx_rsni": 255,
                            "rx_rcpi": -51,
                            "tx_rcpi": 255,
                        },
                        {
                            "uid": "nl-217",
                            "type": "WLAN",
                            "state": "CONNECTED",
                            "last_connected": 1644618833,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-128",
                            "node_interface_1_uid": "ni-230",
                            "node_interface_2_uid": "ni-127",
                            "max_data_rate_rx": 72200,
                            "max_data_rate_tx": 72200,
                            "cur_data_rate_rx": 54000,
                            "cur_data_rate_tx": 72200,
                            "cur_availability_rx": 100,
                            "cur_availability_tx": 100,
                            "rx_rsni": 41,
                            "tx_rsni": 255,
                            "rx_rcpi": -48,
                            "tx_rcpi": 255,
                        },
                        {
                            "uid": "nl-198",
                            "type": "WLAN",
                            "state": "CONNECTED",
                            "last_connected": 1644618820,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-105",
                            "node_interface_1_uid": "ni-230",
                            "node_interface_2_uid": "ni-106",
                            "max_data_rate_rx": 72200,
                            "max_data_rate_tx": 72200,
                            "cur_data_rate_rx": 48000,
                            "cur_data_rate_tx": 58500,
                            "cur_availability_rx": 100,
                            "cur_availability_tx": 100,
                            "rx_rsni": 28,
                            "tx_rsni": 255,
                            "rx_rcpi": -61,
                            "tx_rcpi": 255,
                        },
                        {
                            "uid": "nl-213",
                            "type": "WLAN",
                            "state": "CONNECTED",
                            "last_connected": 1644618820,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-111",
                            "node_interface_1_uid": "ni-230",
                            "node_interface_2_uid": "ni-112",
                            "max_data_rate_rx": 72200,
                            "max_data_rate_tx": 72200,
                            "cur_data_rate_rx": 48000,
                            "cur_data_rate_tx": 1000,
                            "cur_availability_rx": 100,
                            "cur_availability_tx": 100,
                            "rx_rsni": 44,
                            "tx_rsni": 255,
                            "rx_rcpi": -45,
                            "tx_rcpi": 255,
                        },
                        {
                            "uid": "nl-224",
                            "type": "WLAN",
                            "state": "CONNECTED",
                            "last_connected": 1644618831,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-197",
                            "node_interface_1_uid": "ni-230",
                            "node_interface_2_uid": "ni-196",
                            "max_data_rate_rx": 72200,
                            "max_data_rate_tx": 72200,
                            "cur_data_rate_rx": 48000,
                            "cur_data_rate_tx": 1000,
                            "cur_availability_rx": 100,
                            "cur_availability_tx": 100,
                            "rx_rsni": 51,
                            "tx_rsni": 255,
                            "rx_rcpi": -38,
                            "tx_rcpi": 255,
                        },
                        {
                            "uid": "nl-182",
                            "type": "WLAN",
                            "state": "CONNECTED",
                            "last_connected": 1644618822,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-56",
                            "node_interface_1_uid": "ni-230",
                            "node_interface_2_uid": "ni-55",
                            "max_data_rate_rx": 72200,
                            "max_data_rate_tx": 72200,
                            "cur_data_rate_rx": 54000,
                            "cur_data_rate_tx": 72200,
                            "cur_availability_rx": 100,
                            "cur_availability_tx": 100,
                            "rx_rsni": 34,
                            "tx_rsni": 255,
                            "rx_rcpi": -55,
                            "tx_rcpi": 255,
                        },
                        {
                            "uid": "nl-205",
                            "type": "WLAN",
                            "state": "CONNECTED",
                            "last_connected": 1644618820,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-109",
                            "node_interface_1_uid": "ni-230",
                            "node_interface_2_uid": "ni-108",
                            "max_data_rate_rx": 72200,
                            "max_data_rate_tx": 72200,
                            "cur_data_rate_rx": 54000,
                            "cur_data_rate_tx": 1000,
                            "cur_availability_rx": 100,
                            "cur_availability_tx": 100,
                            "rx_rsni": 43,
                            "tx_rsni": 255,
                            "rx_rcpi": -46,
                            "tx_rcpi": 255,
                        },
                        {
                            "uid": "nl-240",
                            "type": "WLAN",
                            "state": "CONNECTED",
                            "last_connected": 1644618827,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-95",
                            "node_interface_1_uid": "ni-230",
                            "node_interface_2_uid": "ni-96",
                            "max_data_rate_rx": 72200,
                            "max_data_rate_tx": 72200,
                            "cur_data_rate_rx": 48000,
                            "cur_data_rate_tx": 58500,
                            "cur_availability_rx": 100,
                            "cur_availability_tx": 100,
                            "rx_rsni": 25,
                            "tx_rsni": 255,
                            "rx_rcpi": -64,
                            "tx_rcpi": 255,
                        },
                        {
                            "uid": "nl-146",
                            "type": "WLAN",
                            "state": "CONNECTED",
                            "last_connected": 1642872967,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-167",
                            "node_interface_1_uid": "ni-230",
                            "node_interface_2_uid": "ni-134",
                            "max_data_rate_rx": 144400,
                            "max_data_rate_tx": 144400,
                            "cur_data_rate_rx": 144400,
                            "cur_data_rate_tx": 130000,
                            "cur_availability_rx": 100,
                            "cur_availability_tx": 100,
                            "rx_rsni": 48,
                            "tx_rsni": 255,
                            "rx_rcpi": -41,
                            "tx_rcpi": 255,
                        },
                        {
                            "uid": "nl-232",
                            "type": "WLAN",
                            "state": "CONNECTED",
                            "last_connected": 1644618829,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-18",
                            "node_interface_1_uid": "ni-230",
                            "node_interface_2_uid": "ni-17",
                            "max_data_rate_rx": 72200,
                            "max_data_rate_tx": 72200,
                            "cur_data_rate_rx": 48000,
                            "cur_data_rate_tx": 21700,
                            "cur_availability_rx": 100,
                            "cur_availability_tx": 100,
                            "rx_rsni": 22,
                            "tx_rsni": 255,
                            "rx_rcpi": -67,
                            "tx_rcpi": 255,
                        },
                    ],
                    "ssid": MOCK_MESH_SSID,
                    "opmode": "AP",
                    "security": "WPA2_WPA3_MIXED",
                    "supported_streams_tx": [
                        ["20 MHz", 2],
                        ["40 MHz", 0],
                        ["80 MHz", 0],
                        ["160 MHz", 0],
                        ["80+80 MHz", 0],
                    ],
                    "supported_streams_rx": [
                        ["20 MHz", 2],
                        ["40 MHz", 0],
                        ["80 MHz", 0],
                        ["160 MHz", 0],
                        ["80+80 MHz", 0],
                    ],
                    "current_channel": 13,
                    "phymodes": ["g", "n", "ax"],
                    "channel_utilization": 0,
                    "anpi": -91,
                    "steering_enabled": True,
                    "11k_friendly": True,
                    "11v_friendly": True,
                    "legacy_friendly": True,
                    "rrm_compliant": False,
                    "channel_list": [
                        {"channel": 1},
                        {"channel": 2},
                        {"channel": 3},
                        {"channel": 4},
                        {"channel": 5},
                        {"channel": 6},
                        {"channel": 7},
                        {"channel": 8},
                        {"channel": 9},
                        {"channel": 10},
                        {"channel": 11},
                        {"channel": 12},
                        {"channel": 13},
                    ],
                },
            ],
        },
        {
            "uid": "n-76",
            "device_name": "printer",
            "device_model": "",
            "device_manufacturer": "",
            "device_firmware_version": "",
            "device_mac_address": "AA:BB:CC:00:11:22",
            "is_meshed": False,
            "mesh_role": "unknown",
            "meshd_version": "0.0",
            "node_interfaces": [
                {
                    "uid": "ni-77",
                    "name": "eth0",
                    "type": "LAN",
                    "mac_address": "AA:BB:CC:00:11:22",
                    "blocking_state": "UNKNOWN",
                    "node_links": [
                        {
                            "uid": "nl-78",
                            "type": "LAN",
                            "state": "CONNECTED",
                            "last_connected": 1642872967,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-76",
                            "node_interface_1_uid": "ni-31",
                            "node_interface_2_uid": "ni-77",
                            "max_data_rate_rx": 1000000,
                            "max_data_rate_tx": 1000000,
                            "cur_data_rate_rx": 0,
                            "cur_data_rate_tx": 0,
                            "cur_availability_rx": 99,
                            "cur_availability_tx": 99,
                        }
                    ],
                }
            ],
        },
        {
            "uid": "n-167",
            "device_name": "fritz-repeater",
            "device_model": "FRITZ!Box 7490",
            "device_manufacturer": "AVM",
            "device_firmware_version": "113.07.29",
            "device_mac_address": MOCK_MESH_SLAVE_MAC,
            "is_meshed": True,
            "mesh_role": "slave",
            "meshd_version": "3.13",
            "node_interfaces": [
                {
                    "uid": "ni-140",
                    "name": "LAN:3",
                    "type": "LAN",
                    "mac_address": MOCK_MESH_SLAVE_MAC,
                    "blocking_state": "UNKNOWN",
                    "node_links": [],
                },
                {
                    "uid": "ni-139",
                    "name": "LAN:4",
                    "type": "LAN",
                    "mac_address": MOCK_MESH_SLAVE_MAC,
                    "blocking_state": "UNKNOWN",
                    "node_links": [],
                },
                {
                    "uid": "ni-141",
                    "name": "LAN:2",
                    "type": "LAN",
                    "mac_address": MOCK_MESH_SLAVE_MAC,
                    "blocking_state": "UNKNOWN",
                    "node_links": [],
                },
                {
                    "uid": "ni-134",
                    "name": "UPLINK:2G:0",
                    "type": "WLAN",
                    "mac_address": MOCK_MESH_SLAVE_WIFI1_MAC,
                    "blocking_state": "UNKNOWN",
                    "node_links": [
                        {
                            "uid": "nl-146",
                            "type": "WLAN",
                            "state": "CONNECTED",
                            "last_connected": 1642872967,
                            "node_1_uid": "n-1",
                            "node_2_uid": "n-167",
                            "node_interface_1_uid": "ni-230",
                            "node_interface_2_uid": "ni-134",
                            "max_data_rate_rx": 144400,
                            "max_data_rate_tx": 144400,
                            "cur_data_rate_rx": 144400,
                            "cur_data_rate_tx": 130000,
                            "cur_availability_rx": 100,
                            "cur_availability_tx": 100,
                            "rx_rsni": 48,
                            "tx_rsni": 255,
                            "rx_rcpi": -41,
                            "tx_rcpi": 255,
                        }
                    ],
                    "ssid": "",
                    "opmode": "WDS_REPEATER",
                    "security": "WPA3PSK",
                    "supported_streams_tx": [
                        ["20 MHz", 3],
                        ["40 MHz", 3],
                        ["80 MHz", 0],
                        ["160 MHz", 0],
                        ["80+80 MHz", 0],
                    ],
                    "supported_streams_rx": [
                        ["20 MHz", 3],
                        ["40 MHz", 3],
                        ["80 MHz", 0],
                        ["160 MHz", 0],
                        ["80+80 MHz", 0],
                    ],
                    "current_channel": 13,
                    "phymodes": ["b", "g", "n"],
                    "channel_utilization": 0,
                    "anpi": 255,
                    "steering_enabled": True,
                    "11k_friendly": False,
                    "11v_friendly": True,
                    "legacy_friendly": True,
                    "rrm_compliant": False,
                    "channel_list": [
                        {"channel": 1},
                        {"channel": 2},
                        {"channel": 3},
                        {"channel": 4},
                        {"channel": 5},
                        {"channel": 6},
                        {"channel": 7},
                        {"channel": 8},
                        {"channel": 9},
                        {"channel": 10},
                        {"channel": 11},
                        {"channel": 12},
                        {"channel": 13},
                    ],
                    "client_position": "unknown",
                },
                {
                    "uid": "ni-143",
                    "name": "LANBridge",
                    "type": "LAN",
                    "mac_address": MOCK_MESH_SLAVE_MAC,
                    "blocking_state": "UNKNOWN",
                    "node_links": [],
                },
                {
                    "uid": "ni-142",
                    "name": "LAN:1",
                    "type": "LAN",
                    "mac_address": MOCK_MESH_SLAVE_MAC,
                    "blocking_state": "UNKNOWN",
                    "node_links": [],
                },
            ],
        },
    ],
}


MOCK_USER_DATA = MOCK_CONFIG[DOMAIN][CONF_DEVICES][0]
MOCK_DEVICE_INFO = {
    ATTR_HOST: MOCK_HOST,
    ATTR_NEW_SERIAL_NUMBER: MOCK_SERIAL_NUMBER,
}
MOCK_SSDP_DATA = ssdp.SsdpServiceInfo(
    ssdp_usn="mock_usn",
    ssdp_st="mock_st",
    ssdp_location=f"https://{MOCK_IPS['fritz.box']}:12345/test",
    upnp={
        ATTR_UPNP_FRIENDLY_NAME: "fake_name",
        ATTR_UPNP_UDN: "uuid:only-a-test",
    },
)

MOCK_REQUEST = b'<?xml version="1.0" encoding="utf-8"?><SessionInfo><SID>xxxxxxxxxxxxxxxx</SID><Challenge>xxxxxxxx</Challenge><BlockTime>0</BlockTime><Rights><Name>Dial</Name><Access>2</Access><Name>App</Name><Access>2</Access><Name>HomeAuto</Name><Access>2</Access><Name>BoxAdmin</Name><Access>2</Access><Name>Phone</Name><Access>2</Access><Name>NAS</Name><Access>2</Access></Rights><Users><User last="1">FakeFritzUser</User></Users></SessionInfo>\n'
