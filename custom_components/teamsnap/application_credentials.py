"""Application Credentials for TeamSnap."""

from homeassistant.helpers import application_credentials as app_creds

from .const import DOMAIN, OAUTH2_AUTHORIZE_URL, OAUTH2_TOKEN_URL


class TeamSnapApplicationCredentials(app_creds.AuthorizationServer):
    """TeamSnap OAuth authorization server."""

    def __init__(self, hass):
        super().__init__(
            hass,
            DOMAIN,
            "TeamSnap",
            OAUTH2_AUTHORIZE_URL,
            OAUTH2_TOKEN_URL,
        )