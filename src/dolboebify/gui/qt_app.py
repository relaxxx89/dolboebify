# main.py
"""
Dolboebify 2.0 – futuristic dark-neon MP3 player че гпт пишет вообще футуристик куда там
Requires:  pacman -S python-pyqt5 python-pygame
"""

import sys
from pathlib import Path
import pygame
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QMainWindow, QPushButton, QSlider,
    QVBoxLayout, QWidget, QStyle
)

# ---------- TinyBackend ----------
class TinyBackend:
    def __init__(self):
        pygame.mixer.init()
        self._playlist = []
        self._idx = -1
        self._vol = 0.5
        self._duration = 0

    # playlist
    def clear_playlist(self):
        self._playlist.clear()
        self._idx = -1

    def add_to_playlist(self, path):
        self._playlist.append({"path": str(path), "title": Path(path).stem})

    def load_playlist(self, folder: str) -> int:
        folder = Path(folder)
        exts = ("*.mp3", "*.flac", "*.wav", "*.ogg", "*.m4a", "*.aac", "*.opus")
        files = [f for ext in exts for f in folder.rglob(ext)]
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
        self._duration = pygame.mixer.Sound(self._playlist[idx]["path"]).get_length()

    def play(self, path=None):
        if path is None:
            self.play_index(self._idx)
        else:
            self.play_index(next((i for i, t in enumerate(self._playlist)
                                 if t["path"] == str(path)), 0))

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
        return self._playlist[self._idx]["path"] if 0 <= self._idx < len(self._playlist) else None

    @property
    def playlist(self):
        return self._playlist

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
        self.unknown_cover.fill(Qt.darkGray)

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
        self.cover_lbl.setAlignment(Qt.AlignCenter)
        self.cover_lbl.setPixmap(self.unknown_cover)
        main.addWidget(self.cover_lbl, alignment=Qt.AlignHCenter)

        # track title
        self.track_lbl = QLabel("Nothing playing")
        self.track_lbl.setAlignment(Qt.AlignCenter)
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
        self.progress = QSlider(Qt.Horizontal)
        self.progress.setRange(0, 1000)
        self.progress.sliderMoved.connect(self._seek)
        main.addWidget(self.progress)

        # controls row
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        btn_size = 36
        for name, icon, slot in (
                ("prev", "SP_MediaSkipBackward", self.previous_track),
                ("play", "SP_MediaPlay",        self.toggle_play),
                ("stop", "SP_MediaStop",        self.stop),
                ("next", "SP_MediaSkipForward", self.next_track)):
            btn = QPushButton()
            btn.setFixedSize(btn_size, btn_size)
            btn.setIcon(self.style().standardIcon(getattr(QStyle, icon)))
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
        self.vol_slider = QSlider(Qt.Horizontal)
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
        return f"{s//60:02d}:{s%60:02d}"

    def _load_cover(self, path):
        for name in ("cover.jpg", "folder.jpg", "front.jpg"):
            p = Path(path).with_name(name)
            if p.exists():
                return QPixmap(str(p))
        return self.unknown_cover

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
        self.track_lbl.setText(track.get("title", "Unknown"))
        cover = self._load_cover(track["path"])
        self.cover_lbl.setPixmap(cover.scaled(200, 200, Qt.KeepAspectRatio))

        self._sync_play_icon()

    @pyqtSlot()
    def _sync_play_icon(self):
        icon = QStyle.SP_MediaPause if self.player.is_playing else QStyle.SP_MediaPlay
        self.play_btn.setIcon(self.style().standardIcon(icon))

    @pyqtSlot(int)
    def _seek(self, val):
        # pygame не поддерживает точный seek — оставим заглушку
        pass

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
            self, "Open audio", str(Path.home()),
            "Audio (*.mp3 *.wav *.ogg *.flac *.m4a *.aac *.opus)")
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