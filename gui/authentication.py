from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from gui.widgets import PremiumButton


class AuthenticationWidget(QWidget):
    employee_login_requested = Signal(str, str)
    admin_login_requested = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("authenticationPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 28, 8, 24)
        layout.addStretch()

        card = QFrame()
        card.setObjectName("authenticationCard")
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        card.setMaximumWidth(1200)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(38, 34, 38, 38)
        card_layout.setSpacing(16)

        eyebrow = QLabel("WELCOME BACK")
        eyebrow.setObjectName("authEyebrow")
        eyebrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Sign in to MAYURICAFE")
        title.setObjectName("authTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Access your workspace based on your role")
        subtitle.setObjectName("authSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(eyebrow)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(14)

        sections = QHBoxLayout()
        sections.setSpacing(26)
        employee_card = self._build_login_section(
            "Employee",
            "Manage bookings, tables and customers",
            "Username",
            "Password",
            self._submit_employee_login,
            "Login as Employee",
        )
        admin_card = self._build_login_section(
            "Admin",
            "Access system control and reports",
            "Username",
            "Password",
            self._submit_admin_login,
            "Login as Admin",
        )
        sections.addWidget(employee_card, 1)
        sections.addWidget(admin_card, 1)
        card_layout.addLayout(sections)

        layout.addWidget(card)
        layout.addStretch()

    def _build_login_section(
        self, title, description, username_hint, password_hint, submit, button_text
    ):
        section = QFrame()
        section.setObjectName("authSection")
        content = QVBoxLayout(section)
        content.setContentsMargins(26, 24, 26, 26)
        content.setSpacing(16)

        heading = QLabel(title)
        heading.setObjectName("authSectionTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail = QLabel(description)
        detail.setObjectName("authSectionDescription")
        detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail.setWordWrap(True)
        content.addWidget(heading)
        content.addWidget(detail)
        content.addSpacing(4)

        username = QLineEdit()
        username.setPlaceholderText(username_hint)
        username.setAccessibleName(f"{title} username")
        username.setMinimumHeight(50)
        password = QLineEdit()
        password.setPlaceholderText(password_hint)
        password.setAccessibleName(f"{title} password")
        password.setEchoMode(QLineEdit.EchoMode.Password)
        password.setMinimumHeight(50)
        password.returnPressed.connect(submit)
        content.addWidget(username)
        content.addWidget(password)

        button = PremiumButton(button_text)
        button.setObjectName("primaryButton")
        button.setMinimumHeight(50)
        button.clicked.connect(submit)
        content.addWidget(button)

        if title == "Employee":
            self.employee_username = username
            self.employee_password = password
            self.employee_login_button = button
        else:
            self.admin_username = username
            self.admin_password = password
            self.admin_login_button = button
        return section

    def _submit_employee_login(self):
        self.employee_login_requested.emit(
            self.employee_username.text(),
            self.employee_password.text(),
        )

    def _submit_admin_login(self):
        self.admin_login_requested.emit(
            self.admin_username.text(),
            self.admin_password.text(),
        )

    def clear_passwords(self):
        self.employee_password.clear()
        self.admin_password.clear()
