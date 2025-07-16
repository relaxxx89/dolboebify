"""Custom exceptions for the Dolboebify audio player."""


class DolboebifyError(Exception):
    """Base exception for all Dolboebify errors."""
    pass


class AudioFormatNotSupportedError(DolboebifyError):
    """Raised when an unsupported audio format is encountered."""
    pass


class PlaybackError(DolboebifyError):
    """Raised when there is an error during audio playback."""
    pass


class PlaylistError(DolboebifyError):
    """Raised when there is an error with playlist operations."""
    pass 