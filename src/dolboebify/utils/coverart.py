"""Utilities for fetching track cover art from external sources."""

import json
import os
import re
import time
from pathlib import Path
from typing import Optional, Tuple, Union
from urllib.parse import quote

import requests

from dolboebify.utils.config import get_setting

# Cache directory for downloaded cover art
COVER_CACHE_DIR = Path.home() / ".cache" / "dolboebify" / "covers"

# Ensure the cache directory exists
os.makedirs(COVER_CACHE_DIR, exist_ok=True)

# Cache for failed fetches to avoid repeated attempts
_FAILED_FETCH_CACHE = {}  # {track_path: timestamp}


def parse_track_info(filename: str) -> Tuple[str, str]:
    """
    Parse artist and title from filename.

    Args:
        filename: The filename of the track

    Returns:
        Tuple[str, str]: Artist and title
    """
    # Remove file extension
    name = Path(filename).stem

    # Common patterns: "Artist - Title" or "Artist_-_Title" or "01. Artist - Title"
    patterns = [
        # "Artist - Title" or "01. Artist - Title"
        r"^(?:\d+\.\s*)?(.+?)\s*[-–—]\s*(.+)$",
        # "Artist_-_Title" or "01. Artist_-_Title"
        r"^(?:\d+\.\s*)?(.+?)_-_(.+)$",
    ]

    for pattern in patterns:
        match = re.match(pattern, name)
        if match:
            artist = match.group(1).strip()
            title = match.group(2).strip()

            # Strip trailing underscores if they exist (for Artist_-_Title format)
            if pattern.endswith("_-_(.+)$"):
                artist = artist.rstrip("_")

            return artist, title

    # If no pattern matches, use the whole name as title and empty string as artist
    return "", name


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be used as a filename.

    Args:
        name: The string to sanitize

    Returns:
        str: Sanitized string
    """
    # Replace characters that are invalid in filenames
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def get_cached_cover(artist: str, title: str) -> Optional[str]:
    """
    Check if cover art for the given artist/title is in the cache.

    Args:
        artist: Artist name
        title: Track title

    Returns:
        Optional[str]: Path to cached cover art, or None if not in cache
    """
    if not artist:
        return None

    cache_key = sanitize_filename(f"{artist}_{title}")
    cache_path = COVER_CACHE_DIR / f"{cache_key}.jpg"

    if cache_path.exists():
        return str(cache_path)

    return None


def save_to_cache(artist: str, title: str, image_data: bytes) -> str:
    """
    Save downloaded cover art to the cache.

    Args:
        artist: Artist name
        title: Track title
        image_data: Binary image data

    Returns:
        str: Path to the cached file
    """
    cache_key = sanitize_filename(f"{artist}_{title}")
    cache_path = COVER_CACHE_DIR / f"{cache_key}.jpg"

    with open(cache_path, "wb") as f:
        f.write(image_data)

    return str(cache_path)


def is_fetch_recently_failed(track_path: str) -> bool:
    """
    Check if we recently failed to fetch a cover for this track.

    Args:
        track_path: Path to the track

    Returns:
        bool: True if we recently failed and should not retry yet
    """
    # Get cache TTL from settings
    cache_ttl = get_setting("cover_art", "cache_ttl", 3600)

    if track_path in _FAILED_FETCH_CACHE:
        last_attempt = _FAILED_FETCH_CACHE[track_path]
        if time.time() - last_attempt < cache_ttl:
            return True
        # Expired entry, remove it
        del _FAILED_FETCH_CACHE[track_path]
    return False


def mark_fetch_failed(track_path: str):
    """
    Mark a track as having failed fetching so we don't retry too soon.

    Args:
        track_path: Path to the track
    """
    _FAILED_FETCH_CACHE[track_path] = time.time()


def fetch_from_itunes(artist: str, title: str) -> Optional[str]:
    """
    Fetch album cover from iTunes API.

    Args:
        artist: Artist name
        title: Track title

    Returns:
        Optional[str]: Path to downloaded cover art, or None if not found
    """
    # Check if online fetching is enabled
    if not get_setting("cover_art", "fetch_online", True):
        return None

    # Get request timeout from settings
    timeout = get_setting("cover_art", "timeout", 2.0)

    # Check cache first
    cached = get_cached_cover(artist, title)
    if cached:
        return cached

    if not artist and not title:
        return None

    query = f"{artist} {title}"

    try:
        url = f"https://itunes.apple.com/search?term={quote(query)}&media=music&limit=1"
        response = requests.get(url, timeout=timeout)

        if response.status_code != 200:
            return None

        data = response.json()

        if not data["resultCount"]:
            return None

        item = data["results"][0]

        # Get artwork URL (use the largest available)
        artwork_url = item.get("artworkUrl100")
        if artwork_url:
            # Try to get higher resolution by modifying the URL
            artwork_url = artwork_url.replace("100x100", "600x600")

            # Download the image
            img_response = requests.get(url=artwork_url, timeout=timeout)
            if img_response.status_code == 200:
                return save_to_cache(artist, title, img_response.content)

    except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
        print(f"Error fetching cover from iTunes: {e}")

    return None


def fetch_from_lastfm(artist: str, title: str) -> Optional[str]:
    """
    Fetch album cover from Last.fm API.

    Args:
        artist: Artist name
        title: Track title

    Returns:
        Optional[str]: Path to downloaded cover art, or None if not found
    """
    # Check if online fetching is enabled
    if not get_setting("cover_art", "fetch_online", True):
        return None

    # Get request timeout from settings
    timeout = get_setting("cover_art", "timeout", 2.0)

    # Last.fm API key (you would need to register for a proper key)
    # For this example, we're using a placeholder key - replace with a real one
    api_key = "12dec50c463b791ff530a6297d6c5638"

    # Check cache first
    cached = get_cached_cover(artist, title)
    if cached:
        return cached

    if not artist:
        return None

    try:
        # Try track.getInfo first
        url = (
            f"http://ws.audioscrobbler.com/2.0/?"
            f"method=track.getInfo&api_key={api_key}&"
            f"artist={quote(artist)}&track={quote(title)}&format=json"
        )
        response = requests.get(url, timeout=timeout)

        if response.status_code == 200:
            data = response.json()
            if "track" in data and "album" in data["track"]:
                album = data["track"]["album"]
                if "image" in album:
                    # Get the largest image (last in the list)
                    for img in reversed(album["image"]):
                        if img["size"] == "extralarge" and img["#text"]:
                            img_url = img["#text"]
                            try:
                                img_response = requests.get(
                                    img_url, timeout=timeout
                                )
                                if img_response.status_code == 200:
                                    return save_to_cache(
                                        artist, title, img_response.content
                                    )
                            except requests.RequestException:
                                pass

        # If track.getInfo didn't work, try artist.getInfo
        url = (
            f"http://ws.audioscrobbler.com/2.0/?"
            f"method=artist.getInfo&api_key={api_key}&"
            f"artist={quote(artist)}&format=json"
        )
        response = requests.get(url, timeout=timeout)

        if response.status_code == 200:
            data = response.json()
            if "artist" in data and "image" in data["artist"]:
                # Get the largest image (last in the list)
                for img in reversed(data["artist"]["image"]):
                    if img["size"] == "mega" and img["#text"]:
                        img_url = img["#text"]
                        try:
                            img_response = requests.get(
                                img_url, timeout=timeout
                            )
                            if img_response.status_code == 200:
                                return save_to_cache(
                                    artist, title, img_response.content
                                )
                        except requests.RequestException:
                            pass

    except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
        print(f"Error fetching cover from Last.fm: {e}")

    return None


def fetch_cover_art(track_path: Union[str, Path]) -> Optional[str]:
    """
    Fetch cover art for a track from various external APIs.

    This function tries different sources in the following order:
    1. Local cache
    2. iTunes API
    3. Last.fm API

    Args:
        track_path: Path to the audio file

    Returns:
        Optional[str]: Path to the downloaded cover art, or None if not found
    """
    # Check if cover art functionality is enabled
    if not get_setting("cover_art", "enabled", True):
        return None

    # Convert to string for consistent handling
    track_path_str = str(Path(track_path).absolute())

    # Check if we recently failed to fetch this cover
    if is_fetch_recently_failed(track_path_str):
        return None

    # Extract the filename
    filename = Path(track_path).name

    # Try to parse artist and title from the filename
    artist, title = parse_track_info(filename)

    # Check if we already have this cover art in cache
    cached = get_cached_cover(artist, title)
    if cached:
        return cached

    # Check if online fetching is enabled
    if not get_setting("cover_art", "fetch_online", True):
        return None

    try:
        # Try iTunes API
        cover = fetch_from_itunes(artist, title)
        if cover:
            return cover

        # Try Last.fm API
        cover = fetch_from_lastfm(artist, title)
        if cover:
            return cover
    except Exception as e:
        print(f"Unexpected error fetching cover art: {e}")

    # If we get here, we failed to find a cover
    mark_fetch_failed(track_path_str)
    return None
