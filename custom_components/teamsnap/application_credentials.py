"""Application Credentials for TeamSnap."""

from __future__ import annotations

from homeassistant.components.application_credentials import ClientCredential
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.config_entry_oauth2_flow import (
    LocalOAuth2Implementation,
)

from .const import OAUTH2_AUTHORIZE_URL, OAUTH2_TOKEN_URL

# Token lifetime we tell Home Assistant when TeamSnap does not return expires_in.
# TeamSnap does not provide refresh_token, so we use a long value (30 days) so HA
# does not try to refresh; re-auth is triggered when the API returns 401 instead.
DEFAULT_TOKEN_EXPIRES_IN = 2592000  # 30 days


class TeamSnapOAuth2Implementation(LocalOAuth2Implementation):
    """TeamSnap OAuth2 implementation that normalizes token for HA (adds expires_in)."""

    async def async_resolve_external_data(self, external_data):
        """Resolve authorization code to tokens; add expires_in when missing."""
        token = await super().async_resolve_external_data(external_data)
        if "expires_in" not in token:
            token["expires_in"] = DEFAULT_TOKEN_EXPIRES_IN
        return token

    async def async_refresh_token(self, token):
        """Refresh token. TeamSnap does not provide refresh_token; trigger re-auth when needed."""
        if not token.get("refresh_token"):
            raise ConfigEntryAuthFailed(
                "TeamSnap does not provide refresh tokens; please re-authenticate the integration."
            )
        return await super().async_refresh_token(token)


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