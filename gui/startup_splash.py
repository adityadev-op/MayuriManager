from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QWidget

from gui.branding import LOGO_PATH


class StartupSplash(QWidget):
    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint,
        )
        self.setObjectName("startupSplash")
        self.setFixedSize(420, 440)
        self.setStyleSheet(
            "QWidget#startupSplash { background-color: #fdfaf4; }"
            "QLabel#splashCaption { color: #806b57; font-size: 11px; }"
        )

        self.logo = QLabel()
        self.logo.setObjectName("splashLogo")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo.setAccessibleName("Mayuri Cafe logo")
        self.logo.setPixmap(QPixmap(str(LOGO_PATH)))
        self.logo.setScaledContents(True)
        self.logo.setGeometry(175, 155, 70, 70)

        caption = QLabel("Cafe operations, thoughtfully managed", self)
        caption.setObjectName("splashCaption")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caption.setGeometry(20, 370, 380, 24)

        self.logo_animation = QPropertyAnimation(self.logo, b"geometry", self)
        self.logo_animation.setDuration(850)
        self.logo_animation.setStartValue(QRect(175, 155, 70, 70))
        self.logo_animation.setEndValue(QRect(60, 40, 300, 300))
        self.logo_animation.setEasingCurve(QEasingCurve.Type.OutBack)

    def showEvent(self, event):
        super().showEvent(event)
        screen = self.screen()
        if screen is not None:
            self.move(screen.availableGeometry().center() - self.rect().center())
        self.logo_animation.start()
