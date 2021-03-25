"""Tracks devices by sending a ICMP echo request (ping)."""
from datetime import timedelta
import logging
import subprocess
import sys

from icmplib import NameLookupError, ping as icmp_ping
import voluptuous as vol

from homeassistant import const, util
from homeassistant.components.device_tracker import PLATFORM_SCHEMA
from homeassistant.components.device_tracker.const import (
    CONF_SCAN_INTERVAL,
    SCAN_INTERVAL,
    SOURCE_TYPE_ROUTER,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.util.async_ import run_callback_threadsafe
from homeassistant.util.process import kill_subprocess

from . import async_get_next_ping_id, can_use_icmp_lib_with_privilege
from .const import ICMP_TIMEOUT, PING_ATTEMPTS_COUNT, PING_TIMEOUT

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0
CONF_PING_COUNT = "count"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(const.CONF_HOSTS): {cv.slug: cv.string},
        vol.Optional(CONF_PING_COUNT, default=1): cv.positive_int,
    }
)


class Host:
    """A single host to track."""

    def __init__(self, ip_address, dev_id, hass, config):
        """Initialize the Host pinger."""
        self.hass = hass
        self.ip_address = ip_address
        self.dev_id = dev_id
        self._count = config[CONF_PING_COUNT]


class HostSubProcess(Host):
    """Host object with ping detection."""

    def __init__(self, ip_address, dev_id, hass, config, privileged):
        """Initialize the Host pinger."""
        super().__init__(ip_address, dev_id, hass, config)
        if sys.platform == "win32":
            self._ping_cmd = ["ping", "-n", "1", "-w", "1000", ip_address]
        else:
            self._ping_cmd = ["ping", "-n", "-q", "-c1", "-W1", ip_address]

    def ping(self):
        """Send an ICMP echo request and return True if success."""
        pinger = subprocess.Popen(
            self._ping_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        try:
            pinger.communicate(timeout=1 + PING_TIMEOUT)
            return pinger.returncode == 0
        except subprocess.TimeoutExpired:
            kill_subprocess(pinger)
            return False

        except subprocess.CalledProcessError:
            return False

    def update(self, see):
        """Update device state by sending one or more ping messages."""
        failed = 0
        while failed < self._count:  # check more times if host is unreachable
            if self.ping():
                see(dev_id=self.dev_id, source_type=SOURCE_TYPE_ROUTER)
                return True
            failed += 1

        _LOGGER.debug("No response from %s failed=%d", self.ip_address, failed)


class HostICMPLib(Host):
    """Host object with ping detection."""

    def __init__(self, ip_address, dev_id, hass, config, privileged):
        """Initialize the Host pinger."""
        super().__init__(ip_address, dev_id, hass, config)
        self._privileged = privileged

    def ping(self):
        """Send an ICMP echo request and return True if success."""
        next_id = run_callback_threadsafe(
            self.hass.loop, async_get_next_ping_id, self.hass
        ).result()

        try:
            data = icmp_ping(
                self.ip_address,
                count=PING_ATTEMPTS_COUNT,
                timeout=ICMP_TIMEOUT,
                privileged=self._privileged,
                id=next_id,
            )
        except NameLookupError:
            return False

        return data.is_alive

    def update(self, see):
        """Update device state by sending one or more ping messages."""
        if self.ping():
            see(dev_id=self.dev_id, source_type=SOURCE_TYPE_ROUTER)
            return True

        _LOGGER.debug(
            "No response from %s (%s) failed=%d",
            self.ip_address,
            self.dev_id,
            PING_ATTEMPTS_COUNT,
        )


def setup_scanner(hass, config, see, discovery_info=None):
    """Set up the Host objects and return the update function."""

    privileged = can_use_icmp_lib_with_privilege()
    if privileged is None:
        host_cls = HostSubProcess
    else:
        host_cls = HostICMPLib

    hosts = [
        host_cls(ip, dev_id, hass, config, privileged)
        for (dev_id, ip) in config[const.CONF_HOSTS].items()
    ]
    interval = config.get(
        CONF_SCAN_INTERVAL,
        timedelta(seconds=len(hosts) * config[CONF_PING_COUNT]) + SCAN_INTERVAL,
    )
    _LOGGER.debug(
        "Started ping tracker with interval=%s on hosts: %s",
        interval,
        ",".join([host.ip_address for host in hosts]),
    )

    def update_interval(now):
        """Update all the hosts on every interval time."""
        try:
            for host in hosts:
                host.update(see)
        finally:
            hass.helpers.event.track_point_in_utc_time(
                update_interval, util.dt.utcnow() + interval
            )

    update_interval(None)
    return True
