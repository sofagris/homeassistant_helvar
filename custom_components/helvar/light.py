"""Support for Helvar light devices."""
from __future__ import annotations

import logging
from typing import Any, Optional, Tuple

import aiohelvar

# Import the device class from the component that you want to support
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN as HELVAR_DOMAIN
from .router import HelvarRouter

_LOGGER = logging.getLogger(__name__)


async def asynnc_setup_platform(
    hass: HomeAssistant,
    config: dict[str, Any],
    add_entities: AddEntitiesCallback,
    discovery_info: Optional[dict[str, Any]] = None,
) -> None:
    """Not currently used."""


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Helvar lights from a config entry."""
    router: HelvarRouter = hass.data[HELVAR_DOMAIN][config_entry.entry_id]

    devices = [
        HelvarLight(device, router)
        for device in router.api.devices.get_light_devices()
    ]

    _LOGGER.info("Adding %s helvar devices", len(devices))

    async_add_entities(devices)


class HelvarLight(LightEntity):
    """Representation of a Helvar Light."""

    def __init__(self, device: aiohelvar.devices.Device, router: HelvarRouter) -> None:
        """Initialize an HelvarLight."""
        self.router = router
        self.device = device
        self._attr_rgb_color: Optional[Tuple[int, int, int]] = None
        self._attr_rgbw_color: Optional[Tuple[int, int, int, int]] = None

        # TODO: Implement proper feature detection from aiohelvar
        # For now, we'll use a minimal set of features to avoid warnings
        # Once aiohelvar supports feature detection, we should:
        # 1. Query the device for supported features
        # 2. Set supported_color_modes based on actual device capabilities
        # 3. Set initial color_mode based on current device state
        self._attr_supported_color_modes: set[ColorMode] = {ColorMode.BRIGHTNESS}
        self._attr_color_mode: ColorMode = ColorMode.BRIGHTNESS

        self.register_subscription()

    def register_subscription(self) -> None:
        """Register subscription."""

        async def async_router_callback_device(device: aiohelvar.devices.Device) -> None:
            """Handle device updates."""
            _LOGGER.debug("Received status update for %s", device)
            self.async_write_ha_state()

        self.router.api.devices.register_subscription(
            self.device.address, async_router_callback_device
        )

    @property
    def unique_id(self) -> str:
        """
        Return the unique ID of this Helvar light.

        This isn't truly unique as we do not get a serial number or MAC address from the Helvar APIs.

        We use the device's bus network address which is at least guaranteed to be unique at any point in time.

        """
        return f"{self.device.address}-light"

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self.device.name

    @property
    def brightness(self) -> Optional[int]:
        """Return the brightness of the light."""
        return self.device.brightness

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self.brightness > 0 if self.brightness is not None else False

    @property
    def color_mode(self) -> ColorMode:
        """Return the color mode of the light."""
        # TODO: Implement proper color mode detection from device state
        # For now, we'll just return BRIGHTNESS since that's what we support
        return ColorMode.BRIGHTNESS

    @property
    def rgb_color(self) -> Optional[Tuple[int, int, int]]:
        """Return the RGB color value."""
        # TODO: Implement RGB color support when aiohelvar supports it
        return None

    @property
    def rgbw_color(self) -> Optional[Tuple[int, int, int, int]]:
        """Return the RGBW color value."""
        # TODO: Implement RGBW color support when aiohelvar supports it
        return None

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        """Return supported color modes."""
        # TODO: Implement proper feature detection from aiohelvar
        # For now, we only support brightness to avoid warnings
        return self._attr_supported_color_modes

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        # TODO: Implement RGB/RGBW support when aiohelvar supports it
        # For now, we only handle brightness
        brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        await self.router.api.devices.set_device_brightness(
            self.device.address, brightness
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self.router.api.devices.set_device_brightness(self.device.address, 0)

    # async def async_update(self):
    #     """Fetch new state data for this light.

    #     This is the only method that should fetch new data for Home Assistant.
    #     """
    #     # the underlying objects are automatically updated, and all properties read directly from
    #     # those objects.
    #     return True
