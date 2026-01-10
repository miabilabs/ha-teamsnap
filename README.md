# ha-teamsnap

![TeamSnap Logo](icon.png)

Home Assistant Integration for TeamSnap

Just a dad, trying to make sense of his kids Sports commitments, with Home Assistant.  More to come!

## Installation

Install this integration through [HACS](https://hacs.xyz/) (Home Assistant Community Store) or manually by copying the `custom_components/teamsnap` folder to your Home Assistant `custom_components` directory.

## Configuration

### Step 1: Create a TeamSnap OAuth Application

1. Go to [https://auth.teamsnap.com](https://auth.teamsnap.com) and sign in
2. Create a new OAuth application
3. **Important:** Set the redirect URI to:
   ```
   https://YOUR_HOME_ASSISTANT_URL/auth/external/callback
   ```
   
   Replace `YOUR_HOME_ASSISTANT_URL` with your actual Home Assistant URL:
   - For local access: `homeassistant.local:8123` or `192.168.1.100:8123`
   - For remote access: `yourdomain.duckdns.org` or your custom domain
   
   **Example redirect URIs:**
   - `https://homeassistant.local:8123/auth/external/callback`
   - `https://192.168.1.100:8123/auth/external/callback`
   - `https://yourdomain.duckdns.org/auth/external/callback`

4. Save your **Client ID** and **Client Secret** - you'll need these in the next step

### Step 2: Add the Integration in Home Assistant

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **TeamSnap** and select it
4. Enter your **Client ID** and **Client Secret** from Step 1
5. Complete the OAuth authorization flow
6. Your TeamSnap integration is now configured!

## Features

- Track upcoming games and practices
- Monitor team schedules
- Get notified about sports events

More features coming soon!