"""Config flow to configure StarLine component."""
from typing import Optional
from starline import StarlineAuth
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_APP_ID,
    CONF_APP_SECRET,
    CONF_MFA_CODE,
    CONF_CAPTCHA_CODE,
    LOGGER,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    ERROR_AUTH_APP,
    ERROR_AUTH_USER,
    ERROR_AUTH_MFA,
    DATA_USER_ID,
    DATA_SLNET_TOKEN,
    DATA_SLID_TOKEN,
    DATA_EXPIRES,
)


@config_entries.HANDLERS.register(DOMAIN)
class StarlineFlowHandler(config_entries.ConfigFlow):
    """Handle a StarLine config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize flow."""
        self._app_id: Optional[str] = None
        self._app_secret: Optional[str] = None
        self._username: Optional[str] = None
        self._password: Optional[str] = None
        self._mfa_code: Optional[str] = None

        self._app_code = None
        self._app_token = None
        self._user_slid = None
        self._user_id = None
        self._slnet_token = None
        self._slnet_token_expires = None
        self._captcha_image = None
        self._captcha_sid = None
        self._captcha_code = None
        self._phone_number = None

        self._auth = StarlineAuth()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return StarlineOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        return await self.async_step_init(user_input)

    async def async_step_init(self, user_input=None):
        """Handle a flow initialized by the user."""
        return await self.async_step_auth_app(user_input)

    async def async_step_auth_app(self, user_input=None, error=None):
        """Authenticate application step."""
        if user_input is not None:
            self._app_id = user_input[CONF_APP_ID]
            self._app_secret = user_input[CONF_APP_SECRET]
            return await self._async_authenticate_app(error)
        return self._async_form_auth_app(error)

    async def async_step_auth_user(self, user_input=None, error=None):
        """Authenticate user step."""
        if user_input is not None:
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]
            return await self._async_authenticate_user(error)
        return self._async_form_auth_user(error)

    async def async_step_auth_mfa(self, user_input=None, error=None):
        """Authenticate mfa step."""
        if user_input is not None:
            self._mfa_code = user_input[CONF_MFA_CODE]
            return await self._async_authenticate_user(error)
        return self._async_form_auth_mfa(error)

    async def async_step_auth_captcha(self, user_input=None, error=None):
        """Captcha verification step."""
        if user_input is not None:
            self._captcha_code = user_input[CONF_CAPTCHA_CODE]
            return await self._async_authenticate_user(error)
        return self._async_form_auth_captcha(error)

    def _async_form_auth_app(self, error=None):
        """Authenticate application form."""
        errors = {}
        if error is not None:
            errors["base"] = error

        return self.async_show_form(
            step_id="auth_app",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_APP_ID, default=self._app_id or vol.UNDEFINED
                    ): str,
                    vol.Required(
                        CONF_APP_SECRET, default=self._app_secret or vol.UNDEFINED
                    ): str,
                }
            ),
            errors=errors,
        )

    def _async_form_auth_user(self, error=None):
        """Authenticate user form."""
        errors = {}
        if error is not None:
            errors["base"] = error

        return self.async_show_form(
            step_id="auth_user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME, default=self._username or vol.UNDEFINED
                    ): str,
                    vol.Required(
                        CONF_PASSWORD, default=self._password or vol.UNDEFINED
                    ): str,
                }
            ),
            errors=errors,
        )

    def _async_form_auth_mfa(self, error=None):
        """Authenticate mfa form."""
        errors = {}
        if error is not None:
            errors["base"] = error

        return self.async_show_form(
            step_id="auth_mfa",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MFA_CODE, default=self._mfa_code or vol.UNDEFINED
                    ): str
                }
            ),
            errors=errors,
            description_placeholders={"phone_number": self._phone_number},
        )

    def _async_form_auth_captcha(self, error=None):
        """Captcha verification form."""
        errors = {}
        if error is not None:
            errors["base"] = error

        return self.async_show_form(
            step_id="auth_captcha",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CAPTCHA_CODE, default=self._captcha_code or vol.UNDEFINED
                    ): str
                }
            ),
            errors=errors,
            description_placeholders={
                "captcha_img": '<img src="' + self._captcha_image + '"/>'
            },
        )

    async def _async_authenticate_app(self, error=None):
        """Authenticate application."""
        try:
            self._app_code = self._auth.get_app_code(self._app_id, self._app_secret)
            self._app_token = self._auth.get_app_token(
                self._app_id, self._app_secret, self._app_code
            )
            return self._async_form_auth_user(error)
        except Exception as err:  # pylint: disable=broad-except
            LOGGER.error("Error auth StarLine: %s", err)
            return self._async_form_auth_app(ERROR_AUTH_APP)

    async def _async_authenticate_user(self, error=None):
        """Authenticate user."""
        try:
            state, data = self._auth.get_slid_user_token(
                self._app_token,
                self._username,
                self._password,
                self._mfa_code,
                self._captcha_sid,
                self._captcha_code,
            )

            if state == 1:
                self._user_slid = data["user_token"]
                return await self._async_get_entry()

            if "phone" in data:
                self._phone_number = data["phone"]
                if state == 0:
                    error = ERROR_AUTH_MFA
                return self._async_form_auth_mfa(error)

            if "captchaSid" in data:
                self._captcha_sid = data["captchaSid"]
                self._captcha_image = data["captchaImg"]
                return self._async_form_auth_captcha(error)

            raise Exception(data)
        except Exception as err:  # pylint: disable=broad-except
            LOGGER.error("Error auth user: %s", err)
            return self._async_form_auth_user(ERROR_AUTH_USER)

    async def _async_get_entry(self):
        """Create entry."""
        self._slnet_token, self._slnet_token_expires, self._user_id = self._auth.get_user_id(
            self._user_slid
        )

        return self.async_create_entry(
            title="Application " + self._app_id,
            data={
                DATA_USER_ID: self._user_id,
                DATA_SLNET_TOKEN: self._slnet_token,
                DATA_SLID_TOKEN: self._user_slid,
                DATA_EXPIRES: self._slnet_token_expires,
            },
        )


class StarlineOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle StarLine options."""

    def __init__(self, config_entry):
        """Initialize StarLine options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Manage the StarLine options."""
        return await self.async_step_settings()

    async def async_step_settings(self, user_input=None):
        """Manage the StarLine options."""
        if user_input is not None:
            self.options[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            return self.async_create_entry(title="", data=self.options)

        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=10))
                }
            ),
        )
