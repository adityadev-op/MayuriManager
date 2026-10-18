import unittest
from datetime import date
from unittest.mock import patch

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from admin import admin_service
from gui.admin import AdminWidget


class AdminServiceTests(unittest.TestCase):
    def setUp(self):
        self.cursor = unittest.mock.Mock()
        self.connection = unittest.mock.Mock()
        self.connection.cursor.return_value = self.cursor

    def test_create_menu_item_commits_item_fields(self):
        self.cursor.lastrowid = 31
        with patch.object(
            admin_service, "get_connection", return_value=self.connection
        ):
            item_id = admin_service.create_menu_item(
                4, "  Masala Tea ", "  Spiced tea  ", 35.5, True
            )

        self.assertEqual(item_id, 31)
        query, values = self.cursor.execute.call_args.args
        self.assertIn("INSERT INTO menu_items", query)
        self.assertEqual(values, (4, "Masala Tea", "Spiced tea", 35.5, True))
        self.connection.commit.assert_called_once_with()
        self.connection.rollback.assert_not_called()

    def test_create_menu_item_rolls_back_on_database_failure(self):
        self.cursor.execute.side_effect = RuntimeError("insert failed")
        with (
            patch.object(
                admin_service, "get_connection", return_value=self.connection
            ),
            self.assertRaisesRegex(RuntimeError, "insert failed"),
        ):
            admin_service.create_menu_item(4, "Tea", "", 30)

        self.connection.rollback.assert_called_once_with()
        self.connection.commit.assert_not_called()

    def test_sales_details_query_includes_order_items_guest_and_employee(self):
        report = [{
            "order_id": 42,
            "order_date": date(2026, 10, 18),
            "customer_name": "Maya",
            "customer_phone": "123",
            "employee_name": "Aarav",
            "order_type": "dine_in",
            "item_name": "Tea",
            "quantity": 2,
            "unit_price": 30,
            "item_total": 60,
            "payment_methods": "cash",
            "payment_statuses": "completed",
        }]
        self.cursor.fetchall.return_value = report
        start_date = date(2026, 10, 1)
        end_date = date(2026, 10, 18)

        with patch.object(
            admin_service, "get_connection", return_value=self.connection
        ):
            result = admin_service.get_sales_details(start_date, end_date)

        query, values = self.cursor.execute.call_args.args
        self.assertIn("FROM orders AS o", query)
        self.assertIn("INNER JOIN order_items AS oi", query)
        self.assertIn("oi.quantity * oi.unit_price AS item_total", query)
        self.assertIn("LEFT JOIN customers", query)
        self.assertIn("LEFT JOIN employees", query)
        self.assertIn("DATE(o.order_date) BETWEEN %s AND %s", query)
        self.assertEqual(values, (start_date, end_date))
        self.assertEqual(result, report)
        self.assertEqual(self.connection.commit.call_count, 2)
        self.cursor.close.assert_called_once_with()

    def test_revenue_report_uses_completed_payment_amount_and_date(self):
        report = [
            {
                "revenue_date": date(2026, 10, 18),
                "bill_count": 5,
                "revenue": 1250,
            }
        ]
        self.cursor.fetchall.return_value = report
        start_date = date(2026, 10, 1)
        end_date = date(2026, 10, 18)

        with patch.object(
            admin_service, "get_connection", return_value=self.connection
        ):
            result = admin_service.get_revenue_by_day(start_date, end_date)

        query, values = self.cursor.execute.call_args.args
        self.assertIn("FROM payments AS p", query)
        self.assertIn("p.payment_status = 'completed'", query)
        self.assertIn("SUM(p.amount) AS revenue", query)
        self.assertIn("DATE(p.payment_date) BETWEEN %s AND %s", query)
        self.assertEqual(values, (start_date, end_date))
        self.assertEqual(result, report)

    def test_employee_report_counts_bills_and_billed_amount_by_date(self):
        report = [
            {
                "employee_id": 12,
                "employee_name": "Aarav",
                "bill_count": 3,
                "total_billed": 700,
            }
        ]
        self.cursor.fetchall.return_value = report
        start_date = date(2026, 10, 1)
        end_date = date(2026, 10, 18)

        with patch.object(
            admin_service, "get_connection", return_value=self.connection
        ):
            result = admin_service.get_employee_bill_counts(start_date, end_date)

        query, values = self.cursor.execute.call_args.args
        self.assertIn("COUNT(DISTINCT o.order_id)", query)
        self.assertIn("LEFT JOIN orders", query)
        self.assertIn("o.order_status != 'cancelled'", query)
        self.assertEqual(values, (start_date, end_date))
        self.assertEqual(result, report)

    def test_category_sales_report_aggregates_quantities_and_order_value(self):
        report = [
            {
                "category_name": "Drinks",
                "items_sold": 4,
                "category_revenue": 120,
            }
        ]
        self.cursor.fetchall.return_value = report
        start_date = date(2026, 10, 1)
        end_date = date(2026, 10, 18)

        with patch.object(
            admin_service, "get_connection", return_value=self.connection
        ):
            result = admin_service.get_category_sales(start_date, end_date)

        query, values = self.cursor.execute.call_args.args
        self.assertIn("SUM(oi.quantity)", query)
        self.assertIn("SUM(oi.quantity * oi.unit_price)", query)
        self.assertIn("LEFT JOIN categories AS c", query)
        self.assertIn("o.order_status != 'cancelled'", query)
        self.assertEqual(values, (start_date, end_date))
        self.assertEqual(result, report)

    def test_date_reports_reject_reversed_ranges(self):
        with self.assertRaisesRegex(ValueError, "Start date"):
            admin_service.get_sales_details(date(2026, 10, 18), date(2026, 10, 1))

        with self.assertRaisesRegex(ValueError, "Start date"):
            admin_service.get_revenue_by_day(date(2026, 10, 18), date(2026, 10, 1))

        with self.assertRaisesRegex(ValueError, "Start date"):
            admin_service.get_employee_bill_counts(
                date(2026, 10, 18), date(2026, 10, 1)
            )


class AdminWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.widget = AdminWidget()

    def test_database_search_filters_across_all_columns(self):
        self.widget.table_columns = ["customer_name", "phone"]
        self.widget.table_rows = [
            {"customer_name": "Maya", "phone": "123"},
            {"customer_name": "Aarav", "phone": "456"},
        ]

        self.widget.search_input.setText("456")

        self.assertEqual(self.widget.database_table.rowCount(), 1)
        self.assertEqual(
            self.widget.database_table.item(0, 0).text(),
            "Aarav",
        )
        self.assertIn("1 of 2", self.widget.database_status.text())

    def test_menu_form_calls_service_and_clears_input_after_success(self):
        self.widget.category_combo.addItem("Drinks", 4)
        self.widget.item_name_input.setText("Masala Tea")
        self.widget.item_description_input.setText("Spiced tea")
        self.widget.item_price_input.setValue(35)

        with patch(
            "gui.admin.admin_service.create_menu_item", return_value=31
        ) as create_item:
            self.widget.add_menu_item()

        create_item.assert_called_once_with(4, "Masala Tea", "Spiced tea", 35, True)
        self.assertEqual(self.widget.item_name_input.text(), "")
        self.assertIn("ID 31", self.widget.menu_status.text())

    def test_order_details_display_guest_employee_and_item_totals(self):
        report = [
            {
                "order_id": 42,
                "order_date": "2026-10-18 13:30:00",
                "customer_name": "Maya",
                "customer_phone": "123",
                "employee_name": "Aarav",
                "order_type": "dine_in",
                "item_name": "Masala Tea",
                "quantity": 2,
                "unit_price": 30,
                "item_total": 60,
                "payment_methods": "cash",
                "payment_statuses": "completed",
            }
        ]
        with patch(
            "gui.admin.admin_service.get_sales_details", return_value=report
        ):
            self.widget.load_sales_details()

        self.assertEqual(self.widget.sales_detail_table.rowCount(), 1)
        self.assertEqual(
            self.widget.sales_detail_table.item(0, 2).text(),
            "Maya",
        )
        self.assertEqual(
            self.widget.sales_detail_table.item(0, 4).text(),
            "Aarav",
        )
        self.assertEqual(
            self.widget.sales_detail_table.item(0, 9).text(),
            "₹60.00",
        )
        self.assertEqual(
            self.widget.sales_detail_summary.text(),
            "1 bills  ·  1 item lines  ·  ₹60.00 ordered value",
        )

    def test_load_order_details_button_fetches_fresh_rows_each_press(self):
        first_result = [{
            "order_id": 41,
            "order_date": "2026-10-18 12:00:00",
            "customer_name": "Maya",
            "customer_phone": "123",
            "employee_name": "Aarav",
            "order_type": "takeaway",
            "item_name": "Tea",
            "quantity": 1,
            "unit_price": 30,
            "item_total": 30,
            "payment_methods": "cash",
            "payment_statuses": "completed",
        }]
        second_result = [{
            **first_result[0],
            "order_id": 42,
            "item_name": "Coffee",
            "item_total": 50,
        }]

        with patch(
            "gui.admin.admin_service.get_sales_details",
            side_effect=[first_result, second_result],
        ) as fetch_details:
            self.widget.load_sales_button.click()
            self.assertEqual(
                self.widget.sales_detail_table.item(0, 0).text(),
                "41",
            )
            self.widget.load_sales_button.click()

        self.assertEqual(fetch_details.call_count, 2)
        self.assertEqual(
            fetch_details.call_args_list[0].args,
            (
                self.widget.sales_detail_start.date().toPython(),
                self.widget.sales_detail_end.date().toPython(),
            ),
        )
        self.assertEqual(self.widget.sales_detail_table.rowCount(), 1)
        self.assertEqual(
            self.widget.sales_detail_table.item(0, 0).text(),
            "42",
        )
        self.assertEqual(
            self.widget.sales_detail_table.item(0, 6).text(),
            "Coffee",
        )

    def test_revenue_report_displays_completed_payment_totals(self):
        report = [
            {
                "revenue_date": date(2026, 10, 18),
                "bill_count": 2,
                "revenue": 350,
            }
        ]
        with patch(
            "gui.admin.admin_service.get_revenue_by_day", return_value=report
        ):
            self.widget.load_revenue_report()

        self.assertEqual(self.widget.revenue_table.rowCount(), 1)
        self.assertEqual(
            self.widget.revenue_summary.text(),
            "₹350.00 revenue received  ·  2 completed bills",
        )
        self.assertEqual(
            self.widget.revenue_table.item(0, 2).text(),
            "₹350.00",
        )
        self.assertEqual(
            self.widget.revenue_view.currentWidget(),
            self.widget.revenue_table,
        )
        self.assertEqual(
            self.widget.revenue_chart._points,
            [(date(2026, 10, 18), 350.0)],
        )

    def test_admin_dashboard_uses_live_range_data_for_kpis_categories_and_staff(self):
        revenue_rows = [
            {"revenue_date": date(2026, 10, 18), "bill_count": 2, "revenue": 350},
            {"revenue_date": date(2026, 10, 17), "bill_count": 1, "revenue": 150},
        ]
        category_rows = [
            {
                "category_name": "Drinks",
                "items_sold": 4,
                "category_revenue": 300,
            },
            {
                "category_name": "Pastries",
                "items_sold": 2,
                "category_revenue": 200,
            },
        ]
        employee_rows = [
            {
                "employee_id": 12,
                "employee_name": "Aarav",
                "bill_count": 2,
                "total_billed": 350,
            },
            {
                "employee_id": 13,
                "employee_name": "Maya",
                "bill_count": 1,
                "total_billed": 150,
            },
        ]

        with (
            patch(
                "gui.admin.admin_service.get_revenue_by_day",
                return_value=revenue_rows,
            ) as get_revenue,
            patch(
                "gui.admin.admin_service.get_category_sales",
                return_value=category_rows,
            ) as get_categories,
            patch(
                "gui.admin.admin_service.get_employee_bill_counts",
                return_value=employee_rows,
            ) as get_employees,
        ):
            self.widget.dashboard_range.setCurrentIndex(1)

        expected_dates = (
            self.widget.dashboard_start.date().toPython(),
            self.widget.dashboard_end.date().toPython(),
        )
        get_revenue.assert_called_once_with(*expected_dates)
        get_categories.assert_called_once_with(*expected_dates)
        get_employees.assert_called_once_with(*expected_dates)
        self.assertEqual(
            self.widget.dashboard_metric_values["revenue"].text(),
            "₹500.00",
        )
        self.assertEqual(
            self.widget.dashboard_metric_values["orders"].text(),
            "3",
        )
        self.assertEqual(
            self.widget.dashboard_metric_values["average"].text(),
            "₹166.67",
        )
        self.assertEqual(self.widget.dashboard_category_table.rowCount(), 2)
        self.assertEqual(
            self.widget.dashboard_category_table.item(0, 3).text(),
            "60.0%",
        )
        self.assertEqual(self.widget.dashboard_employee_rows.count(), 2)

    def test_empty_revenue_report_has_a_clear_empty_state(self):
        with patch("gui.admin.admin_service.get_revenue_by_day", return_value=[]):
            self.widget.load_revenue_report()

        self.assertEqual(self.widget.revenue_table.rowCount(), 0)
        self.assertEqual(
            self.widget.revenue_view.currentWidget(),
            self.widget.revenue_empty,
        )
        self.assertIn("No completed payments", self.widget.revenue_empty.text())
        self.assertEqual(self.widget.revenue_chart._points, [])

    def test_manual_report_refresh_dispatches_for_selected_report(self):
        with (
            patch.object(self.widget, "load_dashboard") as load_dashboard,
            patch.object(self.widget, "load_sales_details") as load_details,
            patch.object(self.widget, "load_revenue_report") as load_revenue,
        ):
            self.widget.refresh_sales_reports()
            load_dashboard.assert_called_once_with()
            self.widget.tabs.setCurrentIndex(3)
            load_details.assert_called_once_with()
            load_details.reset_mock()
            self.widget.refresh_sales_reports()
            load_details.assert_called_once_with()
            self.widget.tabs.setCurrentIndex(4)
            load_revenue.assert_called_once_with()
            load_revenue.reset_mock()
            self.widget.refresh_sales_reports()
            load_revenue.assert_called_once_with()

    def test_sales_refresh_timer_runs_every_thirty_seconds(self):
        self.assertEqual(self.widget.refresh_timer.interval(), 30_000)


if __name__ == "__main__":
    unittest.main()
