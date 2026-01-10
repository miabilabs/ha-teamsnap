"""Config flow for TeamSnap integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN, OAUTH2_AUTHORIZE_URL, OAUTH2_TOKEN_URL

_LOGGER = logging.getLogger(__name__)


class TeamSnapOAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler,
    domain=DOMAIN,
):
    """Handle a config flow for TeamSnap OAuth2."""

    DOMAIN = DOMAIN
    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self._client_id: str | None = None
        self._client_secret: str | None = None

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @property
    def oauth_implementation(self) -> config_entry_oauth2_flow.AbstractOAuth2Implementation:
        """Return OAuth2 implementation."""
        # Get credentials from instance variables
        if not self._client_id or not self._client_secret:
            # If credentials aren't set yet, return an implementation that will
            # fail with a clear error message when OAuth is actually attempted,
            # rather than causing a 500 error when this property is accessed.
            # This allows the flow to initialize and show the credentials form.
            # The error will be caught in async_step_pick_implementation and
            # the user will be redirected to enter credentials.
            _LOGGER.debug(
                "OAuth credentials not yet provided - returning error implementation. "
                "User will be prompted to enter credentials."
            )
            return TeamSnapOAuth2ErrorImplementation(self.hass)

        return TeamSnapOAuth2Implementation(self.hass, self._client_id, self._client_secret)

    async def async_step_pick_implementation(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Override to collect credentials before showing OAuth implementation picker."""
        # If credentials aren't set, show the credentials form first
        if not self._client_id or not self._client_secret:
            return await self.async_step_user(user_input)
        
        # Credentials are set, try to proceed with OAuth flow
        # If oauth_implementation raises an error, catch it and show the form
        try:
            return await super().async_step_pick_implementation(user_input)
        except (ValueError, Exception) as err:
            # If credentials are invalid or missing, show the form with an error
            # This catches errors from both the error implementation and actual OAuth failures
            _LOGGER.warning("OAuth implementation error: %s", err)
            return await self.async_step_user(user_input)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step to collect OAuth credentials."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        # Always show the credentials form first - don't call parent's async_step_user
        # until credentials are provided
        errors: dict[str, str] = {}
        error_base: str | None = None

        if user_input is not None:
            client_id = user_input.get("client_id", "").strip()
            client_secret = user_input.get("client_secret", "").strip()

            if not client_id:
                errors["client_id"] = "client_id_required"
            if not client_secret:
                errors["client_secret"] = "client_secret_required"

            if not errors:
                # Store credentials in instance variables for OAuth implementation
                self._client_id = client_id
                self._client_secret = client_secret

                # Now proceed with OAuth flow by calling pick_implementation directly
                # This avoids the parent's async_step_user which might access oauth_implementation
                # before credentials are set
                try:
                    return await super().async_step_pick_implementation()
                except Exception as err:
                    # If there's an error with the OAuth implementation, show it to the user
                    _LOGGER.error("OAuth flow error: %s", err)
                    error_base = "oauth_setup_error"
                    # Clear credentials so user can try again
                    self._client_id = None
                    self._client_secret = None

        # Get the redirect URI that Home Assistant will use for OAuth
        # Format: https://<home-assistant-url>/auth/external/callback
        # Use external_url if available, otherwise fall back to internal_url
        base_url = self.hass.config.external_url or self.hass.config.internal_url
        if base_url:
            redirect_uri = f"{base_url}/auth/external/callback"
        else:
            # Fallback: show placeholder if URLs aren't configured
            redirect_uri = "https://YOUR_HOME_ASSISTANT_URL/auth/external/callback"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("client_id"): str,
                    vol.Required("client_secret"): str,
                }
            ),
            description_placeholders={
                "docs_url": "https://www.teamsnap.com/documentation/apiv3/authorization",
                "redirect_uri": redirect_uri,
            },
            errors=errors if not error_base else {"base": error_base},
        )


class TeamSnapOAuth2Implementation(
    config_entry_oauth2_flow.LocalOAuth2Implementation,
):
    """OAuth2 implementation for TeamSnap."""

    def __init__(
        self, hass: HomeAssistant, client_id: str, client_secret: str
    ) -> None:
        """Initialize TeamSnap OAuth2 implementation."""
        super().__init__(
            hass,
            DOMAIN,
            client_id,
            client_secret,
            OAUTH2_AUTHORIZE_URL,
            OAUTH2_TOKEN_URL,
        )

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data that needs to be appended to the authorize url."""
        return {"scope": "read"}

    async def async_resolve_external_data(self, external_data: Any) -> dict[str, Any]:
        """Resolve external data to tokens."""
        # This is called after the OAuth flow completes
        return external_data


class TeamSnapOAuth2ErrorImplementation(
    config_entry_oauth2_flow.LocalOAuth2Implementation,
):
    """Error implementation that fails with a clear message when OAuth is attempted."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize error implementation."""
        # Use placeholder values that will cause OAuth to fail with a clear error
        super().__init__(
            hass,
            DOMAIN,
            "",  # Empty client_id will cause OAuth to fail
            "",  # Empty client_secret will cause OAuth to fail
            OAUTH2_AUTHORIZE_URL,
            OAUTH2_TOKEN_URL,
        )

    async def async_generate_authorize_url(self, flow_id: str) -> str:
        """Generate authorize URL - will raise error with clear message."""
        raise ValueError(
            "OAuth credentials must be provided. Please enter your Client ID and Client Secret "
            "in the configuration form before proceeding with OAuth authentication."
        )
