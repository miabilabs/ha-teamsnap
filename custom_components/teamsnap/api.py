"""TeamSnap API client.

TeamSnap API v3 is Collection+JSON. We parse collection.items[].data (name/value)
and each item's links (rel/href) so we follow links instead of constructing URLs.
See: https://www.teamsnap.com/documentation/apiv3/collection-json
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

from .const import API_BASE_URL, API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class TeamSnapAPIError(Exception):
    """Base exception for TeamSnap API errors."""


def _link_href(links: list[dict[str, Any]], rel: str) -> str | None:
    """Return href for the first link with the given rel, or None."""
    if not isinstance(links, list):
        return None
    for link in links:
        if isinstance(link, dict) and link.get("rel") == rel:
            href = link.get("href")
            if href:
                return str(href)
    return None


def _parse_collection_items(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse Collection+JSON response into a list of flat dicts with _links.

    TeamSnap API v3 uses Collection+JSON:
    - collection.items[].data = list of {"name", "value"[, "type"]}
    - collection.items[].links = list of {"rel", "href"} for followable links
    We convert each item to {name: value, ...} and add "_links" from item.links.
    """
    result: list[dict[str, Any]] = []
    if not isinstance(response, dict):
        _LOGGER.debug("API response is not a dict: %s", type(response).__name__)
        return result

    collection = response.get("collection")
    if not isinstance(collection, dict):
        if "error" in (response.get("collection") or {}):
            _LOGGER.warning(
                "API returned error: %s",
                (response.get("collection") or {}).get("error"),
            )
        _LOGGER.debug(
            "API response missing collection or not dict; top-level keys: %s",
            list(response.keys()) if response else [],
        )
        return result

    if "error" in collection:
        _LOGGER.warning("API collection error: %s", collection.get("error"))
        return result

    items = collection.get("items")
    if not isinstance(items, list):
        _LOGGER.debug(
            "API collection has no items list; collection keys: %s",
            list(collection.keys()),
        )
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
        # Preserve item links per Collection+JSON so we can follow rel/href
        item_links = item.get("links")
        if isinstance(item_links, list):
            flat["_links"] = [
                {"rel": l.get("rel"), "href": l.get("href")}
                for l in item_links
                if isinstance(l, dict) and l.get("rel") and l.get("href")
            ]
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
        """Make a request to the TeamSnap API. endpoint may be a path or full Collection+JSON href."""
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            url = endpoint
        else:
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
        if not items:
            _LOGGER.warning(
                "TeamSnap API: GET /me returned no user data. Response keys: %s",
                list(data.keys()) if data else "empty",
            )
            return {}
        return items[0]

    async def async_get_teams(self) -> list[dict[str, Any]]:
        """Get all teams for the authenticated user (follow Collection+JSON 'teams' link)."""
        user = await self.async_get_user()
        user_id = user.get("id")
        if user_id is None:
            _LOGGER.warning("TeamSnap API: no user id from /me; cannot fetch teams")
            return []
        # Prefer following the 'teams' link from /me per Collection+JSON
        user_links = user.get("_links") or []
        teams_href = _link_href(user_links, "teams")
        if teams_href:
            data = await self._request("GET", teams_href)
        else:
            data = await self._request("GET", f"/teams/search?user_id={user_id}")
        teams = _parse_collection_items(data)
        _LOGGER.info(
            "TeamSnap API: teams returned %d team(s) for user_id=%s",
            len(teams),
            user_id,
        )
        return teams

    async def async_get_team_events(
        self, team_id: int | str, team_links: list[dict[str, Any]] | None = None
    ) -> list[dict[str, Any]]:
        """Get all events for a specific team (follow Collection+JSON 'events' link if available)."""
        events_href = _link_href(team_links or [], "events") if team_links else None
        if events_href:
            data = await self._request("GET", events_href)
        else:
            data = await self._request("GET", f"/events/search?team_id={team_id}")
        events = _parse_collection_items(data)
        _LOGGER.debug(
            "TeamSnap API: events for team_id=%s returned %d event(s)",
            team_id,
            len(events),
        )
        return events

    async def async_get_event(
        self, event_id: int | str
    ) -> dict[str, Any]:
        """Get details for a specific event."""
        data = await self._request("GET", f"/events/{event_id}")
        items = _parse_collection_items(data)
        return items[0] if items else {}
