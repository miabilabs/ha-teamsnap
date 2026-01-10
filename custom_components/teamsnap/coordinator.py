"""Data update coordinator for TeamSnap."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
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
            # Fetch user's teams
            teams = await self.api_client.async_get_teams()
            if not teams:
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
        except TeamSnapAPIError as err:
            error_msg = str(err)
            if "Authentication failed" in error_msg or "401" in error_msg:
                _LOGGER.error(
                    "Authentication failed - token may be expired. "
                    "Please reconfigure the integration."
                )
            raise UpdateFailed(f"Error fetching TeamSnap data: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching TeamSnap data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def _get_next_game(
        self, events_by_team: dict[int, list[dict[str, Any]]]
    ) -> dict[str, Any] | None:
        """Get the next upcoming game."""
        now = dt_util.utcnow()
        next_game = None
        next_game_time = None

        for team_id, events in events_by_team.items():
            for event in events:
                event_type = event.get("event_type", "").lower()
                if "game" not in event_type and "match" not in event_type:
                    continue

                start_date = event.get("start_date")
                if not start_date:
                    continue

                try:
                    event_time = dt_util.parse_datetime(start_date)
                    if event_time and event_time > now:
                        if next_game_time is None or event_time < next_game_time:
                            next_game_time = event_time
                            next_game = {
                                **event,
                                "team_id": team_id,
                            }
                except (ValueError, TypeError):
                    continue

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
                event_type = event.get("event_type", "").lower()
                if "practice" not in event_type:
                    continue

                start_date = event.get("start_date")
                if not start_date:
                    continue

                try:
                    event_time = dt_util.parse_datetime(start_date)
                    if event_time and event_time > now:
                        if next_practice_time is None or event_time < next_practice_time:
                            next_practice_time = event_time
                            next_practice = {
                                **event,
                                "team_id": team_id,
                            }
                except (ValueError, TypeError):
                    continue

        return next_practice

    def _count_upcoming_events(
        self, events_by_team: dict[int, list[dict[str, Any]]]
    ) -> int:
        """Count all upcoming events."""
        now = dt_util.utcnow()
        count = 0

        for events in events_by_team.values():
            for event in events:
                start_date = event.get("start_date")
                if not start_date:
                    continue

                try:
                    event_time = dt_util.parse_datetime(start_date)
                    if event_time and event_time > now:
                        count += 1
                except (ValueError, TypeError):
                    continue

        return count

    @property
    def teams(self) -> list[dict[str, Any]]:
        """Return the cached teams."""
        return self._teams

    @property
    def events(self) -> dict[int, list[dict[str, Any]]]:
        """Return the cached events."""
        return self._events
