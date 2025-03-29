"""Helvar Router."""
import logging
import re
import aiohelvar

from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_HOST, CONF_PORT, CONF_CLUSTER_ID, CONF_ROUTER_ID

_LOGGER = logging.getLogger(__name__)


class HelvarRouter:
    """Manages a Helvar Router."""

    def __init__(self, hass, config_entry):
        """Initialize the system."""
        self.config_entry = config_entry
        self.hass = hass
        self.available = True
        self.api = None

    @property
    def host(self):
        """Return the host of this router."""
        return self.config_entry.data[CONF_HOST]

    @property
    def port(self):
        """Return the host of this router."""
        return self.config_entry.data[CONF_PORT]

    @property
    def cluster_id(self):
        """Return the cluster id of this router."""
        return self.config_entry.data.get(CONF_CLUSTER_ID)

    @property
    def router_id(self):
        """Return the router id of this router."""
        return self.config_entry.data.get(CONF_ROUTER_ID)

    async def async_setup(self, tries=0):
        """Set up a helvar router based on host parameter."""
        host = self.host
        port = self.port
        cluster_id = self.cluster_id
        router_id = self.router_id
        hass = self.hass

        # Assume that host is in the format of 192.168.x.y
        # if not, try to resolve ip from host like this
        # Requires socket library
        # Test if host is an ip address

        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", host):
            ip = host
        else:
            import socket
            try:
                ip = socket.gethostbyname(host)
            except socket.gaierror:
                _LOGGER.error("Error resolving host %s", host)
                raise ConfigEntryNotReady

        if cluster_id is None:
            cluster_id = ip.split(".")[2]
        if router_id is None:
            router_id = ip.split(".")[3]

        router = aiohelvar.Router(host, port, cluster_id, router_id)

        try:
            await router.connect()
            await router.initialize()

        except ConnectionError as err:
            _LOGGER.error("Error connecting to the Helvar router at %s", host)
            raise ConfigEntryNotReady from err

        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unknown error connecting with Helvar router at %s", host)
            return False

        self.api = router
        # self.sensor_manager = SensorManager(self)

        # Set up platforms
        await hass.config_entries.async_forward_entry_setups(
            self.config_entry, ["light", "select"]
        )

        return True
