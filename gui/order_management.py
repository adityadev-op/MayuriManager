from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from gui.widgets import PremiumButton
from Receptionist.orders import get_active_orders


class OrderManagementWidget(QWidget):
    def __init__(self, on_dashboard, on_tables, parent=None):
        super().__init__(parent)
        self.on_dashboard = on_dashboard
        self.on_tables = on_tables
        self.orders = []
        self.load_error = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(18)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.setSpacing(5)
        title = QLabel("Live orders")
        title.setObjectName("pageTitleLeft")
        subtitle = QLabel("Current orders from the cafe database.")
        subtitle.setObjectName("pageSubtitleLeft")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading, 1)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("orderSearch")
        self.search_input.setPlaceholderText("Search order ID or guest...")
        self.search_input.setAccessibleName("Search active orders")
        self.search_input.setMinimumWidth(250)
        self.search_input.textChanged.connect(self._render_orders)
        header.addWidget(self.search_input)
        self.refresh_button = PremiumButton("Refresh")
        self.refresh_button.setObjectName("secondaryButton")
        self.refresh_button.setMinimumHeight(42)
        self.refresh_button.clicked.connect(self.refresh_orders)
        header.addWidget(self.refresh_button)
        layout.addLayout(header)

        navigation = QHBoxLayout()
        self.dashboard_button = PremiumButton("Dashboard")
        self.dashboard_button.setObjectName("textButton")
        self.dashboard_button.clicked.connect(self.on_dashboard)
        self.orders_label = QLabel("Live orders")
        self.orders_label.setObjectName("employeeNavActive")
        self.tables_button = PremiumButton("Seat management")
        self.tables_button.setObjectName("textButton")
        self.tables_button.clicked.connect(self.on_tables)
        navigation.addWidget(self.dashboard_button)
        navigation.addWidget(self.orders_label)
        navigation.addWidget(self.tables_button)
        navigation.addStretch()
        layout.addLayout(navigation)

        self.status_label = QLabel("Orders have not been loaded.")
        self.status_label.setObjectName("mutedNote")
        layout.addWidget(self.status_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.viewport().setAutoFillBackground(False)
        self.scroll_area.viewport().setStyleSheet("background: transparent;")
        self.cards_container = QWidget()
        self.cards_container.setObjectName("orderCardsContainer")
        self.cards_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setHorizontalSpacing(16)
        self.cards_layout.setVerticalSpacing(16)
        self.cards_layout.setColumnStretch(0, 1)
        self.cards_layout.setColumnStretch(1, 1)
        self.scroll_area.setWidget(self.cards_container)
        layout.addWidget(self.scroll_area, 1)

    def refresh_orders(self):
        self.status_label.setText("Refreshing active orders...")
        try:
            self.orders = get_active_orders()
            self.load_error = None
        except Exception as error:
            self.orders = []
            self.load_error = str(error)
            self._render_orders()
            self.status_label.setText(f"Could not load active orders: {error}")
            return

        self._render_orders()

    def _render_orders(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if self.load_error:
            self.status_label.setText(f"Could not load active orders: {self.load_error}")
            self._add_empty_state("Refresh to try loading orders again.")
            return

        search = self.search_input.text().strip().casefold()
        visible_orders = [
            order
            for order in self.orders
            if not search
            or search in str(order["order_id"]).casefold()
            or search in str(order.get("customer_name") or "").casefold()
        ]
        if not self.orders:
            self.status_label.setText("No active orders right now.")
            self._add_empty_state("New orders will appear here after they are saved.")
            return
        if not visible_orders:
            self.status_label.setText(
                f"No active orders match “{self.search_input.text().strip()}”."
            )
            self._add_empty_state("Try another order ID or guest name.")
            return

        self.status_label.setText(
            f"{len(visible_orders)} active order"
            f"{'s' if len(visible_orders) != 1 else ''} · "
            f"Updated {datetime.now().strftime('%I:%M:%S %p').lstrip('0')}"
        )
        for index, order in enumerate(visible_orders):
            card = self._order_card(order)
            self.cards_layout.addWidget(
                card,
                index // 2,
                index % 2,
                Qt.AlignmentFlag.AlignTop,
            )

    def _order_card(self, order):
        card = QFrame()
        card.setObjectName("orderCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        order_id = QLabel(f"ORDER #{order['order_id']}")
        order_id.setObjectName("orderCardId")
        status = QLabel(str(order.get("order_status") or "Unknown").replace("_", " ").title())
        status.setObjectName("orderStatusBadge")
        status.setProperty("state", str(order.get("order_status") or "unknown").lower())
        header.addWidget(order_id)
        header.addStretch()
        header.addWidget(status)
        layout.addLayout(header)

        customer = QLabel(order.get("customer_name") or "Guest details unavailable")
        customer.setObjectName("orderCardCustomer")
        layout.addWidget(customer)

        divider = QFrame()
        divider.setObjectName("orderCardDivider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        shown_items = order["items"][:4]
        for item in shown_items:
            row = QHBoxLayout()
            item_name = QLabel(f"{item['quantity']} × {item['item_name']}")
            item_name.setObjectName("orderCardItem")
            item_total = QLabel(
                f"₹{float(item['unit_price']) * int(item['quantity']):,.2f}"
            )
            item_total.setObjectName("orderCardAmount")
            row.addWidget(item_name, 1)
            row.addWidget(item_total)
            layout.addLayout(row)
        remaining = len(order["items"]) - len(shown_items)
        if remaining > 0:
            more_items = QLabel(f"and {remaining} more item type(s)")
            more_items.setObjectName("mutedNote")
            layout.addWidget(more_items)
        if not order["items"]:
            no_items = QLabel("No item details recorded.")
            no_items.setObjectName("mutedNote")
            layout.addWidget(no_items)

        divider = QFrame()
        divider.setObjectName("orderCardDivider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        footer = QHBoxLayout()
        detail = QLabel(self._order_service_summary(order))
        detail.setObjectName("orderCardMeta")
        detail.setWordWrap(True)
        footer.addWidget(detail, 1)
        total = QLabel(f"₹{float(order['total_amount']):,.2f}")
        total.setObjectName("orderCardTotal")
        footer.addWidget(total)
        layout.addLayout(footer)

        details_button = PremiumButton("View details")
        details_button.setObjectName("secondaryButton")
        details_button.setMinimumHeight(38)
        details_button.setProperty("order_id", order["order_id"])
        details_button.clicked.connect(self._show_details_for_sender)
        layout.addWidget(details_button)
        return card

    def _show_details_for_sender(self):
        button = self.sender()
        if button is None:
            return
        order_id = button.property("order_id")
        order = next(
            (item for item in self.orders if item["order_id"] == order_id),
            None,
        )
        if order is not None:
            self._show_details(order)

    def _order_service_summary(self, order):
        service = str(order.get("order_type") or "service").replace("_", " ").title()
        table_number = order.get("table_number")
        if table_number is not None:
            service += f" · Table {table_number}"
        employee = order.get("employee_name")
        if employee:
            service += f" · {employee}"
        order_date = order.get("order_date")
        if hasattr(order_date, "strftime"):
            service += f" · {order_date.strftime('%d %b, %I:%M %p').lstrip('0')}"
        elif order_date:
            service += f" · {order_date}"
        return service

    def _show_details(self, order):
        details = [
            f"Order #{order['order_id']}",
            f"Guest: {order.get('customer_name') or 'Not recorded'}",
            f"Phone: {order.get('customer_phone') or 'Not recorded'}",
            f"Status: {str(order.get('order_status') or 'Unknown').replace('_', ' ').title()}",
            f"Service: {self._order_service_summary(order)}",
            "",
            "Items:",
        ]
        details.extend(
            f"  {item['quantity']} × {item['item_name']} — "
            f"₹{float(item['unit_price']) * int(item['quantity']):,.2f}"
            for item in order["items"]
        )
        details.extend(("", f"Total: ₹{float(order['total_amount']):,.2f}"))
        QMessageBox.information(self, f"Order #{order['order_id']}", "\n".join(details))

    def _add_empty_state(self, message):
        empty = QFrame()
        empty.setObjectName("orderEmptyState")
        empty_layout = QVBoxLayout(empty)
        empty_layout.setContentsMargins(26, 24, 26, 24)
        empty_title = QLabel("No orders to show")
        empty_title.setObjectName("employeePanelTitle")
        empty_message = QLabel(message)
        empty_message.setObjectName("mutedNote")
        empty_message.setWordWrap(True)
        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_message)
        self.cards_layout.addWidget(empty, 0, 0, 1, 2, Qt.AlignmentFlag.AlignTop)
