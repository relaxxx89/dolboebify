# Dolboebify

A modern GUI audio player written in Python that supports various audio formats.

## Screenshots
<img width="945" height="1022" alt="image" src="https://github.com/user-attachments/assets/1af07966-45f2-40d5-93c2-b7cbdf01f323" />

# (WHAT A HEEEEEEEEEEL GOOFY AHH PLAYER LOL)

## Features

- Supports multiple audio formats (MP3, WAV, FLAC, OGG, etc.)
- Simple and intuitive graphical interface
- Playlist management
- Volume control and audio visualization
- Automatic track image retrieval from online sources
- Custom track image API

## Installation

```bash
# Install from source
git clone https://github.com/relaxxx89/dolboebify.git
cd dolboebify
pip install -e .

# Or install from PyPI (when published)
pip install dolboebify
```

## Usage

```bash
# Start the player
dolboebify

# You can also use Python directly
python -m dolboebify
```

### Track Image API

The player supports associating custom images with tracks and automatically fetching album art from online sources:

```python
from dolboebify.core import Player

# Create a player instance
player = Player()

# Add a track to the playlist
player.add_to_playlist("path/to/track.mp3")

# Manually set a custom image for a track
player.set_track_image("path/to/track.mp3", "path/to/cover.jpg")

# Get the image associated with a track (includes online fetching)
cover_path = player.get_track_image("path/to/track.mp3")

# Remove an image association
player.remove_track_image("path/to/track.mp3")
```

## Dependencies

- python-vlc - Core audio playback
- pygame - Audio processing
- pydub - Audio file handling
- PyQt5 - Graphical user interface
- requests - For online album art retrieval

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
isort src tests
```

## License

This project is licensed under the GNU License - see the LICENSE file for details.
