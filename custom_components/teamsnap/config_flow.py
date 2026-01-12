"""Config flow for TeamSnap integration."""

from __future__ import annotations

from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN


class TeamSnapConfigFlow(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle a config flow for TeamSnap."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        return await self.async_step_pick_implementation(user_input)