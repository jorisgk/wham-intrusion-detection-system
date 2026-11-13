
"""WHAM Intrusion Detection System."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.event import async_track_state_change_event

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_MEDIA_PLAYERS = "media_players"
CONF_ARTISTS = "artists"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration."""
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up the integration from a config entry."""

    players = entry.options.get(CONF_MEDIA_PLAYERS, [])
    artists = entry.options.get(CONF_ARTISTS, ["Wham!"])

    artists = [artist.casefold() for artist in artists if artist.strip()]

    muted_by_integration = set()

    async def process_player(entity_id, state):
        """Check the media title and control mute."""

        if state is None:
            return

        media_title = state.attributes.get("media_title", "") or ""
        title = media_title.casefold()

        detected = any(artist in title for artist in artists)

        if detected and entity_id not in muted_by_integration:
            already_muted = state.attributes.get("is_volume_muted", False)

            if already_muted:
                return

            try:
                await hass.services.async_call(
                    "media_player",
                    "volume_mute",
                    {
                        "entity_id": entity_id,
                        "is_volume_muted": True,
                    },
                    blocking=True,
                )

                muted_by_integration.add(entity_id)
                _LOGGER.warning(
                    "WHAM filter activated for %s. Track: %s",
                    entity_id,
                    media_title,
                )

            except Exception:
                _LOGGER.exception(
                    "Could not mute %s",
                    entity_id,
                )

        elif not detected and entity_id in muted_by_integration:
            try:
                await hass.services.async_call(
                    "media_player",
                    "volume_mute",
                    {
                        "entity_id": entity_id,
                        "is_volume_muted": False,
                    },
                    blocking=True,
                )

                muted_by_integration.remove(entity_id)
                _LOGGER.info(
                    "WHAM filter deactivated for %s",
                    entity_id,
                )

            except Exception:
                _LOGGER.exception(
                    "Could not unmute %s",
                    entity_id,
                )

    async def handle_state_change(event: Event):
        """Handle media player state changes."""

        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")

        await process_player(entity_id, new_state)

    if players:
        entry.async_on_unload(
            async_track_state_change_event(
                hass,
                players,
                handle_state_change,
            )
        )

        for entity_id in players:
            await process_player(
                entity_id,
                hass.states.get(entity_id),
            )

    entry.runtime_data = muted_by_integration
    entry.async_on_unload(
        entry.add_update_listener(async_reload_entry)
    )

    _LOGGER.info("WHAM Intrusion Detection System started.")

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload the integration."""

    muted_players = getattr(entry, "runtime_data", set())

    for entity_id in list(muted_players):
        await hass.services.async_call(
            "media_player",
            "volume_mute",
            {
                "entity_id": entity_id,
                "is_volume_muted": False,
            },
            blocking=True,
        )

    return True


async def async_reload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Reload the integration when options change."""

    await hass.config_entries.async_reload(entry.entry_id)
