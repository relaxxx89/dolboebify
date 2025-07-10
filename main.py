import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QLabel, QListWidget, QMessageBox
)
from PyQt5.QtCore import Qt
import vlc
import os

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Dolboebify Music Player')
        self.setGeometry(200, 200, 500, 350)
        self.setStyleSheet("background-color: #23272f; color: #fff;")

        self.player = vlc.MediaPlayer()
        self.playlist = []
        self.current_index = -1

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Playlist
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("background-color: #181a20; color: #fff; border: none;")
        self.list_widget.itemDoubleClicked.connect(self.play_selected)

        # Controls
        self.play_btn = QPushButton('▶')
        self.pause_btn = QPushButton('⏸')
        self.stop_btn = QPushButton('⏹')
        self.prev_btn = QPushButton('⏮')
        self.next_btn = QPushButton('⏭')
        self.open_btn = QPushButton('Загрузить')

        for btn in [self.play_btn, self.pause_btn, self.stop_btn, self.prev_btn, self.next_btn, self.open_btn]:
            btn.setFixedHeight(40)
            btn.setStyleSheet("QPushButton { background-color: #2d313a; border-radius: 8px; font-size: 18px; } QPushButton:hover { background-color: #3a3f4b; }")

        self.play_btn.clicked.connect(self.play)
        self.pause_btn.clicked.connect(self.pause)
        self.stop_btn.clicked.connect(self.stop)
        self.prev_btn.clicked.connect(self.prev)
        self.next_btn.clicked.connect(self.next)
        self.open_btn.clicked.connect(self.open_files)

        # Now playing label
        self.now_playing = QLabel('')
        self.now_playing.setAlignment(Qt.AlignCenter)
        self.now_playing.setStyleSheet("font-size: 16px; margin: 10px;")

        # Layouts
        controls = QHBoxLayout()
        controls.addWidget(self.prev_btn)
        controls.addWidget(self.play_btn)
        controls.addWidget(self.pause_btn)
        controls.addWidget(self.stop_btn)
        controls.addWidget(self.next_btn)
        controls.addWidget(self.open_btn)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.now_playing)
        main_layout.addWidget(self.list_widget)
        main_layout.addLayout(controls)

        central_widget.setLayout(main_layout)

    def open_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, 'Выберите аудиофайлы', '',
            'Audio Files (*.mp3 *.wav *.flac)'
        )
        if files:
            for file in files:
                if file not in self.playlist:
                    self.playlist.append(file)
                    self.list_widget.addItem(os.path.basename(file))

    def play_selected(self, item):
        index = self.list_widget.row(item)
        self.play_track(index)

    def play(self):
        if self.current_index == -1 and self.playlist:
            self.play_track(0)
        elif self.player.get_state() == vlc.State.Paused:
            self.player.play()
        elif self.current_index != -1:
            self.player.play()
        else:
            QMessageBox.information(self, 'Плеер', 'Сначала загрузите и выберите трек!')

    def pause(self):
        if self.player.is_playing():
            self.player.pause()

    def stop(self):
        self.player.stop()
        self.now_playing.setText('')

    def next(self):
        if self.playlist and self.current_index + 1 < len(self.playlist):
            self.play_track(self.current_index + 1)

    def prev(self):
        if self.playlist and self.current_index > 0:
            self.play_track(self.current_index - 1)

    def play_track(self, index):
        if 0 <= index < len(self.playlist):
            self.current_index = index
            media = vlc.Media(self.playlist[index])
            self.player.set_media(media)
            self.player.play()
            self.now_playing.setText(f'Сейчас играет: {os.path.basename(self.playlist[index])}')
            self.list_widget.setCurrentRow(index)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MusicPlayer()
    window.show()
    sys.exit(app.exec_())
