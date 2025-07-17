"""Utilities for cleaning up cache and temporary files."""

import os
import shutil
from pathlib import Path

from dolboebify.utils.coverart import COVER_CACHE_DIR


def clear_cover_cache() -> int:
    """
    Clear all cached cover art files.
    
    Returns:
        int: Number of files removed
    """
    if not COVER_CACHE_DIR.exists():
        return 0
        
    # Count files before deletion
    file_count = sum(1 for _ in COVER_CACHE_DIR.glob("*.jpg"))
    
    # Remove all files in the cache directory
    for file_path in COVER_CACHE_DIR.glob("*.jpg"):
        try:
            os.unlink(file_path)
        except OSError as e:
            print(f"Error removing {file_path}: {e}")
            
    return file_count


def reset_failed_fetch_cache():
    """Reset the in-memory cache of failed fetch attempts."""
    # Import here to avoid circular imports
    from dolboebify.utils.coverart import _FAILED_FETCH_CACHE
    _FAILED_FETCH_CACHE.clear()


def cleanup_all():
    """Clean up all caches and temporary files."""
    files_removed = clear_cover_cache()
    reset_failed_fetch_cache()
    print(f"Removed {files_removed} cached cover art files")
    print("Reset failed fetch cache")


if __name__ == "__main__":
    # Can be run as a standalone script
    cleanup_all() 