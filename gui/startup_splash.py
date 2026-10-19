import logging
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QVBoxLayout, QWidget


logger = logging.getLogger(__name__)
STARTUP_VIDEO_PATH = Path(__file__).resolve().parent / "assets" / "opening_video.mp4"


class StartupSplash(QWidget):
    finished = Signal()

    def __init__(self, video_path=STARTUP_VIDEO_PATH, parent=None):
        super().__init__(parent)
        self._finished = False
        self._playback_started = False
        self.video_path = Path(video_path)
        self.setObjectName("startupSplash")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet("QWidget#startupSplash { background-color: #000000; }")

        self.video_widget = QVideoWidget(self)
        self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.video_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.video_widget.installEventFilter(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.video_widget)

        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.7)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.errorOccurred.connect(self._on_playback_error)

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        if self._playback_started:
            return
        self._playback_started = True
        self.player.setSource(QUrl.fromLocalFile(str(self.video_path)))
        self.player.play()

    def closeEvent(self, event):
        self.player.stop()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._finish()
            event.accept()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self._finish()
        event.accept()

    def eventFilter(self, watched, event):
        if watched is self.video_widget:
            if event.type() == QEvent.Type.MouseButtonPress:
                self._finish()
                return True
            if (
                event.type() == QEvent.Type.KeyPress
                and event.key() == Qt.Key.Key_Escape
            ):
                self._finish()
                return True
        return super().eventFilter(watched, event)

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._finish()

    def _on_playback_error(self, error, error_string):
        del error
        logger.error("Could not play the startup video: %s", error_string)
        self._finish()

    def _finish(self):
        if self._finished:
            return
        self._finished = True
        self.player.stop()
        self.finished.emit()
