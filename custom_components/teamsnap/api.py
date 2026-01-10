"""TeamSnap API client."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import API_BASE_URL, API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class TeamSnapAPIError(Exception):
    """Base exception for TeamSnap API errors."""


class TeamSnapAPIClient:
    """Client for interacting with TeamSnap API v3."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        access_token: str,
    ) -> None:
        """Initialize the TeamSnap API client."""
        self._session = session
        self._access_token = access_token
        self._update_headers()

    def _update_headers(self) -> None:
        """Update headers with current access token."""
        self._headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def update_token(self, access_token: str) -> None:
        """Update the access token."""
        self._access_token = access_token
        self._update_headers()

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make a request to the TeamSnap API."""
        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            async with self._session.request(
                method,
                url,
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
                **kwargs,
            ) as response:
                if response.status == 401:
                    _LOGGER.warning("Unauthorized - token may need refresh")
                    raise TeamSnapAPIError("Authentication failed - token may be expired")
                
                response.raise_for_status()
                
                try:
                    data = await response.json()
                except aiohttp.ContentTypeError:
                    _LOGGER.warning("Response was not JSON, returning empty dict")
                    return {}
                    
                return data
        except aiohttp.ClientResponseError as err:
            _LOGGER.error(
                "TeamSnap API error: %s %s - %s",
                err.status,
                err.message,
                err.request_info.url if hasattr(err, "request_info") else url,
            )
            raise TeamSnapAPIError(f"API request failed: {err.status} {err.message}") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Error communicating with TeamSnap API: %s", err)
            raise TeamSnapAPIError(f"API request failed: {err}") from err
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
