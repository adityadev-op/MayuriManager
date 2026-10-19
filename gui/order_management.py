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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gui.widgets import PremiumButton
from Receptionist.orders import (
    complete_order,
    get_active_orders,
    get_completed_orders,
)


class OrderManagementWidget(QWidget):
    def __init__(self, on_dashboard, on_tables, on_order_completed=None, parent=None):
        super().__init__(parent)
        self.on_dashboard = on_dashboard
        self.on_tables = on_tables
        self.on_order_completed = on_order_completed or self.refresh_orders
        self.orders = []
        self.completed_orders = []
        self.load_error = None
        self.can_complete_orders = False
        self._completion_button_style = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(18)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.setSpacing(5)
        self.title_label = QLabel("Live orders")
        self.title_label.setObjectName("pageTitleLeft")
        self.subtitle_label = QLabel("Current orders from the cafe database.")
        self.subtitle_label.setObjectName("pageSubtitleLeft")
        heading.addWidget(self.title_label)
        heading.addWidget(self.subtitle_label)
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

        self.navigation = QWidget()
        navigation = QHBoxLayout(self.navigation)
        navigation.setContentsMargins(0, 0, 0, 0)
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
        layout.addWidget(self.navigation)

        self.order_sections = QTabWidget()
        self.queue_page, self.status_label, self.cards_container, self.cards_layout = (
            self._build_order_section("Orders have not been loaded.")
        )
        (
            self.completed_page,
            self.completed_status_label,
            self.completed_cards_container,
            self.completed_cards_layout,
        ) = self._build_order_section("Completed orders have not been loaded.")
        self.order_sections.addTab(self.queue_page, "Order queue")
        self.order_sections.addTab(self.completed_page, "Completed orders")
        layout.addWidget(self.order_sections, 1)
        self.order_sections.currentChanged.connect(self._render_orders)

    def _build_order_section(self, initial_status):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        status_label = QLabel(initial_status)
        status_label.setObjectName("mutedNote")
        layout.addWidget(status_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.viewport().setAutoFillBackground(False)
        scroll_area.viewport().setStyleSheet("background: transparent;")
        cards_container = QWidget()
        cards_container.setObjectName("orderCardsContainer")
        cards_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        cards_layout = QGridLayout(cards_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setHorizontalSpacing(16)
        cards_layout.setVerticalSpacing(16)
        cards_layout.setColumnStretch(0, 1)
        cards_layout.setColumnStretch(1, 1)
        scroll_area.setWidget(cards_container)
        layout.addWidget(scroll_area, 1)
        return page, status_label, cards_container, cards_layout

    def set_order_manager_mode(self, enabled):
        self.can_complete_orders = enabled
        self.navigation.setVisible(not enabled)
        if enabled:
            self.title_label.setText("Order management")
            self.subtitle_label.setText(
                "Review the live queue, complete finished orders and check completed orders."
            )
        else:
            self.title_label.setText("Live orders")
            self.subtitle_label.setText("Current orders from the cafe database.")
        self._render_orders()

    def set_completion_button_theme(
        self,
        *,
        accent,
        accent_hover,
        accent_deep,
        surface_alt,
        border,
        muted,
    ):
        self._completion_button_style = f"""
            QPushButton {{
                background-color: {accent};
                border: 1px solid {accent_deep};
                color: #ffffff;
            }}
            QPushButton:hover {{
                background-color: {accent_hover};
                border-color: {accent_hover};
            }}
            QPushButton:pressed {{ background-color: {accent_deep}; }}
            QPushButton:disabled {{
                background-color: {surface_alt};
                border-color: {border};
                color: {muted};
            }}
            QPushButton:focus {{ border: 2px solid {accent_deep}; }}
        """
        self._render_orders()

    def refresh_orders(self):
        self.status_label.setText("Refreshing the order queue...")
        try:
            self.orders = get_active_orders()
            self.completed_orders = get_completed_orders()
            self.load_error = None
        except Exception as error:
            self.orders = []
            self.completed_orders = []
            self.load_error = str(error)
            self._render_orders()
            self.status_label.setText(f"Could not load active orders: {error}")
            self.completed_status_label.setText(
                f"Could not load completed orders: {error}"
            )
            return

        self._render_orders()

    def _render_orders(self):
        self._render_order_list(
            self.orders,
            self.cards_layout,
            self.status_label,
            completed=False,
        )
        self._render_order_list(
            self.completed_orders,
            self.completed_cards_layout,
            self.completed_status_label,
            completed=True,
        )

    def _render_order_list(self, orders, cards_layout, status_label, completed):
        while cards_layout.count():
            item = cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if self.load_error:
            status_label.setText(f"Could not load orders: {self.load_error}")
            self._add_empty_state(
                cards_layout,
                "Refresh to try loading orders again.",
            )
            return

        search = self.search_input.text().strip().casefold()
        visible_orders = [
            order
            for order in orders
            if not search
            or search in str(order["order_id"]).casefold()
            or search in str(order.get("customer_name") or "").casefold()
        ]
        section_name = "completed order" if completed else "active order"
        if not orders:
            status_label.setText(
                "No completed orders yet."
                if completed
                else "No active orders right now."
            )
            self._add_empty_state(
                cards_layout,
                (
                    "Orders will appear here after they are marked completed."
                    if completed
                    else "New orders will appear here after they are saved."
                ),
            )
            return
        if not visible_orders:
            status_label.setText(
                f"No {section_name}s match “{self.search_input.text().strip()}”."
            )
            self._add_empty_state(cards_layout, "Try another order ID or guest name.")
            return

        status_label.setText(
            f"{len(visible_orders)} {section_name}"
            f"{'s' if len(visible_orders) != 1 else ''} · "
            f"Updated {datetime.now().strftime('%I:%M:%S %p').lstrip('0')}"
        )
        for index, order in enumerate(visible_orders):
            card = self._order_card(order, completed=completed)
            cards_layout.addWidget(
                card,
                index // 2,
                index % 2,
                Qt.AlignmentFlag.AlignTop,
            )

    def _order_card(self, order, completed=False):
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
        if self.can_complete_orders and not completed:
            complete_button = PremiumButton("Mark as completed")
            complete_button.setObjectName("orderCompleteButton")
            complete_button.setStyleSheet(self._completion_button_style)
            complete_button.setMinimumHeight(42)
            complete_button.setProperty("order_id", order["order_id"])
            complete_button.clicked.connect(self._complete_order_for_sender)
            layout.addWidget(complete_button)
        return card

    def _complete_order_for_sender(self):
        button = self.sender()
        if button is None:
            return
        order_id = button.property("order_id")
        try:
            complete_order(order_id)
        except Exception as error:
            QMessageBox.critical(
                self,
                f"Could not complete order #{order_id}",
                str(error),
            )
            self.refresh_orders()
            return
        self.on_order_completed()

    def _show_details_for_sender(self):
        button = self.sender()
        if button is None:
            return
        order_id = button.property("order_id")
        order = next(
            (
                item
                for item in (*self.orders, *self.completed_orders)
                if item["order_id"] == order_id
            ),
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

    def _add_empty_state(self, cards_layout, message):
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
        cards_layout.addWidget(empty, 0, 0, 1, 2, Qt.AlignmentFlag.AlignTop)
