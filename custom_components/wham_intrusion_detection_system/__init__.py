
"""WHAM Intrusion Detection System."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "wham_intrusion_detection_system"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the integration."""
    return True

