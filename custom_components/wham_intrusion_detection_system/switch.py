"""WHAM protection switch."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from . import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Set up WHAM switch."""

    async_add_entities([WhamProtectionSwitch(entry)])


class WhamProtectionSwitch(SwitchEntity):
    """Control WHAM protection."""

    _attr_has_entity_name = True
    _attr_name = "WHAM IDS Beveiliging"
    _attr_icon = "mdi:shield-check"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry):
        self.runtime = entry.runtime_data
        self._attr_unique_id = f"{entry.entry_id}_protection"

    @property
    def is_on(self):
        return self.runtime.enabled

    async def async_turn_on(self, **kwargs):
        await self.runtime.set_enabled(True)

    async def async_turn_off(self, **kwargs):
        await self.runtime.set_enabled(False)

    async def async_added_to_hass(self):
        self.runtime.entities.add(self)

    async def async_will_remove_from_hass(self):
        self.runtime.entities.discard(self)
