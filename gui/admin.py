from datetime import date, datetime, timedelta

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
    QLayout,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QScrollArea,
    QStackedWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from admin import admin_service
from gui.widgets import PremiumButton, RevenueChart
from services import employee_sessions


class AdminWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_columns = []
        self.table_rows = []
        self.table_names = []
        self.dashboard_categories = []
        self.dashboard_employees = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 14, 0, 0)
        layout.setSpacing(16)
        title = QLabel("Admin Console")
        title.setObjectName("pageTitleLeft")
        subtitle = QLabel(
            "Manage the menu, inspect cafe records and review sales performance."
        )
        subtitle.setObjectName("pageSubtitleLeft")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_dashboard_tab(), "Dashboard")
        self.tabs.addTab(self._build_menu_tab(), "Menu")
        self.tabs.addTab(self._build_database_tab(), "Database")
        self.tabs.addTab(self._build_sales_details_tab(), "Sales details")
        self.tabs.addTab(self._build_revenue_tab(), "Revenue")
        self.tabs.addTab(self._build_employee_tab(), "Employee bills")
        self.tabs.addTab(self._build_employee_sessions_tab(), "Employee logins")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs, 1)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(30_000)
        self.refresh_timer.timeout.connect(self._refresh_visible_report)
        self.refresh_timer.start()

    def load(self):
        self._on_tab_changed(self.tabs.currentIndex())

    def refresh_sales_reports(self):
        if self.tabs.currentIndex() == 0:
            self.load_dashboard()
        elif self.tabs.currentIndex() == 3:
            self.load_sales_details()
        elif self.tabs.currentIndex() == 4:
            self.load_revenue_report()
        elif self.tabs.currentIndex() == 5:
            self.load_employee_report()
        elif self.tabs.currentIndex() == 6:
            self.load_employee_sessions()

    def _refresh_visible_report(self):
        if self.isVisible():
            self.refresh_sales_reports()

    def _build_dashboard_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 16, 8, 8)
        layout.setSpacing(16)

        controls_card = QFrame()
        controls_card.setObjectName("adminDashboardControls")
        controls = QHBoxLayout(controls_card)
        controls.setContentsMargins(16, 10, 16, 10)
        controls.setSpacing(10)
        range_label = QLabel("DATE RANGE")
        range_label.setObjectName("adminDashboardEyebrow")
        controls.addWidget(range_label)
        self.dashboard_range = QComboBox()
        self.dashboard_range.addItems(
            ("Last 7 days", "Last 30 days", "This month", "Custom range")
        )
        self.dashboard_range.setMinimumHeight(40)
        self.dashboard_range.currentIndexChanged.connect(
            self._on_dashboard_range_changed
        )
        controls.addWidget(self.dashboard_range)
        self.dashboard_start = self._date_edit(date.today().replace(day=1))
        self.dashboard_end = self._date_edit(date.today())
        self.dashboard_start.hide()
        self.dashboard_end.hide()
        controls.addWidget(self.dashboard_start)
        self.dashboard_range_separator = QLabel("to")
        self.dashboard_range_separator.hide()
        controls.addWidget(self.dashboard_range_separator)
        controls.addWidget(self.dashboard_end)
        self.dashboard_start.dateChanged.connect(self._on_dashboard_custom_date_changed)
        self.dashboard_end.dateChanged.connect(self._on_dashboard_custom_date_changed)
        self.dashboard_refresh = self._button("Refresh dashboard")
        self.dashboard_refresh.clicked.connect(self.load_dashboard)
        controls.addWidget(self.dashboard_refresh)
        controls.addStretch()
        layout.addWidget(controls_card)

        metrics = QHBoxLayout()
        metrics.setSpacing(14)
        self.dashboard_metric_values = {}
        for key, title, note in (
            ("revenue", "Total revenue", "Completed payments"),
            ("orders", "Completed bills", "Paid orders in range"),
            ("average", "Average bill", "Revenue per completed bill"),
        ):
            card = QFrame()
            card.setObjectName("adminMetricCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 18, 20, 18)
            card_layout.setSpacing(7)
            label = QLabel(title.upper())
            label.setObjectName("adminMetricLabel")
            value = QLabel("—")
            value.setObjectName("adminMetricValue")
            value.setMinimumHeight(42)
            description = QLabel(note)
            description.setObjectName("mutedNote")
            card_layout.addWidget(label)
            card_layout.addWidget(value)
            card_layout.addWidget(description)
            self.dashboard_metric_values[key] = value
            metrics.addWidget(card, 1)
        layout.addLayout(metrics)

        reports = QHBoxLayout()
        reports.setSpacing(14)
        category_card = QFrame()
        category_card.setObjectName("adminDashboardPanel")
        category_layout = QVBoxLayout(category_card)
        category_layout.setContentsMargins(18, 16, 18, 16)
        category_layout.setSpacing(10)
        category_header = QHBoxLayout()
        category_title = QLabel("Top-selling categories")
        category_title.setObjectName("adminDashboardPanelTitle")
        self.category_range_label = QLabel()
        self.category_range_label.setObjectName("adminDashboardEyebrow")
        category_header.addWidget(category_title)
        category_header.addStretch()
        category_header.addWidget(self.category_range_label)
        category_layout.addLayout(category_header)
        self.dashboard_category_table = self._table()
        self.dashboard_category_table.setColumnCount(4)
        self.dashboard_category_table.setHorizontalHeaderLabels(
            ["CATEGORY", "ITEMS SOLD", "ORDER VALUE", "SHARE"]
        )
        self.dashboard_category_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        for column in (1, 2, 3):
            self.dashboard_category_table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        self.dashboard_category_view, self.dashboard_category_empty = self._table_view(
            self.dashboard_category_table,
            "No category sales in this date range.",
        )
        category_layout.addWidget(self.dashboard_category_view, 1)
        self.dashboard_category_status = QLabel("Category sales will appear here.")
        self.dashboard_category_status.setObjectName("mutedNote")
        category_layout.addWidget(self.dashboard_category_status)
        reports.addWidget(category_card, 3)

        employee_card = QFrame()
        employee_card.setObjectName("adminDashboardPanel")
        employee_layout = QVBoxLayout(employee_card)
        employee_layout.setContentsMargins(18, 16, 18, 16)
        employee_layout.setSpacing(10)
        employee_header = QHBoxLayout()
        employee_title = QLabel("Employee performance")
        employee_title.setObjectName("adminDashboardPanelTitle")
        self.employee_range_label = QLabel()
        self.employee_range_label.setObjectName("adminDashboardEyebrow")
        employee_header.addWidget(employee_title)
        employee_header.addStretch()
        employee_header.addWidget(self.employee_range_label)
        employee_layout.addLayout(employee_header)
        self.dashboard_employee_scroll = QScrollArea()
        self.dashboard_employee_scroll.setObjectName("adminPerformanceScroll")
        self.dashboard_employee_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.dashboard_employee_scroll.setWidgetResizable(True)
        self.dashboard_employee_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        employee_rows_container = QWidget()
        self.dashboard_employee_rows_container = employee_rows_container
        self.dashboard_employee_rows = QVBoxLayout(employee_rows_container)
        self.dashboard_employee_rows.setContentsMargins(0, 0, 0, 0)
        self.dashboard_employee_rows.setSpacing(12)
        self.dashboard_employee_rows.setSizeConstraint(
            QLayout.SizeConstraint.SetMinimumSize
        )
        self.dashboard_employee_scroll.setWidget(employee_rows_container)
        employee_layout.addWidget(self.dashboard_employee_scroll, 1)
        self.dashboard_employee_empty = QLabel(
            "No employee bills in this date range."
        )
        self.dashboard_employee_empty.setObjectName("emptyState")
        self.dashboard_employee_empty.setWordWrap(True)
        self.dashboard_employee_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        employee_layout.addWidget(self.dashboard_employee_empty, 1)
        self.dashboard_employee_status = QLabel("Employee totals will appear here.")
        self.dashboard_employee_status.setObjectName("mutedNote")
        employee_layout.addWidget(self.dashboard_employee_status)
        reports.addWidget(employee_card, 2)
        layout.addLayout(reports, 1)

        actions = QHBoxLayout()
        self.dashboard_status = QLabel("Dashboard reports have not been loaded.")
        self.dashboard_status.setObjectName("mutedNote")
        actions.addWidget(self.dashboard_status, 1)
        menu_button = self._button("Manage menu")
        menu_button.setObjectName("secondaryButton")
        menu_button.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        actions.addWidget(menu_button)
        sales_button = self._button("Sales details")
        sales_button.setObjectName("secondaryButton")
        sales_button.clicked.connect(lambda: self.tabs.setCurrentIndex(3))
        actions.addWidget(sales_button)
        layout.addLayout(actions)
        return page

    def _on_dashboard_range_changed(self, index):
        custom = index == 3
        self.dashboard_start.setVisible(custom)
        self.dashboard_end.setVisible(custom)
        self.dashboard_range_separator.setVisible(custom)
        if index < 3:
            start_date, end_date = self._dashboard_date_range()
            self.dashboard_start.setDate(start_date)
            self.dashboard_end.setDate(end_date)
            self.load_dashboard()

    def _on_dashboard_custom_date_changed(self):
        if self.dashboard_range.currentIndex() == 3:
            self.load_dashboard()

    def _dashboard_date_range(self):
        end_date = date.today()
        range_index = self.dashboard_range.currentIndex()
        if range_index == 0:
            start_date = end_date - timedelta(days=6)
        elif range_index == 1:
            start_date = end_date - timedelta(days=29)
        elif range_index == 2:
            start_date = end_date.replace(day=1)
        else:
            start_date = self.dashboard_start.date().toPython()
            end_date = self.dashboard_end.date().toPython()
        return start_date, end_date

    def load_dashboard(self):
        start_date, end_date = self._dashboard_date_range()
        period = f"{start_date:%d %b} – {end_date:%d %b %Y}"
        self.dashboard_status.setText("Loading dashboard reports…")
        self.dashboard_status.repaint()
        self.category_range_label.setText(period)
        self.employee_range_label.setText(period)
        try:
            revenue_rows = admin_service.get_revenue_by_day(start_date, end_date)
            categories = admin_service.get_category_sales(start_date, end_date)
            employees = admin_service.get_employee_bill_counts(start_date, end_date)
        except Exception as error:
            for value in self.dashboard_metric_values.values():
                value.setText("—")
            self.dashboard_category_table.setRowCount(0)
            self._show_table_state(
                self.dashboard_category_view,
                self.dashboard_category_table,
                self.dashboard_category_empty,
                f"Dashboard reports unavailable: {error}",
            )
            self.dashboard_category_status.setText(str(error))
            self._clear_dashboard_employees()
            self.dashboard_employee_status.setText(str(error))
            self.dashboard_status.setText("Dashboard reports unavailable.")
            self._show_error("Could not load admin dashboard", error)
            return

        paid_orders = sum(int(row["bill_count"] or 0) for row in revenue_rows)
        revenue = sum(float(row["revenue"] or 0) for row in revenue_rows)
        average = revenue / paid_orders if paid_orders else 0
        self.dashboard_metric_values["revenue"].setText(f"₹{revenue:,.2f}")
        self.dashboard_metric_values["orders"].setText(f"{paid_orders:,}")
        self.dashboard_metric_values["average"].setText(f"₹{average:,.2f}")
        self._render_dashboard_categories(categories)
        self._render_dashboard_employees(employees)
        self.dashboard_status.setText(
            f"Paid-order metrics · {period} · Updated "
            f"{datetime.now().strftime('%I:%M:%S %p').lstrip('0')}"
        )

    def _render_dashboard_categories(self, categories):
        self.dashboard_categories = categories
        self.dashboard_category_table.setRowCount(len(categories))
        total = sum(float(row["category_revenue"] or 0) for row in categories)
        for row_index, row in enumerate(categories):
            amount = float(row["category_revenue"] or 0)
            values = (
                str(row["category_name"]),
                f"{int(row['items_sold'] or 0):,}",
                f"₹{amount:,.2f}",
                f"{amount / total:.1%}" if total else "—",
            )
            for column, value in enumerate(values):
                self.dashboard_category_table.setItem(
                    row_index, column, QTableWidgetItem(value)
                )
        self._show_table_state(
            self.dashboard_category_view,
            self.dashboard_category_table,
            self.dashboard_category_empty,
            "No category sales in this date range.",
        )
        self.dashboard_category_status.setText(
            f"{len(categories):,} category group(s) · share based on ordered value"
        )

    def _render_dashboard_employees(self, employees):
        self.dashboard_employees = employees
        self._clear_dashboard_employees()
        positive_employees = [
            employee for employee in employees if int(employee["bill_count"] or 0) > 0
        ][:5]
        self.dashboard_employee_empty.setVisible(not positive_employees)
        self.dashboard_employee_scroll.setVisible(bool(positive_employees))
        maximum_bills = max(
            (int(employee["bill_count"]) for employee in positive_employees),
            default=1,
        )
        for employee in positive_employees:
            row = QWidget()
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(5)
            heading = QHBoxLayout()
            name = QLabel(employee["employee_name"])
            name.setObjectName("adminPerformanceName")
            totals = QLabel(
                f"₹{float(employee['total_billed'] or 0):,.2f} · "
                f"{int(employee['bill_count']):,} bills"
            )
            totals.setObjectName("adminPerformanceTotals")
            heading.addWidget(name, 1)
            heading.addWidget(totals)
            progress = QProgressBar()
            progress.setObjectName("adminPerformanceBar")
            progress.setRange(0, maximum_bills)
            progress.setValue(int(employee["bill_count"]))
            progress.setTextVisible(False)
            progress.setFixedHeight(7)
            row_layout.addLayout(heading)
            row_layout.addWidget(progress)
            row.setMinimumHeight(row_layout.sizeHint().height())
            self.dashboard_employee_rows.addWidget(row)
        self.dashboard_employee_status.setText(
            f"Showing up to {len(positive_employees)} team members by bill count."
        )

    def _clear_dashboard_employees(self):
        while self.dashboard_employee_rows.count():
            item = self.dashboard_employee_rows.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

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
        self.database_view, self.database_empty = self._table_view(
            self.database_table, "Select a table to browse its records."
        )
        layout.addWidget(self.database_view, 1)
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
        self.sales_detail_view, self.sales_detail_empty = self._table_view(
            self.sales_detail_table,
            "No ordered items were recorded in this date range.",
        )
        layout.addWidget(self.sales_detail_view, 1)
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
        report_body = QHBoxLayout()
        report_body.setSpacing(14)
        self.revenue_view, self.revenue_empty = self._table_view(
            self.revenue_table,
            "No completed payments were recorded in this date range.",
        )
        report_body.addWidget(self.revenue_view, 3)
        chart_card = QFrame()
        chart_card.setObjectName("sectionCard")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(12, 10, 12, 10)
        chart_layout.setSpacing(6)
        chart_title = QLabel("Daily revenue")
        chart_title.setObjectName("eyebrow")
        self.revenue_chart = RevenueChart()
        chart_layout.addWidget(chart_title)
        chart_layout.addWidget(self.revenue_chart, 1)
        report_body.addWidget(chart_card, 2)
        layout.addLayout(report_body, 1)
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
        self.employee_view, self.employee_empty = self._table_view(
            self.employee_table,
            "No employee bills were recorded in this date range.",
        )
        layout.addWidget(self.employee_view, 1)
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
        button = PremiumButton(text)
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
        table.verticalHeader().setDefaultSectionSize(40)
        table.horizontalHeader().setMinimumHeight(38)
        table.setAccessibleDescription(
            "Read-only report table. Use arrow keys to navigate rows and columns."
        )
        return table

    def _table_view(self, table, empty_message):
        view = QStackedWidget()
        empty_state = QLabel(empty_message)
        empty_state.setObjectName("emptyState")
        empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_state.setWordWrap(True)
        empty_state.setAccessibleName(empty_message)
        view.addWidget(table)
        view.addWidget(empty_state)
        view.setCurrentWidget(empty_state)
        return view, empty_state

    def _show_table_state(self, view, table, empty_label, message):
        empty_label.setText(message)
        view.setCurrentWidget(table if table.rowCount() else empty_label)

    def _show_loading_state(self, view, empty_label, status):
        status.setText("Loading…")
        status.repaint()
        empty_label.setText("Loading records…")
        view.setCurrentWidget(empty_label)
        view.repaint()

    def _on_tab_changed(self, index):
        if index == 0:
            self.load_dashboard()
        elif index == 1:
            self.load_categories()
        elif index == 2:
            self.load_tables()
        elif index == 3:
            self.load_sales_details()
        elif index == 4:
            self.load_revenue_report()
        elif index == 5:
            self.load_employee_report()
        elif index == 6:
            self.load_employee_sessions()

    def load_categories(self):
        self.menu_status.setText("Loading menu categories…")
        self.menu_status.repaint()
        try:
            categories = admin_service.get_menu_categories()
        except Exception as error:
            self.menu_status.setText(f"Categories unavailable: {error}")
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
        self._show_loading_state(
            self.database_view, self.database_empty, self.database_status
        )
        try:
            tables = admin_service.get_database_tables()
        except Exception as error:
            self.database_table.setRowCount(0)
            self._show_table_state(
                self.database_view,
                self.database_table,
                self.database_empty,
                f"Could not load database tables: {error}",
            )
            self.database_status.setText("Database tables unavailable.")
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
            self._show_table_state(
                self.database_view,
                self.database_table,
                self.database_empty,
                "No database tables were found.",
            )
            self.database_status.setText("No database tables were found.")

    def load_selected_table(self):
        table_name = self.table_combo.currentText()
        if not table_name:
            return
        self._show_loading_state(
            self.database_view, self.database_empty, self.database_status
        )
        try:
            columns, rows = admin_service.get_table_rows(table_name)
        except Exception as error:
            self.database_table.setRowCount(0)
            self._show_table_state(
                self.database_view,
                self.database_table,
                self.database_empty,
                f"Could not load {table_name}: {error}",
            )
            self.database_status.setText(f"Could not load {table_name}.")
            self._show_error(f"Could not load {table_name}", error)
            return
        self.table_columns = columns
        self.table_rows = rows
        self.search_input.clear()
        self._display_database_rows(rows)
        self._show_table_state(
            self.database_view,
            self.database_table,
            self.database_empty,
            f"No records are available in {table_name}.",
        )
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
        self._show_table_state(
            self.database_view,
            self.database_table,
            self.database_empty,
            "No records match your search.",
        )
        self.database_status.setText(
            f"Showing {len(matching_rows):,} of {len(self.table_rows):,} loaded record(s)."
        )

    def load_sales_details(self):
        start_date = self.sales_detail_start.date().toPython()
        end_date = self.sales_detail_end.date().toPython()
        self._show_loading_state(
            self.sales_detail_view,
            self.sales_detail_empty,
            self.sales_detail_status,
        )
        try:
            rows = admin_service.get_sales_details(start_date, end_date)
        except Exception as error:
            self.sales_detail_table.setRowCount(0)
            self._show_table_state(
                self.sales_detail_view,
                self.sales_detail_table,
                self.sales_detail_empty,
                f"Sales details unavailable: {error}",
            )
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
        self._show_table_state(
            self.sales_detail_view,
            self.sales_detail_table,
            self.sales_detail_empty,
            "No ordered items were recorded in this date range.",
        )
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
        self._show_loading_state(
            self.revenue_view, self.revenue_empty, self.revenue_status
        )
        try:
            rows = admin_service.get_revenue_by_day(start_date, end_date)
        except Exception as error:
            self.revenue_table.setRowCount(0)
            self.revenue_chart.set_points([])
            self._show_table_state(
                self.revenue_view,
                self.revenue_table,
                self.revenue_empty,
                f"Revenue unavailable: {error}",
            )
            self.revenue_summary.setText("Revenue unavailable.")
            self.revenue_status.setText(str(error))
            self._show_error("Could not calculate revenue", error)
            return

        self.revenue_table.setRowCount(len(rows))
        total_revenue = 0
        total_bills = 0
        chart_points = []
        for row_index, row in enumerate(rows):
            revenue = float(row["revenue"] or 0)
            bills = int(row["bill_count"] or 0)
            total_revenue += revenue
            total_bills += bills
            chart_points.append((row["revenue_date"], revenue))
            values = (
                str(row["revenue_date"]),
                str(bills),
                f"₹{revenue:,.2f}",
            )
            for column, value in enumerate(values):
                self.revenue_table.setItem(
                    row_index, column, QTableWidgetItem(value)
                )
        self.revenue_chart.set_points(chart_points)
        self._show_table_state(
            self.revenue_view,
            self.revenue_table,
            self.revenue_empty,
            "No completed payments were recorded in this date range.",
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
        self._show_loading_state(
            self.employee_view, self.employee_empty, self.employee_status
        )
        try:
            rows = admin_service.get_employee_bill_counts(start_date, end_date)
        except Exception as error:
            self.employee_table.setRowCount(0)
            self._show_table_state(
                self.employee_view,
                self.employee_table,
                self.employee_empty,
                f"Employee report unavailable: {error}",
            )
            self.employee_status.setText("Employee report unavailable.")
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
        self._show_table_state(
            self.employee_view,
            self.employee_table,
            self.employee_empty,
            "No employee bills were recorded in this date range.",
        )
        self.employee_status.setText(
            f"{total_bills:,} bills generated from {start_date:%d %b %Y} "
            f"to {end_date:%d %b %Y}."
            if rows
            else "No employee bills were recorded in this date range."
        )

    def _build_employee_sessions_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 16, 8, 8)
        layout.setSpacing(12)

        controls = QHBoxLayout()
        description = QLabel(
            "Employee sign-in times and session duration. Active sessions update on refresh."
        )
        description.setObjectName("mutedNote")
        controls.addWidget(description, 1)
        refresh = self._button("Refresh login history")
        refresh.clicked.connect(self.load_employee_sessions)
        controls.addWidget(refresh)
        layout.addLayout(controls)

        self.employee_sessions_table = self._table()
        self.employee_sessions_table.setColumnCount(6)
        self.employee_sessions_table.setHorizontalHeaderLabels(
            ["EMPLOYEE ID", "EMPLOYEE", "ROLE", "SIGNED IN", "SIGNED OUT", "DURATION"]
        )
        for column in (0, 2, 3, 4, 5):
            self.employee_sessions_table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        self.employee_sessions_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.employee_sessions_view, self.employee_sessions_empty = self._table_view(
            self.employee_sessions_table,
            "No employee login sessions have been recorded.",
        )
        layout.addWidget(self.employee_sessions_view, 1)
        self.employee_sessions_status = QLabel(
            "Employee login history has not been loaded."
        )
        self.employee_sessions_status.setObjectName("mutedNote")
        layout.addWidget(self.employee_sessions_status)
        return page

    def load_employee_sessions(self):
        self._show_loading_state(
            self.employee_sessions_view,
            self.employee_sessions_empty,
            self.employee_sessions_status,
        )
        try:
            rows = employee_sessions.get_employee_login_history()
        except Exception as error:
            self.employee_sessions_table.setRowCount(0)
            self._show_table_state(
                self.employee_sessions_view,
                self.employee_sessions_table,
                self.employee_sessions_empty,
                f"Employee login history unavailable: {error}",
            )
            self.employee_sessions_status.setText(
                "Employee login history unavailable."
            )
            self._show_error("Could not load employee login history", error)
            return

        self.employee_sessions_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            logout_time = row["logout_time"]
            values = (
                str(row["employee_id"]),
                str(row["employee_name"]),
                str(row["job_role"]),
                self._format_session_time(row["login_time"]),
                self._format_session_time(logout_time) if logout_time else "Active",
                self._format_session_duration(row["duration_seconds"]),
            )
            for column, value in enumerate(values):
                self.employee_sessions_table.setItem(
                    row_index, column, QTableWidgetItem(value)
                )
        self._show_table_state(
            self.employee_sessions_view,
            self.employee_sessions_table,
            self.employee_sessions_empty,
            "No employee login sessions have been recorded.",
        )
        self.employee_sessions_status.setText(
            f"{len(rows):,} most recent employee login session(s)."
            if rows
            else "No employee login sessions have been recorded."
        )

    @staticmethod
    def _format_session_time(value):
        return value.strftime("%d %b %Y %I:%M:%S %p") if hasattr(value, "strftime") else str(value)

    @staticmethod
    def _format_session_duration(seconds):
        total_seconds = max(0, int(seconds or 0))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}h {minutes}m"
        if minutes:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    def _show_error(self, title, error):
        QMessageBox.critical(self, title, str(error))
