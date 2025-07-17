"""Configuration utilities for Dolboebify."""

import json
import os
from pathlib import Path

# Default configuration
DEFAULT_CONFIG = {
    "cover_art": {
        "enabled": True,
        "fetch_online": True,
        "timeout": 2.0,
        "cache_ttl": 3600,  # 1 hour
    },
    "player": {
        "default_volume": 70,
        "remember_last_position": True,
    },
    "ui": {
        "theme": "dark",
        "show_track_numbers": True,
    },
}

# Config file path
CONFIG_DIR = Path.home() / ".config" / "dolboebify"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config():
    """Load configuration from file or create default if it doesn't exist."""
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            # Ensure all default values exist
            for section, values in DEFAULT_CONFIG.items():
                if section not in config:
                    config[section] = values
                else:
                    for key, value in values.items():
                        if key not in config[section]:
                            config[section][key] = value
        return config
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """Save configuration to file."""
    # Ensure config directory exists
    os.makedirs(CONFIG_DIR, exist_ok=True)

    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving config: {e}")
        return False


def get_setting(section, key, default=None):
    """
    Get a setting from the configuration.

    Args:
        section: Section name
        key: Setting key
        default: Default value if the setting doesn't exist

    Returns:
        The setting value or default if not found
    """
    config = load_config()
    return config.get(section, {}).get(key, default)


def set_setting(section, key, value):
    """
    Set a setting in the configuration.

    Args:
        section: Section name
        key: Setting key
        value: Value to set

    Returns:
        bool: True if successful, False otherwise
    """
    config = load_config()

    if section not in config:
        config[section] = {}

    config[section][key] = value
    return save_config(config)
