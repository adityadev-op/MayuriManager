from datetime import date
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from admin import admin_service


class AdminWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_columns = []
        self.table_rows = []
        self.table_names = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 14, 0, 0)
        layout.setSpacing(16)
        title = QLabel("Admin workspace")
        title.setObjectName("pageTitleLeft")
        subtitle = QLabel(
            "Manage the menu, inspect cafe records and review sales performance."
        )
        subtitle.setObjectName("pageSubtitleLeft")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_menu_tab(), "Menu")
        self.tabs.addTab(self._build_database_tab(), "Database")
        self.tabs.addTab(self._build_sales_details_tab(), "Sales details")
        self.tabs.addTab(self._build_revenue_tab(), "Revenue")
        self.tabs.addTab(self._build_employee_tab(), "Employee bills")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs, 1)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(30_000)
        self.refresh_timer.timeout.connect(self._refresh_visible_report)
        self.refresh_timer.start()

    def load(self):
        self._on_tab_changed(self.tabs.currentIndex())

    def refresh_sales_reports(self):
        if self.tabs.currentIndex() == 2:
            self.load_sales_details()
        elif self.tabs.currentIndex() == 3:
            self.load_revenue_report()

    def _refresh_visible_report(self):
        if self.isVisible():
            self.refresh_sales_reports()

    def _build_menu_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(16)

        card = QFrame()
        card.setObjectName("sectionCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)
        card_layout.setSpacing(14)
        heading = QLabel("Add a menu item")
        heading.setObjectName("sectionTitle")
        description = QLabel(
            "Create an item in an existing category. It will be available to employee orders."
        )
        description.setObjectName("mutedNote")
        card_layout.addWidget(heading)
        card_layout.addWidget(description)

        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)
        self.category_combo = QComboBox()
        self.category_combo.setMinimumHeight(42)
        self.item_name_input = self._line_edit("e.g. Masala Tea")
        self.item_description_input = self._line_edit("Short description (optional)")
        self.item_price_input = QDoubleSpinBox()
        self.item_price_input.setRange(0.01, 999999.99)
        self.item_price_input.setDecimals(2)
        self.item_price_input.setPrefix("₹ ")
        self.item_price_input.setMinimumHeight(42)
        self.item_available = QCheckBox("Available for ordering")
        self.item_available.setChecked(True)
        form.addRow("Category", self.category_combo)
        form.addRow("Item name", self.item_name_input)
        form.addRow("Description", self.item_description_input)
        form.addRow("Price", self.item_price_input)
        form.addRow("", self.item_available)
        card_layout.addLayout(form)

        actions = QHBoxLayout()
        self.menu_status = QLabel("Add an item to make it available on the employee menu.")
        self.menu_status.setObjectName("mutedNote")
        self.add_item_button = self._button("Add menu item")
        self.add_item_button.clicked.connect(self.add_menu_item)
        actions.addWidget(self.menu_status, 1)
        actions.addWidget(self.add_item_button)
        card_layout.addLayout(actions)
        layout.addWidget(card)
        layout.addStretch()
        return page

    def _build_database_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 16, 8, 8)
        layout.setSpacing(12)

        controls = QHBoxLayout()
        self.table_combo = QComboBox()
        self.table_combo.setMinimumWidth(220)
        self.table_combo.setMinimumHeight(42)
        self.table_combo.currentIndexChanged.connect(self.load_selected_table)
        self.search_input = self._line_edit("Search visible table records")
        self.search_input.textChanged.connect(self.filter_table_rows)
        self.refresh_tables_button = self._button("Refresh")
        self.refresh_tables_button.clicked.connect(self.load_tables)
        controls.addWidget(QLabel("Database table"))
        controls.addWidget(self.table_combo)
        controls.addWidget(self.search_input, 1)
        controls.addWidget(self.refresh_tables_button)
        layout.addLayout(controls)

        self.database_table = self._table()
        layout.addWidget(self.database_table, 1)
        self.database_status = QLabel(
            "Select a table to browse its records. Search filters the loaded rows."
        )
        self.database_status.setObjectName("mutedNote")
        layout.addWidget(self.database_status)
        return page

    def _build_sales_details_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 16, 8, 8)
        layout.setSpacing(12)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("From"))
        self.sales_detail_start = self._date_edit(date.today().replace(day=1))
        controls.addWidget(self.sales_detail_start)
        controls.addWidget(QLabel("To"))
        self.sales_detail_end = self._date_edit(date.today())
        controls.addWidget(self.sales_detail_end)
        self.load_sales_button = self._button("Load order details")
        self.load_sales_button.clicked.connect(self.load_sales_details)
        controls.addWidget(self.load_sales_button)
        controls.addStretch()
        layout.addLayout(controls)

        self.sales_detail_summary = QLabel(
            "Choose dates to see orders, guests, employees and ordered items."
        )
        self.sales_detail_summary.setObjectName("sectionTitle")
        layout.addWidget(self.sales_detail_summary)
        self.sales_detail_table = self._table()
        self.sales_detail_table.setColumnCount(12)
        self.sales_detail_table.setHorizontalHeaderLabels(
            [
                "ORDER #",
                "ORDERED AT",
                "CUSTOMER",
                "PHONE",
                "EMPLOYEE",
                "TYPE",
                "ITEM",
                "QTY",
                "UNIT PRICE",
                "ITEM TOTAL",
                "PAYMENT METHOD",
                "PAYMENT STATUS",
            ]
        )
        self.sales_detail_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.sales_detail_table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.sales_detail_table, 1)
        self.sales_detail_status = QLabel()
        self.sales_detail_status.setObjectName("mutedNote")
        layout.addWidget(self.sales_detail_status)
        return page

    def _build_revenue_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 16, 8, 8)
        layout.setSpacing(12)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("From"))
        self.revenue_start = self._date_edit(date.today().replace(day=1))
        controls.addWidget(self.revenue_start)
        controls.addWidget(QLabel("To"))
        self.revenue_end = self._date_edit(date.today())
        controls.addWidget(self.revenue_end)
        refresh = self._button("Calculate revenue")
        refresh.clicked.connect(self.load_revenue_report)
        controls.addWidget(refresh)
        controls.addStretch()
        layout.addLayout(controls)

        self.revenue_summary = QLabel("Choose dates to calculate received revenue.")
        self.revenue_summary.setObjectName("sectionTitle")
        layout.addWidget(self.revenue_summary)
        self.revenue_table = self._table()
        self.revenue_table.setColumnCount(3)
        self.revenue_table.setHorizontalHeaderLabels(
            ["PAYMENT DATE", "COMPLETED BILLS", "REVENUE RECEIVED"]
        )
        self.revenue_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.revenue_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.revenue_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        layout.addWidget(self.revenue_table, 1)
        self.revenue_status = QLabel()
        self.revenue_status.setObjectName("mutedNote")
        layout.addWidget(self.revenue_status)
        return page

    def _build_employee_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 16, 8, 8)
        layout.setSpacing(12)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("From"))
        self.employee_start = self._date_edit(date.today().replace(day=1))
        controls.addWidget(self.employee_start)
        controls.addWidget(QLabel("To"))
        self.employee_end = self._date_edit(date.today())
        controls.addWidget(self.employee_end)
        refresh = self._button("Show employee bills")
        refresh.clicked.connect(self.load_employee_report)
        controls.addWidget(refresh)
        controls.addStretch()
        layout.addLayout(controls)

        self.employee_table = self._table()
        self.employee_table.setColumnCount(4)
        self.employee_table.setHorizontalHeaderLabels(
            ["EMPLOYEE ID", "EMPLOYEE", "BILLS GENERATED", "TOTAL BILLED"]
        )
        self.employee_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.employee_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.employee_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.employee_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        layout.addWidget(self.employee_table, 1)
        self.employee_status = QLabel()
        self.employee_status.setObjectName("mutedNote")
        layout.addWidget(self.employee_status)
        return page

    def _line_edit(self, placeholder):
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setMinimumHeight(42)
        return field

    def _button(self, text):
        button = QPushButton(text)
        button.setObjectName("primaryButton")
        button.setMinimumHeight(42)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    def _date_edit(self, initial_date):
        widget = QDateEdit()
        widget.setCalendarPopup(True)
        widget.setDisplayFormat("dd MMM yyyy")
        widget.setDate(initial_date)
        widget.setMinimumHeight(42)
        return widget

    def _table(self):
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSortingEnabled(True)
        table.verticalHeader().setVisible(False)
        return table

    def _on_tab_changed(self, index):
        if index == 0:
            self.load_categories()
        elif index == 1:
            self.load_tables()
        elif index == 2:
            self.load_sales_details()
        elif index == 3:
            self.load_revenue_report()
        elif index == 4:
            self.load_employee_report()

    def load_categories(self):
        try:
            categories = admin_service.get_menu_categories()
        except Exception as error:
            self._show_error("Could not load menu categories", error)
            return
        self.category_combo.clear()
        for category in categories:
            self.category_combo.addItem(
                category["category_name"], category["category_id"]
            )
        if not categories:
            self.menu_status.setText(
                "No categories exist yet. Add a category before adding menu items."
            )

    def add_menu_item(self):
        category_id = self.category_combo.currentData()
        try:
            item_id = admin_service.create_menu_item(
                category_id,
                self.item_name_input.text(),
                self.item_description_input.text(),
                self.item_price_input.value(),
                self.item_available.isChecked(),
            )
        except Exception as error:
            self._show_error("Could not add menu item", error)
            return
        self.menu_status.setText(f"Menu item added successfully (ID {item_id}).")
        self.item_name_input.clear()
        self.item_description_input.clear()
        self.item_price_input.setValue(0.01)

    def load_tables(self):
        try:
            tables = admin_service.get_database_tables()
        except Exception as error:
            self._show_error("Could not load database tables", error)
            return
        previous = self.table_combo.currentText()
        self.table_names = tables
        self.table_combo.blockSignals(True)
        self.table_combo.clear()
        self.table_combo.addItems(tables)
        if previous in tables:
            self.table_combo.setCurrentText(previous)
        self.table_combo.blockSignals(False)
        if tables:
            self.load_selected_table()
        else:
            self.database_table.clear()
            self.database_table.setRowCount(0)
            self.database_status.setText("No database tables were found.")

    def load_selected_table(self):
        table_name = self.table_combo.currentText()
        if not table_name:
            return
        try:
            columns, rows = admin_service.get_table_rows(table_name)
        except Exception as error:
            self._show_error(f"Could not load {table_name}", error)
            return
        self.table_columns = columns
        self.table_rows = rows
        self.search_input.clear()
        self._display_database_rows(rows)
        self.database_status.setText(f"{len(rows):,} record(s) in {table_name}.")

    def _display_database_rows(self, rows):
        table = self.database_table
        table.setSortingEnabled(False)
        table.clear()
        table.setColumnCount(len(self.table_columns))
        table.setHorizontalHeaderLabels(self.table_columns)
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, column in enumerate(self.table_columns):
                value = row.get(column)
                text = "" if value is None else str(value)
                table.setItem(row_index, column_index, QTableWidgetItem(text))
        table.setSortingEnabled(True)
        table.resizeColumnsToContents()

    def filter_table_rows(self, text):
        needle = text.casefold().strip()
        matching_rows = [
            row
            for row in self.table_rows
            if not needle
            or any(
                needle in ("" if row.get(column) is None else str(row[column])).casefold()
                for column in self.table_columns
            )
        ]
        self._display_database_rows(matching_rows)
        self.database_status.setText(
            f"Showing {len(matching_rows):,} of {len(self.table_rows):,} loaded record(s)."
        )

    def load_sales_details(self):
        start_date = self.sales_detail_start.date().toPython()
        end_date = self.sales_detail_end.date().toPython()
        try:
            rows = admin_service.get_sales_details(start_date, end_date)
        except Exception as error:
            self.sales_detail_table.setRowCount(0)
            self.sales_detail_summary.setText("Sales details unavailable.")
            self.sales_detail_status.setText(str(error))
            self._show_error("Could not load sales details", error)
            return

        self.sales_detail_table.setSortingEnabled(False)
        self.sales_detail_table.setRowCount(len(rows))
        order_ids = set()
        order_total = 0
        for row_index, row in enumerate(rows):
            order_ids.add(row["order_id"])
            item_total = float(row["item_total"] or 0)
            order_total += item_total
            values = (
                str(row["order_id"]),
                str(row["order_date"] or ""),
                str(row["customer_name"] or "Guest"),
                str(row["customer_phone"] or "—"),
                str(row["employee_name"] or "—"),
                str(row["order_type"] or "—").replace("_", " ").title(),
                str(row["item_name"] or "—"),
                str(row["quantity"] or 0),
                f"₹{float(row['unit_price'] or 0):,.2f}",
                f"₹{item_total:,.2f}",
                str(row["payment_methods"] or "—"),
                str(row["payment_statuses"] or "Not recorded"),
            )
            for column, value in enumerate(values):
                self.sales_detail_table.setItem(
                    row_index, column, QTableWidgetItem(value)
                )
        self.sales_detail_table.setSortingEnabled(True)
        self.sales_detail_summary.setText(
            f"{len(order_ids):,} bills  ·  {len(rows):,} item lines  ·  "
            f"₹{order_total:,.2f} ordered value"
        )
        self.sales_detail_status.setText(
            f"Updated {datetime.now():%H:%M:%S}  ·  "
            f"Orders from {start_date:%d %b %Y} to {end_date:%d %b %Y}."
            if rows
            else f"Updated {datetime.now():%H:%M:%S}  ·  "
            "No ordered items were recorded in this date range."
        )

    def load_revenue_report(self):
        start_date = self.revenue_start.date().toPython()
        end_date = self.revenue_end.date().toPython()
        try:
            rows = admin_service.get_revenue_by_day(start_date, end_date)
        except Exception as error:
            self.revenue_table.setRowCount(0)
            self.revenue_summary.setText("Revenue unavailable.")
            self.revenue_status.setText(str(error))
            self._show_error("Could not calculate revenue", error)
            return

        self.revenue_table.setRowCount(len(rows))
        total_revenue = 0
        total_bills = 0
        for row_index, row in enumerate(rows):
            revenue = float(row["revenue"] or 0)
            bills = int(row["bill_count"] or 0)
            total_revenue += revenue
            total_bills += bills
            values = (
                str(row["revenue_date"]),
                str(bills),
                f"₹{revenue:,.2f}",
            )
            for column, value in enumerate(values):
                self.revenue_table.setItem(
                    row_index, column, QTableWidgetItem(value)
                )
        self.revenue_summary.setText(
            f"₹{total_revenue:,.2f} revenue received  ·  "
            f"{total_bills:,} completed bills"
        )
        self.revenue_status.setText(
            f"Updated {datetime.now():%H:%M:%S}  ·  "
            f"Completed payments from {start_date:%d %b %Y} to "
            f"{end_date:%d %b %Y}."
            if rows
            else f"Updated {datetime.now():%H:%M:%S}  ·  "
            "No completed payments were recorded in this date range."
        )

    def load_employee_report(self):
        start_date = self.employee_start.date().toPython()
        end_date = self.employee_end.date().toPython()
        try:
            rows = admin_service.get_employee_bill_counts(start_date, end_date)
        except Exception as error:
            self._show_error("Could not load employee report", error)
            return

        self.employee_table.setRowCount(len(rows))
        total_bills = 0
        for row_index, row in enumerate(rows):
            bill_count = int(row["bill_count"] or 0)
            total_bills += bill_count
            values = (
                str(row["employee_id"]),
                str(row["employee_name"]),
                str(bill_count),
                f"₹{float(row['total_billed'] or 0):,.2f}",
            )
            for column, value in enumerate(values):
                self.employee_table.setItem(row_index, column, QTableWidgetItem(value))
        self.employee_status.setText(
            f"{total_bills:,} bills generated from {start_date:%d %b %Y} "
            f"to {end_date:%d %b %Y}."
        )

    def _show_error(self, title, error):
        QMessageBox.critical(self, title, str(error))
