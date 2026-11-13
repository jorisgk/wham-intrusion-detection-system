
"""WHAM Intrusion Detection System."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event

DOMAIN = "wham_intrusion_detection_system"

CONF_MEDIA_PLAYERS = "media_players"
CONF_ARTISTS = "artists"
CONF_TTS_ENABLED = "tts_enabled"
CONF_TTS_ENTITY = "tts_entity"
CONF_TTS_LANGUAGE = "tts_language"
CONF_TTS_MESSAGE = "tts_message"

DEFAULT_TTS_LANGUAGE = "en-GB"
DEFAULT_TTS_MESSAGE = (
    "Attention! Unauthorized music detected. "
    "Wham protection activated!"
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration."""
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up the integration."""

    options = entry.options

    players = options.get(CONF_MEDIA_PLAYERS, [])
    artists = options.get(CONF_ARTISTS, ["Wham!"])

    if isinstance(artists, str):
        artists = artists.splitlines()

    artists = [
        artist.strip().casefold()
        for artist in artists
        if artist.strip()
    ]

    tts_enabled = options.get(CONF_TTS_ENABLED, True)
    tts_entity = options.get(CONF_TTS_ENTITY)
    tts_language = options.get(
        CONF_TTS_LANGUAGE, DEFAULT_TTS_LANGUAGE
    )
    tts_message = options.get(
        CONF_TTS_MESSAGE, DEFAULT_TTS_MESSAGE
    )

    muted_by_integration = set()
    processing = set()

    def is_filtered(state) -> bool:
        """Check whether the current track matches an artist."""

        if state is None:
            return False

        media_title = (
            state.attributes.get("media_title", "") or ""
        ).casefold()

        media_artist = (
            state.attributes.get("media_artist", "") or ""
        ).casefold()

        searchable = f"{media_title} {media_artist}"

        return any(artist in searchable for artist in artists)

    async def process_player(entity_id: str, state) -> None:
        """Check a player and apply the WHAM filter."""

        if entity_id in processing or state is None:
            return

        detected = is_filtered(state)

        if detected and entity_id not in muted_by_integration:
            if state.attributes.get("is_volume_muted", False):
                return

            processing.add(entity_id)

            try:
                _LOGGER.warning(
                    "WHAM filter detected a match on %s",
                    entity_id,
                )

                # Announce through the same media player if enabled.
                if tts_enabled and tts_entity:
                    try:
                        await hass.services.async_call(
                            "tts",
                            "speak",
                            {
                                "entity_id": tts_entity,
                                "media_player_entity_id": entity_id,
                                "message": tts_message,
                                "language": tts_language,
                            },
                            blocking=True,
                        )
                    except Exception:
                        _LOGGER.exception(
                            "TTS announcement failed on %s. "
                            "The player will still be muted.",
                            entity_id,
                        )
                elif tts_enabled:
                    _LOGGER.warning(
                        "TTS is enabled but no TTS entity is selected. "
                        "Muting without announcement."
                    )

                # Mute after the announcement attempt.
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

                _LOGGER.info(
                    "WHAM filter muted %s",
                    entity_id,
                )

            except Exception:
                _LOGGER.exception(
                    "Could not activate WHAM filter on %s",
                    entity_id,
                )

            finally:
                processing.discard(entity_id)

        elif not detected and entity_id in muted_by_integration:
            processing.add(entity_id)

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

                muted_by_integration.discard(entity_id)

                _LOGGER.info(
                    "WHAM filter deactivated on %s",
                    entity_id,
                )

            except Exception:
                _LOGGER.exception(
                    "Could not deactivate WHAM filter on %s",
                    entity_id,
                )

            finally:
                processing.discard(entity_id)

    async def handle_state_change(event: Event) -> None:
        """Handle media player state changes."""

        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")

        if entity_id:
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

    _LOGGER.info(
        "WHAM Intrusion Detection System started with %s players, "
        "%s artists and TTS %s.",
        len(players),
        len(artists),
        "enabled" if tts_enabled else "disabled",
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload the integration."""

    muted_players = getattr(entry, "runtime_data", set())

    for entity_id in list(muted_players):
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
        except Exception:
            _LOGGER.exception(
                "Could not unmute %s during unload",
                entity_id,
            )

    return True


async def async_reload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Reload the integration when options change."""

    await hass.config_entries.async_reload(entry.entry_id)
