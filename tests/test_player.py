"""Tests for the Player class."""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from dolboebify.core import Player
from dolboebify.utils.exceptions import AudioFormatNotSupportedError


class TestPlayer:
    """Tests for the Player class."""

    @pytest.fixture
    def player(self):
        """Fixture to create a Player instance."""
        with mock.patch("vlc.Instance"):
            player = Player()
            yield player

    def test_init(self, player):
        """Test that a Player can be initialized."""
        assert player is not None
        assert player.volume == 70
        assert player.playlist == []
        assert player.current_index == -1

    def test_volume_setter(self, player):
        """Test setting the volume."""
        player.volume = 50
        assert player.volume == 50

        player.volume = -10
        assert player.volume == 50  # Should not change

        player.volume = 110
        assert player.volume == 50  # Should not change

    def test_is_format_supported(self, player):
        """Test format checking."""
        assert player._is_format_supported("file.mp3") is True
        assert player._is_format_supported("file.wav") is True
        assert player._is_format_supported("file.ogg") is True
        assert player._is_format_supported("file.flac") is True
        assert player._is_format_supported("file.txt") is False
        assert player._is_format_supported("file.xyz") is False

    @mock.patch("pathlib.Path.exists")
    def test_load_nonexistent_file(self, mock_exists, player):
        """Test loading a file that doesn't exist."""
        mock_exists.return_value = False
        with pytest.raises(FileNotFoundError):
            player.load("nonexistent_file.mp3")

    @mock.patch("pathlib.Path.exists")
    def test_load_unsupported_format(self, mock_exists, player):
        """Test loading a file with unsupported format."""
        mock_exists.return_value = True
        with pytest.raises(AudioFormatNotSupportedError):
            player.load("file.xyz")

    @mock.patch("pathlib.Path.exists")
    def test_add_to_playlist(self, mock_exists, player):
        """Test adding a track to the playlist."""
        mock_exists.return_value = True

        # Mock the format check
        player._is_format_supported = mock.MagicMock(return_value=True)

        result = player.add_to_playlist("track.mp3")
        assert result is True
        assert len(player.playlist) == 1
        assert player.playlist[0]["path"] == "track.mp3"
        assert player.current_index == 0

    def test_clear_playlist(self, player):
        """Test clearing the playlist."""
        # Set up a playlist first
        with mock.patch("pathlib.Path.exists", return_value=True):
            player._is_format_supported = mock.MagicMock(return_value=True)
            player.add_to_playlist("track1.mp3")
            player.add_to_playlist("track2.mp3")

        assert len(player.playlist) == 2

        player.clear_playlist()
        assert player.playlist == []
        assert player.current_index == -1
