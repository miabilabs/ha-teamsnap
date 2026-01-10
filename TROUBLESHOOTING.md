# Troubleshooting Guide

## "missing_configuration" Error

If you're seeing a "missing_configuration" error when trying to add the TeamSnap integration, follow these steps:

### Step 1: Enable Debug Logging

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Find the **TeamSnap** integration (or try to add it)
3. Click the three dots (⋮) in the top right
4. Select **Enable debug logging**
5. Try adding the integration again
6. Check the logs (see Step 2)

### Step 2: Check Home Assistant Logs

**Option A: Via UI**
1. Go to **Settings** → **System** → **Logs**
2. Look for entries containing `teamsnap` or `OAuth`
3. Copy the relevant log entries

**Option B: Via Configuration File**
1. SSH into your Home Assistant instance
2. Check the logs: `tail -f /config/home-assistant.log | grep -i teamsnap`
3. Or view full logs: `cat /config/home-assistant.log | grep -i teamsnap`

**Option C: Enable Logger Component**
Add this to your `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.teamsnap: debug
```

Then restart Home Assistant and try again.

### Step 3: Verify Your OAuth Application

1. Go to [https://auth.teamsnap.com](https://auth.teamsnap.com)
2. Sign in to your TeamSnap account
3. Check your OAuth application:
   - **Client ID** and **Client Secret** are present
   - **Redirect URI** matches exactly: `https://YOUR_HOME_ASSISTANT_URL/auth/external/callback`
   - Replace `YOUR_HOME_ASSISTANT_URL` with your actual Home Assistant URL
   - Examples:
     - `https://homeassistant.local:8123/auth/external/callback`
     - `https://192.168.1.100:8123/auth/external/callback`
     - `https://yourdomain.duckdns.org/auth/external/callback`

### Step 4: Verify Home Assistant URLs

1. Go to **Settings** → **System** → **Network**
2. Ensure both **Internal URL** and **External URL** are set correctly
3. The redirect URI shown in the integration form must match what's in your TeamSnap OAuth app

### Step 5: Check for Common Issues

- **Credentials copied correctly?** Make sure there are no extra spaces before/after the Client ID or Client Secret
- **OAuth app saved?** Ensure you clicked "Save" after creating/updating your OAuth application in TeamSnap
- **Full restart?** After updating the integration, perform a **full restart** of Home Assistant (not just a reload)

### Step 6: Review Log Output

When you see the "missing_configuration" error, look for these log entries:

- `"User submitted credentials"` - Confirms credentials were received
- `"Credentials stored in instance variables"` - Confirms credentials were stored
- `"OAuth implementation created"` - Confirms implementation was created
- `"OAuth flow error"` - Shows the actual error

The logs will help identify where the flow is failing.

## Still Having Issues?

If you're still experiencing issues after following these steps:

1. **Collect logs** with debug logging enabled (see Step 1)
2. **Take a screenshot** of the error message
3. **Note your Home Assistant version** (Settings → System → Information)
4. **Check the GitHub Issues** at [https://github.com/miabilabs/ha-teamsnap/issues](https://github.com/miabilabs/ha-teamsnap/issues)
5. **Create a new issue** with the collected information

## Common Error Messages

### "missing_configuration"
- **Cause:** Home Assistant cannot find a valid OAuth implementation
- **Solution:** Verify credentials are correct and redirect URI matches exactly

### "oauth_setup_error"
- **Cause:** Unable to initialize OAuth flow
- **Solution:** Check that Client ID and Client Secret are valid

### "client_id_required" or "client_secret_required"
- **Cause:** One or both fields are empty
- **Solution:** Enter both Client ID and Client Secret
