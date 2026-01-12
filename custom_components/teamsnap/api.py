"""TeamSnap API client."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

from .const import API_BASE_URL, API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class TeamSnapAPIError(Exception):
    """Base exception for TeamSnap API errors."""


class TeamSnapAPIClient:
    """Client for interacting with TeamSnap API v3."""

    def __init__(
        self,
        session: OAuth2Session,
    ) -> None:
        """Initialize the TeamSnap API client."""
        self._session = session

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make a request to the TeamSnap API."""
        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"

        try:
            response = await self._session.async_request(
                method,
                url,
                timeout=API_TIMEOUT,
                **kwargs,
            )

            if response.status == 401:
                _LOGGER.warning("Unauthorized - token may need refresh")
                raise TeamSnapAPIError("Authentication failed - token may be expired")

            try:
                data = await response.json()
            except Exception:
                _LOGGER.warning("Response was not JSON, returning empty dict")
                return {}

            return data

        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout communicating with TeamSnap API: %s", err)
            raise TeamSnapAPIError(f"API request timed out: {err}") from err

    async def async_get_user(self) -> dict[str, Any]:
        """Get the authenticated user's information."""
        return await self._request("GET", "/me")

    async def async_get_teams(self) -> list[dict[str, Any]]:
        """Get all teams for the authenticated user."""
        data = await self._request("GET", "/teams")
        # TeamSnap API returns data in a collection format
        if isinstance(data, dict) and "collection" in data:
            return data["collection"]
        if isinstance(data, list):
            return data
        return []

    async def async_get_team_events(
        self, team_id: int | str
    ) -> list[dict[str, Any]]:
        """Get all events for a specific team."""
        data = await self._request("GET", f"/teams/{team_id}/events")
        # TeamSnap API returns data in a collection format
        if isinstance(data, dict) and "collection" in data:
            return data["collection"]
        if isinstance(data, list):
            return data
        return []

    async def async_get_event(
        self, event_id: int | str
    ) -> dict[str, Any]:
        """Get details for a specific event."""
        return await self._request("GET", f"/events/{event_id}")
