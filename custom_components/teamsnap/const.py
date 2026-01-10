"""Constants for the TeamSnap integration."""

DOMAIN = "teamsnap"

# OAuth 2.0 Configuration
OAUTH2_AUTHORIZE_URL = "https://auth.teamsnap.com/oauth/authorize"
OAUTH2_TOKEN_URL = "https://auth.teamsnap.com/oauth/token"

# API Configuration
API_BASE_URL = "https://api.teamsnap.com/v3"
API_TIMEOUT = 30

# Default update interval (in seconds)
DEFAULT_UPDATE_INTERVAL = 900  # 15 minutes

# Sensor attributes
ATTR_NEXT_GAME = "next_game"
ATTR_NEXT_GAME_DATE = "next_game_date"
ATTR_NEXT_GAME_TIME = "next_game_time"
ATTR_NEXT_GAME_LOCATION = "next_game_location"
ATTR_NEXT_GAME_OPPONENT = "next_game_opponent"
ATTR_NEXT_PRACTICE = "next_practice"
ATTR_UPCOMING_EVENTS = "upcoming_events"
ATTR_TEAM_NAME = "team_name"
ATTR_TEAM_ID = "team_id"
