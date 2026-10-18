from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from Receptionist.tables import get_cafe_tables, vacate_cafe_table
from gui.widgets import PremiumButton


class TableManagementWidget(QWidget):
    def __init__(
        self,
        on_dashboard,
        on_orders,
        on_admin,
        on_tables_updated,
        parent=None,
    ):
        super().__init__(parent)
        self.on_dashboard = on_dashboard
        self.on_orders = on_orders
        self.on_admin = on_admin
        self.on_tables_updated = on_tables_updated
        self.tables = []
        self.load_error = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(16)

        heading = QHBoxLayout()
        title_group = QVBoxLayout()
        title_group.setSpacing(5)
        title = QLabel("Seat management")
        title.setObjectName("pageTitleLeft")
        subtitle = QLabel("Review allocated and available cafe seats.")
        subtitle.setObjectName("pageSubtitleLeft")
        title_group.addWidget(title)
        title_group.addWidget(subtitle)
        heading.addLayout(title_group, 1)
        self.refresh_button = PremiumButton("Refresh seats")
        self.refresh_button.setObjectName("secondaryButton")
        self.refresh_button.setMinimumHeight(42)
        self.refresh_button.clicked.connect(self.refresh_tables)
        heading.addWidget(self.refresh_button)
        layout.addLayout(heading)

        navigation = QHBoxLayout()
        self.dashboard_button = PremiumButton("Dashboard")
        self.dashboard_button.setObjectName("textButton")
        self.dashboard_button.clicked.connect(self.on_dashboard)
        self.orders_button = PremiumButton("Live orders")
        self.orders_button.setObjectName("textButton")
        self.orders_button.clicked.connect(self.on_orders)
        self.seats_label = QLabel("Seat management")
        self.seats_label.setObjectName("employeeNavActive")
        self.admin_button = PremiumButton("Admin console")
        self.admin_button.setObjectName("textButton")
        self.admin_button.clicked.connect(self.on_admin)
        navigation.addWidget(self.dashboard_button)
        navigation.addWidget(self.orders_button)
        navigation.addWidget(self.seats_label)
        navigation.addWidget(self.admin_button)
        navigation.addStretch()
        layout.addLayout(navigation)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.allocated_count = self._metric_card(metrics, "ALLOCATED")
        self.available_count = self._metric_card(metrics, "AVAILABLE")
        self.total_count = self._metric_card(metrics, "TOTAL SEATS")
        layout.addLayout(metrics)

        self.status_label = QLabel("Seat information has not been loaded.")
        self.status_label.setObjectName("mutedNote")
        layout.addWidget(self.status_label)

        columns = QHBoxLayout()
        columns.setSpacing(16)
        self.allocated_rows = self._seat_column(
            "Allocated seats",
            "Occupied seats can be released manually when guests leave.",
            "allocatedSeats",
        )
        self.available_rows = self._seat_column(
            "Available seats",
            "Seats ready for the next dine-in order.",
            "availableSeats",
        )
        columns.addWidget(self.allocated_rows["card"], 1)
        columns.addWidget(self.available_rows["card"], 1)
        layout.addLayout(columns, 1)

    def _metric_card(self, parent_layout, title):
        card = QFrame()
        card.setObjectName("adminMetricCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 14, 18, 14)
        label = QLabel(title)
        label.setObjectName("adminMetricLabel")
        value = QLabel("—")
        value.setObjectName("adminMetricValue")
        value.setMinimumHeight(38)
        card_layout.addWidget(label)
        card_layout.addWidget(value)
        parent_layout.addWidget(card, 1)
        return value

    def _seat_column(self, title, description, object_name):
        card = QFrame()
        card.setObjectName("employeePanel")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)
        header = QLabel(title)
        header.setObjectName("employeePanelTitle")
        note = QLabel(description)
        note.setObjectName("employeePanelDescription")
        note.setWordWrap(True)
        layout.addWidget(header)
        layout.addWidget(note)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.viewport().setStyleSheet("background: transparent;")
        container = QWidget()
        container.setObjectName(object_name)
        container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        rows = QVBoxLayout(container)
        rows.setContentsMargins(0, 0, 0, 0)
        rows.setSpacing(8)
        rows.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)
        return {"card": card, "container": container, "layout": rows}

    def refresh_tables(self):
        self.status_label.setText("Refreshing seat information...")
        try:
            self.tables = get_cafe_tables()
            self.load_error = None
        except Exception as error:
            self.tables = []
            self.load_error = str(error)
            self._render_tables()
            self.status_label.setText(f"Could not load seats: {error}")
            return
        self._render_tables()

    def _render_tables(self):
        for column in (self.allocated_rows, self.available_rows):
            rows = column["layout"]
            while rows.count():
                item = rows.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        if self.load_error:
            self.allocated_count.setText("—")
            self.available_count.setText("—")
            self.total_count.setText("—")
            self._add_empty_state(
                self.allocated_rows["layout"],
                "Seat information is unavailable.",
            )
            self._add_empty_state(
                self.available_rows["layout"],
                "Refresh to try loading seats again.",
            )
            return

        allocated = [
            table for table in self.tables
            if str(table["table_status"]).casefold() == "occupied"
        ]
        available = [
            table for table in self.tables
            if str(table["table_status"]).casefold() == "available"
        ]
        other = [
            table for table in self.tables
            if str(table["table_status"]).casefold() not in ("occupied", "available")
        ]
        self.allocated_count.setText(f"{len(allocated):,}")
        self.available_count.setText(f"{len(available):,}")
        self.total_count.setText(f"{len(self.tables):,}")

        for table in allocated:
            self.allocated_rows["layout"].addWidget(
                self._seat_row(table, allocated=True)
            )
        for table in available:
            self.available_rows["layout"].addWidget(
                self._seat_row(table, allocated=False)
            )
        for table in other:
            self.available_rows["layout"].addWidget(
                self._seat_row(table, allocated=False, other_status=True)
            )
        if not allocated:
            self._add_empty_state(
                self.allocated_rows["layout"],
                "No allocated seats right now.",
            )
        if not available and not other:
            self._add_empty_state(
                self.available_rows["layout"],
                "No available seats right now.",
            )
        self.status_label.setText(
            f"Seat status from the cafe database · Updated "
            f"{datetime.now().strftime('%I:%M:%S %p').lstrip('0')}"
        )

    def _seat_row(self, table, allocated, other_status=False):
        row = QFrame()
        row.setObjectName("seatRow")
        row.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(12, 10, 12, 10)
        row_layout.setSpacing(10)
        details = QVBoxLayout()
        details.setSpacing(3)
        name = QLabel(f"Table {table['table_number']}")
        name.setObjectName("seatRowTitle")
        capacity = QLabel(f"{table['capacity']} seats")
        capacity.setObjectName("employeePanelDescription")
        details.addWidget(name)
        details.addWidget(capacity)
        row_layout.addLayout(details, 1)

        status_text = str(table["table_status"]).replace("_", " ").title()
        status = QLabel(status_text)
        status.setObjectName("seatStatusBadge")
        status.setProperty(
            "state",
            "allocated" if allocated else "available" if not other_status else "other",
        )
        row_layout.addWidget(status)
        if allocated:
            vacate = PremiumButton("Vacate")
            vacate.setObjectName("seatVacateButton")
            vacate.setMinimumHeight(36)
            vacate.setAccessibleName(
                f"Vacate table {table['table_number']}"
            )
            vacate.setProperty("table_id", table["table_id"])
            vacate.clicked.connect(self._confirm_vacate_from_sender)
            row_layout.addWidget(vacate)
        return row

    def _confirm_vacate_from_sender(self):
        button = self.sender()
        if button is None:
            return
        table_id = button.property("table_id")
        table = next(
            (seat for seat in self.tables if seat["table_id"] == table_id),
            None,
        )
        if table is not None:
            self._confirm_vacate(table)

    def _confirm_vacate(self, table):
        answer = QMessageBox.question(
            self,
            "Vacate seat",
            f"Mark Table {table['table_number']} as available?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            vacate_cafe_table(table["table_id"])
        except Exception as error:
            QMessageBox.critical(
                self,
                "Could not vacate seat",
                f"Table {table['table_number']} was not updated: {error}",
            )
            self.refresh_tables()
            return

        self.refresh_tables()
        self.on_tables_updated()

    @staticmethod
    def _add_empty_state(layout, message):
        label = QLabel(message)
        label.setObjectName("emptyState")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
