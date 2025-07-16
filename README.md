# Dolboebify

A modern audio player written in Python that supports various audio formats.

## Features

- Supports multiple audio formats (MP3, WAV, FLAC, OGG, etc.)
- Simple and intuitive interface
- Both command-line (CLI) and graphical (GUI) interfaces
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

### Command-Line Interface (CLI)

```bash
# Start the player in CLI mode (default)
dolboebify
dolboebify --cli

# Play a specific file
dolboebify play /path/to/audio/file.mp3

# Create and play a playlist
dolboebify playlist /path/to/playlist/directory
```

### Graphical Interface (GUI)

```bash
# Start the player with GUI
dolboebify --gui

# You can also use Python directly
python -m dolboebify --gui
```

## Dependencies

- python-vlc - Core audio playback
- pygame - Audio processing
- pydub - Audio file handling
- click - Command line interface
- rich - Terminal UI
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

This project is licensed under the MIT License - see the LICENSE file for details.
