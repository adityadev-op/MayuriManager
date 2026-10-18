import os
import secrets
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from Database_ import connection
from gui.admin import AdminWidget
from gui.booking import BookingWidget
from gui.order_management import OrderManagementWidget
from gui.table_management import TableManagementWidget
from gui.widgets import PremiumButton
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
        self.order_management_page = OrderManagementWidget(
            self._open_employee_workspace,
            self._open_table_management,
            self._open_admin_workspace,
        )
        self.table_management_page = TableManagementWidget(
            self._open_employee_workspace,
            self._open_order_management,
            self._open_admin_workspace,
            self._on_tables_updated,
        )
        self.admin_page = self._build_admin_page()

        for page in (
            self.home_page,
            self.roles_page,
            self.employee_page,
            self.booking_page,
            self.order_management_page,
            self.table_management_page,
            self.admin_page,
        ):
            self.stack.addWidget(page)

        shell_layout.addWidget(self.stack, 1)
        self.setCentralWidget(shell)
        self._apply_theme()
        self._show_page(self.home_page)
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
        brand_caption = QLabel("Cafe operations, thoughtfully managed")
        brand_caption.setObjectName("brandCaption")
        brand.addWidget(brand_name)
        brand.addWidget(brand_caption)

        layout.addWidget(mark)
        layout.addLayout(brand)
        layout.addStretch()

        self.live_clock = QLabel()
        self.live_clock.setObjectName("liveClock")
        self.live_clock.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.live_clock)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_live_clock)
        self.clock_timer.start(1000)
        self._update_live_clock()

        self.theme_button = PremiumButton("☼")
        self.theme_button.setObjectName("themeButton")
        self.theme_button.setFixedSize(42, 42)
        self.theme_button.setAccessibleName("Switch to dark theme")
        self.theme_button.setToolTip("Switch to dark theme")
        self.theme_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_button.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_button)
        return bar

    def _build_home_page(self):
        page = QWidget()
        page.setObjectName("welcomePage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(16)
        layout.addStretch()

        content = QWidget()
        content.setMaximumWidth(1040)
        content.setMinimumWidth(760)
        content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        hero = QFrame()
        hero.setObjectName("welcomeHero")
        hero.setAccessibleName("MAYURICAFE welcome")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(62, 52, 62, 48)
        hero_layout.setSpacing(16)
        hero_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        eyebrow = QLabel("REFINED CAFE MANAGEMENT")
        eyebrow.setObjectName("welcomeEyebrow")
        eyebrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Welcome to MAYURICAFE")
        title.setObjectName("welcomeTitle")
        title.setWordWrap(True)
        title.setMinimumWidth(620)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description = QLabel(
            "A thoughtful workspace for your cafe's daily rhythm. Manage bookings "
            "and live orders as an employee, or explore reports and performance "
            "in the admin console."
        )
        description.setObjectName("welcomeDescription")
        description.setWordWrap(True)
        description.setMaximumWidth(760)
        description.setMinimumWidth(620)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)

        actions = QHBoxLayout()
        actions.setSpacing(14)
        actions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.enter_cafe_button = PremiumButton("Enter Cafe")
        self.enter_cafe_button.setObjectName("primaryButton")
        self.enter_cafe_button.setMinimumSize(190, 54)
        self.enter_cafe_button.setAccessibleName("Enter cafe workspace")
        self.enter_cafe_button.clicked.connect(
            lambda: self._show_page(self.roles_page)
        )
        self.quick_guide_button = PremiumButton("Quick Guide")
        self.quick_guide_button.setObjectName("secondaryButton")
        self.quick_guide_button.setMinimumSize(170, 54)
        self.quick_guide_button.clicked.connect(self._show_quick_guide)
        actions.addWidget(self.enter_cafe_button)
        actions.addWidget(self.quick_guide_button)

        hero_layout.addWidget(eyebrow)
        hero_layout.addWidget(title)
        hero_layout.addWidget(description, alignment=Qt.AlignmentFlag.AlignHCenter)
        hero_layout.addSpacing(6)
        hero_layout.addLayout(actions)

        content_layout.addWidget(hero)

        capabilities = QHBoxLayout()
        capabilities.setContentsMargins(24, 22, 24, 22)
        capabilities.setSpacing(22)
        for symbol, text in (
            ("01", "Employee workspace"),
            ("02", "Admin console"),
            ("03", "Live reporting"),
        ):
            badge = QWidget()
            badge_layout = QHBoxLayout(badge)
            badge_layout.setContentsMargins(0, 0, 0, 0)
            badge_layout.setSpacing(9)
            marker = QLabel(symbol)
            marker.setObjectName("capabilityMarker")
            marker.setAlignment(Qt.AlignmentFlag.AlignCenter)
            marker.setFixedSize(28, 28)
            label = QLabel(text)
            label.setObjectName("capabilityLabel")
            badge_layout.addWidget(marker)
            badge_layout.addWidget(label)
            capabilities.addWidget(badge, 1, Qt.AlignmentFlag.AlignCenter)
        content_layout.addLayout(capabilities)

        layout.addWidget(content, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 14, 0, 0)
        copyright_note = QLabel(
            f"© {datetime.now().year} MAYURICAFE · Desktop cafe management"
        )
        copyright_note.setObjectName("welcomeCopyright")
        footer.addWidget(copyright_note)
        footer.addStretch()
        footer_note = QLabel("GOOD FOOD. THOUGHTFUL SERVICE.")
        footer_note.setObjectName("footerNote")
        footer.addWidget(footer_note)
        layout.addLayout(footer)
        return page

    def _show_quick_guide(self):
        QMessageBox.information(
            self,
            "MAYURICAFE quick guide",
            "Choose Enter Cafe to select a workspace.\n\n"
            "Employee: look up a guest, add menu items, select dine-in or "
            "takeaway, assign an employee, then review and save the paid order.\n\n"
            "Admin: enter the admin password to manage menu items, browse "
            "records, and review sales and revenue reports.",
        )

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

        back = PremiumButton("Back to welcome")
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
        button = PremiumButton(action)
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
        page.setObjectName("employeePage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(20)

        heading_row = QHBoxLayout()
        heading_row.addWidget(
            self._page_heading(
                "Employee dashboard",
                "Your service desk for the day.",
            ),
            1,
        )
        self.employee_live_badge = QLabel("●  WAITING FOR DATA")
        self.employee_live_badge.setObjectName("employeeLiveBadge")
        self.employee_live_badge.setProperty("state", "waiting")
        self.employee_live_badge.setAccessibleName("Cafe database connection status")
        heading_row.addWidget(self.employee_live_badge, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(heading_row)

        navigation = QFrame()
        navigation.setObjectName("employeeNavigation")
        nav_layout = QHBoxLayout(navigation)
        nav_layout.setContentsMargins(18, 8, 18, 8)
        nav_layout.setSpacing(18)
        dashboard_label = QLabel("Dashboard")
        dashboard_label.setObjectName("employeeNavActive")
        nav_layout.addWidget(dashboard_label)
        bookings_button = PremiumButton("New booking")
        bookings_button.setObjectName("employeeNavButton")
        bookings_button.clicked.connect(self._start_booking)
        nav_layout.addWidget(bookings_button)
        orders_button = PremiumButton("Live orders")
        orders_button.setObjectName("employeeNavButton")
        orders_button.clicked.connect(self._open_order_management)
        nav_layout.addWidget(orders_button)
        tables_button = PremiumButton("Seat management")
        tables_button.setObjectName("employeeNavButton")
        tables_button.clicked.connect(self._open_table_management)
        nav_layout.addWidget(tables_button)
        admin_button = PremiumButton("Admin console")
        admin_button.setObjectName("employeeNavButton")
        admin_button.clicked.connect(self._open_admin_workspace)
        nav_layout.addWidget(admin_button)
        nav_layout.addStretch()
        self.employee_refresh_button = PremiumButton("Refresh data")
        self.employee_refresh_button.setObjectName("secondaryButton")
        self.employee_refresh_button.setMinimumHeight(38)
        self.employee_refresh_button.clicked.connect(self._refresh_employee_stats)
        nav_layout.addWidget(self.employee_refresh_button)
        layout.addWidget(navigation)

        self.employee_stat_values = {}
        self.employee_stat_badges = {}
        self.employee_stat_targets = {}
        self.employee_stat_animations = {}
        stats = QHBoxLayout()
        stats.setSpacing(16)
        for key, label, note in (
            ("todays_bookings", "TODAY'S ORDERS", "Orders placed today"),
            ("available_tables", "AVAILABLE TABLES", "Ready for dine-in"),
            ("open_orders", "OPEN ORDERS", "Awaiting completion"),
        ):
            card, value, badge = self._employee_stat_card(label, note, key)
            self.employee_stat_values[key] = value
            self.employee_stat_badges[key] = badge
            stats.addWidget(card)
        layout.addLayout(stats)

        dashboard_body = QHBoxLayout()
        dashboard_body.setSpacing(18)
        dashboard_body.addWidget(self._build_employee_operations_card(), 7)
        dashboard_body.addWidget(self._build_employee_actions_column(), 4)
        layout.addLayout(dashboard_body, 1)

        footer = QHBoxLayout()
        self.employee_status = QLabel("Cafe information has not been refreshed yet.")
        self.employee_status.setObjectName("mutedNote")
        footer.addWidget(self.employee_status, 1)
        footer.addWidget(self._back_button(self.roles_page))
        layout.addLayout(footer)
        return page

    def _employee_stat_card(self, label, note, key):
        card = QFrame()
        card.setObjectName("employeeMetricCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(8)
        top_row = QHBoxLayout()
        marker = QLabel({"todays_bookings": "01", "available_tables": "02", "open_orders": "03"}[key])
        marker.setObjectName("employeeMetricMarker")
        marker.setAlignment(Qt.AlignmentFlag.AlignCenter)
        marker.setFixedSize(34, 34)
        top_row.addWidget(marker)
        top_row.addStretch()
        badge = QLabel("WAITING")
        badge.setObjectName("employeeMetricBadge")
        badge.setProperty("state", "waiting")
        top_row.addWidget(badge)
        title = QLabel(label)
        title.setObjectName("employeeMetricTitle")
        value = QLabel("—")
        value.setObjectName("employeeMetricValue")
        description = QLabel(note)
        description.setObjectName("employeeMetricNote")
        layout.addLayout(top_row)
        layout.addWidget(title)
        layout.addWidget(value)
        layout.addWidget(description)
        return card, value, badge

    def _build_employee_operations_card(self):
        card = QFrame()
        card.setObjectName("employeePanel")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Today's service")
        title.setObjectName("employeePanelTitle")
        label = QLabel("SERVICE FLOW")
        label.setObjectName("employeePanelEyebrow")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(label)
        layout.addLayout(header)

        description = QLabel(
            "Take each guest from their details through order, service, team "
            "assignment and payment in one guided flow."
        )
        description.setObjectName("employeePanelDescription")
        description.setWordWrap(True)
        layout.addWidget(description)

        stages = QHBoxLayout()
        stages.setSpacing(8)
        for number, title_text in (
            ("01", "Guest"),
            ("02", "Order"),
            ("03", "Service"),
            ("04", "Team"),
            ("05", "Payment"),
        ):
            stage = QFrame()
            stage.setObjectName("employeeFlowStage")
            stage_layout = QVBoxLayout(stage)
            stage_layout.setContentsMargins(10, 12, 10, 12)
            stage_layout.setSpacing(6)
            stage_number = QLabel(number)
            stage_number.setObjectName("employeeFlowNumber")
            stage_name = QLabel(title_text)
            stage_name.setObjectName("employeeFlowName")
            stage_layout.addWidget(stage_number)
            stage_layout.addWidget(stage_name)
            stages.addWidget(stage, 1)
        layout.addLayout(stages)

        footnote = QLabel(
            "Your dashboard counts update from the cafe database and refresh automatically."
        )
        footnote.setObjectName("mutedNote")
        footnote.setWordWrap(True)
        layout.addWidget(footnote)
        layout.addStretch()
        return card

    def _build_employee_actions_column(self):
        column = QWidget()
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        booking_card = QFrame()
        booking_card.setObjectName("employeeBookingCard")
        booking_layout = QVBoxLayout(booking_card)
        booking_layout.setContentsMargins(24, 24, 24, 24)
        booking_layout.setSpacing(12)
        kicker = QLabel("READY FOR THE NEXT GUEST?")
        kicker.setObjectName("employeeBookingKicker")
        title = QLabel("Start a new booking")
        title.setObjectName("employeeBookingTitle")
        description = QLabel(
            "Open the guided flow to add a guest, build their order and take payment."
        )
        description.setObjectName("employeeBookingDescription")
        description.setWordWrap(True)
        button = PremiumButton("Create booking")
        button.setObjectName("employeeBookingButton")
        button.setMinimumHeight(46)
        button.clicked.connect(self._start_booking)
        booking_layout.addWidget(kicker)
        booking_layout.addWidget(title)
        booking_layout.addWidget(description)
        booking_layout.addSpacing(4)
        booking_layout.addWidget(button)
        layout.addWidget(booking_card)

        status_card = QFrame()
        status_card.setObjectName("employeePanel")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(20, 18, 20, 18)
        status_layout.setSpacing(8)
        status_title = QLabel("Cafe status")
        status_title.setObjectName("employeePanelEyebrow")
        status_detail = QLabel(
            "Dashboard figures are read from the active cafe database connection."
        )
        status_detail.setObjectName("employeePanelDescription")
        status_detail.setWordWrap(True)
        status_layout.addWidget(status_title)
        status_layout.addWidget(status_detail)
        layout.addWidget(status_card)
        layout.addStretch()
        return column

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
        button = PremiumButton("Back")
        button.setObjectName("textButton")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda: self._show_page(target))
        return button

    def _start_booking(self):
        self.booking_page.start()
        self._show_page(self.booking_page)

    def _open_employee_workspace(self):
        self._refresh_employee_stats()
        self._show_page(self.employee_page)

    def _open_order_management(self):
        self.order_management_page.refresh_orders()
        self._show_page(self.order_management_page)

    def _open_table_management(self):
        self.table_management_page.refresh_tables()
        self._show_page(self.table_management_page)

    def _on_tables_updated(self):
        self._refresh_employee_stats()
        self.order_management_page.refresh_orders()

    def _refresh_employee_stats(self):
        try:
            stats = get_employee_dashboard_stats()
        except Exception as error:
            for value in self.employee_stat_values.values():
                value.setText("—")
            for key, timer in self.employee_stat_animations.items():
                timer.stop()
                self.employee_stat_targets[key] = 0
            self._set_employee_connection_status("unavailable")
            self.employee_status.setText(f"Could not refresh cafe information: {error}")
            return

        for key, value in self.employee_stat_values.items():
            self._animate_stat_value(key, int(stats[key]))
            self.employee_stat_badges[key].setText("LIVE")
            self.employee_stat_badges[key].setProperty("state", "online")
            self._refresh_widget_style(self.employee_stat_badges[key])
        self._set_employee_connection_status("online")
        self.employee_status.setText(
            f"Live cafe information · Updated {datetime.now().strftime('%I:%M:%S %p').lstrip('0')}"
        )

    def _set_employee_connection_status(self, state):
        if state == "online":
            self.employee_live_badge.setText("●  LIVE DATA")
            self.employee_live_badge.setProperty("state", "online")
            badge_text = "LIVE"
        elif state == "unavailable":
            self.employee_live_badge.setText("●  DATA UNAVAILABLE")
            self.employee_live_badge.setProperty("state", "error")
            badge_text = "UNAVAILABLE"
        else:
            self.employee_live_badge.setText("●  WAITING FOR DATA")
            self.employee_live_badge.setProperty("state", "waiting")
            badge_text = "WAITING"

        self._refresh_widget_style(self.employee_live_badge)
        for badge in self.employee_stat_badges.values():
            badge.setText(badge_text)
            badge.setProperty("state", state)
            self._refresh_widget_style(badge)

    @staticmethod
    def _refresh_widget_style(widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _animate_stat_value(self, key, target):
        value = self.employee_stat_values[key]
        timer = self.employee_stat_animations.get(key)
        start = self.employee_stat_targets.get(key, 0)
        if timer is not None:
            timer.stop()
            try:
                start = int(value.text().replace(',', ''))
            except ValueError:
                pass
        self.employee_stat_targets[key] = target
        steps = 18
        tick = {'index': 0}
        timer = QTimer(value)
        timer.setInterval(16)

        def advance():
            tick['index'] += 1
            progress = min(tick['index'] / steps, 1)
            eased = 1 - (1 - progress) ** 3
            current = round(start + (target - start) * eased)
            value.setText(f"{current:,}")
            if progress >= 1:
                timer.stop()
                timer.deleteLater()
                self.employee_stat_animations.pop(key, None)

        timer.timeout.connect(advance)
        self.employee_stat_animations[key] = timer
        timer.start()

    def _update_live_clock(self):
        self.live_clock.setText(
            f"LIVE  ·  {datetime.now().strftime('%a, %d %b  ·  %I:%M %p').lstrip('0')}"
        )

    def _auto_refresh_employee_stats(self):
        if self.stack.currentWidget() is self.employee_page:
            self._refresh_employee_stats()
        elif self.stack.currentWidget() is self.order_management_page:
            self.order_management_page.refresh_orders()
        elif self.stack.currentWidget() is self.table_management_page:
            self.table_management_page.refresh_tables()

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
        self.order_management_page.refresh_orders()
        self.admin_widget.refresh_sales_reports()
        self._show_page(self.employee_page)
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "Booking saved",
            f"Order #{order_id} and its completed payment were saved.",
        )

    def _show_page(self, page):
        self.stack.setCurrentWidget(page)

    def _toggle_theme(self):
        self.is_dark = not self.is_dark
        self.theme_button.setText("☾" if self.is_dark else "☀")
        theme_action = "light" if self.is_dark else "dark"
        self.theme_button.setAccessibleName(f"Switch to {theme_action} theme")
        self.theme_button.setToolTip(f"Switch to {theme_action} theme")
        self._apply_theme()

    def _apply_theme(self):
        if self.is_dark:
            colors = {
                "background": "#11100f",
                "background_end": "#1b1511",
                "surface": "#1b1917",
                "surface_alt": "#24211e",
                "hero_start": "#32251c",
                "hero_end": "#211a16",
                "text": "#f7f2ec",
                "muted": "#aaa198",
                "border": "#37312b",
                "accent": "#f28b45",
                "accent_hover": "#ff9b58",
                "accent_deep": "#d7652d",
                "accent_soft": "#3b2a1e",
                "input": "#191816",
                "welcome_bg": "#1c1714",
                "welcome_card": "#2b211b",
                "welcome_card_mid": "#38271f",
                "welcome_ink": "#f7eee5",
                "welcome_accent": "#e97832",
                "welcome_muted": "#c0a98f",
                "welcome_gold": "#73573f",
            }
        else:
            colors = {
                "background": "#fffdfa",
                "background_end": "#fff7ef",
                "surface": "#ffffff",
                "surface_alt": "#fff4ea",
                "hero_start": "#fff0df",
                "hero_end": "#f8dfca",
                "text": "#28241f",
                "muted": "#82796f",
                "border": "#efe4d9",
                "accent": "#e97832",
                "accent_hover": "#d96825",
                "accent_deep": "#bd5624",
                "accent_soft": "#fff0e5",
                "input": "#fcfbf9",
                "welcome_bg": "#f5f1ed",
                "welcome_card": "#fefdfb",
                "welcome_card_mid": "#ffefe6",
                "welcome_ink": "#2b1810",
                "welcome_accent": "#c85a17",
                "welcome_muted": "#8b7355",
                "welcome_gold": "#e5cba8",
            }

        self.setStyleSheet(
            f"""
            QMainWindow {{
                background: {colors['background']};
            }}
            QWidget {{
                color: {colors['text']};
                font-family: "Noto Sans", "Inter", "Aptos", "Segoe UI", sans-serif;
                font-size: 14px;
            }}
            QWidget#appShell {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {colors['background']}, stop:1 {colors['background_end']});
            }}
            QStackedWidget {{
                background: transparent;
            }}
            QWidget#employeePage {{ background: transparent; }}
            QFrame#employeeNavigation {{
                background: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 15px;
            }}
            QFrame#employeeMetricCard, QFrame#employeePanel {{
                background: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 20px;
            }}
            QFrame#employeeMetricCard:hover, QFrame#employeePanel:hover {{
                border-color: {colors['welcome_gold']};
            }}
            QLabel#employeeMetricMarker {{
                background: {colors['accent_soft']};
                border: none;
                border-radius: 17px;
            }}
            QFrame#employeeFlowStage {{
                background: {colors['surface_alt']};
                border: 1px solid {colors['border']};
                border-radius: 13px;
            }}
            QFrame#employeeBookingCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {colors['welcome_card']},
                    stop:0.54 {colors['welcome_card_mid']},
                    stop:1 {colors['welcome_bg']});
                border: 1px solid {colors['welcome_gold']};
                border-radius: 22px;
            }}
            QFrame#orderCard, QFrame#orderEmptyState {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {colors['surface']}, stop:1 {colors['surface_alt']});
                border: 1px solid {colors['border']};
                border-radius: 22px;
            }}
            QFrame#orderCard:hover {{ border-color: {colors['welcome_gold']}; }}
            QFrame#orderCardDivider {{ background: {colors['border']}; border: none; }}
            QFrame#adminDashboardControls, QFrame#adminMetricCard,
            QFrame#adminDashboardPanel {{
                background: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 18px;
            }}
            QFrame#adminMetricCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {colors['surface']}, stop:1 {colors['surface_alt']});
                border-radius: 21px;
            }}
            QFrame#seatRow {{
                background: {colors['surface_alt']};
                border: 1px solid {colors['border']};
                border-radius: 14px;
            }}
            QProgressBar#adminPerformanceBar {{
                border: none;
                border-radius: 3px;
                background: {colors['surface_alt']};
            }}
            QProgressBar#adminPerformanceBar::chunk {{
                border-radius: 3px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {colors['welcome_accent']}, stop:1 {colors['accent']});
            }}
            QWidget#welcomePage {{
                background: {colors['welcome_bg']};
            }}
            QFrame#heroCard, QFrame#roleCard, QFrame#statCard,
            QFrame#sectionCard, QFrame#summaryCard, QFrame#sidebar {{
                background: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 22px;
            }}
            QFrame#heroCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {colors['hero_start']}, stop:1 {colors['hero_end']});
                border: 1px solid {colors['border']};
                border-radius: 28px;
            }}
            QFrame#welcomeHero {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {colors['welcome_card']},
                    stop:0.52 {colors['welcome_card_mid']},
                    stop:1 {colors['welcome_bg']});
                border: 1px solid {colors['welcome_gold']};
                border-radius: 40px;
            }}
            QFrame#featureCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {colors['accent_soft']}, stop:1 {colors['hero_start']});
                border: 1px solid {colors['border']};
                border-radius: 22px;
            }}
            QFrame#roleCard:hover, QFrame#statCard:hover {{
                border-color: {colors['accent']};
            }}
            QLabel#brandMark {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {colors['accent_hover']}, stop:1 {colors['accent_deep']});
                color: #ffffff;
                border-radius: 50%;
                font-size: 20px;
                font-weight: 800;
            }}
            QLabel#brandName {{ font-size: 14px; font-weight: 800; letter-spacing: 1.4px; }}
            QLabel#brandCaption {{ color: {colors['muted']}; font-size: 9px; letter-spacing: 1.4px; }}
            QLabel#employeeLiveBadge {{
                background: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 13px;
                padding: 8px 12px;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 0.7px;
            }}
            QLabel#employeeLiveBadge[state="online"] {{ color: #397354; }}
            QLabel#employeeLiveBadge[state="error"] {{ color: #b74735; }}
            QLabel#employeeLiveBadge[state="waiting"] {{ color: {colors['muted']}; }}
            QLabel#employeeNavActive {{
                background: {colors['accent_soft']};
                color: {colors['accent_deep']};
                border-radius: 10px;
                padding: 10px 13px;
                font-weight: 750;
            }}
            QLabel#employeeMetricMarker {{
                color: {colors['accent_deep']};
                font-size: 11px;
                font-weight: 800;
            }}
            QLabel#employeeMetricBadge {{
                background: {colors['surface_alt']};
                border-radius: 9px;
                padding: 5px 8px;
                font-size: 9px;
                font-weight: 800;
                letter-spacing: 0.4px;
            }}
            QLabel#employeeMetricBadge[state="online"] {{ color: #397354; }}
            QLabel#employeeMetricBadge[state="unavailable"] {{ color: #b74735; }}
            QLabel#employeeMetricBadge[state="waiting"] {{ color: {colors['muted']}; }}
            QLabel#employeeMetricTitle, QLabel#employeePanelEyebrow,
            QLabel#employeeBookingKicker {{
                color: {colors['welcome_muted']};
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 1.1px;
            }}
            QLabel#employeeMetricValue {{
                color: {colors['text']};
                font-family: "Noto Serif", "Georgia", "Palatino Linotype", "Times New Roman", serif;
                font-size: 34px;
                font-weight: 700;
            }}
            QLabel#employeeMetricNote {{ color: {colors['muted']}; font-size: 12px; }}
            QLabel#employeePanelTitle, QLabel#employeeBookingTitle {{
                color: {colors['text']};
                font-family: "Noto Serif", "Georgia", "Palatino Linotype", "Times New Roman", serif;
                font-size: 22px;
                font-weight: 700;
            }}
            QLabel#employeePanelDescription {{ color: {colors['muted']}; font-size: 12px; }}
            QLabel#employeeFlowNumber {{
                color: {colors['accent']};
                font-size: 10px;
                font-weight: 800;
            }}
            QLabel#employeeFlowName {{ font-size: 12px; font-weight: 700; }}
            QLabel#employeeBookingKicker {{ color: {colors['welcome_accent']}; }}
            QLabel#employeeBookingTitle {{ color: {colors['welcome_ink']}; font-size: 24px; }}
            QLabel#employeeBookingDescription {{ color: {colors['welcome_muted']}; font-size: 12px; }}
            QLabel#orderCardId, QLabel#orderCardMeta {{
                color: {colors['welcome_muted']};
                font-size: 10px;
                font-weight: 700;
            }}
            QLabel#orderCardId {{ letter-spacing: 1px; }}
            QLabel#orderCardCustomer {{
                color: {colors['welcome_ink']};
                font-family: "Noto Serif", "Georgia", "Palatino Linotype", "Times New Roman", serif;
                font-size: 20px;
                font-weight: 700;
            }}
            QLabel#orderCardItem {{ color: {colors['text']}; font-size: 12px; }}
            QLabel#orderCardAmount {{ color: {colors['text']}; font-size: 12px; font-weight: 650; }}
            QLabel#orderCardTotal {{
                color: {colors['welcome_ink']};
                font-size: 16px;
                font-weight: 800;
            }}
            QLabel#orderStatusBadge {{
                background: {colors['accent_soft']};
                color: {colors['accent_deep']};
                border-radius: 10px;
                padding: 6px 10px;
                font-size: 10px;
                font-weight: 800;
            }}
            QLabel#orderStatusBadge[state="ready"] {{ background: #e7f3eb; color: #397354; }}
            QLabel#orderStatusBadge[state="preparing"] {{ background: #fff0df; color: #a45320; }}
            QLabel#orderStatusBadge[state="pending"] {{ background: {colors['accent_soft']}; color: {colors['accent_deep']}; }}
            QLabel#adminDashboardEyebrow, QLabel#adminMetricLabel {{
                color: {colors['welcome_muted']};
                font-size: 9px;
                font-weight: 800;
                letter-spacing: 1px;
            }}
            QLabel#adminMetricValue {{
                color: {colors['welcome_ink']};
                font-family: "Noto Serif", "Georgia", "Palatino Linotype", "Times New Roman", serif;
                font-size: 26px;
                font-weight: 700;
            }}
            QLabel#adminDashboardPanelTitle {{
                color: {colors['text']};
                font-family: "Noto Serif", "Georgia", "Palatino Linotype", "Times New Roman", serif;
                font-size: 19px;
                font-weight: 700;
            }}
            QLabel#adminPerformanceName {{ font-size: 11px; font-weight: 750; }}
            QLabel#adminPerformanceTotals {{ color: {colors['welcome_muted']}; font-size: 10px; font-weight: 700; }}
            QLabel#seatRowTitle {{ color: {colors['text']}; font-size: 13px; font-weight: 750; }}
            QLabel#seatStatusBadge {{
                background: {colors['accent_soft']};
                color: {colors['accent_deep']};
                border-radius: 9px;
                padding: 5px 8px;
                font-size: 10px;
                font-weight: 750;
            }}
            QLabel#seatStatusBadge[state="available"] {{ background: #e7f3eb; color: #397354; }}
            QLabel#seatStatusBadge[state="other"] {{ background: {colors['surface']}; color: {colors['muted']}; }}
            QLabel#eyebrow, QLabel#statLabel, QLabel#fieldLabel {{
                color: {colors['accent']};
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 1.3px;
            }}
            QLabel#liveClock {{ color: {colors['muted']}; font-size: 11px; font-weight: 650; letter-spacing: 0.5px; padding: 0 10px; }}
            QLabel#heroTitle {{ font-family: "Noto Serif", "Georgia", "Palatino Linotype", "Times New Roman", serif; font-size: 50px; font-weight: 700; letter-spacing: 1.6px; }}
            QLabel#heroDescription {{ color: {colors['muted']}; font-size: 17px; }}
            QLabel#welcomeEyebrow {{
                color: {colors['welcome_accent']};
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 2.2px;
            }}
            QLabel#welcomeTitle {{
                color: {colors['welcome_ink']};
                font-family: "Noto Serif", "Georgia", "Palatino Linotype", "Times New Roman", serif;
                font-size: 44px;
                font-weight: 650;
                letter-spacing: -0.3px;
            }}
            QLabel#welcomeDescription {{
                color: {colors['welcome_ink']};
                font-size: 16px;
            }}
            QLabel#capabilityMarker {{
                background: {colors['welcome_accent']};
                color: #ffffff;
                border-radius: 14px;
                font-size: 10px;
                font-weight: 800;
            }}
            QLabel#capabilityLabel {{
                color: {colors['welcome_muted']};
                font-size: 12px;
                font-weight: 650;
            }}
            QLabel#welcomeCopyright {{
                color: {colors['welcome_muted']};
                font-size: 11px;
                font-weight: 500;
            }}
            QLabel#footerNote {{ color: {colors['welcome_muted']}; font-size: 10px; letter-spacing: 2px; }}
            QLabel#pageTitle, QLabel#pageTitleLeft {{ font-family: "Noto Serif", "Georgia", "Palatino Linotype", "Times New Roman", serif; font-size: 30px; font-weight: 700; letter-spacing: 0.2px; }}
            QLabel#pageSubtitle, QLabel#pageSubtitleLeft, QLabel#cardDescription,
            QLabel#mutedNote {{ color: {colors['muted']}; }}
            QLabel#pageSubtitle {{ font-size: 15px; }}
            QLabel#pageSubtitleLeft {{ font-size: 14px; }}
            QLabel#cardNumber {{ color: {colors['accent']}; font-size: 13px; font-weight: 800; }}
            QLabel#cardTitle {{ font-family: "Noto Serif", "Georgia", "Palatino Linotype", "Times New Roman", serif; font-size: 24px; font-weight: 700; }}
            QLabel#sectionTitle {{ font-family: "Noto Serif", "Georgia", "Palatino Linotype", "Times New Roman", serif; font-size: 20px; font-weight: 700; }}
            QLabel#statValue, QLabel#totalValue {{ font-size: 26px; font-weight: 800; }}
            QLabel#summaryCaption {{ color: {colors['muted']}; font-size: 9px; font-weight: 800; letter-spacing: 1px; }}
            QLabel#summaryValue {{ font-size: 13px; font-weight: 700; }}
            QLabel#emptyState {{ color: {colors['muted']}; padding: 24px; }}
            QLabel#bookingStep {{
                color: {colors['muted']};
                background: {colors['surface_alt']};
                border-radius: 9px;
                padding: 8px 6px;
                font-size: 10px;
                font-weight: 750;
                letter-spacing: 0.6px;
            }}
            QLabel#bookingStep[active="true"] {{
                color: #ffffff;
                background: {colors['accent_deep']};
            }}
            QLabel#bookingStep[complete="true"] {{
                color: {colors['accent_deep']};
                background: {colors['accent_soft']};
            }}
            QFrame#bookingSummary {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {colors['surface']}, stop:1 {colors['surface_alt']});
                border: 1px solid {colors['border']};
                border-radius: 14px;
            }}
            QProgressBar#bookingProgress {{
                border: none;
                border-radius: 2px;
                background: {colors['surface_alt']};
            }}
            QProgressBar#bookingProgress::chunk {{
                border-radius: 2px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {colors['accent']}, stop:1 {colors['accent_hover']});
            }}
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
                border-radius: 12px;
                padding: 0 12px;
                selection-background-color: {colors['accent']};
            }}
            QLineEdit:focus {{ border: 1px solid {colors['accent']}; }}
            QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
                background: {colors['input']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
                padding: 0 10px;
                min-height: 40px;
            }}
            QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
                border: 2px solid {colors['accent_deep']};
            }}
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
                border-radius: 14px;
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
            QTableWidget::item {{ padding: 5px 7px; border: none; }}
            QTableWidget:focus {{
                border: 2px solid {colors['accent_deep']};
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
            QCheckBox:focus {{
                color: {colors['accent_deep']};
            }}
            QTabWidget::pane {{
                border: 1px solid {colors['border']};
                border-radius: 16px;
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
            QTabBar::tab:focus {{
                color: {colors['accent_deep']};
                border-bottom: 2px solid {colors['accent_deep']};
            }}
            QPushButton {{
                border: none;
                border-radius: 10px;
                padding: 0 18px;
                font-weight: 700;
                letter-spacing: 0.2px;
            }}
            QPushButton:focus {{
                border: 2px solid {colors['accent_deep']};
            }}
            QPushButton#primaryButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {colors['accent_hover']}, stop:1 {colors['accent_deep']});
                color: #ffffff;
            }}
            QPushButton#primaryButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {colors['accent_hover']}, stop:1 {colors['accent_deep']});
                border: 1px solid {colors['accent_hover']};
                color: #ffffff;
            }}
            QPushButton#primaryButton:pressed {{
                background: {colors['accent_deep']};
                padding-top: 2px;
            }}
            QPushButton#primaryButton:disabled {{ background: {colors['surface_alt']}; color: {colors['muted']}; }}
            QPushButton#employeeNavButton {{
                background: transparent;
                color: {colors['muted']};
                padding: 0 10px;
            }}
            QPushButton#employeeNavButton:hover {{
                background: {colors['accent_soft']};
                color: {colors['accent_deep']};
            }}
            QPushButton#employeeBookingButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {colors['welcome_accent']}, stop:1 {colors['accent_deep']});
                color: #ffffff;
                border-radius: 13px;
            }}
            QPushButton#employeeBookingButton:hover {{
                background: {colors['accent_hover']};
                border: 1px solid {colors['welcome_accent']};
                color: #ffffff;
            }}
            QPushButton#employeeBookingButton:pressed {{
                background: {colors['accent_deep']};
                padding-top: 2px;
            }}
            QPushButton#seatVacateButton {{
                background: {colors['surface']};
                color: {colors['accent_deep']};
                border: 1px solid {colors['border']};
                border-radius: 10px;
            }}
            QPushButton#seatVacateButton:hover {{
                background: {colors['accent_soft']};
                border-color: {colors['accent_deep']};
                color: {colors['accent_deep']};
            }}
            QPushButton#secondaryButton, QPushButton#themeButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {colors['surface']}, stop:1 {colors['surface_alt']});
                color: {colors['text']};
                border: 1px solid {colors['border']};
            }}
            QPushButton#themeButton {{
                border-radius: 21px;
                padding: 0;
                font-size: 20px;
            }}
            QPushButton#secondaryButton:hover, QPushButton#themeButton:hover {{
                background: {colors['accent_soft']};
                border: 1px solid {colors['accent_deep']};
                color: {colors['accent_deep']};
            }}
            QPushButton#secondaryButton:pressed, QPushButton#themeButton:pressed {{
                background: {colors['accent_soft']};
                padding-top: 2px;
            }}
            QPushButton#textButton {{ background: transparent; color: {colors['muted']}; }}
            QPushButton#textButton:hover {{
                background: {colors['accent_soft']};
                color: {colors['accent_deep']};
            }}
            QPushButton#textButton:pressed {{ padding-top: 2px; }}
            QScrollArea {{ background: transparent; }}
            """
        )
