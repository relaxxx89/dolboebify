"""Utility modules for the Dolboebify audio player."""

from dolboebify.utils.cleanup import (
    clear_cover_cache,
    reset_failed_fetch_cache,
)
from dolboebify.utils.config import get_setting
from dolboebify.utils.coverart import fetch_cover_art
from dolboebify.utils.exceptions import (
    AudioFormatNotSupportedError,
    DolboebifyError,
    PlaybackError,
    PlaylistError,
)
from dolboebify.utils.fileutils import (
    check_file_type,
    get_audio_files,
    get_file_info,
    get_supported_formats,
)

__all__ = [
    "DolboebifyError",
    "AudioFormatNotSupportedError",
    "PlaybackError",
    "PlaylistError",
    "get_supported_formats",
    "get_audio_files",
    "check_file_type",
    "get_file_info",
    "fetch_cover_art",
    "get_setting",
    "clear_cover_cache",
    "reset_failed_fetch_cache",
]
