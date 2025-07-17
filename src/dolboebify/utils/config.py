"""Configuration settings for the Dolboebify player."""

import json
import os
from pathlib import Path
from typing import Any, Dict

# Default configuration
DEFAULT_CONFIG = {
    # Cover art settings
    "cover_art": {
        "enabled": True,
        "fetch_online": True,
        "timeout": 2.0,  # Request timeout in seconds
        "cache_ttl": 3600,  # Failed cache TTL in seconds (1 hour)
        "cache_max_size": 1000,  # Maximum number of cached covers
    }
}

# Configuration directory
CONFIG_DIR = Path.home() / ".config" / "dolboebify"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Ensure the config directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)

# The loaded configuration
_config = None


def get_config() -> Dict[str, Any]:
    """
    Get the application configuration.

    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    global _config

    if _config is not None:
        return _config

    # Try to load config from file
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                user_config = json.load(f)

            # Merge with defaults to ensure all required keys are present
            _config = DEFAULT_CONFIG.copy()
            _update_dict_recursive(_config, user_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}")
            _config = DEFAULT_CONFIG.copy()
    else:
        # Use defaults and save to file
        _config = DEFAULT_CONFIG.copy()
        save_config()

    return _config


def save_config():
    """Save the current configuration to disk."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(_config or DEFAULT_CONFIG, f, indent=2)
    except IOError as e:
        print(f"Error saving config: {e}")


def _update_dict_recursive(base_dict: Dict, update_dict: Dict):
    """
    Update a nested dictionary recursively.

    Args:
        base_dict: Dictionary to update
        update_dict: Values to update with
    """
    for key, value in update_dict.items():
        if (
            key in base_dict
            and isinstance(base_dict[key], dict)
            and isinstance(value, dict)
        ):
            _update_dict_recursive(base_dict[key], value)
        else:
            base_dict[key] = value


def get_setting(section: str, key: str, default=None) -> Any:
    """
    Get a specific setting from the configuration.

    Args:
        section: Configuration section
        key: Setting key
        default: Default value if not found

    Returns:
        Any: The setting value or default
    """
    config = get_config()
    return config.get(section, {}).get(key, default)
