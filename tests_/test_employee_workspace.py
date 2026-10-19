import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from Receptionist import orders
from gui.main_window import MainWindow
from services.authentication import AuthenticatedAccount


class EmployeeWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_dashboard_stats_query_counts_today_tables_and_open_orders(self):
        cursor = unittest.mock.Mock()
        stats = {
            "todays_bookings": 8,
            "available_tables": 5,
            "open_orders": 3,
        }
        cursor.fetchone.return_value = stats
        database = unittest.mock.Mock()
        database.cursor.return_value = cursor

        with patch.object(orders, "get_connection", return_value=database):
            result = orders.get_employee_dashboard_stats()

        query = cursor.execute.call_args.args[0]
        self.assertIn("DATE(order_date) = CURRENT_DATE()", query)
        self.assertIn("table_status = 'available'", query)
        self.assertIn("order_status NOT IN ('completed', 'cancelled')", query)
        self.assertEqual(result, stats)
        self.assertEqual(database.commit.call_count, 2)
        cursor.close.assert_called_once_with()

    def test_employee_workspace_fetches_live_stats_when_opened(self):
        stats = {
            "todays_bookings": 8,
            "available_tables": 5,
            "open_orders": 3,
        }
        with patch(
            "gui.main_window.get_employee_dashboard_stats",
            return_value=stats,
        ) as fetch_stats:
            window = MainWindow()
            window.authenticated_account = AuthenticatedAccount(
                "aaray", "Aaray Sharma", "employee", 1, "Receptionist"
            )
            window._open_employee_workspace()

        QTest.qWait(350)
        fetch_stats.assert_called_once_with()
        self.assertEqual(
            {
                key: value.text()
                for key, value in window.employee_stat_values.items()
            },
            {
                "todays_bookings": "8",
                "available_tables": "5",
                "open_orders": "3",
            },
        )
        self.assertIn("Updated", window.employee_status.text())

    def test_failed_stats_refresh_shows_error_and_clears_stale_values(self):
        window = MainWindow()
        for value in window.employee_stat_values.values():
            value.setText("9")

        with patch(
            "gui.main_window.get_employee_dashboard_stats",
            side_effect=ConnectionError("database unavailable"),
        ):
            window._refresh_employee_stats()

        self.assertTrue(
            all(
                value.text() == "—"
                for value in window.employee_stat_values.values()
            )
        )
        self.assertIn("database unavailable", window.employee_status.text())
        self.assertEqual(window.employee_live_badge.property("state"), "error")
        self.assertTrue(
            all(
                badge.text() == "UNAVAILABLE"
                for badge in window.employee_stat_badges.values()
            )
        )

    def test_employee_dashboard_uses_real_counts_and_existing_actions(self):
        window = MainWindow()

        self.assertEqual(window.employee_live_badge.property("state"), "waiting")
        self.assertEqual(
            [badge.text() for badge in window.employee_stat_badges.values()],
            ["WAITING", "WAITING", "WAITING"],
        )
        self.assertEqual(window.employee_refresh_button.text(), "Refresh data")
        self.assertIn(
            "Start a new booking",
            [label.text() for label in window.employee_page.findChildren(type(window.employee_status))],
        )
        page_text = " ".join(
            label.text() for label in window.employee_page.findChildren(type(window.employee_status))
        )
        self.assertIn("Today's service", page_text)
        self.assertIn("Guest", page_text)
        self.assertIn("Payment", page_text)
        self.assertNotIn("Kitchen Display connected", page_text)
        window.close()

    def test_periodic_refresh_only_queries_while_employee_workspace_is_open(self):
        with patch(
            "gui.main_window.get_employee_dashboard_stats"
        ) as fetch_stats:
            window = MainWindow()
            window.authenticated_account = AuthenticatedAccount(
                "aaray", "Aaray Sharma", "employee", 1, "Receptionist"
            )
            window.stack.setCurrentWidget(window.auth_page)
            window._auto_refresh_employee_stats()
            fetch_stats.assert_not_called()

            window.stack.setCurrentWidget(window.employee_page)
            fetch_stats.return_value = {
                "todays_bookings": 0,
                "available_tables": 0,
                "open_orders": 0,
            }
            window._auto_refresh_employee_stats()
            fetch_stats.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
