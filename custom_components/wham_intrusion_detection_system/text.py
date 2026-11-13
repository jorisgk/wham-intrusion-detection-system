"""WHAM blocked artists text entity."""

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from . import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Set up WHAM text entity."""

    async_add_entities([WhamBlockedArtistsText(entry)])


class WhamBlockedArtistsText(TextEntity):
    """Edit the blocked artist list."""

    _attr_has_entity_name = True
    _attr_name = "WHAM IDS Geblokkeerde artiesten"
    _attr_icon = "mdi:music"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = TextMode.TEXT
    _attr_native_min = 0
    _attr_native_max = 255

    def __init__(self, entry):
        self.runtime = entry.runtime_data
        self._attr_unique_id = f"{entry.entry_id}_blocked_artists"

    @property
    def native_value(self):
        return ", ".join(self.runtime.artists)

    async def async_set_value(self, value):
        artists = [
            artist.strip()
            for artist in value.replace("\n", ",").split(",")
            if artist.strip()
        ]

        await self.runtime.set_artists(artists)

    async def async_added_to_hass(self):
        self.runtime.entities.add(self)

    async def async_will_remove_from_hass(self):
        self.runtime.entities.discard(self)
