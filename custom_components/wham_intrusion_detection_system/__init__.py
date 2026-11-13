"""WHAM Intrusion Detection System."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event

DOMAIN = "wham_intrusion_detection_system"

PLATFORMS = ["switch", "text", "binary_sensor"]

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


class WhamRuntime:
    """Store runtime data and handle WHAM detection."""

    def __init__(
        self,
        hass,
        players,
        artists,
        tts_enabled,
        tts_entity,
        tts_language,
        tts_message,
    ):
        self.hass = hass
        self.players = players
        self.artists = artists

        self.tts_enabled = tts_enabled
        self.tts_entity = tts_entity
        self.tts_language = tts_language
        self.tts_message = tts_message

        self.enabled = True
        self.detected_players = set()
        self.muted_by_integration = set()
        self.processing = set()
        self.entities = set()

    def notify(self):
        """Update all integration entities."""
        for entity in self.entities:
            entity.async_write_ha_state()

    def is_filtered(self, state):
        """Check whether the current track matches a blocked artist."""

        if state is None:
            return False

        media_title = (
            state.attributes.get("media_title", "") or ""
        ).casefold()

        media_artist = (
            state.attributes.get("media_artist", "") or ""
        ).casefold()

        searchable = f"{media_title} {media_artist}"

        return any(
            artist in searchable
            for artist in self.artists
        )

    async def process_player(self, entity_id, state):
        """Check a player and apply the WHAM filter."""

        if entity_id in self.processing or state is None:
            return

        if not self.enabled:
            return

        detected = self.is_filtered(state)

        if detected:
            if entity_id not in self.detected_players:
                self.detected_players.add(entity_id)
                self.notify()

            if entity_id in self.muted_by_integration:
                return

            # Do not take over a player that was already muted.
            if state.attributes.get("is_volume_muted", False):
                return

            self.processing.add(entity_id)

            try:
                _LOGGER.warning(
                    "WHAM filter detected a match on %s",
                    entity_id,
                )

                if self.tts_enabled and self.tts_entity:
                    try:
                        await self.hass.services.async_call(
                            "tts",
                            "speak",
                            {
                                "entity_id": self.tts_entity,
                                "media_player_entity_id": entity_id,
                                "message": self.tts_message,
                                "language": self.tts_language,
                            },
                            blocking=True,
                        )
                    except Exception:
                        _LOGGER.exception(
                            "TTS announcement failed on %s. "
                            "The player will still be muted.",
                            entity_id,
                        )

                elif self.tts_enabled:
                    _LOGGER.warning(
                        "TTS is enabled but no TTS entity is selected. "
                        "Muting without announcement."
                    )

                await self.hass.services.async_call(
                    "media_player",
                    "volume_mute",
                    {
                        "entity_id": entity_id,
                        "is_volume_muted": True,
                    },
                    blocking=True,
                )

                self.muted_by_integration.add(entity_id)

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
                self.processing.discard(entity_id)

        else:
            if entity_id in self.detected_players:
                self.detected_players.discard(entity_id)
                self.notify()

            if entity_id in self.muted_by_integration:
                self.processing.add(entity_id)

                try:
                    await self.hass.services.async_call(
                        "media_player",
                        "volume_mute",
                        {
                            "entity_id": entity_id,
                            "is_volume_muted": False,
                        },
                        blocking=True,
                    )

                    self.muted_by_integration.discard(entity_id)

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
                    self.processing.discard(entity_id)

    async def set_enabled(self, enabled):
        """Enable or disable WHAM protection."""

        self.enabled = enabled

        if not enabled:
            self.detected_players.clear()

            for entity_id in list(self.muted_by_integration):
                try:
                    await self.hass.services.async_call(
                        "media_player",
                        "volume_mute",
                        {
                            "entity_id": entity_id,
                            "is_volume_muted": False,
                        },
                        blocking=True,
                    )

                    self.muted_by_integration.discard(entity_id)

                except Exception:
                    _LOGGER.exception(
                        "Could not unmute %s",
                        entity_id,
                    )

            self.notify()
            return

        self.notify()

        # Check the currently playing tracks immediately.
        for entity_id in self.players:
            await self.process_player(
                entity_id,
                self.hass.states.get(entity_id),
            )

    async def set_artists(self, artists):
        """Update the blocked artist list."""

        self.artists = [
            artist.strip().casefold()
            for artist in artists
            if artist.strip()
        ]

        self.detected_players.clear()

        # Re-evaluate all selected players.
        for entity_id in self.players:
            await self.process_player(
                entity_id,
                self.hass.states.get(entity_id),
            )

        self.notify()


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

    runtime = WhamRuntime(
        hass=hass,
        players=players,
        artists=artists,
        tts_enabled=options.get(CONF_TTS_ENABLED, True),
        tts_entity=options.get(CONF_TTS_ENTITY),
        tts_language=options.get(
            CONF_TTS_LANGUAGE,
            DEFAULT_TTS_LANGUAGE,
        ),
        tts_message=options.get(
            CONF_TTS_MESSAGE,
            DEFAULT_TTS_MESSAGE,
        ),
    )

    entry.runtime_data = runtime

    async def handle_state_change(event: Event):
        """Handle media player state changes."""

        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")

        if entity_id:
            await runtime.process_player(entity_id, new_state)

    if players:
        entry.async_on_unload(
            async_track_state_change_event(
                hass,
                players,
                handle_state_change,
            )
        )

    entry.async_on_unload(
        entry.add_update_listener(async_reload_entry)
    )

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    for entity_id in players:
        await runtime.process_player(
            entity_id,
            hass.states.get(entity_id),
        )

    _LOGGER.info(
        "WHAM Intrusion Detection System started with %s players, "
        "%s artists and TTS %s.",
        len(players),
        len(artists),
        "enabled" if runtime.tts_enabled else "disabled",
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload the integration."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if not unload_ok:
        return False

    runtime = entry.runtime_data

    for entity_id in list(runtime.muted_by_integration):
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
