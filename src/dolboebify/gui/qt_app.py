"""
Dolboebify 2.0 – futuristic dark-neon MP3 player че гпт пишет вообще
футуристик куда там
Requires:  pacman -S python-pyqt5 python-pygame
"""

import sys
from pathlib import Path
from typing import Optional

import pygame
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSlider,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from dolboebify.utils.coverart import fetch_cover_art

# Ensure Qt constants are available
# Alignment flags
AlignCenter = (
    Qt.AlignmentFlag.AlignCenter
    if hasattr(Qt, "AlignmentFlag")
    else Qt.AlignCenter
)
AlignHCenter = (
    Qt.AlignmentFlag.AlignHCenter
    if hasattr(Qt, "AlignmentFlag")
    else Qt.AlignHCenter
)

# Colors
black = Qt.GlobalColor.black if hasattr(Qt, "GlobalColor") else Qt.black
darkGray = (
    Qt.GlobalColor.darkGray if hasattr(Qt, "GlobalColor") else Qt.darkGray
)

# Orientation
Horizontal = (
    Qt.Orientation.Horizontal if hasattr(Qt, "Orientation") else Qt.Horizontal
)

# Image scaling
KeepAspectRatio = (
    Qt.AspectRatioMode.KeepAspectRatio
    if hasattr(Qt, "AspectRatioMode")
    else Qt.KeepAspectRatio
)

# Media style icons
SP_MediaPlay = (
    QStyle.StandardPixmap.SP_MediaPlay
    if hasattr(QStyle, "StandardPixmap")
    else QStyle.SP_MediaPlay
)
SP_MediaPause = (
    QStyle.StandardPixmap.SP_MediaPause
    if hasattr(QStyle, "StandardPixmap")
    else QStyle.SP_MediaPause
)
SP_MediaStop = (
    QStyle.StandardPixmap.SP_MediaStop
    if hasattr(QStyle, "StandardPixmap")
    else QStyle.SP_MediaStop
)
SP_MediaSkipForward = (
    QStyle.StandardPixmap.SP_MediaSkipForward
    if hasattr(QStyle, "StandardPixmap")
    else QStyle.SP_MediaSkipForward
)
SP_MediaSkipBackward = (
    QStyle.StandardPixmap.SP_MediaSkipBackward
    if hasattr(QStyle, "StandardPixmap")
    else QStyle.SP_MediaSkipBackward
)


# Thread for fetching cover art without blocking the UI
class CoverArtFetcher(QThread):
    # Signal to be emitted when cover art is found
    cover_found = pyqtSignal(str, str)

    def __init__(self, track_path):
        super().__init__()
        self.track_path = track_path

    def run(self):
        # Fetch cover in background thread
        cover_path = fetch_cover_art(self.track_path)
        if cover_path:
            # Emit signal with track path and cover path
            self.cover_found.emit(
                str(Path(self.track_path).absolute()), cover_path
            )


# ---------- TinyBackend ----------
class TinyBackend:
    def __init__(self):
        pygame.mixer.init()
        self._playlist = []
        self._idx = -1
        self._vol = 0.5
        self._duration = 0
        self._track_images = {}  # Maps track paths to image paths

        # Supported image formats
        self.SUPPORTED_IMAGE_FORMATS = [
            "jpg",
            "jpeg",
            "png",
            "webp",
            "bmp",
        ]

    # playlist
    def clear_playlist(self):
        self._playlist.clear()
        self._idx = -1

    def add_to_playlist(self, path):
        self._playlist.append({"path": str(path), "title": Path(path).stem})

    def load_playlist(self, folder: str) -> int:
        folder_path = Path(folder)
        exts = (
            "*.mp3",
            "*.flac",
            "*.wav",
            "*.ogg",
            "*.m4a",
            "*.aac",
            "*.opus",
        )
        files = []
        for ext in exts:
            files.extend(folder_path.rglob(ext))

        for f in files:
            self.add_to_playlist(str(f))
        return len(files)

    # playback
    def play_index(self, idx):
        if not (0 <= idx < len(self._playlist)):
            return
        self._idx = idx
        pygame.mixer.music.load(self._playlist[idx]["path"])
        pygame.mixer.music.play()
        self._duration = pygame.mixer.Sound(
            self._playlist[idx]["path"]
        ).get_length()

    def play(self, path=None):
        if path is None:
            self.play_index(self._idx)
        else:
            self.play_index(
                next(
                    (
                        i
                        for i, t in enumerate(self._playlist)
                        if t["path"] == str(path)
                    ),
                    0,
                )
            )

    def pause(self):
        pygame.mixer.music.pause()

    def stop(self):
        pygame.mixer.music.stop()

    def previous_track(self):
        if not self._playlist:
            return False
        self.play_index((self._idx - 1) % len(self._playlist))
        return True

    def next_track(self):
        if not self._playlist:
            return False
        self.play_index((self._idx + 1) % len(self._playlist))
        return True

    # volume
    @property
    def volume(self):
        return int(self._vol * 100)

    def set_volume(self, v):
        self._vol = max(0, min(v / 100, 1))
        pygame.mixer.music.set_volume(self._vol)

    # position
    @property
    def position(self):
        return pygame.mixer.music.get_pos() / 1000

    @property
    def duration(self):
        return self._duration

    @property
    def is_playing(self):
        return pygame.mixer.music.get_busy()

    @property
    def current_index(self):
        return self._idx

    @property
    def current_media(self):
        return (
            self._playlist[self._idx]["path"]
            if 0 <= self._idx < len(self._playlist)
            else None
        )

    @property
    def playlist(self):
        return self._playlist

    def _is_image_format_supported(self, file_path) -> bool:
        """Check if the image file format is supported."""
        ext = Path(file_path).suffix.lower()[1:]
        return ext in self.SUPPORTED_IMAGE_FORMATS

    def set_track_image(self, track_path, image_path) -> bool:
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
        for track in self._playlist:
            if Path(track["path"]).absolute() == track_path.absolute():
                track["image"] = str(image_path.absolute())

        return True

    def get_track_image(self, track_path) -> Optional[str]:
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

        # Try to fetch cover art from online sources
        online_cover = fetch_cover_art(track_path)
        if online_cover:
            # Cache this association for future use
            self._track_images[track_path] = online_cover

            # Update playlist entry if this track is in the playlist
            for track in self._playlist:
                if str(Path(track["path"]).absolute()) == track_path:
                    track["image"] = online_cover

            return online_cover

        return None

    def remove_track_image(self, track_path) -> bool:
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
            for track in self._playlist:
                if (
                    str(Path(track["path"]).absolute()) == track_path
                    and "image" in track
                ):
                    del track["image"]

            return True

        return False


# ---------- neon style ----------
DARK_STYLE = """
/* Main window */
QMainWindow {
    background-color: #0d0d0d;
}

QLabel {
    color: #ffffff;
    font-family: "Segoe UI", Roboto, Oxygen, Ubuntu;
}

/* Buttons */
QPushButton {
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    color: #ffffff;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #bb00ff, stop:1 #00aaff);
    font-size: 13px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #cc22ff, stop:1 #22bbff);
}
QPushButton:pressed {
    background-color: #0a0a0a;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 4px;
    background: #222;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
    background: #00ffff;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #bb00ff, stop:1 #00aaff);
    border-radius: 2px;
}

/* Playlist */
QListWidget {
    background-color: #111;
    border: none;
    border-radius: 8px;
    color: #ffffff;
    outline: 0;
}
QListWidget::item {
    padding: 6px;
}
QListWidget::item:selected {
    background-color: rgba(0, 255, 255, 100);
}
"""


class PlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.player = TinyBackend()
        self.setWindowTitle("Dolboebify 2.0")
        self.setGeometry(200, 150, 820, 640)
        self.setStyleSheet(DARK_STYLE)

        # fallback cover
        self.unknown_cover = QPixmap(200, 200)
        self.unknown_cover.fill(darkGray)

        # Keep track of active cover art fetchers
        self._cover_fetchers = {}

        self.setup_ui()
        self.setup_timers()
        self.show()

    # ---------- UI ----------
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main = QVBoxLayout(central)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(10)

        # cover label
        self.cover_lbl = QLabel()
        self.cover_lbl.setFixedSize(200, 200)
        self.cover_lbl.setScaledContents(True)
        self.cover_lbl.setAlignment(AlignCenter)
        self.cover_lbl.setPixmap(self.unknown_cover)
        main.addWidget(self.cover_lbl, alignment=AlignHCenter)

        # track title
        self.track_lbl = QLabel("Nothing playing")
        self.track_lbl.setAlignment(AlignCenter)
        f = QFont("Segoe UI", 14, QFont.Bold)
        self.track_lbl.setFont(f)
        main.addWidget(self.track_lbl)

        # time row
        time_row = QHBoxLayout()
        self.cur_lbl = QLabel("00:00")
        self.tot_lbl = QLabel("00:00")
        time_row.addWidget(self.cur_lbl)
        time_row.addStretch()
        time_row.addWidget(self.tot_lbl)
        main.addLayout(time_row)

        # progress slider
        self.progress = QSlider(Horizontal)
        self.progress.setRange(0, 1000)
        self.progress.sliderMoved.connect(self._seek)
        main.addWidget(self.progress)

        # controls row
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        btn_size = 36
        for name, icon, slot in (
            ("prev", SP_MediaSkipBackward, self.previous_track),
            ("play", SP_MediaPlay, self.toggle_play),
            ("stop", SP_MediaStop, self.stop),
            ("next", SP_MediaSkipForward, self.next_track),
        ):
            btn = QPushButton()
            btn.setFixedSize(btn_size, btn_size)
            btn.setIcon(self.style().standardIcon(icon))
            btn.clicked.connect(slot)
            setattr(self, name + "_btn", btn)
            ctrl.addWidget(btn)

        ctrl.addStretch()
        open_btn = QPushButton("Open File")
        open_btn.setMinimumHeight(28)
        open_btn.clicked.connect(self.open_file)
        ctrl.addWidget(open_btn)

        main.addLayout(ctrl)

        # volume
        vol_box = QHBoxLayout()
        vol_box.addWidget(QLabel("Vol"))
        self.vol_slider = QSlider(Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(self.player.volume)
        self.vol_slider.valueChanged.connect(self.set_volume)
        vol_box.addWidget(self.vol_slider)
        self.vol_lbl = QLabel(str(self.player.volume))
        vol_box.addWidget(self.vol_lbl)
        main.addLayout(vol_box)

        # playlist
        lbl = QLabel("Playlist")
        lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        main.addWidget(lbl)

        self.playlist = QListWidget()
        self.playlist.itemDoubleClicked.connect(self._play_item)
        main.addWidget(self.playlist)

    # ---------- Timers ----------
    def setup_timers(self):
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start()

    # ---------- Helpers ----------
    def format_time(self, sec):
        s = int(sec)
        return f"{s//60:02d}:{s % 60:02d}"

    def _load_cover(self, path):
        # First check if the track has an image associated with it through the API
        cover_path = self.player.get_track_image(path)
        if cover_path and Path(cover_path).exists():
            return QPixmap(cover_path)

        # If no cover found, create a loading placeholder
        loading_pixmap = QPixmap(200, 200)
        loading_pixmap.fill(
            black
        )  # Use black background for the loading cover

        # Start a background thread to fetch the cover from online sources
        self._start_cover_fetch(path)

        # Fallback to the old method for local files
        for name in ("cover.jpg", "folder.jpg", "front.jpg"):
            p = Path(path).with_name(name)
            if p.exists():
                return QPixmap(str(p))

        return self.unknown_cover

    def _start_cover_fetch(self, path):
        """Start a background thread to fetch cover art."""
        # Clean up any previous fetcher for this track
        path_key = str(Path(path).absolute())
        if path_key in self._cover_fetchers:
            old_fetcher = self._cover_fetchers[path_key]
            if old_fetcher.isRunning():
                old_fetcher.terminate()
                old_fetcher.wait()

        # Create and start a new fetcher
        fetcher = CoverArtFetcher(path)
        fetcher.cover_found.connect(self._on_cover_found)
        fetcher.start()

        # Store a reference to prevent garbage collection
        self._cover_fetchers[path_key] = fetcher

    @pyqtSlot(str, str)
    def _on_cover_found(self, track_path, cover_path):
        """Handle when a cover is found by the background thread."""
        # Update the track in the player's associations
        self.player._track_images[track_path] = cover_path

        # Only update UI if this is the currently playing track
        current_track = (
            str(Path(self.player.current_media).absolute())
            if self.player.current_media
            else None
        )
        if current_track == track_path:
            self.cover_lbl.setPixmap(QPixmap(cover_path))

        # Clean up the fetcher
        if track_path in self._cover_fetchers:
            del self._cover_fetchers[track_path]

    @pyqtSlot()
    def update_ui(self):
        if self.player.current_index < 0:
            return
        pos = self.player.position
        dur = self.player.duration
        self.cur_lbl.setText(self.format_time(pos))
        self.tot_lbl.setText(self.format_time(dur))
        if dur:
            self.progress.setValue(int(1000 * pos / dur))

        track = self.player.playlist[self.player.current_index]
        title = track.get("title", "Unknown")
        self.track_lbl.setText(title)

        cover = self._load_cover(track["path"])
        self.cover_lbl.setPixmap(cover.scaled(200, 200, KeepAspectRatio))

        self._sync_play_icon()

    @pyqtSlot()
    def _sync_play_icon(self):
        icon = SP_MediaPause if self.player.is_playing else SP_MediaPlay
        self.play_btn.setIcon(self.style().standardIcon(icon))

    @pyqtSlot(int)
    def _seek(self, val):
        """
        Seek to a position in the current track.

        Args:
            val: Position as 0-1000 value representing track percentage
        """
        if not self.player.playlist or self.player.current_index < 0:
            return

        if val < 0:
            val = 0
        elif val > 1000:
            val = 1000

        # Calculate position in seconds
        dur = self.player.duration
        if dur > 0:
            pos = (val / 1000) * dur

            # For pygame backend, we'll restart the track and skip forward
            # (since pygame doesn't support direct seeking)
            if pos > 0:
                path = self.player.playlist[self.player.current_index]["path"]
                self.player.play(path)
                # Some backends might not support exact seeking, this is a fallback
                # that works with the pygame implementation
                pass  # We'll implement this in a future version

    @pyqtSlot()
    def toggle_play(self):
        if not self.player.playlist:
            return
        if self.player.is_playing:
            self.player.pause()
        else:
            self.player.play()
        self._sync_play_icon()

    @pyqtSlot()
    def stop(self):
        self.player.stop()
        self.progress.setValue(0)
        self._sync_play_icon()

    @pyqtSlot()
    def previous_track(self):
        self.player.previous_track()

    @pyqtSlot()
    def next_track(self):
        self.player.next_track()

    @pyqtSlot(int)
    def set_volume(self, v):
        self.player.set_volume(v)
        self.vol_lbl.setText(str(v))

    # ---------- File operations ----------
    @pyqtSlot()
    def open_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Open audio",
            str(Path.home()),
            "Audio (*.mp3 *.wav *.ogg *.flac *.m4a *.aac *.opus)",
        )
        if not files:
            return
        self.player.clear_playlist()
        for f in files:
            self.player.add_to_playlist(f)
        self._fill_playlist()
        if self.player.playlist:
            self.player.play_index(0)

    def _fill_playlist(self):
        self.playlist.clear()
        for t in self.player.playlist:
            QListWidgetItem(t["title"], self.playlist)
        self.playlist.setCurrentRow(self.player.current_index)

    @pyqtSlot()
    def _play_item(self, item):
        row = self.playlist.row(item)
        if 0 <= row < len(self.player.playlist):
            self.player.play_index(row)


class GUIApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle("Fusion")
        self.window = PlayerWindow()

    def run(self):
        return self.app.exec_()


if __name__ == "__main__":
    sys.exit(GUIApp().run())
