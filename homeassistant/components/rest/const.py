"""The rest component constants."""

DOMAIN = "rest"

DEFAULT_METHOD = "GET"
DEFAULT_VERIFY_SSL = True
DEFAULT_FORCE_UPDATE = False

DEFAULT_BINARY_SENSOR_NAME = "REST Binary Sensor"
DEFAULT_SENSOR_NAME = "REST Sensor"
CONF_JSON_ATTRS = "json_attributes"
CONF_JSON_ATTRS_PATH = "json_attributes_path"

REST_IDX = "rest_idx"
PLATFORM_IDX = "platform_idx"

COORDINATOR = "coordinator"
REST = "rest"

REST_DATA = "rest_data"

METHODS = ["POST", "GET"]

XML_MIME_TYPES = (
    "application/atom+xml",
    "application/rdf+xml",
    "application/rss+xml",
    "application/x-rss+xml",
    "application/xhtml+xml",
    "application/xml",
    "text/xml",
)
