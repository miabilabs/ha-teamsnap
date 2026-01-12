"""Application Credentials for TeamSnap."""

from homeassistant.core import HomeAssistant
from homeassistant.components.application_credentials import AuthorizationServer

from .const import OAUTH2_AUTHORIZE_URL, OAUTH2_TOKEN_URL


async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    """Return authorization server."""
    return AuthorizationServer(
        authorize_url=OAUTH2_AUTHORIZE_URL,
        token_url=OAUTH2_TOKEN_URL,
    )