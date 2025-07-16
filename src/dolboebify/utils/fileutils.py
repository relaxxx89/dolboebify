"""Utilities for file operations."""

from pathlib import Path
from typing import List, Set, Union

from dolboebify.utils.exceptions import AudioFormatNotSupportedError


def get_supported_formats() -> Set[str]:
    """Get the set of supported audio formats."""
    return {
        "mp3",
        "wav",
        "ogg",
        "flac",
        "aac",
        "wma",
        "m4a",
        "aiff",
        "alac",
    }


def get_audio_files(
    directory: Union[str, Path], recursive: bool = True
) -> List[Path]:
    """
    Get all supported audio files in a directory.

    Args:
        directory: Directory to search
        recursive: Whether to search recursively

    Returns:
        List of Path objects for supported audio files
    """
    path = Path(directory)
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Directory not found: {path}")

    supported_formats = get_supported_formats()
    audio_files = []

    if recursive:
        for file_path in path.glob("**/*"):
            if (
                file_path.is_file()
                and file_path.suffix.lower()[1:] in supported_formats
            ):
                audio_files.append(file_path)
    else:
        for file_path in path.glob("*"):
            if (
                file_path.is_file()
                and file_path.suffix.lower()[1:] in supported_formats
            ):
                audio_files.append(file_path)

    return sorted(audio_files)


def check_file_type(file_path: Union[str, Path]) -> str:
    """
    Check the file type and return the format if supported.

    Args:
        file_path: Path to the file

    Returns:
        str: The format name (e.g., "mp3", "wav")

    Raises:
        AudioFormatNotSupportedError: If the format is not supported
        FileNotFoundError: If the file doesn't exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()[1:]
    if ext not in get_supported_formats():
        raise AudioFormatNotSupportedError(f"Format not supported: {ext}")

    return ext


def get_file_info(file_path: Union[str, Path]) -> dict:
    """
    Get basic file information.

    Args:
        file_path: Path to the file

    Returns:
        dict: File information
    """
    path = Path(file_path)
    stats = path.stat()

    return {
        "name": path.name,
        "path": str(path.absolute()),
        "size": stats.st_size,
        "modified": stats.st_mtime,
        "format": path.suffix.lower()[1:],
    }
