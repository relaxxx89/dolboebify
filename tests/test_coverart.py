"""Tests for the cover art fetching functionality."""

from unittest import mock

from dolboebify.utils.coverart import (
    fetch_cover_art,
    fetch_from_itunes,
    fetch_from_lastfm,
    get_cached_cover,
    parse_track_info,
    sanitize_filename,
    save_to_cache,
)


class TestCoverArtFetching:
    """Tests for cover art fetching functionality."""

    def test_parse_track_info(self):
        """Test parsing track info from filenames."""
        # Test standard artist - title format
        artist, title = parse_track_info("Artist - Title.mp3")
        assert artist == "Artist"
        assert title == "Title"

        # Test with track number
        artist, title = parse_track_info("01. Artist - Title.mp3")
        assert artist == "Artist"
        assert title == "Title"

        # Test with underscore format
        artist, title = parse_track_info("Artist_-_Title.mp3")
        assert artist == "Artist"
        assert title == "Title"

        # Test with no artist
        artist, title = parse_track_info("JustTitle.mp3")
        assert artist == ""
        assert title == "JustTitle"

        # Test with different dash types
        artist, title = parse_track_info("Artist – Title.mp3")  # en dash
        assert artist == "Artist"
        assert title == "Title"

    def test_sanitize_filename(self):
        """Test sanitizing filenames."""
        sanitized = sanitize_filename('Artist: "Title"?')
        assert sanitized == "Artist_ _Title__"
        assert "/" not in sanitized
        assert "\\" not in sanitized
        assert ":" not in sanitized
        assert "*" not in sanitized
        assert "?" not in sanitized
        assert '"' not in sanitized
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert "|" not in sanitized

    @mock.patch("os.path.exists")
    def test_get_cached_cover(self, mock_exists):
        """Test getting cached cover art."""
        # Mock that the cache file exists
        mock_exists.return_value = True

        # Test with valid artist and title
        with mock.patch("pathlib.Path.exists", return_value=True):
            cached = get_cached_cover("Artist", "Title")
            assert cached is not None
            assert "Artist_Title.jpg" in cached

        # Test with empty artist
        cached = get_cached_cover("", "Title")
        assert cached is None

    @mock.patch("builtins.open", mock.mock_open())
    def test_save_to_cache(self):
        """Test saving cover art to cache."""
        image_data = b"fake_image_data"

        path = save_to_cache("Artist", "Title", image_data)
        assert path is not None
        assert "Artist_Title.jpg" in path

    @mock.patch("requests.get")
    def test_fetch_from_itunes(self, mock_get):
        """Test fetching cover art from iTunes API."""
        # Mock a successful API response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resultCount": 1,
            "results": [{"artworkUrl100": "https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/b4/7a/aa/b47aaad3-7764-1d69-1f18-5bc66fe0c946/21UMGIM09915.rgb.jpg/100x100bb.jpg"}],
        }

        # Mock the image download
        mock_img_response = mock.Mock()
        mock_img_response.status_code = 200
        mock_img_response.content = b"fake_image_data"

        # Set up the side effect for get calls
        mock_get.side_effect = [mock_response, mock_img_response]

        # Mock the cache save
        with mock.patch(
            "dolboebify.utils.coverart.save_to_cache"
        ) as mock_save:
            mock_save.return_value = "/fake/path/to/cached/image.jpg"

            # Run the test
            result = fetch_from_itunes("Artist", "Title")

            # Verify results
            assert result == "/fake/path/to/cached/image.jpg"
            assert mock_get.call_count == 2

            # Check that URL was modified to get higher resolution
            _, kwargs = mock_get.call_args_list[1]
            assert "600x600" in kwargs.get("url", "")

    @mock.patch("requests.get")
    def test_fetch_from_lastfm(self, mock_get):
        """Test fetching cover art from Last.fm API."""
        # Mock a successful API response for track.getInfo
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "track": {
                "album": {
                    "image": [
                        {"#text": "", "size": "small"},
                        {
                            "#text": "https://lastfm.freetls.fastly.net/i/u/64s/2a96cbd8b46e442fc41c2b86b821562f.jpg",
                            "size": "medium",
                        },
                        {
                            "#text": "https://lastfm.freetls.fastly.net/i/u/174s/2a96cbd8b46e442fc41c2b86b821562f.jpg",
                            "size": "large",
                        },
                        {
                            "#text": "https://lastfm.freetls.fastly.net/i/u/300x300/2a96cbd8b46e442fc41c2b86b821562f.jpg",
                            "size": "extralarge",
                        },
                    ]
                }
            }
        }

        # Mock the image download
        mock_img_response = mock.Mock()
        mock_img_response.status_code = 200
        mock_img_response.content = b"fake_image_data"

        # Set up the side effect for get calls
        mock_get.side_effect = [mock_response, mock_img_response]

        # Mock the cache save
        with mock.patch(
            "dolboebify.utils.coverart.save_to_cache"
        ) as mock_save:
            mock_save.return_value = "/fake/path/to/cached/image.jpg"

            # Run the test
            result = fetch_from_lastfm("Artist", "Title")

            # Verify results
            assert result == "/fake/path/to/cached/image.jpg"
            assert mock_get.call_count == 2

            # Check that the extralarge image was used
            args, _ = mock_get.call_args_list[1]
            assert "extralarge" in args[0]

    @mock.patch("dolboebify.utils.coverart.fetch_from_itunes")
    @mock.patch("dolboebify.utils.coverart.fetch_from_lastfm")
    @mock.patch("dolboebify.utils.coverart.parse_track_info")
    def test_fetch_cover_art(self, mock_parse, mock_lastfm, mock_itunes):
        """Test the main fetch_cover_art function."""
        # Mock the track info parsing
        mock_parse.return_value = ("Artist", "Title")

        # Test when iTunes API finds the cover
        mock_itunes.return_value = "/path/to/itunes/cover.jpg"
        mock_lastfm.return_value = None

        result = fetch_cover_art("track.mp3")
        assert result == "/path/to/itunes/cover.jpg"
        assert mock_itunes.called
        assert not mock_lastfm.called

        # Reset mocks
        mock_itunes.reset_mock()
        mock_lastfm.reset_mock()

        # Test when iTunes fails but Last.fm finds the cover
        mock_itunes.return_value = None
        mock_lastfm.return_value = "/path/to/lastfm/cover.jpg"

        result = fetch_cover_art("track.mp3")
        assert result == "/path/to/lastfm/cover.jpg"
        assert mock_itunes.called
        assert mock_lastfm.called

        # Reset mocks
        mock_itunes.reset_mock()
        mock_lastfm.reset_mock()

        # Test when both APIs fail
        mock_itunes.return_value = None
        mock_lastfm.return_value = None

        result = fetch_cover_art("track.mp3")
        assert result is None
        assert mock_itunes.called
        assert mock_lastfm.called
