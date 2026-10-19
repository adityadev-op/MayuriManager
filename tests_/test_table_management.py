import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

from Receptionist import tables
from gui.main_window import MainWindow
from gui.table_management import TableManagementWidget
from services.authentication import AuthenticatedAccount
from gui.widgets import PremiumButton


class CafeTableServiceTests(unittest.TestCase):
    def test_get_cafe_tables_returns_every_seat_in_table_order(self):
        rows = [
            {
                "table_id": 1,
                "table_number": 1,
                "capacity": 2,
                "table_status": "available",
            },
            {
                "table_id": 2,
                "table_number": 2,
                "capacity": 4,
                "table_status": "occupied",
            },
        ]
        cursor = unittest.mock.Mock()
        cursor.fetchall.return_value = rows
        database = unittest.mock.Mock()
        database.cursor.return_value = cursor

        with patch.object(tables, "get_connection", return_value=database):
            result = tables.get_cafe_tables()

        query = cursor.execute.call_args.args[0]
        self.assertIn("FROM cafe_tables", query)
        self.assertIn("ORDER BY table_number", query)
        self.assertEqual(result, rows)
        self.assertEqual(database.commit.call_count, 2)
        cursor.close.assert_called_once_with()

    def test_vacate_cafe_table_updates_occupied_seat_and_commits(self):
        cursor = unittest.mock.Mock()
        cursor.rowcount = 1
        database = unittest.mock.Mock()
        database.cursor.return_value = cursor

        with patch.object(tables, "get_connection", return_value=database):
            tables.vacate_cafe_table(17)

        query, values = cursor.execute.call_args.args
        self.assertIn("SET table_status = 'available'", query)
        self.assertIn("table_status = 'occupied'", query)
        self.assertEqual(values, (17,))
        database.commit.assert_called_once_with()
        database.rollback.assert_not_called()
        cursor.close.assert_called_once_with()

    def test_vacating_a_stale_or_non_allocated_seat_is_rejected(self):
        cursor = unittest.mock.Mock()
        cursor.rowcount = 0
        database = unittest.mock.Mock()
        database.cursor.return_value = cursor

        with (
            patch.object(tables, "get_connection", return_value=database),
            self.assertRaisesRegex(ValueError, "no longer marked allocated"),
        ):
            tables.vacate_cafe_table(17)

        database.rollback.assert_called_once_with()
        database.commit.assert_not_called()
        cursor.close.assert_called_once_with()

    def test_vacating_without_a_table_id_is_rejected_before_database_access(self):
        with (
            patch.object(tables, "get_connection") as get_connection,
            self.assertRaisesRegex(ValueError, "Choose an allocated table"),
        ):
            tables.vacate_cafe_table(None)

        get_connection.assert_not_called()


class TableManagementWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.dashboard_calls = []
        self.order_calls = []
        self.updated_calls = []
        self.widget = TableManagementWidget(
            lambda: self.dashboard_calls.append(True),
            lambda: self.order_calls.append(True),
            lambda: self.updated_calls.append(True),
        )

    def test_refresh_splits_allocated_and_available_seats(self):
        seats = [
            {
                "table_id": 1,
                "table_number": 101,
                "capacity": 2,
                "table_status": "occupied",
            },
            {
                "table_id": 2,
                "table_number": 102,
                "capacity": 4,
                "table_status": "available",
            },
        ]
        with patch(
            "gui.table_management.get_cafe_tables",
            return_value=seats,
        ) as fetch_tables:
            self.widget.refresh_tables()

        fetch_tables.assert_called_once_with()
        self.assertEqual(self.widget.allocated_count.text(), "1")
        self.assertEqual(self.widget.available_count.text(), "1")
        self.assertEqual(self.widget.total_count.text(), "2")
        self.assertEqual(self.widget.allocated_rows["layout"].count(), 1)
        self.assertEqual(self.widget.available_rows["layout"].count(), 1)
        allocated_row = self.widget.allocated_rows["layout"].itemAt(0).widget()
        available_row = self.widget.available_rows["layout"].itemAt(0).widget()
        self.assertTrue(allocated_row.findChild(PremiumButton))
        self.assertIsNone(available_row.findChild(PremiumButton))
        self.assertIn("Updated", self.widget.status_label.text())

    def test_confirmed_vacate_updates_database_and_refreshes_related_views(self):
        seats = [
            {
                "table_id": 7,
                "table_number": 107,
                "capacity": 2,
                "table_status": "occupied",
            }
        ]
        with (
            patch("gui.table_management.get_cafe_tables", return_value=seats) as fetch,
            patch("gui.table_management.vacate_cafe_table") as vacate,
            patch(
                "gui.table_management.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Yes,
            ) as confirm,
        ):
            self.widget.refresh_tables()
            row = self.widget.allocated_rows["layout"].itemAt(0).widget()
            row.findChild(PremiumButton).click()

        confirm.assert_called_once()
        vacate.assert_called_once_with(7)
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(self.updated_calls, [True])

    def test_declined_vacate_does_not_change_seat_status(self):
        seats = [
            {
                "table_id": 7,
                "table_number": 107,
                "capacity": 2,
                "table_status": "occupied",
            }
        ]
        with (
            patch("gui.table_management.get_cafe_tables", return_value=seats),
            patch("gui.table_management.vacate_cafe_table") as vacate,
            patch(
                "gui.table_management.QMessageBox.question",
                return_value=QMessageBox.StandardButton.No,
            ),
        ):
            self.widget.refresh_tables()
            row = self.widget.allocated_rows["layout"].itemAt(0).widget()
            row.findChild(PremiumButton).click()

        vacate.assert_not_called()
        self.assertEqual(self.updated_calls, [])

    def test_table_screen_surfaces_database_errors(self):
        with patch(
            "gui.table_management.get_cafe_tables",
            side_effect=ConnectionError("database unavailable"),
        ):
            self.widget.refresh_tables()

        self.assertIn("database unavailable", self.widget.status_label.text())
        self.assertEqual(self.widget.allocated_count.text(), "—")
        self.assertEqual(self.widget.available_count.text(), "—")

    def test_seat_navigation_is_wired_from_employee_workspace_and_periodic_refresh(self):
        with (
            patch("gui.main_window.connection.get_connection"),
            patch("gui.table_management.get_cafe_tables", return_value=[]) as fetch,
        ):
            window = MainWindow()
            window.authenticated_account = AuthenticatedAccount(
                "aaray", "Aaray Sharma", "employee", 1, "Receptionist"
            )
            seats_button = next(
                button
                for button in window.employee_page.findChildren(PremiumButton)
                if button.text() == "Seat management"
            )
            seats_button.click()
            self.assertIs(
                window.stack.currentWidget(),
                window.table_management_page,
            )
            fetch.assert_called_once_with()

            window._auto_refresh_employee_stats()
            self.assertEqual(fetch.call_count, 2)
            window.close()


if __name__ == "__main__":
    unittest.main()
