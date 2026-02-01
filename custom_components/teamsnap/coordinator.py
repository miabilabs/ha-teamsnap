"""Data update coordinator for TeamSnap."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import TeamSnapAPIClient, TeamSnapAPIError
from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class TeamSnapDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching TeamSnap data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: TeamSnapAPIClient,
        update_interval: int = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )
        self.api_client = api_client
        self._teams: list[dict[str, Any]] = []
        self._events: dict[int, list[dict[str, Any]]] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from TeamSnap API."""
        try:
            # Fetch user's teams and keep only active (non-archived) teams
            all_teams = await self.api_client.async_get_teams()
            teams = [
                t
                for t in (all_teams or [])
                if isinstance(t, dict)
                and t.get("is_archived_season") is not True
            ]
            if not teams and all_teams:
                _LOGGER.debug(
                    "All %d team(s) are archived; showing none",
                    len(all_teams),
                )
            elif not teams:
                _LOGGER.warning("No teams found for user")
            self._teams = teams

            # Fetch events for each team
            events_by_team: dict[int, list[dict[str, Any]]] = {}
            for team in teams:
                team_id = team.get("id")
                if team_id:
                    try:
                        events = await self.api_client.async_get_team_events(team_id)
                        events_by_team[team_id] = events
                    except TeamSnapAPIError as err:
                        _LOGGER.warning(
                            "Failed to fetch events for team %s: %s", team_id, err
                        )
                        # Continue with other teams even if one fails
                        continue

            self._events = events_by_team

            # Process and structure the data
            return {
                "teams": teams,
                "events": events_by_team,
                "next_game": self._get_next_game(events_by_team),
                "next_practice": self._get_next_practice(events_by_team),
                "upcoming_events_count": self._count_upcoming_events(events_by_team),
            }
        except ConfigEntryAuthFailed:
            raise
        except TeamSnapAPIError as err:
            error_msg = str(err)
            if "Authentication failed" in error_msg or "401" in error_msg:
                _LOGGER.warning(
                    "TeamSnap token expired or invalid; re-authentication required"
                )
                raise ConfigEntryAuthFailed(
                    "TeamSnap token expired or invalid; please re-authenticate the integration."
                ) from err
            raise UpdateFailed(f"Error fetching TeamSnap data: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching TeamSnap data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def _event_start_value(self, event: dict[str, Any]) -> str | None:
        """Get start date/time string from event for display."""
        return event.get("start_date") or event.get("starts_at")

    def _parse_event_start(self, event: dict[str, Any]) -> datetime | None:
        """Parse event start into timezone-aware datetime. Handles start_date + start_time or single field."""
        start_date = event.get("start_date") or event.get("starts_at")
        start_time = event.get("start_time")
        if start_date and start_time and "T" not in str(start_date) and " " not in str(start_date):
            # TeamSnap may return date and time separately; combine for parsing
            combined = f"{start_date}T{start_time}"
            dt = dt_util.parse_datetime(combined)
        elif start_date:
            dt = dt_util.parse_datetime(start_date)
        else:
            dt = None
        if dt is not None and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def _get_next_game(
        self, events_by_team: dict[int, list[dict[str, Any]]]
    ) -> dict[str, Any] | None:
        """Get the next upcoming game."""
        now = dt_util.utcnow()
        next_game = None
        next_game_time = None

        for team_id, events in events_by_team.items():
            for event in events:
                event_type = (
                    event.get("type") or event.get("event_type") or ""
                ).lower()
                if "game" not in event_type and "match" not in event_type:
                    continue

                event_time = self._parse_event_start(event)
                if event_time and event_time > now:
                    if next_game_time is None or event_time < next_game_time:
                        next_game_time = event_time
                        next_game = {
                            **event,
                            "team_id": team_id,
                        }

        return next_game

    def _get_next_practice(
        self, events_by_team: dict[int, list[dict[str, Any]]]
    ) -> dict[str, Any] | None:
        """Get the next upcoming practice."""
        now = dt_util.utcnow()
        next_practice = None
        next_practice_time = None

        for team_id, events in events_by_team.items():
            for event in events:
                event_type = (
                    event.get("type") or event.get("event_type") or ""
                ).lower()
                if "practice" not in event_type:
                    continue

                event_time = self._parse_event_start(event)
                if event_time and event_time > now:
                    if next_practice_time is None or event_time < next_practice_time:
                        next_practice_time = event_time
                        next_practice = {
                            **event,
                            "team_id": team_id,
                        }

        return next_practice

    def _count_upcoming_events(
        self, events_by_team: dict[int, list[dict[str, Any]]]
    ) -> int:
        """Count all upcoming events."""
        now = dt_util.utcnow()
        count = 0

        for events in events_by_team.values():
            for event in events:
                event_time = self._parse_event_start(event)
                if event_time and event_time > now:
                    count += 1

        return count

    @property
    def teams(self) -> list[dict[str, Any]]:
        """Return the cached teams."""
        return self._teams

    @property
    def events(self) -> dict[int, list[dict[str, Any]]]:
        """Return the cached events."""
        return self._events
