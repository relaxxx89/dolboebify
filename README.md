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

## Installation

```bash
# Install from source
git clone https://github.com/yourusername/dolboebify.git
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

## Dependencies

- python-vlc - Core audio playback
- pygame - Audio processing
- pydub - Audio file handling
- PyQt5 - Graphical user interface

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
