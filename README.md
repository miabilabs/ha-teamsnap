# ha-teamsnap

![TeamSnap Logo](icon.png)

Unofficial Home Assistant Integration for TeamSnap

Just a dad, trying to make sense of his kids Sports commitments, with Home Assistant.

## Installation

Install this integration through [HACS](https://hacs.xyz/) (Home Assistant Community Store) or manually by copying the `custom_components/teamsnap` folder to your Home Assistant `custom_components` directory.

## Configuration

### Step 1: Create a TeamSnap OAuth Application

1. Go to [https://auth.teamsnap.com](https://auth.teamsnap.com) and sign in
2. Create a new OAuth application
3. **Important:** Set the redirect URI in your TeamSnap OAuth app. The value must **exactly** match what Home Assistant uses, or you will get an "authorization error" after signing in on TeamSnap.

   **If you use Home Assistant Cloud (Nabu Casa)** — use this redirect URI:
   ```
   https://my.home-assistant.io/redirect/oauth
   ```

   **If you do not use Home Assistant Cloud** — use your Home Assistant URL plus the callback path:
   ```
   https://YOUR_HOME_ASSISTANT_URL/auth/external/callback
   ```
   Replace `YOUR_HOME_ASSISTANT_URL` with your actual Home Assistant URL (include port if not 443), for example:
   - `homeassistant.local:8123`
   - `192.168.1.100:8123`
   - `yourdomain.duckdns.org:8123`

   **Examples (no Cloud):**
   - `https://homeassistant.local:8123/auth/external/callback`
   - `https://192.168.1.100:8123/auth/external/callback`
   - `https://yourdomain.duckdns.org:8123/auth/external/callback`

4. Save your **Client ID** and **Client Secret** — you'll need these in the next step

### Step 2: Configure Application Credentials

1. Go to **Settings** → **Application Credentials**
2. Click **Add Application**
3. Select **TeamSnap** from the list
4. Enter your **Client ID** and **Client Secret** from Step 1
5. Click **Submit** to save

### Step 3: Add the Integration in Home Assistant

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **TeamSnap** and select it
4. When prompted, continue to the external site — you'll be redirected to **auth.teamsnap.com** to sign in and authorize Home Assistant
5. After authorizing, you'll be sent back to Home Assistant and the integration will finish setting up

**Troubleshooting:** If you see an "authorization error" on TeamSnap after entering your credentials, the redirect URI in your TeamSnap OAuth app (Step 1) does not match. Use **Home Assistant Cloud** URI if you use Nabu Casa, or your **exact** Home Assistant URL with `/auth/external/callback` if you do not.

## What This Integration Does

This integration connects Home Assistant to your TeamSnap account, allowing you to track and monitor your kids' sports schedules directly in Home Assistant. Here's what it provides:

### Sensor Entities

The integration creates three sensor entities that automatically update every 15 minutes:

1. **Next Game** (`sensor.teamsnap_next_game`)
   - Shows the date and time of the next upcoming game
   - **State**: Date/time of next game (e.g., "2025-01-15 18:00")
   - **Attributes**:
     - `next_game`: Name of the game/event
     - `next_game_date`: Date of the game
     - `next_game_time`: Time of the game
     - `next_game_location`: Location/venue name
     - `next_game_opponent`: Opponent team name
     - `team_name`: Your team's name
     - `team_id`: Team ID

2. **Upcoming Events Count** (`sensor.teamsnap_upcoming_events_count`)
   - Counts all upcoming events (games, practices, etc.) across all teams
   - **State**: Number of upcoming events
   - **Unit**: "events"
   - Useful for dashboards and automations

3. **Next Practice** (`sensor.teamsnap_next_practice`)
   - Shows the date and time of the next practice session
   - **State**: Date/time of next practice (e.g., "2025-01-14 16:30")
   - **Attributes**:
     - `next_practice`: Name of the practice
     - `team_name`: Your team's name
     - `team_id`: Team ID

### Key Features

- **Multi-Team Support**: Automatically tracks events from all teams in your TeamSnap account
- **Automatic Updates**: Data refreshes every 15 minutes to keep information current
- **Smart Filtering**: Automatically identifies games vs practices and finds the next upcoming event
- **Rich Attributes**: Each sensor includes detailed information for use in automations and dashboards
- **Secure Authentication**: Uses OAuth 2.0 for secure, token-based authentication

### Use Cases

- **Automations**: Create automations that trigger based on game times (e.g., "Turn on lights 1 hour before game")
- **Dashboards**: Display upcoming games and practices on your Home Assistant dashboard
- **Notifications**: Set up notifications for upcoming events
- **Calendar Integration**: Use the sensor data to create calendar events or reminders
- **Voice Assistants**: Ask "When is the next game?" and get the answer from Home Assistant

### Example Automations

```yaml
# Example: Notify 2 hours before a game
automation:
  - alias: "Notify before game"
    trigger:
      - platform: template
        value_template: >
          {{ states('sensor.teamsnap_next_game') != 'unknown' }}
    condition:
      - condition: template
        value_template: >
          {% set next_game = state_attr('sensor.teamsnap_next_game', 'next_game_time') %}
          {% set game_dt = strptime(next_game, '%H:%M') if next_game else None %}
          {{ (game_dt - now()).total_seconds() / 3600 <= 2 if game_dt else false }}
    action:
      - service: notify.mobile_app
        data:
          message: >
            Game in 2 hours! {{ state_attr('sensor.teamsnap_next_game', 'next_game') }}
            at {{ state_attr('sensor.teamsnap_next_game', 'next_game_location') }}
```

More features coming soon!