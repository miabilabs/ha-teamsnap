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

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @property
    def oauth_implementation(self) -> config_entry_oauth2_flow.AbstractOAuth2Implementation:
        """Return OAuth2 implementation."""
        # Get credentials from flow data (set in async_step_user)
        client_id = self.hass.data.get(f"{DOMAIN}_flow_client_id")
        client_secret = self.hass.data.get(f"{DOMAIN}_flow_client_secret")

        if not client_id or not client_secret:
            # Return a placeholder - this will be set before OAuth flow starts
            # In practice, credentials should be set in async_step_user before
            # calling super().async_step_user()
            raise ValueError(
                "Client ID and secret must be provided. "
                "Please register an OAuth app at https://auth.teamsnap.com"
            )

        return TeamSnapOAuth2Implementation(self.hass, client_id, client_secret)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step to collect OAuth credentials."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        errors: dict[str, str] = {}

        if user_input is not None:
            client_id = user_input.get("client_id", "").strip()
            client_secret = user_input.get("client_secret", "").strip()

            if not client_id:
                errors["client_id"] = "client_id_required"
            if not client_secret:
                errors["client_secret"] = "client_secret_required"

            if not errors:
                # Store credentials temporarily for OAuth implementation
                self.hass.data[f"{DOMAIN}_flow_client_id"] = client_id
                self.hass.data[f"{DOMAIN}_flow_client_secret"] = client_secret

                try:
                    # Now proceed with OAuth flow
                    return await super().async_step_user()
                finally:
                    # Clean up temporary credentials after flow completes
                    self.hass.data.pop(f"{DOMAIN}_flow_client_id", None)
                    self.hass.data.pop(f"{DOMAIN}_flow_client_secret", None)

        # Get the redirect URI that Home Assistant will use for OAuth
        # Format: https://<home-assistant-url>/auth/external/callback
        redirect_uri = f"{self.hass.config.api.base_url}/auth/external/callback"

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
            errors=errors,
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
