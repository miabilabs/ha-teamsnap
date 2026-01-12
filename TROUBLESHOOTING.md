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
   - **Where to check**: Go to **Settings** → **System** → **Logs** (or check `/config/home-assistant.log` via SSH)
   - **What to search for**: Look for errors containing:
     - `ImportError`
     - `ModuleNotFoundError`
     - `AttributeError`
     - `SyntaxError`
     - `Unable to import integration: teamsnap`
     - `Setup failed for teamsnap`
   - **Example error messages**:
     ```
     ERROR (MainThread) [homeassistant.loader] Unable to import integration teamsnap: No module named 'custom_components.teamsnap'
     ERROR (MainThread) [homeassistant.setup] Setup failed for teamsnap: Integration failed to initialize
     ```
   - These errors indicate the integration isn't being loaded properly

3. **Clear All Caches**:
   ```bash
   # SSH into Home Assistant
   rm -rf /config/custom_components/teamsnap/__pycache__
   # Also clear Home Assistant's cache
   # Then restart Home Assistant
   ```

### Step 7: Understand What Should Happen After Submitting Credentials

When you enter your Client ID and Client Secret and click Submit, here's the expected flow:

1. **Form Submission** → `async_step_user()` is called with your credentials
2. **Application Credentials** → Credentials are stored via Home Assistant's Application Credentials system
3. **Parent Class Called** → `super().async_step_pick_implementation()` is called
4. **OAuth URL Generated** → Parent class generates the OAuth authorization URL using Application Credentials
5. **Redirect to TeamSnap** → You should be redirected to TeamSnap to authorize

### Step 8: Review Log Output

When you see the "missing_configuration" error, look for these log entries (in order):

**Expected Log Messages:**
```
=== async_step_user called ===
=== USER SUBMITTED FORM ===
User submitted credentials - client_id length: X, client_secret length: Y
Credentials stored via Application Credentials
=== PROCEEDING WITH OAUTH FLOW ===
About to call super().async_step_pick_implementation()
=== CALLING PARENT'S async_step_pick_implementation ===
```

**What These Logs Tell You:**
- If you see **none of these logs** → The integration might not be loading properly (check for import errors)
- If you see logs up to `"CALLING PARENT'S async_step_pick_implementation"` but then get the error → The parent class is not finding our implementation
- If you see `ImportError` or `ModuleNotFoundError` → The integration files aren't being loaded correctly

The logs will help identify exactly where the flow is failing.

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

## Understanding the "missing_configuration" Error

This error typically occurs when Home Assistant's OAuth2 framework (`AbstractOAuth2FlowHandler`) cannot find a valid OAuth implementation via Application Credentials. This can happen if:

1. **Application Credentials not configured** - The Client ID and Client Secret need to be configured in Home Assistant's Application Credentials system
2. **The implementation isn't properly registered** - There might be an error during Application Credentials registration
3. **Python cache is stale** - Old bytecode might be preventing the new code from loading (especially with HACS installations)
4. **OAuth URLs mismatch** - The redirect URI in your TeamSnap OAuth app doesn't match Home Assistant's expected redirect URI

## Still Having Issues?

If you're still experiencing issues after following these steps:

1. **Collect logs** with debug logging enabled (see Step 1)
2. **Verify installation** (check files are in correct location)
3. **Clear Python cache** (especially after HACS updates)
4. **Check for import errors** (see Step 6)
5. **Review expected log messages** (see Step 8) to identify where the flow is failing
6. **Take a screenshot** of the error message
7. **Note your Home Assistant version** (Settings → System → Information)
8. **Note your HACS version** (if using HACS)
9. **Check the GitHub Issues** at [https://github.com/miabilabs/ha-teamsnap/issues](https://github.com/miabilabs/ha-teamsnap/issues)
10. **Create a new issue** with the collected information

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
