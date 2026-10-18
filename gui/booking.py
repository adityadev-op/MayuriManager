from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from Receptionist.customers import get_customer_by_phone
from Receptionist.orders import (
    calculate_bill,
    get_active_employees,
    get_available_cafe_tables,
    get_available_menu_items,
    save_order,
)
from gui.widgets import PremiumButton


class BookingWidget(QWidget):
    order_completed = Signal(int)
    flow_cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.customer = None
        self.customer_lookup_complete = False
        self.menu_items = []
        self.cart = []
        self.tables = []
        self.employees = []
        self.order_type = None
        self.table_id = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(14)

        heading = QVBoxLayout()
        heading.setSpacing(5)
        title = QLabel("New booking")
        title.setObjectName("pageTitleLeft")
        subtitle = QLabel("A guided order flow, from guest details to payment.")
        subtitle.setObjectName("pageSubtitleLeft")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        layout.addLayout(heading)

        self.step_labels = []
        step_row = QHBoxLayout()
        step_row.setSpacing(8)
        for index, label in enumerate(("GUEST", "ORDER", "SERVICE", "TEAM", "PAYMENT")):
            step_label = QLabel(f"{index + 1:02d}  {label}")
            step_label.setObjectName("bookingStep")
            step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.step_labels.append(step_label)
            step_row.addWidget(step_label, 1)
        layout.addLayout(step_row)

        self.step_progress = QProgressBar()
        self.step_progress.setObjectName("bookingProgress")
        self.step_progress.setRange(0, 5)
        self.step_progress.setTextVisible(False)
        self.step_progress.setFixedHeight(5)
        self.step_progress.setAccessibleName("Booking progress")
        layout.addWidget(self.step_progress)

        self.summary_card = QFrame()
        self.summary_card.setObjectName("bookingSummary")
        summary_layout = QHBoxLayout(self.summary_card)
        summary_layout.setContentsMargins(18, 10, 18, 10)
        summary_layout.setSpacing(18)
        self.summary_guest = self._summary_value(summary_layout, "GUEST", "Not selected")
        self.summary_items = self._summary_value(summary_layout, "ORDER", "0 items")
        self.summary_service = self._summary_value(summary_layout, "SERVICE", "Not selected")
        self.summary_total = self._summary_value(summary_layout, "TOTAL", "₹0.00")
        layout.addWidget(self.summary_card)

        self.progress = QLabel()
        self.progress.setObjectName("eyebrow")
        layout.addWidget(self.progress)

        self.stage_stack = QStackedWidget()
        self._build_customer_stage()
        self._build_menu_stage()
        self._build_service_stage()
        self._build_employee_stage()
        self._build_payment_stage()
        layout.addWidget(self.stage_stack, 1)
        self._show_stage(0)

    def start(self):
        self._reset()
        self._show_stage(0)

    def _build_customer_stage(self):
        page, content = self._stage_page("01  GUEST DETAILS")

        phone_row = QHBoxLayout()
        self.phone_input = self._line_edit("Enter guest phone number")
        self.phone_input.textEdited.connect(self._invalidate_customer)
        self.lookup_button = self._button("Find guest", "secondaryButton")
        self.lookup_button.clicked.connect(self._lookup_customer)
        phone_row.addWidget(self.phone_input, 1)
        phone_row.addWidget(self.lookup_button)
        content.addLayout(phone_row)

        self.customer_status = QLabel("Look up a returning guest or register a new one.")
        self.customer_status.setObjectName("mutedNote")
        self.customer_status.setWordWrap(True)
        content.addWidget(self.customer_status)

        self.new_customer_fields = QWidget()
        new_customer_layout = QVBoxLayout(self.new_customer_fields)
        new_customer_layout.setContentsMargins(0, 8, 0, 0)
        new_customer_layout.setSpacing(10)
        self.name_input = self._line_edit("Guest name")
        self.name_input.textChanged.connect(self._refresh_order_summary)
        self.email_input = self._line_edit("Email address (optional)")
        new_customer_layout.addWidget(self._field("GUEST NAME", self.name_input))
        new_customer_layout.addWidget(self._field("EMAIL", self.email_input))
        content.addWidget(self.new_customer_fields)
        self.new_customer_fields.hide()

        content.addStretch()
        content.addLayout(
            self._footer(
                "Cancel",
                "Continue to menu",
                self.cancel,
                self._continue_from_customer,
            )
        )
        self.stage_stack.addWidget(page)

    def _build_menu_stage(self):
        page, content = self._stage_page("02  BUILD THE ORDER")
        add_row = QHBoxLayout()
        self.menu_combo = QComboBox()
        self.menu_combo.setMinimumHeight(42)
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 99)
        self.quantity_input.setValue(1)
        self.quantity_input.setMinimumHeight(42)
        self.add_item_button = self._button("Add item", "primaryButton")
        self.add_item_button.clicked.connect(self._add_item)
        add_row.addWidget(self.menu_combo, 1)
        add_row.addWidget(self.quantity_input)
        add_row.addWidget(self.add_item_button)
        content.addLayout(add_row)

        self.cart_table = QTableWidget(0, 4)
        self.cart_table.setHorizontalHeaderLabels(
            ["ITEM", "QTY", "UNIT PRICE", "AMOUNT"]
        )
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        self.cart_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.cart_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cart_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.cart_table.setMinimumHeight(220)
        content.addWidget(self.cart_table, 1)

        cart_actions = QHBoxLayout()
        self.cart_note = QLabel("Your cart is empty.")
        self.cart_note.setObjectName("mutedNote")
        self.remove_item_button = self._button("Remove selected", "secondaryButton")
        self.remove_item_button.clicked.connect(self._remove_selected_item)
        cart_actions.addWidget(self.cart_note)
        cart_actions.addStretch()
        cart_actions.addWidget(self.remove_item_button)
        content.addLayout(cart_actions)

        self.cart_total = QLabel("Cart total  ·  ₹0.00")
        self.cart_total.setObjectName("sectionTitle")
        content.addWidget(self.cart_total)
        content.addStretch()
        content.addLayout(
            self._footer(
                "Back",
                "Choose service type",
                lambda: self._show_stage(0),
                self._continue_from_menu,
            )
        )
        self.stage_stack.addWidget(page)

    def _build_service_stage(self):
        page, content = self._stage_page("03  SERVICE TYPE")
        self.order_type_combo = QComboBox()
        self.order_type_combo.setMinimumHeight(42)
        self.order_type_combo.addItem("Select dine-in or takeaway", None)
        self.order_type_combo.addItem("Dine-in", "dine_in")
        self.order_type_combo.addItem("Takeaway", "takeaway")
        self.order_type_combo.currentIndexChanged.connect(self._on_order_type_changed)
        content.addWidget(self._field("HOW WILL THE GUEST ORDER?", self.order_type_combo))

        self.table_combo = QComboBox()
        self.table_combo.setMinimumHeight(42)
        self.table_combo.currentIndexChanged.connect(self._refresh_order_summary)
        self.table_field = self._field("AVAILABLE TABLE", self.table_combo)
        content.addWidget(self.table_field)
        content.addStretch()
        content.addLayout(
            self._footer(
                "Back",
                "Choose employee",
                lambda: self._show_stage(1),
                self._continue_from_service,
            )
        )
        self.stage_stack.addWidget(page)
        self._on_order_type_changed()

    def _build_employee_stage(self):
        page, content = self._stage_page("04  SERVICE TEAM")
        self.employee_combo = QComboBox()
        self.employee_combo.setMinimumHeight(42)
        self.employee_combo.addItem("Select an employee", None)
        content.addWidget(self._field("ASSIGNED EMPLOYEE", self.employee_combo))
        note = QLabel("Choose the active team member handling this order.")
        note.setObjectName("mutedNote")
        content.addWidget(note)
        content.addStretch()
        content.addLayout(
            self._footer(
                "Back",
                "Review bill",
                lambda: self._show_stage(2),
                self._continue_from_employee,
            )
        )
        self.stage_stack.addWidget(page)

    def _build_payment_stage(self):
        page, content = self._stage_page("05  REVIEW & PAYMENT")
        self.bill_table = QTableWidget(0, 4)
        self.bill_table.setHorizontalHeaderLabels(
            ["ITEM", "QTY", "UNIT PRICE", "AMOUNT"]
        )
        self.bill_table.horizontalHeader().setStretchLastSection(True)
        self.bill_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.bill_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.bill_table.setMinimumHeight(180)
        content.addWidget(self.bill_table, 1)

        self.order_summary = QLabel()
        self.order_summary.setObjectName("mutedNote")
        content.addWidget(self.order_summary)
        self.bill_total = QLabel()
        self.bill_total.setObjectName("totalValue")
        content.addWidget(self.bill_total)

        payment_row = QHBoxLayout()
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.setMinimumHeight(42)
        self.payment_method_combo.addItem("Select a payment method", None)
        for label, value in (
            ("Cash", "cash"),
            ("UPI", "upi"),
            ("Card", "card"),
        ):
            self.payment_method_combo.addItem(label, value)
        payment_row.addWidget(self._field("PAYMENT METHOD", self.payment_method_combo), 1)
        content.addLayout(payment_row)

        self.payment_complete = QCheckBox("Payment has been completed")
        content.addWidget(self.payment_complete)
        content.addStretch()
        content.addLayout(
            self._footer(
                "Back",
                "Save paid order",
                lambda: self._show_stage(3),
                self._save_booking,
            )
        )
        self.stage_stack.addWidget(page)

    def _stage_page(self, label):
        page = QWidget()
        content = QVBoxLayout(page)
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(14)
        card = QFrame()
        card.setObjectName("sectionCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(14)
        heading = QLabel(label)
        heading.setObjectName("eyebrow")
        card_layout.addWidget(heading)
        content.addWidget(card, 1)
        return page, card_layout

    def _summary_value(self, parent_layout, label, value):
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        caption = QLabel(label)
        caption.setObjectName("summaryCaption")
        value_label = QLabel(value)
        value_label.setObjectName("summaryValue")
        value_label.setWordWrap(True)
        layout.addWidget(caption)
        layout.addWidget(value_label)
        parent_layout.addWidget(wrapper, 1)
        return value_label

    def _refresh_order_summary(self):
        guest_name = self.customer.get("customer_name") if self.customer else None
        if not guest_name and hasattr(self, "name_input"):
            guest_name = self.name_input.text().strip()
        guest_name = guest_name or "Not selected"
        item_count = sum(item["quantity"] for item in self.cart)
        _, total = calculate_bill(self.cart)
        self.summary_guest.setText(guest_name)
        self.summary_items.setText(
            f"{item_count} item{'s' if item_count != 1 else ''}"
        )
        order_type = self.order_type_combo.currentData()
        if order_type == "dine_in":
            service = (
                self.table_combo.currentText()
                if self.table_combo.currentData() is not None
                else "Dine-in"
            )
        elif order_type == "takeaway":
            service = "Takeaway"
        else:
            service = "Not selected"
        self.summary_service.setText(service)
        self.summary_total.setText(f"₹{float(total):,.2f}")

    def _footer(self, back_label, next_label, back_callback, next_callback):
        footer = QHBoxLayout()
        back = self._button(back_label, "textButton")
        back.clicked.connect(back_callback)
        next_button = self._button(next_label, "primaryButton")
        next_button.setMinimumHeight(46)
        next_button.clicked.connect(next_callback)
        footer.addWidget(back)
        footer.addStretch()
        footer.addWidget(next_button)
        return footer

    def _field(self, label, widget):
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        title = QLabel(label)
        title.setObjectName("fieldLabel")
        layout.addWidget(title)
        layout.addWidget(widget)
        return wrapper

    def _line_edit(self, placeholder):
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setMinimumHeight(42)
        return field

    def _button(self, text, object_name):
        button = PremiumButton(text)
        button.setObjectName(object_name)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    def _show_stage(self, index):
        self.stage_stack.setCurrentIndex(index)
        labels = ("GUEST", "ORDER", "SERVICE", "TEAM", "PAYMENT")
        self.progress.setText(
            f"STEP {index + 1} OF {len(labels)}   ·   {labels[index]}"
        )
        self.step_progress.setValue(index + 1)
        for step_index, step_label in enumerate(self.step_labels):
            step_label.setProperty("active", step_index == index)
            step_label.setProperty("complete", step_index < index)
            step_label.setAccessibleName(
                f"Step {step_index + 1}: {labels[step_index]}"
            )
            step_label.setAccessibleDescription(
                "Current step"
                if step_index == index
                else "Complete"
                if step_index < index
                else "Not started"
            )
            step_label.style().unpolish(step_label)
            step_label.style().polish(step_label)
        self._refresh_order_summary()

    def _lookup_customer(self):
        phone = self.phone_input.text().strip()
        if not phone:
            self._warning("Enter a phone number before looking up a guest.")
            return

        try:
            customer = get_customer_by_phone(phone)
        except Exception as error:
            self._error("Could not look up guest", error)
            return

        self.customer = customer
        self.customer_lookup_complete = True
        if customer:
            self.new_customer_fields.hide()
            self.customer_status.setText(
                f"Welcome back, {customer['customer_name']}. Guest details found."
            )
        else:
            self.new_customer_fields.show()
            self.customer_status.setText(
                "New guest. Enter a name to continue; email is optional."
            )
        self._refresh_order_summary()

    def _continue_from_customer(self):
        phone = self.phone_input.text().strip()
        if not phone:
            self._warning("Enter a phone number before continuing.")
            return
        if not self.customer_lookup_complete:
            self._warning("Look up the phone number before continuing.")
            return
        if self.customer is None:
            name = self.name_input.text().strip()
            if not name:
                self._warning("Enter the guest's name before continuing.")
                return
            self.customer = {
                "customer_name": name,
                "phone": phone,
                "email": self.email_input.text().strip() or None,
            }
            self._refresh_order_summary()
        self._load_menu()

    def _load_menu(self):
        try:
            self.menu_items = get_available_menu_items()
        except Exception as error:
            self._error("Could not load menu", error)
            return
        if not self.menu_items:
            self._warning("There are no available menu items to order.")
            return

        self.menu_combo.clear()
        for item in self.menu_items:
            self.menu_combo.addItem(
                f"{item['item_name']}  ·  ₹{float(item['price']):.2f}",
                item["item_id"],
            )
        self._show_stage(1)

    def _add_item(self):
        item_id = self.menu_combo.currentData()
        item = next(
            (menu_item for menu_item in self.menu_items if menu_item["item_id"] == item_id),
            None,
        )
        if item is None:
            self._warning("Select an available menu item.")
            return

        quantity = self.quantity_input.value()
        existing = next(
            (cart_item for cart_item in self.cart if cart_item["item_id"] == item_id),
            None,
        )
        if existing:
            existing["quantity"] += quantity
        else:
            self.cart.append(
                {
                    "item_id": item["item_id"],
                    "item_name": item["item_name"],
                    "price": item["price"],
                    "quantity": quantity,
                }
            )
        self._refresh_cart()

    def _remove_selected_item(self):
        row = self.cart_table.currentRow()
        if row < 0 or row >= len(self.cart):
            self._warning("Select a cart item to remove.")
            return
        self.cart.pop(row)
        self._refresh_cart()

    def _refresh_cart(self):
        self.cart_table.setRowCount(len(self.cart))
        for row, item in enumerate(self.cart):
            amount = item["price"] * item["quantity"]
            values = (
                item["item_name"],
                str(item["quantity"]),
                f"₹{float(item['price']):.2f}",
                f"₹{float(amount):.2f}",
            )
            for column, value in enumerate(values):
                self.cart_table.setItem(row, column, QTableWidgetItem(value))
        _, total = calculate_bill(self.cart)
        self.cart_total.setText(f"Cart total  ·  ₹{float(total):.2f}")
        self.cart_note.setText(
            f"{len(self.cart)} item type(s) in your cart."
            if self.cart
            else "Your cart is empty."
        )

    def _continue_from_menu(self):
        if not self.cart:
            self._warning("Add at least one item before continuing.")
            return
        self._show_stage(2)

    def _on_order_type_changed(self):
        is_dine_in = self.order_type_combo.currentData() == "dine_in"
        self.table_field.setVisible(is_dine_in)
        if is_dine_in:
            self._load_available_tables()
        self._refresh_order_summary()

    def _load_available_tables(self):
        try:
            self.tables = get_available_cafe_tables()
        except Exception as error:
            self.tables = []
            self.table_combo.clear()
            self._error("Could not load available tables", error)
            return False

        self.table_combo.clear()
        if not self.tables:
            self.table_combo.addItem("No tables currently available", None)
            self._warning("No cafe tables are available. Choose takeaway instead.")
            return False

        self.table_combo.addItem("Select an available table", None)
        for table in self.tables:
            self.table_combo.addItem(
                f"Table {table['table_number']}  ·  {table['capacity']} seats",
                table["table_id"],
            )
        return True

    def _continue_from_service(self):
        self.order_type = self.order_type_combo.currentData()
        if self.order_type is None:
            self._warning("Choose dine-in or takeaway before continuing.")
            return
        self.table_id = None
        self._refresh_order_summary()
        if self.order_type == "dine_in":
            if not self.tables:
                if not self._load_available_tables():
                    return
            self.table_id = self.table_combo.currentData()
            if self.table_id is None:
                self._warning("Choose an available table before continuing.")
                return

        try:
            self.employees = get_active_employees()
        except Exception as error:
            self._error("Could not load employees", error)
            return
        if not self.employees:
            self._warning("No active employees found. Add an active employee first.")
            return
        self.employee_combo.clear()
        self.employee_combo.addItem("Select an employee", None)
        for employee in self.employees:
            self.employee_combo.addItem(
                f"{employee['employee_name']}  ·  #{employee['employee_id']}",
                employee["employee_id"],
            )
        self._show_stage(3)

    def _continue_from_employee(self):
        employee_id = self.employee_combo.currentData()
        if employee_id is None:
            self._warning("Select an active employee for this order.")
            return
        bill_items, total = calculate_bill(self.cart)
        self.bill_table.setRowCount(len(bill_items))
        for row, item in enumerate(bill_items):
            values = (
                item["item_name"],
                str(item["quantity"]),
                f"₹{float(item['price']):.2f}",
                f"₹{float(item['line_total']):.2f}",
            )
            for column, value in enumerate(values):
                self.bill_table.setItem(row, column, QTableWidgetItem(value))
        employee = self.employee_combo.currentText()
        service = "Dine-in" if self.order_type == "dine_in" else "Takeaway"
        if self.order_type == "dine_in":
            table_name = self.table_combo.currentText()
            self.order_summary.setText(f"{service}  ·  {table_name}  ·  {employee}")
        else:
            self.order_summary.setText(f"{service}  ·  {employee}")
        self._refresh_order_summary()
        self.bill_total.setText(f"Total  ·  ₹{float(total):.2f}")
        self.payment_complete.setChecked(False)
        self._show_stage(4)

    def _save_booking(self):
        if self.payment_method_combo.currentData() is None:
            self._warning("Choose a payment method before saving the order.")
            return
        if not self.payment_complete.isChecked():
            answer = QMessageBox.question(
                self,
                "Confirm payment",
                "Has the payment been completed? Choose No to cancel this order.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.No:
                self._reset()
                self.flow_cancelled.emit()
                return
            self.payment_complete.setChecked(True)

        try:
            order_id = save_order(
                self.customer,
                self.employee_combo.currentData(),
                self.order_type,
                self.cart,
                self.payment_method_combo.currentData(),
                self.table_id,
            )
        except Exception as error:
            self._error("Could not save order", error)
            return

        self._reset()
        self.order_completed.emit(order_id)

    def cancel(self):
        if self.cart:
            answer = QMessageBox.question(
                self,
                "Cancel booking",
                "Discard this booking? No order has been saved yet.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self._reset()
        self.flow_cancelled.emit()

    def _invalidate_customer(self):
        self.customer = None
        self.customer_lookup_complete = False
        self.new_customer_fields.hide()
        self.customer_status.setText(
            "Look up a returning guest or register a new one."
        )
        self._refresh_order_summary()

    def _reset(self):
        self.customer = None
        self.customer_lookup_complete = False
        self.menu_items = []
        self.cart = []
        self.tables = []
        self.employees = []
        self.order_type = None
        self.table_id = None
        self.phone_input.clear()
        self.name_input.clear()
        self.email_input.clear()
        self.customer_status.setText(
            "Look up a returning guest or register a new one."
        )
        self.new_customer_fields.hide()
        self.menu_combo.clear()
        self.cart_table.setRowCount(0)
        self.cart_note.setText("Your cart is empty.")
        self.cart_total.setText("Cart total  ·  ₹0.00")
        self._refresh_order_summary()
        self.order_type_combo.setCurrentIndex(0)
        self.table_combo.clear()
        self.employee_combo.clear()
        self.bill_table.setRowCount(0)
        self.payment_method_combo.setCurrentIndex(0)
        self.payment_complete.setChecked(False)
        self._show_stage(0)

    def _warning(self, message):
        QMessageBox.warning(self, "Booking", message)

    def _error(self, title, error):
        QMessageBox.critical(self, title, str(error))
