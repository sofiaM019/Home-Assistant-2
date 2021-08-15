"""Sensor from an SQL Query."""
import datetime
import decimal
import logging
import re

import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker
import voluptuous as vol

from homeassistant.components.recorder import CONF_DB_URL, DEFAULT_DB_FILE, DEFAULT_URL
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME, CONF_UNIT_OF_MEASUREMENT, CONF_VALUE_TEMPLATE
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_COLUMN_NAME = "column"
CONF_QUERIES = "queries"
CONF_QUERY = "query"
CONF_QUERY_TEMPLATE = "query_template"

DB_URL_RE = re.compile("//.*:.*@")


def redact_credentials(data):
    """Redact credentials from string data."""
    return DB_URL_RE.sub("//****:****@", data)


def validate_sql_select(value):
    """Validate that value is a SQL SELECT query."""
    if not value.lstrip().lower().startswith("select"):
        raise vol.Invalid("Only SELECT queries allowed")
    return value


def has_at_least_one(keys):
    """Validate that one of query and query_template is defined."""

    def f(obj):
        for k in obj.keys():
            if k in keys:
                return obj
        raise vol.Invalid(f"One of {keys} must be defined")

    return f


# Defined separate schema to validate that one of query and query_template is defined
_AT_LEAST_SCHEMA = has_at_least_one([CONF_QUERY, CONF_QUERY_TEMPLATE])
_QUERY_SCHEME_OTHERS = vol.Schema(
    {
        vol.Exclusive(CONF_QUERY, "queries"): vol.All(
            cv.string
        ),  # Moved validate_sql_select to setup_platform to validate template
        vol.Exclusive(CONF_QUERY_TEMPLATE, "queries"): cv.template,
        vol.Required(CONF_COLUMN_NAME): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
        vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
    },
    required=True,
)

_QUERY_SCHEME = vol.All(_AT_LEAST_SCHEMA, _QUERY_SCHEME_OTHERS)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_QUERIES): [_QUERY_SCHEME], vol.Optional(CONF_DB_URL): cv.string}
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the SQL sensor platform."""
    db_url = config.get(CONF_DB_URL)
    if not db_url:
        db_url = DEFAULT_URL.format(hass_config_path=hass.config.path(DEFAULT_DB_FILE))

    sess = None
    try:
        engine = sqlalchemy.create_engine(db_url)
        sessmaker = scoped_session(sessionmaker(bind=engine))

        # Run a dummy query just to test the db_url
        sess = sessmaker()
        sess.execute("SELECT 1;")

    except sqlalchemy.exc.SQLAlchemyError as err:
        _LOGGER.error(
            "Couldn't connect using %s DB_URL: %s",
            redact_credentials(db_url),
            redact_credentials(str(err)),
        )
        return
    finally:
        if sess:
            sess.close()

    queries = []

    for query in config.get(CONF_QUERIES):
        name = query.get(CONF_NAME)
        query_str = query.get(CONF_QUERY)
        unit = query.get(CONF_UNIT_OF_MEASUREMENT)
        value_template = query.get(CONF_VALUE_TEMPLATE)
        column_name = query.get(CONF_COLUMN_NAME)
        query_template = query.get(CONF_QUERY_TEMPLATE)

        if query_template is not None:
            query_template.hass = hass
            query_str = query_template.async_render(parse_result=False)
        _LOGGER.debug(query_str)

        # Moved here from voluptous to check template
        validate_sql_select(query_str)

        if value_template is not None:
            value_template.hass = hass

        # MSSQL uses TOP and not LIMIT
        if not ("LIMIT" in query_str or "SELECT TOP" in query_str):
            query_str = (
                query_str.replace("SELECT", "SELECT TOP 1")
                if "mssql" in db_url
                else query_str.replace(";", " LIMIT 1;")
            )

        sensor = SQLSensor(
            name,
            sessmaker,
            query_str,
            query_template,
            column_name,
            unit,
            value_template,
        )
        queries.append(sensor)

    add_entities(queries, True)


class SQLSensor(SensorEntity):
    """Representation of an SQL sensor."""

    def __init__(
        self, name, sessmaker, query, query_template, column, unit, value_template
    ):
        """Initialize the SQL sensor."""
        self._name = name
        self._query = query
        self._query_template = query_template
        self._unit_of_measurement = unit
        self._template = value_template
        self._column_name = column
        self.sessionmaker = sessmaker
        self._state = None
        self._attributes = None

    @property
    def name(self):
        """Return the name of the query."""
        return self._name

    @property
    def native_value(self):
        """Return the query's current state."""
        return self._state

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    def update(self):
        """Retrieve sensor data from the query."""

        data = None
        try:

            if self._query_template is not None:
                self._query = self._query_template.async_render(parse_result=False)

            sess = self.sessionmaker()
            result = sess.execute(self._query)
            self._attributes = {}

            if self._query_template is not None:
                _LOGGER.debug(self._query_template)
            _LOGGER.debug(self._query)

            if not result.returns_rows or result.rowcount == 0:
                _LOGGER.warning("%s returned no results", self._query)
                self._state = None
                return

            for res in result.mappings():
                _LOGGER.debug("result = %s", res.items())
                data = res[self._column_name]
                for key, value in res.items():
                    if isinstance(value, decimal.Decimal):
                        value = float(value)
                    if isinstance(value, datetime.date):
                        value = str(value)
                    self._attributes[key] = value
        except sqlalchemy.exc.SQLAlchemyError as err:
            _LOGGER.error(
                "Error executing query %s: %s",
                self._query,
                redact_credentials(str(err)),
            )
            return
        finally:
            sess.close()

        if data is not None and self._template is not None:
            self._state = self._template.async_render_with_possible_json_value(
                data, None
            )
        else:
            self._state = data
