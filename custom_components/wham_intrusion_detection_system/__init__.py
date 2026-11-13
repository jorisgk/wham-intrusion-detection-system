"""WHAM Intrusion Detection System."""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

DOMAIN = "wham_intrusion_detection_system"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the WHAM Intrusion Detection System integration."""
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up WHAM IDS from a config entry."""
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload WHAM IDS."""
    return True
