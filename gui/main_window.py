import os
import secrets

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from Database_ import connection
from gui.admin import AdminWidget
from gui.booking import BookingWidget
from Receptionist.orders import get_employee_dashboard_stats


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        connection.set_password_prompt(self._prompt_database_password)
        self.is_dark = False
        self.setWindowTitle("MAYURICAFE")
        self.resize(1280, 820)
        self.setMinimumSize(900, 640)

        self.stack = QStackedWidget()
        self._effects = {}
        self._animation = None

        shell = QWidget()
        shell.setObjectName("appShell")
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(44, 24, 44, 28)
        shell_layout.setSpacing(20)
        shell_layout.addWidget(self._build_topbar())

        self.home_page = self._build_home_page()
        self.roles_page = self._build_roles_page()
        self.employee_page = self._build_employee_page()
        self.booking_page = self._build_booking_page()
        self.admin_page = self._build_admin_page()

        for page in (
            self.home_page,
            self.roles_page,
            self.employee_page,
            self.booking_page,
            self.admin_page,
        ):
            self.stack.addWidget(page)
            effect = self._opacity_effect(page)
            page.setGraphicsEffect(effect)
            self._effects[page] = effect

        shell_layout.addWidget(self.stack, 1)
        self.setCentralWidget(shell)
        self._apply_theme()
        self._show_page(self.home_page, animate=False)
        self.employee_refresh_timer = QTimer(self)
        self.employee_refresh_timer.setInterval(30_000)
        self.employee_refresh_timer.timeout.connect(self._auto_refresh_employee_stats)
        self.employee_refresh_timer.start()

    def _build_topbar(self):
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        mark = QLabel("M")
        mark.setObjectName("brandMark")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(40, 40)

        brand = QVBoxLayout()
        brand.setSpacing(0)
        brand_name = QLabel("MAYURICAFE")
        brand_name.setObjectName("brandName")
        brand_caption = QLabel("CAFE MANAGEMENT")
        brand_caption.setObjectName("brandCaption")
        brand.addWidget(brand_name)
        brand.addWidget(brand_caption)

        layout.addWidget(mark)
        layout.addLayout(brand)
        layout.addStretch()

        self.theme_button = QPushButton("Dark theme")
        self.theme_button.setObjectName("themeButton")
        self.theme_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_button.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_button)
        return bar

    def _build_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 42, 0, 30)
        layout.addStretch()

        hero = QFrame()
        hero.setObjectName("heroCard")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(68, 58, 68, 58)
        hero_layout.setSpacing(18)

        eyebrow = QLabel("A WARM WELCOME, EVERY TIME")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("MAYURICAFE")
        title.setObjectName("heroTitle")
        title.setWordWrap(True)
        description = QLabel(
            "A calmer way to care for every detail of your cafe."
        )
        description.setObjectName("heroDescription")
        description.setWordWrap(True)

        actions = QHBoxLayout()
        actions.setSpacing(14)
        enter_button = QPushButton("Enter your workspace")
        enter_button.setObjectName("primaryButton")
        enter_button.setMinimumHeight(50)
        enter_button.setCursor(Qt.CursorShape.PointingHandCursor)
        enter_button.clicked.connect(lambda: self._show_page(self.roles_page))
        actions.addWidget(enter_button, 0)
        actions.addStretch()

        hero_layout.addSpacing(12)
        hero_layout.addWidget(eyebrow)
        hero_layout.addWidget(title)
        hero_layout.addWidget(description)
        hero_layout.addSpacing(14)
        hero_layout.addLayout(actions)

        layout.addWidget(hero, 0)
        layout.addStretch()
        footer = QLabel("GOOD FOOD. THOUGHTFUL SERVICE.")
        footer.setObjectName("footerNote")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)
        return page

    def _build_roles_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 34, 0, 20)
        layout.addStretch()

        heading = QLabel("Welcome back")
        heading.setObjectName("pageTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Choose a workspace to get started.")
        subtitle.setObjectName("pageSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)
        layout.addWidget(subtitle)
        layout.addSpacing(28)

        cards = QHBoxLayout()
        cards.setSpacing(18)
        cards.addWidget(
            self._role_card(
                "01",
                "Employee",
                "Bookings, tables and service — all in one place.",
                "Open employee workspace",
                self._open_employee_workspace,
            )
        )
        cards.addWidget(
            self._role_card(
                "02",
                "Admin",
                "A clear view of your people, menu and performance.",
                "Open admin workspace",
                self._open_admin_workspace,
                subdued=True,
            )
        )
        layout.addLayout(cards)
        layout.addStretch()

        back = QPushButton("Back to welcome")
        back.setObjectName("textButton")
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.clicked.connect(lambda: self._show_page(self.home_page))
        layout.addWidget(back, alignment=Qt.AlignmentFlag.AlignCenter)
        return page

    def _role_card(self, number, title, description, action, callback, subdued=False):
        card = QFrame()
        card.setObjectName("roleCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        card.setMinimumHeight(300)
        content = QVBoxLayout(card)
        content.setContentsMargins(30, 28, 30, 28)
        content.setSpacing(15)

        number_label = QLabel(number)
        number_label.setObjectName("cardNumber")
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        description_label = QLabel(description)
        description_label.setObjectName("cardDescription")
        description_label.setWordWrap(True)
        button = QPushButton(action)
        button.setObjectName("secondaryButton" if subdued else "primaryButton")
        button.setMinimumHeight(46)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(callback)

        content.addWidget(number_label)
        content.addStretch()
        content.addWidget(title_label)
        content.addWidget(description_label)
        content.addStretch()
        content.addWidget(button)
        return card

    def _build_employee_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(20)
        layout.addWidget(self._page_heading("Employee workspace", "Your service desk for the day."))

        self.employee_stat_values = {}
        stats = QHBoxLayout()
        stats.setSpacing(14)
        for key, label, note in (
            ("todays_bookings", "TODAY'S BOOKINGS", "Orders placed today"),
            ("available_tables", "AVAILABLE TABLES", "Ready for dine-in"),
            ("open_orders", "OPEN ORDERS", "Awaiting completion"),
        ):
            card, value = self._employee_stat_card(label, note)
            self.employee_stat_values[key] = value
            stats.addWidget(card)
        layout.addLayout(stats)

        employee_actions = QHBoxLayout()
        self.employee_status = QLabel("Live cafe information.")
        self.employee_status.setObjectName("mutedNote")
        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("secondaryButton")
        refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_button.clicked.connect(self._refresh_employee_stats)
        employee_actions.addWidget(self.employee_status, 1)
        employee_actions.addWidget(refresh_button)
        layout.addLayout(employee_actions)

        feature = QFrame()
        feature.setObjectName("featureCard")
        feature_layout = QHBoxLayout(feature)
        feature_layout.setContentsMargins(32, 28, 32, 28)
        feature_layout.setSpacing(24)
        copy = QVBoxLayout()
        copy.setSpacing(8)
        kicker = QLabel("READY FOR THE NEXT GUEST?")
        kicker.setObjectName("eyebrow")
        title = QLabel("Create a booking")
        title.setObjectName("sectionTitle")
        text = QLabel("Start a dine-in or takeaway order with a simple guided flow.")
        text.setObjectName("cardDescription")
        text.setWordWrap(True)
        copy.addWidget(kicker)
        copy.addWidget(title)
        copy.addWidget(text)
        button = QPushButton("Start a new booking")
        button.setObjectName("primaryButton")
        button.setMinimumHeight(48)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(self._start_booking)
        feature_layout.addLayout(copy, 1)
        feature_layout.addWidget(button, 0)
        layout.addWidget(feature)
        layout.addStretch()
        layout.addWidget(self._back_button(self.roles_page))
        return page

    def _employee_stat_card(self, label, note):
        card = QFrame()
        card.setObjectName("statCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(7)
        title = QLabel(label)
        title.setObjectName("statLabel")
        value = QLabel("—")
        value.setObjectName("statValue")
        description = QLabel(note)
        description.setObjectName("mutedNote")
        layout.addWidget(title)
        layout.addWidget(value)
        layout.addWidget(description)
        return card, value

    def _build_booking_page(self):
        page = BookingWidget()
        page.order_completed.connect(self._booking_completed)
        page.flow_cancelled.connect(
            lambda: self._show_page(self.employee_page)
        )
        return page

    def _build_admin_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        self.admin_widget = AdminWidget()
        layout.addWidget(self.admin_widget, 1)
        layout.addWidget(self._back_button(self.roles_page))
        return page

    def _page_heading(self, title, subtitle):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        title_label = QLabel(title)
        title_label.setObjectName("pageTitleLeft")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitleLeft")
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        return widget

    def _stat_card(self, label, value, note):
        card = QFrame()
        card.setObjectName("statCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(7)
        label_widget = QLabel(label)
        label_widget.setObjectName("statLabel")
        value_widget = QLabel(value)
        value_widget.setObjectName("statValue")
        note_widget = QLabel(note)
        note_widget.setObjectName("mutedNote")
        layout.addWidget(label_widget)
        layout.addWidget(value_widget)
        layout.addWidget(note_widget)
        return card

    def _back_button(self, target):
        button = QPushButton("Back")
        button.setObjectName("textButton")
        button.setCursor(__import__("PySide6.QtCore", fromlist=["Qt"]).Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda: self._show_page(target))
        return button

    def _start_booking(self):
        self.booking_page.start()
        self._show_page(self.booking_page)

    def _open_employee_workspace(self):
        self._refresh_employee_stats()
        self._show_page(self.employee_page)

    def _refresh_employee_stats(self):
        try:
            stats = get_employee_dashboard_stats()
        except Exception as error:
            for value in self.employee_stat_values.values():
                value.setText("—")
            self.employee_status.setText(f"Could not refresh cafe information: {error}")
            return

        for key, value in self.employee_stat_values.items():
            value.setText(f"{int(stats[key]):,}")
        self.employee_status.setText("Live cafe information refreshed.")

    def _auto_refresh_employee_stats(self):
        if self.stack.currentWidget() is self.employee_page:
            self._refresh_employee_stats()

    def _open_admin_workspace(self):
        admin_password = os.environ.get("MAYURICAFE_ADMIN_PASSWORD")
        if not admin_password:
            QMessageBox.critical(
                self,
                "Admin access is not configured",
                "Set the MAYURICAFE_ADMIN_PASSWORD environment variable and "
                "restart the application to enable admin access.",
            )
            return

        password, accepted = QInputDialog.getText(
            self,
            "Admin authentication",
            "Enter the admin password:",
            QLineEdit.EchoMode.Password,
        )
        if not accepted:
            return
        if not secrets.compare_digest(password, admin_password):
            QMessageBox.warning(
                self,
                "Access denied",
                "The admin password is incorrect.",
            )
            return

        self.admin_widget.load()
        self._show_page(self.admin_page)

    def _prompt_database_password(self, prompt):
        password, accepted = QInputDialog.getText(
            self,
            "Database connection",
            prompt,
            QLineEdit.EchoMode.Password,
        )
        if not accepted:
            raise ConnectionError("Database password entry was cancelled.")
        return password

    def _booking_completed(self, order_id):
        self._refresh_employee_stats()
        self.admin_widget.refresh_sales_reports()
        self._show_page(self.employee_page)
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "Booking saved",
            f"Order #{order_id} and its completed payment were saved.",
        )

    def _opacity_effect(self, widget):
        effect = QGraphicsOpacityEffect(widget)
        effect.setOpacity(1)
        return effect

    def _show_page(self, page, animate=True):
        self.stack.setCurrentWidget(page)
        if self._animation is not None:
            self._animation.stop()
        effect = self._effects[page]
        effect.setOpacity(0 if animate else 1)
        if animate:
            self._animation = QPropertyAnimation(effect, b"opacity", self)
            self._animation.setDuration(190)
            self._animation.setStartValue(0)
            self._animation.setEndValue(1)
            self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._animation.start()

    def _toggle_theme(self):
        self.is_dark = not self.is_dark
        self.theme_button.setText("Light theme" if self.is_dark else "Dark theme")
        self._apply_theme()

    def _apply_theme(self):
        if self.is_dark:
            colors = {
                "background": "#151412",
                "surface": "#201e1b",
                "surface_alt": "#292621",
                "text": "#f5f1eb",
                "muted": "#aaa39a",
                "border": "#37332d",
                "accent": "#f28b45",
                "accent_hover": "#ff9b58",
                "accent_soft": "#3b2a1e",
                "input": "#191816",
            }
        else:
            colors = {
                "background": "#faf8f5",
                "surface": "#ffffff",
                "surface_alt": "#f5f0e9",
                "text": "#28241f",
                "muted": "#82796f",
                "border": "#ebe5dc",
                "accent": "#e97832",
                "accent_hover": "#d96825",
                "accent_soft": "#fff0e5",
                "input": "#fcfbf9",
            }

        self.setStyleSheet(
            f"""
            QMainWindow {{
                background: {colors['background']};
            }}
            QWidget {{
                color: {colors['text']};
                font-family: "Inter", "Segoe UI", sans-serif;
                font-size: 14px;
            }}
            QWidget#appShell, QStackedWidget {{
                background: {colors['background']};
            }}
            QFrame#heroCard, QFrame#roleCard, QFrame#statCard,
            QFrame#sectionCard, QFrame#summaryCard, QFrame#sidebar {{
                background: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 18px;
            }}
            QFrame#heroCard {{
                background: {colors['surface_alt']};
                border: 1px solid {colors['border']};
                border-radius: 24px;
            }}
            QFrame#featureCard {{
                background: {colors['accent_soft']};
                border: 1px solid {colors['border']};
                border-radius: 18px;
            }}
            QLabel#brandMark {{
                background: {colors['accent']};
                color: #ffffff;
                border-radius: 13px;
                font-size: 20px;
                font-weight: 800;
            }}
            QLabel#brandName {{ font-size: 14px; font-weight: 800; letter-spacing: 1px; }}
            QLabel#brandCaption {{ color: {colors['muted']}; font-size: 9px; letter-spacing: 1.4px; }}
            QLabel#eyebrow, QLabel#statLabel, QLabel#fieldLabel {{
                color: {colors['accent']};
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 1.3px;
            }}
            QLabel#heroTitle {{ font-size: 48px; font-weight: 800; letter-spacing: 2px; }}
            QLabel#heroDescription {{ color: {colors['muted']}; font-size: 17px; }}
            QLabel#footerNote {{ color: {colors['muted']}; font-size: 10px; letter-spacing: 2px; }}
            QLabel#pageTitle, QLabel#pageTitleLeft {{ font-size: 30px; font-weight: 750; }}
            QLabel#pageSubtitle, QLabel#pageSubtitleLeft, QLabel#cardDescription,
            QLabel#mutedNote {{ color: {colors['muted']}; }}
            QLabel#pageSubtitle {{ font-size: 15px; }}
            QLabel#pageSubtitleLeft {{ font-size: 14px; }}
            QLabel#cardNumber {{ color: {colors['accent']}; font-size: 13px; font-weight: 800; }}
            QLabel#cardTitle {{ font-size: 24px; font-weight: 750; }}
            QLabel#sectionTitle {{ font-size: 20px; font-weight: 750; }}
            QLabel#statValue, QLabel#totalValue {{ font-size: 26px; font-weight: 800; }}
            QLabel#navItem, QLabel#navItemActive {{ padding: 11px 9px; border-radius: 9px; }}
            QLabel#navItem {{ color: {colors['muted']}; }}
            QLabel#navItemActive {{ background: {colors['accent_soft']}; color: {colors['accent']}; font-weight: 700; }}
            QLabel#toolChip {{
                background: {colors['surface_alt']};
                border: 1px solid {colors['border']};
                border-radius: 10px;
                padding: 11px 12px;
                font-size: 11px;
                font-weight: 650;
            }}
            QLineEdit {{
                background: {colors['input']};
                border: 1px solid {colors['border']};
                border-radius: 9px;
                padding: 0 12px;
                selection-background-color: {colors['accent']};
            }}
            QLineEdit:focus {{ border: 1px solid {colors['accent']}; }}
            QComboBox, QSpinBox {{
                background: {colors['input']};
                border: 1px solid {colors['border']};
                border-radius: 9px;
                padding: 0 10px;
                min-height: 40px;
            }}
            QComboBox:focus, QSpinBox:focus {{ border: 1px solid {colors['accent']}; }}
            QComboBox QAbstractItemView {{
                background: {colors['surface']};
                color: {colors['text']};
                selection-background-color: {colors['accent_soft']};
                selection-color: {colors['text']};
                border: 1px solid {colors['border']};
            }}
            QTableWidget {{
                background: {colors['surface']};
                alternate-background-color: {colors['surface_alt']};
                border: 1px solid {colors['border']};
                border-radius: 10px;
                gridline-color: {colors['border']};
                selection-background-color: {colors['accent_soft']};
                selection-color: {colors['text']};
            }}
            QHeaderView::section {{
                background: {colors['surface_alt']};
                color: {colors['muted']};
                border: none;
                padding: 9px;
                font-size: 10px;
                font-weight: 800;
            }}
            QCheckBox {{ spacing: 8px; }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {colors['border']};
                border-radius: 5px;
                background: {colors['input']};
            }}
            QCheckBox::indicator:checked {{
                background: {colors['accent']};
                border-color: {colors['accent']};
            }}
            QTabWidget::pane {{
                border: 1px solid {colors['border']};
                border-radius: 12px;
                background: {colors['surface']};
                top: -1px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {colors['muted']};
                padding: 11px 17px;
                margin-right: 5px;
                border-bottom: 2px solid transparent;
                font-weight: 650;
            }}
            QTabBar::tab:selected {{
                color: {colors['accent']};
                border-bottom: 2px solid {colors['accent']};
            }}
            QTabBar::tab:hover {{ color: {colors['text']}; }}
            QPushButton {{
                border: none;
                border-radius: 10px;
                padding: 0 18px;
                font-weight: 700;
            }}
            QPushButton#primaryButton {{
                background: {colors['accent']};
                color: #ffffff;
            }}
            QPushButton#primaryButton:hover {{ background: {colors['accent_hover']}; }}
            QPushButton#primaryButton:disabled {{ background: {colors['surface_alt']}; color: {colors['muted']}; }}
            QPushButton#secondaryButton, QPushButton#themeButton {{
                background: {colors['surface']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
            }}
            QPushButton#secondaryButton:hover, QPushButton#themeButton:hover {{
                border: 1px solid {colors['accent']};
                color: {colors['accent']};
            }}
            QPushButton#textButton {{ background: transparent; color: {colors['muted']}; }}
            QPushButton#textButton:hover {{ color: {colors['accent']}; }}
            QScrollArea {{ background: transparent; }}
            """
        )
