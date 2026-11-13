"""WHAM detection binary sensor."""

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Set up WHAM detection sensor."""

    async_add_entities([WhamDetectionSensor(entry)])


class WhamDetectionSensor(BinarySensorEntity):
    """Show whether WHAM intrusion is detected."""

    _attr_has_entity_name = True
    _attr_name = "WHAM IDS Detectie"
    _attr_icon = "mdi:alert-octagon"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, entry):
        self.runtime = entry.runtime_data
        self._attr_unique_id = f"{entry.entry_id}_detection"

    @property
    def is_on(self):
        return bool(self.runtime.detected_players)

    async def async_added_to_hass(self):
        self.runtime.entities.add(self)

    async def async_will_remove_from_hass(self):
        self.runtime.entities.discard(self)
