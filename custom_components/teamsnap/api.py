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


def _parse_collection_items(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse TeamSnap Collection+JSON response into a list of flat dicts.

    TeamSnap API v3 uses Collection+JSON: collection.items[].data is a list of
    {"name": key, "value": value}. We convert each item to {key: value, ...}.
    """
    result: list[dict[str, Any]] = []
    collection = response.get("collection") if isinstance(response, dict) else None
    if not isinstance(collection, dict):
        return result
    items = collection.get("items")
    if not isinstance(items, list):
        if "error" in collection:
            _LOGGER.warning("API returned error: %s", collection.get("error"))
        return result
    for item in items:
        if not isinstance(item, dict):
            continue
        data = item.get("data")
        if not isinstance(data, list):
            continue
        flat: dict[str, Any] = {}
        for entry in data:
            if isinstance(entry, dict) and "name" in entry:
                flat[entry["name"]] = entry.get("value")
        if flat:
            result.append(flat)
    return result


class TeamSnapAPIClient:
    """Client for interacting with TeamSnap API v3 (Collection+JSON)."""

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

            if response.status >= 400:
                try:
                    body = await response.text()
                except Exception:
                    body = "Unable to read error response"
                raise TeamSnapAPIError(
                    f"API request failed ({response.status}): {body}"
                )

            try:
                data = await response.json()
            except Exception:
                _LOGGER.warning("Response was not JSON, returning empty dict")
                return {}

            return data if isinstance(data, dict) else {}

        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout communicating with TeamSnap API: %s", err)
            raise TeamSnapAPIError(f"API request timed out: {err}") from err

    async def async_get_user(self) -> dict[str, Any]:
        """Get the authenticated user's information (flat dict from Collection+JSON)."""
        data = await self._request("GET", "/me")
        items = _parse_collection_items(data)
        return items[0] if items else {}

    async def async_get_teams(self) -> list[dict[str, Any]]:
        """Get all teams for the authenticated user."""
        user = await self.async_get_user()
        user_id = user.get("id")
        if user_id is None:
            _LOGGER.warning("No user id from /me")
            return []
        data = await self._request("GET", f"/teams/search?user_id={user_id}")
        return _parse_collection_items(data)

    async def async_get_team_events(
        self, team_id: int | str
    ) -> list[dict[str, Any]]:
        """Get all events for a specific team."""
        data = await self._request("GET", f"/events/search?team_id={team_id}")
        return _parse_collection_items(data)

    async def async_get_event(
        self, event_id: int | str
    ) -> dict[str, Any]:
        """Get details for a specific event."""
        data = await self._request("GET", f"/events/{event_id}")
        items = _parse_collection_items(data)
        return items[0] if items else {}
