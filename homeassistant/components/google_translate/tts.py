"""Support for the Google speech service."""
import asyncio
import logging
import re

import aiohttp
from aiohttp.hdrs import REFERER, USER_AGENT
import async_timeout
from gtts_token import gtts_token
import voluptuous as vol

from homeassistant.components.tts import CONF_LANG, PLATFORM_SCHEMA, Provider
from homeassistant.const import HTTP_OK
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

GOOGLE_SPEECH_URL = "https://translate.google.com/translate_tts"
MESSAGE_SIZE = 148

SUPPORT_LANGUAGES = [
    "af",
    "sq",
    "ar",
    "hy",
    "bn",
    "ca",
    "zh",
    "zh-cn",
    "zh-tw",
    "zh-yue",
    "hr",
    "cs",
    "da",
    "nl",
    "en",
    "en-au",
    "en-uk",
    "en-us",
    "eo",
    "fi",
    "fr",
    "de",
    "el",
    "hi",
    "hu",
    "is",
    "id",
    "it",
    "ja",
    "ko",
    "la",
    "lv",
    "mk",
    "no",
    "pl",
    "pt",
    "pt-br",
    "ro",
    "ru",
    "sr",
    "sk",
    "es",
    "es-es",
    "es-mx",
    "es-us",
    "sw",
    "sv",
    "ta",
    "th",
    "tr",
    "vi",
    "cy",
    "uk",
    "bg-BG",
]

DEFAULT_LANG = "en"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Optional(CONF_LANG, default=DEFAULT_LANG): vol.In(SUPPORT_LANGUAGES)}
)


async def async_get_engine(hass, config, discovery_info=None):
    """Set up Google speech component."""
    return GoogleProvider(hass, config[CONF_LANG])


class GoogleProvider(Provider):
    """The Google speech API provider."""

    def __init__(self, hass, lang):
        """Init Google TTS service."""
        self.hass = hass
        self._lang = lang
        self.headers = {
            REFERER: "http://translate.google.com/",
            USER_AGENT: (
                "Mozilla/5.0 (Windows NT 10.0; WOW64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/47.0.2526.106 Safari/537.36"
            ),
        }
        self.name = "Google"

    @property
    def default_language(self):
        """Return the default language."""
        return self._lang

    @property
    def supported_languages(self):
        """Return list of supported languages."""
        return SUPPORT_LANGUAGES

    async def async_get_tts_audio(self, message, language, options=None):
        """Load TTS from google."""

        token = gtts_token.Token()
        websession = async_get_clientsession(self.hass)
        message_parts = self._split_message_to_parts(message)

        data = b""
        for idx, part in enumerate(message_parts):
            part_token = await self.hass.async_add_executor_job(
                token.calculate_token, part
            )

            url_param = {
                "ie": "UTF-8",
                "tl": language,
                "q": part,
                "tk": part_token,
                "total": len(message_parts),
                "idx": idx,
                "client": "tw-ob",
                "textlen": len(part),
            }

            try:
                with async_timeout.timeout(10):
                    request = await websession.get(
                        GOOGLE_SPEECH_URL, params=url_param, headers=self.headers
                    )

                    if request.status != HTTP_OK:
                        _LOGGER.error(
                            "Error %d on load URL %s", request.status, request.url
                        )
                        return None, None
                    data += await request.read()

            except (asyncio.TimeoutError, aiohttp.ClientError):
                _LOGGER.error("Timeout for google speech")
                return None, None

        return "mp3", data

    @staticmethod
    def _split_message_to_parts(message):
        """Split message into single parts."""
        if len(message) <= MESSAGE_SIZE:
            return [message]

        punc = "!()[]?.,;:"
        punc_list = [re.escape(c) for c in punc]
        pattern = "|".join(punc_list)
        parts = re.split(pattern, message)

        def split_by_space(fullstring):
            """Split a string by space."""
            if len(fullstring) > MESSAGE_SIZE:
                idx = fullstring.rfind(" ", 0, MESSAGE_SIZE)
                return [fullstring[:idx]] + split_by_space(fullstring[idx:])
            return [fullstring]

        msg_parts = []
        for part in parts:
            msg_parts += split_by_space(part)

        return [msg for msg in msg_parts if len(msg) > 0]
