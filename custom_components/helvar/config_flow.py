"""Config flow for HelvarNet integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohelvar
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN, CONF_CLUSTER_ID, CONF_ROUTER_ID

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_CLUSTER_ID): cv.positive_int,
        vol.Optional(CONF_ROUTER_ID): cv.positive_int,
    }
)


@config_entries.HANDLERS.register(DOMAIN)
class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Helvar."""

    VERSION = 1

    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self):
        """Initialize the Helvar flow."""
        self.router: aiohelvar.Router | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def validate_input(
        self, hass: HomeAssistant, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate the user input allows us to connect.

        Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
        """
        router = aiohelvar.Router(
            data[CONF_HOST],
            data[CONF_PORT],
            data.get(CONF_CLUSTER_ID),
            data.get(CONF_ROUTER_ID)
        )

        try:
            await router.connect()
        except ConnectionError as initial_exception:
            raise CannotConnect() from initial_exception

        workgroup_name = router.workgroup_name
        self.router = router
        # Return info that you want to store in the config entry.
        return {"title": workgroup_name}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await self.validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
            )

        return self.async_create_entry(title=info["title"], data=user_input)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Helvar integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = {
            vol.Required(
                CONF_HOST,
                default=self.config_entry.data.get(CONF_HOST),
            ): cv.string,
            vol.Optional(
                CONF_PORT,
                default=self.config_entry.data.get(CONF_PORT, DEFAULT_PORT),
            ): cv.port,
            vol.Optional(
                CONF_CLUSTER_ID,
                default=self.config_entry.data.get(CONF_CLUSTER_ID),
            ): cv.positive_int,
            vol.Optional(
                CONF_ROUTER_ID,
                default=self.config_entry.data.get(CONF_ROUTER_ID),
            ): cv.positive_int,
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
