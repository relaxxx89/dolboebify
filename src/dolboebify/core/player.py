"""Core player implementation for audio playback."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import vlc

from dolboebify.utils.exceptions import AudioFormatNotSupportedError


class Player:
    """Core audio player class supporting multiple formats."""

    # Supported audio formats
    SUPPORTED_FORMATS = [
        "mp3",
        "wav",
        "ogg",
        "flac",
        "aac",
        "wma",
        "m4a",
        "aiff",
        "alac",
    ]

    def __init__(self):
        """Initialize the player."""
        self.instance = vlc.Instance("--no-xlib")
        self.media_player = self.instance.media_player_new()
        self.current_media = None
        self.playlist: List[Dict[str, str]] = []
        self.current_index = -1
        self._volume = 70
        self._paused = False
        self._duration = 0
        self.media_player.audio_set_volume(self._volume)

    @property
    def volume(self) -> int:
        """Get the current volume level."""
        return self._volume

    @volume.setter
    def volume(self, value: int):
        """Set the volume level."""
        if 0 <= value <= 100:
            self._volume = value
            self.media_player.audio_set_volume(value)

    @property
    def is_playing(self) -> bool:
        """Check if media is currently playing."""
        return bool(self.media_player.is_playing())

    @property
    def is_paused(self) -> bool:
        """Check if media is paused."""
        return self._paused

    @property
    def duration(self) -> int:
        """Get the total duration of the current track in milliseconds."""
        return self._duration

    @property
    def position(self) -> int:
        """Get the current playback position in milliseconds."""
        if self.current_media:
            return int(self.media_player.get_time())
        return 0

    @position.setter
    def position(self, value: int):
        """Set the playback position in milliseconds."""
        if self.current_media:
            self.media_player.set_time(value)

    @property
    def position_percent(self) -> float:
        """Get the current playback position as a percentage."""
        if self._duration > 0:
            return (self.position / self._duration) * 100
        return 0.0

    @position_percent.setter
    def position_percent(self, value: float):
        """Set the playback position as a percentage."""
        if 0 <= value <= 100 and self._duration > 0:
            position_ms = int((value / 100) * self._duration)
            self.position = position_ms

    def _is_format_supported(self, file_path: Union[str, Path]) -> bool:
        """Check if the file format is supported."""
        ext = os.path.splitext(str(file_path))[1].lower()[1:]
        return ext in self.SUPPORTED_FORMATS

    def load(self, file_path: Union[str, Path]) -> bool:
        """
        Load an audio file.

        Args:
            file_path: Path to the audio file

        Returns:
            bool: True if successful, False otherwise

        Raises:
            AudioFormatNotSupportedError: If the audio format is not supported
            FileNotFoundError: If the file does not exist
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not self._is_format_supported(path):
            raise AudioFormatNotSupportedError(
                f"Format not supported: {path.suffix[1:]}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        # Create a VLC media object
        media = self.instance.media_new(str(path.absolute()))
        self.media_player.set_media(media)
        self.current_media = media

        # Parse media info
        media.parse()
        self._duration = media.get_duration()

        return True

    def play(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """
        Play an audio file. If file_path is None, resume current track.

        Args:
            file_path: Path to the audio file (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        if file_path:
            try:
                self.load(file_path)
            except (FileNotFoundError, AudioFormatNotSupportedError) as e:
                print(f"Error loading file: {e}")
                return False

        result = self.media_player.play()
        self._paused = False
        return result == 0

    def pause(self):
        """Pause playback."""
        self.media_player.pause()
        self._paused = not self._paused

    def stop(self):
        """Stop playback."""
        self.media_player.stop()
        self._paused = False

    def next_track(self) -> bool:
        """Play the next track in the playlist."""
        if not self.playlist or self.current_index >= len(self.playlist) - 1:
            return False

        self.current_index += 1
        track = self.playlist[self.current_index]
        return self.play(track["path"])

    def previous_track(self) -> bool:
        """Play the previous track in the playlist."""
        if not self.playlist or self.current_index <= 0:
            return False

        self.current_index -= 1
        track = self.playlist[self.current_index]
        return self.play(track["path"])

    def add_to_playlist(self, file_path: Union[str, Path]) -> bool:
        """Add a track to the playlist."""
        path = Path(file_path)

        if not path.exists():
            print(f"File not found: {path}")
            return False

        if not self._is_format_supported(path):
            print(f"Format not supported: {path.suffix[1:]}")
            return False

        # Extract metadata if possible
        title = path.stem

        track = {
            "path": str(path),
            "title": title,
        }

        self.playlist.append(track)

        # If this is the first track added, set the current index
        if len(self.playlist) == 1:
            self.current_index = 0

        return True

    def clear_playlist(self):
        """Clear the playlist."""
        self.playlist = []
        self.current_index = -1

    def load_playlist(self, directory: Union[str, Path]) -> int:
        """
        Load all supported audio files from a directory into the playlist.

        Args:
            directory: Path to directory

        Returns:
            int: Number of tracks added
        """
        path = Path(directory)
        if not path.exists() or not path.is_dir():
            print(f"Directory not found: {path}")
            return 0

        count = 0
        for file_path in path.glob("**/*"):
            if file_path.is_file() and self._is_format_supported(file_path):
                if self.add_to_playlist(file_path):
                    count += 1

        return count
