"""Core player implementation for audio playback."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import vlc

from dolboebify.utils.coverart import fetch_cover_art
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

    # Supported image formats for track covers
    SUPPORTED_IMAGE_FORMATS = [
        "jpg",
        "jpeg",
        "png",
        "webp",
        "bmp",
    ]

    def __init__(self):
        """Initialize the player."""
        self.instance = vlc.Instance("--no-xlib")
        self.media_player = (
            self.instance.media_player_new()
            if self.instance is not None
            else None
        )
        self.current_media = None
        self.playlist: List[Dict[str, str]] = []
        self.current_index = -1
        self._volume = 70
        self._paused = False
        self._duration = 0
        if self.media_player is not None:
            self.media_player.audio_set_volume(self._volume)
        self._track_images = {}  # Maps track paths to image paths

    @property
    def volume(self) -> int:
        """Get the current volume level."""
        return self._volume

    @volume.setter
    def volume(self, value: int):
        """Set the volume level."""
        if 0 <= value <= 100:
            self._volume = value
            if self.media_player is not None:
                self.media_player.audio_set_volume(value)

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
        if self.current_media and self.media_player is not None:
            return int(self.media_player.get_time())
        return 0

    @position.setter
    def position(self, value: int):
        """Set the playback position in milliseconds."""
        if self.current_media and self.media_player is not None:
            self.media_player.set_time(value)
        if self._duration > 0:
            return (self.position / self._duration) * 100

        @property
        def position_percent(self) -> float:
            """Get the playback position as a percentage."""
            if self._duration > 0:
                return (self.position / self._duration) * 100
            return 0.0

        @position_percent.setter
        def position_percent(self, value: float):
            """Set the playback position as a percentage."""
            if 0 <= value <= 100 and self._duration > 0:
                position_ms = int((value / 100) * self._duration)
                self.position = position_ms
            self.position = position_ms

    def _is_format_supported(self, file_path: Union[str, Path]) -> bool:
        """Check if the file format is supported."""
        ext = os.path.splitext(str(file_path))[1].lower()[1:]
        return ext in self.SUPPORTED_FORMATS

    def _is_image_format_supported(self, file_path: Union[str, Path]) -> bool:
        """Check if the image file format is supported."""
        ext = os.path.splitext(str(file_path))[1].lower()[1:]
        return ext in self.SUPPORTED_IMAGE_FORMATS

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

        # Create a VLC media object, handling NoneType errors
        if self.instance is None or self.media_player is None:
            raise RuntimeError(
                "VLC instance or media player is not initialized."
            )

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

        if self.media_player is None:
            print("Error: media player is not initialized.")
            return False

        result = self.media_player.play()
        self._paused = False
        return result == 0
        """Pause playback."""
        self.media_player.pause()
        self._paused = not self._paused

    def stop(self):
        """Stop playback."""
        if self.media_player is not None:
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

    def set_track_image(
        self, track_path: Union[str, Path], image_path: Union[str, Path]
    ) -> bool:
        """
        Associate an image with a specific track.

        Args:
            track_path: Path to the audio file
            image_path: Path to the image file

        Returns:
            bool: True if successful, False otherwise

        Raises:
            FileNotFoundError: If the track or image file does not exist
            ValueError: If the image format is not supported
        """
        track_path = Path(track_path)
        image_path = Path(image_path)

        # Validate track and image exist
        if not track_path.exists():
            raise FileNotFoundError(f"Track not found: {track_path}")

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Check if image format is supported
        if not self._is_image_format_supported(image_path):
            raise ValueError(
                f"Image format not supported: {image_path.suffix[1:]}. "
                f"Supported formats: {', '.join(self.SUPPORTED_IMAGE_FORMATS)}"
            )

        # Store the association
        self._track_images[str(track_path.absolute())] = str(
            image_path.absolute()
        )

        # If the track is in the playlist, update its metadata
        for track in self.playlist:
            if Path(track["path"]).absolute() == track_path.absolute():
                track["image"] = str(image_path.absolute())

        return True

    def get_track_image(self, track_path: Union[str, Path]) -> Optional[str]:
        """
        Get the image path associated with a specific track.

        Args:
            track_path: Path to the audio file

        Returns:
            Optional[str]: Path to the image file, or None if no image is associated
        """
        track_path = str(Path(track_path).absolute())

        # Check if we have a custom image set for this track
        if track_path in self._track_images:
            return self._track_images[track_path]

        # Look for standard cover files in the track's directory
        path = Path(track_path)
        for name in (
            "cover.jpg",
            "folder.jpg",
            "front.jpg",
            "album.jpg",
            "artwork.jpg",
        ):
            cover_path = path.parent / name
            if cover_path.exists():
                return str(cover_path)

        # If no local cover found, try fetching from online sources
        online_cover = fetch_cover_art(track_path)
        if online_cover:
            # Cache this association for future use
            self._track_images[track_path] = online_cover

            # Update playlist entry if this track is in the playlist
            for track in self.playlist:
                track_path_abs = Path(track["path"]).absolute()
                if track_path_abs == Path(track_path).absolute():
                    track["image"] = online_cover

            return online_cover

        return None

    def remove_track_image(self, track_path: Union[str, Path]) -> bool:
        """
        Remove the image association for a specific track.

        Args:
            track_path: Path to the audio file

        Returns:
            bool: True if an association was removed, False if none existed
        """
        track_path = str(Path(track_path).absolute())

        if track_path in self._track_images:
            del self._track_images[track_path]

            # Update any playlist entries
            for track in self.playlist:
                is_match = (
                    Path(track["path"]).absolute()
                    == Path(track_path).absolute()
                )
                if is_match and "image" in track:
                    del track["image"]

            return True

        return False
