"""Config flow for TeamSnap integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TeamSnapConfigFlow(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle a config flow for TeamSnap."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        if self.source == "reauth":
            return await self.async_step_reauth()

        # For OAuth2 flows, we delegate to the parent class to handle implementation picking
        return await super().async_step_user(user_input)

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> FlowResult:
        """Create the config entry after successful OAuth."""
        user_info = await self.async_oauth_create_entry_data(data)
        _LOGGER.debug("OAuth flow completed, creating entry with user info: %s", user_info)
        return self.async_create_entry(title="TeamSnap", data=data)