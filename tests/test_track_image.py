"""Tests for track image API functionality."""

import os
from pathlib import Path
from unittest import mock

import pytest

from dolboebify.core import Player
from dolboebify.utils.exceptions import AudioFormatNotSupportedError


class TestTrackImageAPI:
    """Tests for the track image API functionality."""

    @pytest.fixture
    def player(self):
        """Fixture to create a Player instance."""
        with mock.patch("vlc.Instance"):
            player = Player()
            yield player

    def test_image_format_supported(self, player):
        """Test image format checking."""
        assert player._is_image_format_supported("image.jpg") is True
        assert player._is_image_format_supported("image.jpeg") is True
        assert player._is_image_format_supported("image.png") is True
        assert player._is_image_format_supported("image.webp") is True
        assert player._is_image_format_supported("image.bmp") is True
        assert player._is_image_format_supported("image.tiff") is False
        assert player._is_image_format_supported("image.gif") is False

    @mock.patch("pathlib.Path.exists")
    def test_set_track_image(self, mock_exists, player):
        """Test setting and getting track images."""
        # Mock path existence check
        mock_exists.return_value = True
        
        # Add a track to the playlist
        with mock.patch.object(player, "_is_format_supported", return_value=True):
            player.add_to_playlist("track.mp3")
        
        # Set image for the track
        with mock.patch.object(player, "_is_image_format_supported", return_value=True):
            result = player.set_track_image("track.mp3", "cover.jpg")
            assert result is True
            
        # Check if the image is associated with the track
        track_path = str(Path("track.mp3").absolute())
        assert track_path in player._track_images
        assert player._track_images[track_path] == str(Path("cover.jpg").absolute())
        
        # Check that playlist entry was updated
        assert player.playlist[0].get("image") == str(Path("cover.jpg").absolute())
        
        # Get the track image
        image_path = player.get_track_image("track.mp3")
        assert image_path == str(Path("cover.jpg").absolute())
        
    @mock.patch("pathlib.Path.exists")
    def test_remove_track_image(self, mock_exists, player):
        """Test removing track image association."""
        # Mock path existence check
        mock_exists.return_value = True
        
        # Add a track to the playlist and set an image
        with mock.patch.object(player, "_is_format_supported", return_value=True):
            player.add_to_playlist("track.mp3")
            
        with mock.patch.object(player, "_is_image_format_supported", return_value=True):
            player.set_track_image("track.mp3", "cover.jpg")
            
        track_path = str(Path("track.mp3").absolute())
        assert track_path in player._track_images
        
        # Remove the track image
        result = player.remove_track_image("track.mp3")
        assert result is True
        assert track_path not in player._track_images
        assert "image" not in player.playlist[0]
        
        # Try removing non-existent association
        result = player.remove_track_image("nonexistent.mp3")
        assert result is False
        
    @mock.patch("pathlib.Path.exists")
    def test_get_standard_covers(self, mock_exists, player):
        """Test finding standard cover files in track directory."""
        # Setup function to mock file existence based on name
        def mock_path_exists(path):
            if path.name in ["track.mp3", "album.jpg"]:
                return True
            return False
            
        mock_exists.side_effect = mock_path_exists
        
        # Test finding a standard cover file
        with mock.patch.object(Path, "parent") as mock_parent:
            mock_parent.return_value = Path("/fake/path")
            with mock.patch("pathlib.Path.with_name") as mock_with_name:
                # Set up the mock for Path.with_name().exists()
                mock_with_name.return_value = Path("/fake/path/album.jpg")
                
                image_path = player.get_track_image("track.mp3")
                assert image_path is not None
                
    @mock.patch("pathlib.Path.exists")
    def test_invalid_image_format(self, mock_exists, player):
        """Test setting an image with invalid format."""
        mock_exists.return_value = True
        
        with mock.patch.object(player, "_is_image_format_supported", return_value=False):
            with pytest.raises(ValueError):
                player.set_track_image("track.mp3", "cover.xyz")
                
    @mock.patch("pathlib.Path.exists")
    def test_nonexistent_track_or_image(self, mock_exists, player):
        """Test setting an image with nonexistent track or image."""
        # Mock track doesn't exist
        mock_exists.side_effect = [False, True]  # track doesn't exist, image exists
        with pytest.raises(FileNotFoundError):
            player.set_track_image("nonexistent.mp3", "cover.jpg")
            
        # Mock image doesn't exist
        mock_exists.side_effect = [True, False]  # track exists, image doesn't exist
        with pytest.raises(FileNotFoundError):
            player.set_track_image("track.mp3", "nonexistent.jpg") 