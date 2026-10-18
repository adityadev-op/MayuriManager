import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from gui.order_management import OrderManagementWidget
from gui.main_window import MainWindow
from gui.widgets import PremiumButton


class OrderManagementWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.dashboard_calls = []
        self.admin_calls = []
        self.widget = OrderManagementWidget(
            lambda: self.dashboard_calls.append(True),
            lambda: self.dashboard_calls.append("seats"),
            lambda: self.admin_calls.append(True),
        )

    def test_refresh_renders_database_orders_and_search_filters_cards(self):
        order = {
            "order_id": 42,
            "order_date": None,
            "order_status": "pending",
            "order_type": "takeaway",
            "total_amount": 110,
            "customer_name": "Maya",
            "customer_phone": "9876543210",
            "employee_name": "Aarav",
            "table_number": None,
            "items": [
                {"item_name": "Tea", "quantity": 2, "unit_price": 30},
                {"item_name": "Cake", "quantity": 1, "unit_price": 50},
            ],
        }
        with patch(
            "gui.order_management.get_active_orders",
            return_value=[order],
        ) as fetch_orders:
            self.widget.refresh_orders()

        fetch_orders.assert_called_once_with()
        self.assertEqual(self.widget.cards_layout.count(), 1)
        self.assertIn("1 active order", self.widget.status_label.text())
        self.assertTrue(
            any(
                label.text() == "Maya"
                for label in self.widget.cards_container.findChildren(QLabel)
            )
        )

        self.widget.search_input.setText("no match")
        self.assertEqual(self.widget.cards_layout.count(), 1)
        self.assertEqual(
            self.widget.cards_layout.itemAt(0).widget().objectName(),
            "orderEmptyState",
        )
        self.assertIn("No active orders match", self.widget.status_label.text())

    def test_refresh_failure_is_reported_and_does_not_show_stale_orders(self):
        with patch(
            "gui.order_management.get_active_orders",
            side_effect=ConnectionError("database unavailable"),
        ):
            self.widget.refresh_orders()

        self.assertEqual(self.widget.orders, [])
        self.assertIn("database unavailable", self.widget.status_label.text())
        self.assertEqual(
            self.widget.cards_layout.itemAt(0).widget().objectName(),
            "orderEmptyState",
        )

    def test_order_details_and_navigation_actions(self):
        order = {
            "order_id": 42,
            "order_date": None,
            "order_status": "pending",
            "order_type": "takeaway",
            "total_amount": 60,
            "customer_name": "Maya",
            "customer_phone": "9876543210",
            "employee_name": "Aarav",
            "table_number": None,
            "items": [
                {"item_name": "Tea", "quantity": 2, "unit_price": 30},
            ],
        }
        self.widget.orders = [order]
        card = self.widget._order_card(order)
        with patch("gui.order_management.QMessageBox.information") as show_details:
            card.findChild(PremiumButton).click()
        self.assertIn("2 × Tea", show_details.call_args.args[2])

        self.widget.dashboard_button.click()
        self.widget.tables_button.click()
        self.widget.admin_button.click()
        self.assertEqual(self.dashboard_calls, [True, "seats"])
        self.assertEqual(self.admin_calls, [True])

    def test_empty_database_result_shows_honest_empty_state(self):
        with patch("gui.order_management.get_active_orders", return_value=[]):
            self.widget.refresh_orders()

        self.assertEqual(self.widget.status_label.text(), "No active orders right now.")
        self.assertEqual(
            self.widget.cards_layout.itemAt(0).widget().objectName(),
            "orderEmptyState",
        )

    def test_employee_live_orders_action_opens_and_loads_order_screen(self):
        with (
            patch("gui.main_window.connection.set_password_prompt"),
            patch("gui.order_management.get_active_orders", return_value=[]) as fetch_orders,
        ):
            window = MainWindow()
            live_orders_button = next(
                button
                for button in window.employee_page.findChildren(PremiumButton)
                if button.text() == "Live orders"
            )
            live_orders_button.click()

        self.assertIs(window.stack.currentWidget(), window.order_management_page)
        fetch_orders.assert_called_once_with()
        window.close()

    def test_visible_order_management_refreshes_with_dashboard_timer(self):
        with (
            patch("gui.main_window.connection.set_password_prompt"),
            patch("gui.order_management.get_active_orders", return_value=[]) as fetch_orders,
        ):
            window = MainWindow()
            window.stack.setCurrentWidget(window.order_management_page)
            window._auto_refresh_employee_stats()

        fetch_orders.assert_called_once_with()
        window.close()


if __name__ == "__main__":
    unittest.main()
