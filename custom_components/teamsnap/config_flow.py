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
            # If credentials aren't set yet, return an error implementation
            # This should only happen during initial flow setup, not after credentials are provided
            _LOGGER.debug("OAuth credentials not set, returning error implementation")
            return TeamSnapOAuth2ErrorImplementation(self.hass)

        # Ensure credentials are non-empty strings
        if not self._client_id.strip() or not self._client_secret.strip():
            _LOGGER.warning("OAuth credentials are empty strings")
            return TeamSnapOAuth2ErrorImplementation(self.hass)

        # Create and return a valid implementation
        _LOGGER.debug("Creating OAuth implementation with provided credentials")
        return TeamSnapOAuth2Implementation(self.hass, self._client_id, self._client_secret)

    async def async_step_pick_implementation(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Override to collect credentials before showing OAuth implementation picker."""
        # If credentials aren't set, show the credentials form first
        if not self._client_id or not self._client_secret:
            return await self.async_step_user(user_input)
        
        # Credentials are set, verify implementation is valid before proceeding
        try:
            impl = self.oauth_implementation
            _LOGGER.debug("OAuth implementation validated, proceeding with flow")
        except Exception as impl_err:
            _LOGGER.error("OAuth implementation validation failed: %s", impl_err, exc_info=True)
            return await self.async_step_user(user_input)
        
        # Proceed with OAuth flow
        try:
            return await super().async_step_pick_implementation(user_input)
        except Exception as err:
            error_msg = str(err).lower()
            _LOGGER.error("OAuth flow error in pick_implementation: %s", err, exc_info=True)
            
            # Check if it's a missing_configuration error
            if "missing_configuration" in error_msg or "missing configuration" in error_msg:
                _LOGGER.error(
                    "OAuth configuration missing. This may indicate: "
                    "1) Client ID/Secret are incorrect, "
                    "2) Redirect URI mismatch, or "
                    "3) OAuth app not properly configured in TeamSnap"
                )
            
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

        # Get the redirect URI that Home Assistant will use for OAuth
        # Format: https://<home-assistant-url>/auth/external/callback
        # Use external_url if available, otherwise fall back to internal_url
        base_url = self.hass.config.external_url or self.hass.config.internal_url
        if base_url:
            redirect_uri = f"{base_url}/auth/external/callback"
        else:
            # Fallback: show placeholder if URLs aren't configured
            redirect_uri = "https://YOUR_HOME_ASSISTANT_URL/auth/external/callback"

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

                # Validate that we can create a valid implementation before proceeding
                # This ensures the parent class will find a properly configured implementation
                try:
                    impl = self.oauth_implementation
                    # Verify it's not the error implementation
                    if isinstance(impl, TeamSnapOAuth2ErrorImplementation):
                        raise ValueError("OAuth implementation is error implementation - credentials not set")
                    # Verify the implementation was created successfully
                    if not isinstance(impl, TeamSnapOAuth2Implementation):
                        raise ValueError(f"Unexpected implementation type: {type(impl)}")
                    _LOGGER.debug(
                        "OAuth implementation validated successfully, client_id: %s",
                        client_id[:10] + "..." if len(client_id) > 10 else client_id
                    )
                except Exception as impl_err:
                    _LOGGER.error(
                        "Failed to create or validate OAuth implementation: %s",
                        impl_err,
                        exc_info=True
                    )
                    error_base = "oauth_setup_error"
                    self._client_id = None
                    self._client_secret = None
                else:
                    # Implementation is valid, proceed with OAuth flow
                    # The parent class should now find a properly configured implementation
                    try:
                        _LOGGER.debug("Proceeding with OAuth flow")
                        result = await super().async_step_pick_implementation()
                        _LOGGER.debug("OAuth flow pick_implementation completed successfully")
                        return result
                    except Exception as err:
                        error_str = str(err).lower()
                        _LOGGER.error("OAuth flow error: %s", err, exc_info=True)
                        
                        # Check for specific error types
                        if "missing_configuration" in error_str or "missing configuration" in error_str:
                            error_base = "missing_configuration"
                            _LOGGER.error(
                                "OAuth configuration missing. Verify: "
                                "1) Client ID/Secret are correct, "
                                "2) Redirect URI in TeamSnap matches: %s, "
                                "3) OAuth app is properly configured",
                                redirect_uri
                            )
                        else:
                            error_base = "oauth_setup_error"
                        
                        # Clear credentials so user can try again
                        self._client_id = None
                        self._client_secret = None

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
        # Validate credentials before passing to parent
        if not client_id or not client_id.strip():
            raise ValueError("client_id cannot be empty")
        if not client_secret or not client_secret.strip():
            raise ValueError("client_secret cannot be empty")
        
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
