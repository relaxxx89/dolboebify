"""PyQt5 GUI implementation for the Dolboebify audio player."""

import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont
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

from dolboebify.core import Player
from dolboebify.utils.exceptions import AudioFormatNotSupportedError


class PlayerWindow(QMainWindow):
    """Main window for the Dolboebify GUI player."""

    def __init__(self):
        """Initialize the player window."""
        super().__init__()

        # Set up the player
        self.player = Player()

        # Setup UI
        self.setWindowTitle("Dolboebify")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()

        # Setup timers for updating position
        self.position_timer = QTimer()
        self.position_timer.setInterval(1000)
        self.position_timer.timeout.connect(self.update_position)
        self.position_timer.start()

        self.show()

    def setup_ui(self):
        """Set up the user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Now playing label
        self.now_playing_label = QLabel("No track playing")
        self.now_playing_label.setAlignment(Qt.AlignCenter)
        self.now_playing_label.setFont(QFont("Arial", 12, QFont.Bold))
        main_layout.addWidget(self.now_playing_label)

        # Time display
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)
        main_layout.addLayout(time_layout)

        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.sliderMoved.connect(self.set_position)
        main_layout.addWidget(self.progress_slider)

        # Control buttons
        controls_layout = QHBoxLayout()

        self.play_button = QPushButton()
        self.play_button.setIcon(
            self.style().standardIcon(QStyle.SP_MediaPlay)
        )
        self.play_button.clicked.connect(self.toggle_playback)

        self.prev_button = QPushButton()
        self.prev_button.setIcon(
            self.style().standardIcon(QStyle.SP_MediaSkipBackward)
        )
        self.prev_button.clicked.connect(self.previous_track)

        self.next_button = QPushButton()
        self.next_button.setIcon(
            self.style().standardIcon(QStyle.SP_MediaSkipForward)
        )
        self.next_button.clicked.connect(self.next_track)

        self.stop_button = QPushButton()
        self.stop_button.setIcon(
            self.style().standardIcon(QStyle.SP_MediaStop)
        )
        self.stop_button.clicked.connect(self.stop)

        self.open_file_button = QPushButton("Open File")
        self.open_file_button.clicked.connect(self.open_file)

        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.open_folder)

        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addWidget(self.open_file_button)
        controls_layout.addWidget(self.open_folder_button)

        main_layout.addLayout(controls_layout)

        # Volume control
        volume_layout = QHBoxLayout()
        volume_label = QLabel("Volume:")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.player.volume)
        self.volume_slider.valueChanged.connect(self.set_volume)

        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        main_layout.addLayout(volume_layout)

        # Playlist
        playlist_label = QLabel("Playlist")
        playlist_label.setFont(QFont("Arial", 10, QFont.Bold))
        main_layout.addWidget(playlist_label)

        self.playlist_widget = QListWidget()
        self.playlist_widget.itemDoubleClicked.connect(
            self.playlist_item_clicked
        )
        main_layout.addWidget(self.playlist_widget)

    def format_time(self, milliseconds: int) -> str:
        """Format milliseconds as MM:SS."""
        seconds = int(milliseconds / 1000)
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"

    @pyqtSlot()
    def update_position(self):
        """Update the current playback position."""
        if self.player.current_media and self.player.is_playing:
            # Update progress slider
            position_percent = self.player.position_percent
            self.progress_slider.setValue(int(position_percent))

            # Update time labels
            self.current_time_label.setText(
                self.format_time(self.player.position)
            )
            self.total_time_label.setText(
                self.format_time(self.player.duration)
            )

            # Update track info
            if self.player.playlist and self.player.current_index >= 0:
                track_title = self.player.playlist[self.player.current_index][
                    "title"
                ]
                self.now_playing_label.setText(f"Now Playing: {track_title}")

    @pyqtSlot(int)
    def set_position(self, position: int):
        """Set the playback position from slider value."""
        self.player.position_percent = position

    @pyqtSlot()
    def toggle_playback(self):
        """Toggle play/pause."""
        if not self.player.current_media:
            return

        if self.player.is_playing:
            self.player.pause()
            self.play_button.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay)
            )
        else:
            self.player.play()
            self.play_button.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause)
            )

    @pyqtSlot()
    def stop(self):
        """Stop playback."""
        self.player.stop()
        self.play_button.setIcon(
            self.style().standardIcon(QStyle.SP_MediaPlay)
        )
        self.progress_slider.setValue(0)
        self.current_time_label.setText("00:00")

    @pyqtSlot(int)
    def set_volume(self, volume: int):
        """Set the volume level."""
        self.player.volume = volume

    @pyqtSlot()
    def previous_track(self):
        """Play the previous track in the playlist."""
        if self.player.previous_track():
            self.play_button.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause)
            )
            self.update_playlist_selection()

    @pyqtSlot()
    def next_track(self):
        """Play the next track in the playlist."""
        if self.player.next_track():
            self.play_button.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause)
            )
            self.update_playlist_selection()

    @pyqtSlot()
    def open_file(self):
        """Open a file dialog to select an audio file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Audio File",
            str(Path.home()),
            "Audio Files (*.mp3 *.wav *.ogg *.flac *.aac *.wma "
            "*.m4a *.aiff *.alac)",
        )

        if file_path:
            try:
                self.player.clear_playlist()
                self.playlist_widget.clear()
                self.player.add_to_playlist(file_path)
                self.update_playlist()
                self.player.play(file_path)
                self.play_button.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause)
                )
            except (FileNotFoundError, AudioFormatNotSupportedError) as e:
                self.now_playing_label.setText(f"Error: {str(e)}")

    @pyqtSlot()
    def open_folder(self):
        """Open a folder dialog to select a directory with audio files."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Open Directory",
            str(Path.home()),
            QFileDialog.ShowDirsOnly,
        )

        if directory:
            self.player.clear_playlist()
            self.playlist_widget.clear()
            count = self.player.load_playlist(directory)

            if count > 0:
                self.update_playlist()
                self.player.play(self.player.playlist[0]["path"])
                self.play_button.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause)
                )
            else:
                self.now_playing_label.setText(
                    "No supported audio files found in directory"
                )

    def update_playlist(self):
        """Update the playlist widget with tracks from player's playlist."""
        self.playlist_widget.clear()

        for track in self.player.playlist:
            item = QListWidgetItem(track["title"])
            self.playlist_widget.addItem(item)

        self.update_playlist_selection()

    def update_playlist_selection(self):
        """Highlight the current track in the playlist."""
        if self.player.current_index >= 0:
            self.playlist_widget.setCurrentRow(self.player.current_index)

    @pyqtSlot(QListWidgetItem)
    def playlist_item_clicked(self, item):
        """Play the clicked playlist item."""
        index = self.playlist_widget.row(item)
        if 0 <= index < len(self.player.playlist):
            self.player.current_index = index
            self.player.play(self.player.playlist[index]["path"])
            self.play_button.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause)
            )


class GUIApp:
    """GUI application wrapper for Dolboebify."""

    def __init__(self):
        """Initialize the GUI application."""
        self.app = QApplication(sys.argv)
        self.window = PlayerWindow()

    def run(self):
        """Run the application."""
        return self.app.exec_()
