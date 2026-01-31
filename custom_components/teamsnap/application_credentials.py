"""Application Credentials for TeamSnap."""

from __future__ import annotations

from homeassistant.components.application_credentials import ClientCredential
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    LocalOAuth2Implementation,
)

from .const import OAUTH2_AUTHORIZE_URL, OAUTH2_TOKEN_URL

# Default token lifetime when TeamSnap does not return expires_in (seconds).
# TeamSnap returns created_at but not expires_in; HA requires expires_in.
DEFAULT_TOKEN_EXPIRES_IN = 7200  # 2 hours


class TeamSnapOAuth2Implementation(LocalOAuth2Implementation):
    """TeamSnap OAuth2 implementation that normalizes token for HA (adds expires_in)."""

    async def async_resolve_external_data(self, external_data):
        """Resolve authorization code to tokens; add expires_in when missing."""
        token = await super().async_resolve_external_data(external_data)
        if "expires_in" not in token:
            token["expires_in"] = DEFAULT_TOKEN_EXPIRES_IN
        return token


async def async_get_auth_implementation(
    hass: HomeAssistant, auth_domain: str, credential: ClientCredential
) -> TeamSnapOAuth2Implementation:
    """Return TeamSnap OAuth2 implementation with expires_in handling."""
    return TeamSnapOAuth2Implementation(
        hass,
        auth_domain,
        credential.client_id,
        credential.client_secret,
        OAUTH2_AUTHORIZE_URL,
        OAUTH2_TOKEN_URL,
    )