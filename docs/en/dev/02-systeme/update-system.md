---
i18n:
  en: "Update System"
  fr: "Système de mises à jour"
---

# Update System

## Overview

The game includes an automatic update checking system that queries the GitHub API to detect newly published versions.

## Architecture

### Modules

**`src/utils/update_checker.py`**

Main update checking module:

- `check_for_updates()`: Checks if an update is available (respects cache and config)
- `check_for_updates_force()`: Forces checking (ignores cache and dev mode)
- `get_current_version()`: Returns current game version
- `_should_check_updates()`: Determines if a check should be performed
- `_update_cache()`: Updates cache file
- `_get_cached_update_info()`: Retrieves info from cache

**`src/ui/update_notification.py`**

Visual notification widget:

- Displays a discreet notification in the top-right corner
- Two buttons: "Download" (opens GitHub) and "Later" (closes)
- Mouse event handling (hover, click)
- Rendering with transparency and animations

### Main Menu Integration

**`main.py`**

The main menu launches the check asynchronously:

```python
def _check_for_updates_async(self):
    """Checks for updates asynchronously."""
    def check_updates():
        update_info = check_for_updates()
        if update_info:
            new_version, release_url = update_info
            current_version = get_project_version()
            self.update_notification = UpdateNotification(
                new_version, 
                current_version, 
                release_url
            )
    
    thread = threading.Thread(target=check_updates, daemon=True)
    thread.start()
```

## How It Works

### 1. Startup Check

When the main menu launches:

1. A daemon thread is created to avoid blocking the UI
2. `check_for_updates()` is called
3. The system checks if verification should be performed:
   - `check_updates` config must be `true`
   - Dev mode must be disabled
   - Cache must be expired (>24h) or non-existent

### 2. GitHub API Request

If checking is authorized:

```python
GITHUB_API_URL = "https://api.github.com/repos/Fydyr/Galad-Islands/releases/latest"
response = requests.get(GITHUB_API_URL, timeout=5)
data = response.json()
latest_version = data.get("tag_name", "").lstrip("v")
release_url = data.get("html_url", "")
```

### 3. Version Comparison

Uses the `packaging` module for semantic comparison:

```python
from packaging import version

if version.parse(latest_version) > version.parse(__version__):
    return (latest_version, release_url)
```

### 4. Caching

Result saved in `.update_cache.json`:

```json
{
  "last_check": "2025-11-02T18:04:52.652667",
  "update_available": false,
  "new_version": null,
  "release_url": null,
  "current_version": "0.10.0"
}
```

### 5. Notification Display

If an update is detected, an `UpdateNotification` is created and displayed in the menu.

## Configuration

### Parameters

**`galad_config.json`**

```json
{
  "check_updates": true,  // Enable/disable checking
  "dev_mode": false       // If true, ignore checks
}
```

### Constants

**`src/utils/update_checker.py`**

```python
GITHUB_API_URL = "https://api.github.com/repos/Fydyr/Galad-Islands/releases/latest"
TIMEOUT = 5  # Request timeout in seconds
CACHE_FILE = ".update_cache.json"
CACHE_DURATION_HOURS = 24  # Cache validity duration
```

## Error Handling

The system is robust and handles several error cases:

| Error | Behavior |
|-------|----------|
| Network timeout | Uses cache if available |
| GitHub API error | Log warning, return cache |
| Corrupted cache | Ignore and recheck |
| No connection | Fails silently |
| Dev mode enabled | Ignore check |

**Example handling**:

```python
try:
    response = requests.get(GITHUB_API_URL, timeout=TIMEOUT)
    response.raise_for_status()
    # Processing...
except requests.exceptions.Timeout:
    logger.warning("Timeout exceeded")
    return _get_cached_update_info()
except requests.exceptions.RequestException as e:
    logger.warning(f"Network error: {e}")
    return _get_cached_update_info()
```

## User Interface

### Notification

**Appearance**:

- Position: Top-right corner
- Size: 350x120 pixels
- Style: Semi-transparent blue background with border
- Effects: Button hover

**Buttons**:

- **"Download"**: Opens `release_url` in browser via `webbrowser.open()`
- **"Later"**: Closes notification (`dismissed = True`)

**Event Handling**:

```python
def handle_event(self, event: pygame.event.Event) -> bool:
    if event.type == pygame.MOUSEMOTION:
        self._update_hover_state(mouse_x, mouse_y)
        return True
    elif event.type == pygame.MOUSEBUTTONDOWN:
        if download_rect.collidepoint(mouse_x, mouse_y):
            self._open_release_page()
            self.dismissed = True
            return True
        elif later_rect.collidepoint(mouse_x, mouse_y):
            self.dismissed = True
            return True
    return False
```

### Options (to be implemented)

A "Check for updates" option will be added in the Options menu with:

- ☑️ Checkbox "Automatically check on startup"
- 🔄 "Check now" button (calls `check_for_updates_force()`)
- ℹ️ Behavior description (24h cache, ignore in dev mode)

## Testing

### Manual Test

**Test script**: `test_update_notification.py`

Forces notification display with a mocked version:

```bash
python3 test_update_notification.py
```

### Check Test

```python
from src.utils.update_checker import check_for_updates

result = check_for_updates()
if result:
    version, url = result
    print(f"Update available: {version}")
    print(f"URL: {url}")
else:
    print("No update available")
```

### Forced Test (ignores cache and dev mode)

```python
from src.utils.update_checker import check_for_updates_force

result = check_for_updates_force()
# Always performs a network check
```

## Translations

### i18n Keys

**French (`assets/locales/french.py`)**:

```python
"update.available_title": "Mise à jour disponible",
"update.available_message": "Une nouvelle version ({version}) est disponible !\nVous utilisez actuellement la version {current_version}.",
"update.download_button": "Télécharger",
"update.later_button": "Plus tard",
"update.checking": "Vérification des mises à jour...",
"update.no_update": "Vous utilisez la dernière version !",
"update.check_failed": "Impossible de vérifier les mises à jour",
```

**English (`assets/locales/english.py`)**:

```python
"update.available_title": "Update Available",
"update.available_message": "A new version ({version}) is available!\nYou are currently using version {current_version}.",
"update.download_button": "Download",
"update.later_button": "Later",
"update.checking": "Checking for updates...",
"update.no_update": "You are using the latest version!",
"update.check_failed": "Unable to check for updates",
```

## Best Practices

### Development

- ✅ Always enable `dev_mode: true` during development
- ✅ Use `check_for_updates_force()` for testing
- ✅ Check logs with DEBUG level
- ✅ Test with and without internet connection

### Production

- ✅ Cache limits GitHub requests (max 1/day)
- ✅ Check is asynchronous (no UI blocking)
- ✅ Errors are silent (no crashes)
- ✅ User can disable the feature

### GitHub Rate Limiting

GitHub API allows:

- **60 requests/hour** for unauthenticated IP
- **5000 requests/hour** with OAuth token

Our system respects these limits with:

- 24h cache (max 1 request/day/user)
- 5 seconds timeout
- Robust error handling

## Dependencies

```txt
requests>=2.31.0  # HTTP requests to GitHub API
packaging>=23.0   # Semantic version comparison
```

## Related Files

```text
src/
  utils/
    update_checker.py        # Check logic
  ui/
    update_notification.py   # Notification widget
  version.py                 # Current version (__version__)
  settings/
    settings.py              # Configuration (check_updates)
main.py                      # Main menu integration
galad_config.json            # User config
.update_cache.json           # Cache (generated)
requirements.txt             # Dependencies
```

## Future Enhancements

### Proposed

- [ ] "Check now" button in Options
- [ ] Beta/pre-release version notification
- [ ] Direct download in application
- [ ] Changelog displayed in notification
- [ ] Offline mode support (no error if no connection)

### Under Discussion

- [ ] Auto-update (automatic download and installation)
- [ ] Update channels (stable, beta, dev)
- [ ] Anonymous usage statistics
