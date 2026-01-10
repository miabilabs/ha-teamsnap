"""The TeamSnap integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TeamSnapAPIClient
from .const import DOMAIN
from .coordinator import TeamSnapDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TeamSnap from a config entry."""
    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
    )

    session = async_get_clientsession(hass)
    
    # Get the access token from the OAuth2 implementation
    # The token is stored in the config entry data after OAuth flow
    try:
        # Try to get token from implementation
        token = await implementation.async_resolve_token({})
        access_token = token.get("access_token")
        
        # Fallback to entry data if implementation doesn't return token
        if not access_token and "token" in entry.data:
            access_token = entry.data["token"].get("access_token")
            
        if not access_token:
            _LOGGER.error("No access token available in config entry")
            return False
    except Exception as err:
        _LOGGER.error("Failed to resolve access token: %s", err)
        # Try fallback to entry data
        if "token" in entry.data:
            access_token = entry.data["token"].get("access_token")
            if not access_token:
                return False
        else:
            return False

    api_client = TeamSnapAPIClient(session, access_token)

    coordinator = TeamSnapDataUpdateCoordinator(hass, api_client)

    # Fetch initial data so we have data when entities are added
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("Failed to fetch initial data from TeamSnap: %s", err)
        # Don't fail setup if initial fetch fails - coordinator will retry
        pass

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
