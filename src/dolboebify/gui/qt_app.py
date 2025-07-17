"""
Dolboebify – modern dark UI for Hyprland/Arch feel.
Requires: PyQt5 (pacman -S python-pyqt5)
"""

import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QLinearGradient
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QMainWindow, QPushButton, QSlider, QStyle,
    QVBoxLayout, QWidget
)

from dolboebify.core import Player
from dolboebify.utils.exceptions import AudioFormatNotSupportedError

# -------------------------------------------------
#  Style-sheet (dark theme)
# -------------------------------------------------
DARK_STYLE = """
/* Main window */
QMainWindow {
    background-color: #121212;
}

/* Labels */
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
    background-color: #1e1e1e;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #323232;
}
QPushButton:pressed {
    background-color: #0a0a0a;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 4px;
    background: #353535;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
    background: #bb86fc;
}
QSlider::sub-page:horizontal {
    background: #bb86fc;
    border-radius: 2px;
}

/* Playlist */
QListWidget {
    background-color: #1e1e1e;
    border: none;
    border-radius: 8px;
    color: #ffffff;
    outline: 0;
}
QListWidget::item {
    padding: 6px;
}
QListWidget::item:selected {
    background-color: #bb86fc;
    color: #121212;
}
"""


class PlayerWindow(QMainWindow):
    """Main window with modern dark theme."""

    def __init__(self):
        super().__init__()
        self.player = Player()
        self.setWindowTitle("Dolboebify")
        self.setGeometry(200, 150, 820, 640)
        self.setStyleSheet(DARK_STYLE)
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

        # Top info
        self.track_lbl = QLabel("Nothing playing")
        self.track_lbl.setAlignment(Qt.AlignCenter)
        f = QFont("Segoe UI", 14, QFont.Bold)
        self.track_lbl.setFont(f)
        main.addWidget(self.track_lbl)

        # Time row
        time_row = QHBoxLayout()
        self.cur_lbl = QLabel("00:00")
        self.tot_lbl = QLabel("00:00")
        time_row.addWidget(self.cur_lbl)
        time_row.addStretch()
        time_row.addWidget(self.tot_lbl)
        main.addLayout(time_row)

        # Progress slider
        self.progress = QSlider(Qt.Horizontal)
        self.progress.setRange(0, 1000)
        self.progress.sliderMoved.connect(self._seek)
        main.addWidget(self.progress)

        # Controls
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
        for txt, slot in (("Open File", self.open_file),
                          ("Open Folder", self.open_folder)):
            btn = QPushButton(txt)
            btn.setMinimumHeight(28)
            btn.clicked.connect(slot)
            ctrl.addWidget(btn)

        main.addLayout(ctrl)

        # Volume slider
        vol_box = QHBoxLayout()
        vol_box.addWidget(QLabel("Vol"))
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(self.player.volume)
        self.vol_slider.valueChanged.connect(self.set_volume)
        vol_box.addWidget(self.vol_slider)
        vol_box.addWidget(QLabel("100"))
        main.addLayout(vol_box)

        # Playlist
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

    # ---------- Logic helpers ----------
    def format_time(self, ms):
        s = int(ms // 1000)
        return f"{s//60:02d}:{s%60:02d}"

    @pyqtSlot()
    def update_ui(self):
        if not self.player.current_media:
            return
        pos = self.player.position
        dur = self.player.duration
        self.cur_lbl.setText(self.format_time(pos))
        self.tot_lbl.setText(self.format_time(dur))
        if dur:
            self.progress.setValue(int(1000 * pos / dur))
        if self.player.playlist and self.player.current_index >= 0:
            self.track_lbl.setText(self.player.playlist[self.player.current_index]["title"])
        self._sync_play_icon()

    @pyqtSlot()
    def _sync_play_icon(self):
        icon = QStyle.SP_MediaPause if self.player.is_playing else QStyle.SP_MediaPlay
        self.play_btn.setIcon(self.style().standardIcon(icon))

    @pyqtSlot(int)
    def _seek(self, val):
        self.player.position_percent = val / 10

    @pyqtSlot()
    def toggle_play(self):
        if not self.player.current_media:
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
        if self.player.previous_track():
            self._sync_play_icon()

    @pyqtSlot()
    def next_track(self):
        if self.player.next_track():
            self._sync_play_icon()

    @pyqtSlot()
    def set_volume(self, v):
        self.player.volume = v

    # ---------- File operations ----------
    @pyqtSlot()
    def open_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Open audio", str(Path.home()),
            "Audio (*.mp3 *.wav *.ogg *.flac *.m4a *.aac *.opus)")
        if file:
            self._load([file])

    @pyqtSlot()
    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open folder", str(Path.home()))
        if folder:
            self.player.clear_playlist()
            count = self.player.load_playlist(folder)
            self._fill_playlist()
            if count:
                self.player.play(self.player.playlist[0]["path"])
                self._sync_play_icon()

    def _load(self, paths):
        self.player.clear_playlist()
        for p in paths:
            self.player.add_to_playlist(p)
        self._fill_playlist()
        if self.player.playlist:
            self.player.play(self.player.playlist[0]["path"])
            self._sync_play_icon()

    def _fill_playlist(self):
        self.playlist.clear()
        for t in self.player.playlist:
            QListWidgetItem(t["title"], self.playlist)
        self.playlist.setCurrentRow(self.player.current_index)

    @pyqtSlot(QListWidgetItem)
    def _play_item(self, item):
        row = self.playlist.row(item)
        if 0 <= row < len(self.player.playlist):
            self.player.current_index = row
            self.player.play(self.player.playlist[row]["path"])
            self._sync_play_icon()


class GUIApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle("Fusion")
        self.window = PlayerWindow()

    def run(self):
        return self.app.exec_()


if __name__ == "__main__":
    sys.exit(GUIApp().run())