
"""Config flow for WHAM Intrusion Detection System."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

from . import DOMAIN

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


class WhamIntrusionDetectionConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle the config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle initial setup."""

        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        schema = vol.Schema({
            vol.Required(
                CONF_NAME,
                default="WHAM Intrusion Detection System",
            ): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Create options flow."""
        return WhamIntrusionDetectionOptionsFlow()


class WhamIntrusionDetectionOptionsFlow(
    config_entries.OptionsFlow
):
    """Handle integration options."""

    async def async_step_init(self, user_input=None):
        """Manage integration options."""

        if user_input is not None:
            artists = [
                artist.strip()
                for artist in user_input.get(
                    CONF_ARTISTS, ""
                ).splitlines()
                if artist.strip()
            ]

            return self.async_create_entry(
                title="",
                data={
                    CONF_MEDIA_PLAYERS: user_input.get(
                        CONF_MEDIA_PLAYERS, []
                    ),
                    CONF_ARTISTS: artists,
                    CONF_TTS_ENABLED: user_input.get(
                        CONF_TTS_ENABLED, True
                    ),
                    CONF_TTS_ENTITY: user_input.get(
                        CONF_TTS_ENTITY
                    ),
                    CONF_TTS_LANGUAGE: user_input.get(
                        CONF_TTS_LANGUAGE,
                        DEFAULT_TTS_LANGUAGE,
                    ),
                    CONF_TTS_MESSAGE: user_input.get(
                        CONF_TTS_MESSAGE,
                        DEFAULT_TTS_MESSAGE,
                    ),
                },
            )

        options = self.config_entry.options

        current_players = options.get(CONF_MEDIA_PLAYERS, [])
        current_artists = options.get(CONF_ARTISTS, ["Wham!"])

        schema = vol.Schema({
            vol.Optional(
                CONF_MEDIA_PLAYERS,
                default=current_players,
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="media_player",
                    multiple=True,
                )
            ),
            vol.Optional(
                CONF_ARTISTS,
                default="\n".join(current_artists),
            ): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Optional(
                CONF_TTS_ENABLED,
                default=options.get(CONF_TTS_ENABLED, True),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_TTS_ENTITY,
                default=options.get(CONF_TTS_ENTITY),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="tts",
                    multiple=False,
                )
            ),
            vol.Optional(
                CONF_TTS_LANGUAGE,
                default=options.get(
                    CONF_TTS_LANGUAGE,
                    DEFAULT_TTS_LANGUAGE,
                ),
            ): selector.TextSelector(),
            vol.Optional(
                CONF_TTS_MESSAGE,
                default=options.get(
                    CONF_TTS_MESSAGE,
                    DEFAULT_TTS_MESSAGE,
                ),
            ): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
