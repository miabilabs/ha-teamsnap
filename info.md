# TeamSnap Integration

Home Assistant integration for TeamSnap - manage your kids' sports commitments with Home Assistant.

## Features

- Track upcoming games and practices
- Monitor team schedules across multiple teams
- Get detailed information about next games (location, opponent, time)
- Count upcoming events for planning
- Automatic updates every 15 minutes

## Installation

Install this integration through [HACS](https://hacs.xyz/) or manually by copying the `custom_components/teamsnap` folder to your Home Assistant `custom_components` directory.

## Configuration

1. Register an OAuth application at [https://auth.teamsnap.com](https://auth.teamsnap.com)
2. Set the redirect URI to: `https://YOUR_HOME_ASSISTANT_URL/auth/external/callback`
3. Add the integration in Home Assistant through Settings → Devices & Services
4. Enter your OAuth Client ID and Client Secret
5. Complete the OAuth authorization flow

For detailed setup instructions, see the [README](README.md).
