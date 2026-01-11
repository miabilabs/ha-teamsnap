# Troubleshooting Guide

## "missing_configuration" Error

If you're seeing a "missing_configuration" error when trying to add the TeamSnap integration, follow these steps:

### Important: HACS Installation Notes

If you installed this integration via HACS as a **custom repository**, there are additional steps you may need to take:

1. **Verify Integration is Loaded**: Check if Home Assistant recognizes the integration
   - After restart, check logs for: `Loading integration: teamsnap` or `Setting up teamsnap`
   - If you see `Unable to import integration: teamsnap` or similar errors, the files aren't loading correctly

2. **Clear Python Cache**: After updating via HACS, Python bytecode cache might be stale
   - SSH into your Home Assistant instance
   - Remove the cache: `rm -rf /config/custom_components/teamsnap/__pycache__`
   - Or manually delete the `__pycache__` folder in the integration directory
   - **This is critical** - stale cache can cause the "missing_configuration" error

3. **Full Restart Required**: After HACS updates, always perform a **full restart** of Home Assistant (not just a reload)
   - Go to **Settings** → **System** → **Restart**
   - Wait for Home Assistant to fully restart (can take a few minutes)

4. **Verify Installation Location**: Ensure the integration is installed in the correct location
   - Should be at: `/config/custom_components/teamsnap/`
   - Verify all files are present: `__init__.py`, `config_flow.py`, `manifest.json`, `strings.json`, etc.
   - Check file permissions are correct (should be readable by Home Assistant)

5. **Manual Installation Alternative**: If HACS continues to cause issues, try manual installation:
   - Download the latest code from GitHub
   - Copy the `custom_components/teamsnap` folder to `/config/custom_components/`
   - Delete any `__pycache__` folders
   - Restart Home Assistant
   - This helps determine if the issue is HACS-specific or code-related

### Step 1: Enable Debug Logging

**Option A: Via Configuration File (Recommended if integration isn't installed yet)**

1. Go to **Settings** → **Developer Tools** → **YAML**
2. Or edit your `configuration.yaml` file directly
3. Add the following:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.teamsnap: debug
   ```
4. Click **Check Configuration** to verify it's valid
5. Click **Restart** to apply the changes
6. Try adding the integration again
7. Check the logs (see Step 2)

**Option B: Via Integration Card (Only if integration is already installed)**

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Find the **TeamSnap** integration card
3. Click the three dots (⋮) in the top right corner of the TeamSnap card
4. Select **Enable debug logging**
5. Try adding/updating the integration again
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

### Step 6: Verify Integration Files Are Loaded

If using HACS, verify the integration files are properly loaded:

1. **Check Integration Directory**:
   - SSH into Home Assistant
   - Verify files exist: `ls -la /config/custom_components/teamsnap/`
   - Should see: `__init__.py`, `config_flow.py`, `manifest.json`, `strings.json`, etc.

2. **Check for Import Errors**:
   - Look in logs for any `ImportError` or `ModuleNotFoundError` related to `teamsnap`
   - These would indicate the integration isn't being loaded properly

3. **Clear All Caches**:
   ```bash
   # SSH into Home Assistant
   rm -rf /config/custom_components/teamsnap/__pycache__
   # Also clear Home Assistant's cache
   # Then restart Home Assistant
   ```

### Step 7: Review Log Output

When you see the "missing_configuration" error, look for these log entries:

- `"User submitted credentials"` - Confirms credentials were received
- `"Credentials stored in instance variables"` - Confirms credentials were stored
- `"OAuth implementation created"` - Confirms implementation was created
- `"OAuth flow error"` - Shows the actual error
- Any `ImportError` or `ModuleNotFoundError` - Indicates file loading issues

The logs will help identify where the flow is failing.

## HACS Installation Specific Issues

If you installed via HACS as a custom repository and are experiencing issues:

### Verify Integration is Properly Installed

1. **Check Installation Location**:
   - SSH into Home Assistant
   - Verify: `ls -la /config/custom_components/teamsnap/`
   - Should contain: `__init__.py`, `config_flow.py`, `manifest.json`, `strings.json`, etc.

2. **Clear Python Cache** (Important after HACS updates):
   ```bash
   # SSH into Home Assistant
   rm -rf /config/custom_components/teamsnap/__pycache__
   ```

3. **Verify Integration is Loaded**:
   - Check logs for: `Loading integration: teamsnap`
   - Look for any `ImportError` or `ModuleNotFoundError` related to teamsnap
   - If you see import errors, the integration files may not be in the correct location

4. **Manual Installation Test**:
   - If HACS continues to cause issues, try manual installation:
     - Download the latest code from GitHub
     - Copy `custom_components/teamsnap` folder to `/config/custom_components/`
     - Delete any `__pycache__` folders
     - Restart Home Assistant
   - This helps determine if the issue is HACS-specific or code-related

### HACS Update Process

When updating via HACS:
1. Go to **HACS** → **Integrations**
2. Find **TeamSnap**
3. Click **Update Information** (refresh icon)
4. If update is available, click **Download**
5. **Important**: Perform a **full restart** (not reload) of Home Assistant
6. Clear Python cache: `rm -rf /config/custom_components/teamsnap/__pycache__`
7. Restart again if needed

## Still Having Issues?

If you're still experiencing issues after following these steps:

1. **Collect logs** with debug logging enabled (see Step 1)
2. **Verify installation** (check files are in correct location)
3. **Clear Python cache** (especially after HACS updates)
4. **Take a screenshot** of the error message
5. **Note your Home Assistant version** (Settings → System → Information)
6. **Note your HACS version** (if using HACS)
7. **Check the GitHub Issues** at [https://github.com/miabilabs/ha-teamsnap/issues](https://github.com/miabilabs/ha-teamsnap/issues)
8. **Create a new issue** with the collected information

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
