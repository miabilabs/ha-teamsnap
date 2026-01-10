"""Sensor platform for TeamSnap integration."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
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

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="next_game",
        name="Next Game",
        icon="mdi:soccer",
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
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TeamSnap sensor entities."""
    coordinator: TeamSnapDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        TeamSnapSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    ]

    async_add_entities(entities)


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
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_name = f"TeamSnap {description.name}"

    @property
    def native_value(self) -> str | int | None:
        """Return the state of the sensor."""
        data = self.coordinator.data
        if not data:
            return None

        key = self.entity_description.key

        if key == "next_game":
            next_game = data.get("next_game")
            if next_game:
                start_date = next_game.get("start_date")
                if start_date:
                    try:
                        dt = dt_util.parse_datetime(start_date)
                        if dt:
                            return dt.strftime("%Y-%m-%d %H:%M")
                    except (ValueError, TypeError):
                        pass
            return None

        if key == "upcoming_events_count":
            return data.get("upcoming_events_count", 0)

        if key == "next_practice":
            next_practice = data.get("next_practice")
            if next_practice:
                start_date = next_practice.get("start_date")
                if start_date:
                    try:
                        dt = dt_util.parse_datetime(start_date)
                        if dt:
                            return dt.strftime("%Y-%m-%d %H:%M")
                    except (ValueError, TypeError):
                        pass
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
            start_date = next_game.get("start_date")
            if start_date:
                try:
                    dt = dt_util.parse_datetime(start_date)
                    if dt:
                        attrs[ATTR_NEXT_GAME_DATE] = dt.strftime("%Y-%m-%d")
                        attrs[ATTR_NEXT_GAME_TIME] = dt.strftime("%H:%M")
                except (ValueError, TypeError):
                    pass
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
            if team_id:
                team = next(
                    (t for t in teams if t.get("id") == team_id),
                    teams[0] if teams else None,
                )
            else:
                team = teams[0] if teams else None

            if team:
                attrs[ATTR_TEAM_NAME] = team.get("name", "Unknown")

        attrs[ATTR_UPCOMING_EVENTS] = data.get("upcoming_events_count", 0)

        return attrs
