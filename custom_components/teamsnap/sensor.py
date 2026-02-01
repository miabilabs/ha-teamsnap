"""Sensor platform for TeamSnap integration."""

from __future__ import annotations

from datetime import datetime

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_NEXT_GAME,
    ATTR_NEXT_GAME_DATE,
    ATTR_NEXT_GAME_LOCATION,
    ATTR_NEXT_GAME_OPPONENT,
    ATTR_NEXT_GAME_TIME,
    ATTR_NEXT_PRACTICE,
    ATTR_TEAM_ID,
    ATTR_TEAM_NAME,
    ATTR_UPCOMING_EVENTS,
    DOMAIN,
)
from .coordinator import TeamSnapDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Max number of upcoming games/practices to list per team (keeps attributes manageable)
MAX_UPCOMING_GAMES = 20
MAX_UPCOMING_PRACTICES = 20

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="next_game",
        name="Next Game",
        icon="mdi:soccer",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="upcoming_events_count",
        name="Upcoming Events Count",
        icon="mdi:calendar-multiple",
        native_unit_of_measurement="events",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="next_practice",
        name="Next Practice",
        icon="mdi:whistle",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
)


def _event_start_value(event: dict[str, Any]) -> str | None:
    """Get start date/time string from event for display."""
    return (
        event.get("start_date")
        or event.get("starts_at")
        or event.get("start")
        or event.get("game_date")
        or event.get("date")
    )


def _get_event_type_str(event: dict[str, Any]) -> str:
    """Return a string we can check for game/practice; tries type, event_type, event_type_id, name, kind."""
    t = event.get("type") or event.get("event_type") or event.get("kind") or ""
    if isinstance(t, (int, float)):
        t = str(int(t))
    elif not isinstance(t, str):
        t = ""
    name = event.get("name") or ""
    if isinstance(name, str):
        t = f"{t} {name}"
    etid = event.get("event_type_id")
    if etid is not None:
        t = f"{t} {etid}"
    return t.lower()


def _parse_event_start_datetime(event: dict[str, Any]) -> datetime | None:
    """Parse event start into timezone-aware datetime. Tries multiple field names."""
    from datetime import timezone as tz

    start_date = (
        event.get("start_date")
        or event.get("starts_at")
        or event.get("start")
        or event.get("game_date")
        or event.get("date")
    )
    start_time = event.get("start_time")
    if start_date and start_time and "T" not in str(start_date) and " " not in str(start_date):
        combined = f"{start_date}T{start_time}"
        dt = dt_util.parse_datetime(combined)
    elif start_date:
        dt = dt_util.parse_datetime(start_date)
    else:
        dt = None
    if dt is not None and dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz.utc)
    return dt


def _format_upcoming_game(event: dict[str, Any]) -> str:
    """Format a game event as a readable string."""
    start = _event_start_value(event)
    dt_str = ""
    if start:
        try:
            dt = dt_util.parse_datetime(start)
            if dt:
                local = dt_util.as_local(dt)
                dt_str = local.strftime("%b %d, %Y %I:%M %p")
        except (ValueError, TypeError):
            dt_str = start
    opponent = event.get("opponent_name") or event.get("opponent") or "TBD"
    location = event.get("location_name") or event.get("location") or "TBD"
    return f"{dt_str} - vs {opponent} @ {location}".strip(" -")


def _format_upcoming_practice(event: dict[str, Any]) -> str:
    """Format a practice event as a readable string."""
    start = _event_start_value(event)
    dt_str = ""
    if start:
        try:
            dt = dt_util.parse_datetime(start)
            if dt:
                local = dt_util.as_local(dt)
                dt_str = local.strftime("%b %d, %Y %I:%M %p")
        except (ValueError, TypeError):
            dt_str = start
    location = event.get("location_name") or event.get("location") or "TBD"
    name = event.get("name") or "Practice"
    return f"{dt_str} - {name} @ {location}".strip(" -")


def _build_team_upcoming_lists(
    events: list[dict[str, Any]],
) -> tuple[list[str], list[str], str | None, str | None]:
    """Build lists of upcoming games and practices, plus next game/practice summary strings."""
    now = dt_util.utcnow()
    upcoming_games: list[tuple[Any, dict]] = []
    upcoming_practices: list[tuple[Any, dict]] = []

    for event in events:
        event_time = _parse_event_start_datetime(event)
        if not event_time or event_time <= now:
            continue

        event_type_str = _get_event_type_str(event)
        is_game = (
            "game" in event_type_str
            or "match" in event_type_str
            or event.get("event_type_id") == 1
        )
        is_practice = (
            "practice" in event_type_str
            or event.get("event_type_id") == 2
        )
        if is_game:
            upcoming_games.append((event_time, event))
        elif is_practice:
            upcoming_practices.append((event_time, event))

    upcoming_games.sort(key=lambda x: x[0])
    upcoming_practices.sort(key=lambda x: x[0])

    games_list = [_format_upcoming_game(e) for _, e in upcoming_games[:MAX_UPCOMING_GAMES]]
    practices_list = [
        _format_upcoming_practice(e) for _, e in upcoming_practices[:MAX_UPCOMING_PRACTICES]
    ]

    next_game_str = _format_upcoming_game(upcoming_games[0][1]) if upcoming_games else None
    next_practice_str = (
        _format_upcoming_practice(upcoming_practices[0][1]) if upcoming_practices else None
    )

    return games_list, practices_list, next_game_str, next_practice_str


async def _add_new_team_sensors(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: TeamSnapDataUpdateCoordinator,
) -> None:
    """Check for new teams in coordinator data and add sensors for them."""
    meta = (hass.data.get(DOMAIN) or {}).get("_sensor_meta", {}).get(entry.entry_id)
    if not meta:
        return
    data = coordinator.data
    if not data:
        return
    teams = data.get("teams", [])
    existing_ids = meta["team_sensor_ids"]
    new_teams = [
        t
        for t in teams
        if isinstance(t, dict)
        and t.get("id") is not None
        and t.get("id") not in existing_ids
    ]
    if not new_teams:
        return
    for team in new_teams:
        existing_ids.add(team.get("id"))
    new_entities = [
        TeamSnapTeamScheduleSensor(coordinator, team) for team in new_teams
    ]
    add_entities = meta["add_entities"]
    await add_entities(new_entities)
    _LOGGER.debug("Added %d new team schedule sensor(s)", len(new_entities))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TeamSnap sensor entities."""
    if DOMAIN not in hass.data:
        _LOGGER.error("TeamSnap domain not found in hass.data")
        return

    if entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.error("TeamSnap coordinator not found for entry %s", entry.entry_id)
        return

    coordinator: TeamSnapDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Store callback and team IDs so we can add new team sensors when coordinator updates
    hass.data[DOMAIN].setdefault("_sensor_meta", {})[entry.entry_id] = {
        "add_entities": async_add_entities,
        "team_sensor_ids": set(),
    }
    meta = hass.data[DOMAIN]["_sensor_meta"][entry.entry_id]

    # Ensure we have data so we can create per-team sensors
    if coordinator.data is None:
        await coordinator.async_request_refresh()

    entities: list[SensorEntity] = [
        TeamSnapSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    ]

    teams = (coordinator.data or {}).get("teams", [])
    for team in teams:
        if not isinstance(team, dict) or team.get("id") is None:
            continue
        meta["team_sensor_ids"].add(team.get("id"))
        entities.append(TeamSnapTeamScheduleSensor(coordinator, team))

    async_add_entities(entities)

    # When coordinator updates, check for new teams and add sensors for them
    def _listen() -> None:
        hass.async_create_task(_add_new_team_sensors(hass, entry, coordinator))

    coordinator.async_add_listener(_listen)


class TeamSnapSensor(CoordinatorEntity[TeamSnapDataUpdateCoordinator], SensorEntity):
    """Representation of a TeamSnap sensor."""

    def __init__(
        self,
        coordinator: TeamSnapDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description

        # Generate unique ID safely
        entry_id = getattr(coordinator.config_entry, 'entry_id', 'unknown') if coordinator.config_entry else 'unknown'
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_name = f"TeamSnap {description.name}"

    @property
    def native_value(self) -> datetime | int | None:
        """Return the state of the sensor."""
        data = self.coordinator.data
        if not data:
            return None

        key = self.entity_description.key

        if key == "next_game":
            next_game = data.get("next_game")
            if next_game:
                dt = _parse_event_start_datetime(next_game)
                if dt:
                    return dt_util.as_local(dt)
                _LOGGER.debug(
                    "Next game event has no parseable start; keys: %s",
                    list(next_game.keys()),
                )
            return None

        if key == "upcoming_events_count":
            return data.get("upcoming_events_count", 0)

        if key == "next_practice":
            next_practice = data.get("next_practice")
            if next_practice:
                dt = _parse_event_start_datetime(next_practice)
                if dt:
                    return dt_util.as_local(dt)
                _LOGGER.debug(
                    "Next practice event has no parseable start; keys: %s",
                    list(next_practice.keys()),
                )
            return None

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        data = self.coordinator.data
        if not data:
            return {}

        attrs: dict[str, Any] = {}

        # Add next game attributes
        next_game = data.get("next_game")
        if next_game:
            attrs[ATTR_NEXT_GAME] = next_game.get("name", "Unknown")
            dt = _parse_event_start_datetime(next_game)
            if dt:
                attrs[ATTR_NEXT_GAME_DATE] = dt.strftime("%Y-%m-%d")
                attrs[ATTR_NEXT_GAME_TIME] = dt.strftime("%H:%M")
            attrs[ATTR_NEXT_GAME_LOCATION] = next_game.get("location_name", "Unknown")
            attrs[ATTR_NEXT_GAME_OPPONENT] = next_game.get("opponent_name", "Unknown")
            attrs[ATTR_TEAM_ID] = next_game.get("team_id")

        # Add next practice attributes
        next_practice = data.get("next_practice")
        if next_practice:
            attrs[ATTR_NEXT_PRACTICE] = next_practice.get("name", "Unknown")
            attrs[ATTR_TEAM_ID] = next_practice.get("team_id")

        # Add team information
        teams = data.get("teams", [])
        if teams:
            # Use the first team or the team from next_game/next_practice
            team_id = attrs.get(ATTR_TEAM_ID)
            team = None

            if team_id:
                # Find team by ID
                team = next(
                    (t for t in teams if t and t.get("id") == team_id),
                    None,
                )

            # Fallback to first team if no specific team found
            if not team and teams:
                team = teams[0]

            if team and isinstance(team, dict):
                attrs[ATTR_TEAM_NAME] = team.get("name", "Unknown")

        attrs[ATTR_UPCOMING_EVENTS] = data.get("upcoming_events_count", 0)

        return attrs


class TeamSnapTeamScheduleSensor(
    CoordinatorEntity[TeamSnapDataUpdateCoordinator], SensorEntity
):
    """Sensor that lists upcoming games and practices for a single team."""

    _attr_icon = "mdi:calendar-multiple"
    _attr_native_unit_of_measurement = "events"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: TeamSnapDataUpdateCoordinator,
        team: dict[str, Any],
    ) -> None:
        """Initialize the per-team schedule sensor."""
        super().__init__(coordinator)
        self._team = team
        team_id = team.get("id")
        team_name = team.get("name", "Unknown")
        entry_id = (
            getattr(coordinator.config_entry, "entry_id", "unknown")
            if coordinator.config_entry
            else "unknown"
        )
        self._attr_unique_id = f"{entry_id}_team_{team_id}"
        self._attr_name = f"TeamSnap Upcoming - {team_name}"

    @property
    def native_value(self) -> int:
        """Return the number of upcoming events for this team."""
        data = self.coordinator.data
        if not data:
            return 0
        events_by_team = data.get("events", {})
        team_id = self._team.get("id")
        events = events_by_team.get(team_id, [])
        games_list, practices_list, _, _ = _build_team_upcoming_lists(events)
        return len(games_list) + len(practices_list)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return upcoming games and practices lists for this team."""
        data = self.coordinator.data
        if not data:
            return {
                ATTR_TEAM_ID: self._team.get("id"),
                ATTR_TEAM_NAME: self._team.get("name", "Unknown"),
                "upcoming_games": [],
                "upcoming_practices": [],
                "next_game": None,
                "next_practice": None,
            }
        events_by_team = data.get("events", {})
        team_id = self._team.get("id")
        events = events_by_team.get(team_id, [])
        games_list, practices_list, next_game_str, next_practice_str = (
            _build_team_upcoming_lists(events)
        )
        return {
            ATTR_TEAM_ID: team_id,
            ATTR_TEAM_NAME: self._team.get("name", "Unknown"),
            "upcoming_games": games_list,
            "upcoming_practices": practices_list,
            "next_game": next_game_str,
            "next_practice": next_practice_str,
        }
