import unittest
from unittest.mock import Mock, patch

from services import employee_sessions


class EmployeeSessionServiceTests(unittest.TestCase):
    def setUp(self):
        self.cursor = Mock()
        self.database = Mock()
        self.database.cursor.return_value = self.cursor

    def test_start_employee_login_creates_table_and_records_employee(self):
        self.cursor.lastrowid = 31
        with patch.object(
            employee_sessions, "get_connection", return_value=self.database
        ) as get_connection:
            login_id = employee_sessions.start_employee_login(
                2, "Diya Patel", "Cashier"
            )

        self.assertEqual(login_id, 31)
        self.assertEqual(get_connection.call_count, 2)
        queries = [call.args[0] for call in self.cursor.execute.call_args_list]
        self.assertIn("CREATE TABLE IF NOT EXISTS employe_login", queries[0])
        self.assertIn("INSERT INTO employe_login", queries[1])
        self.assertEqual(
            self.cursor.execute.call_args_list[1].args[1],
            (2, "Diya Patel", "Cashier"),
        )
        self.assertEqual(self.database.commit.call_count, 2)
        self.database.rollback.assert_not_called()
        self.assertEqual(self.cursor.close.call_count, 2)

    def test_end_employee_login_records_logout_and_requires_open_session(self):
        self.cursor.rowcount = 1
        with patch.object(
            employee_sessions, "get_connection", return_value=self.database
        ):
            employee_sessions.end_employee_login(31)

        query, values = self.cursor.execute.call_args.args
        self.assertIn("UPDATE employe_login", query)
        self.assertIn("logout_time IS NULL", query)
        self.assertEqual(values, (31,))
        self.database.commit.assert_called_once_with()

    def test_end_employee_login_rolls_back_if_session_is_not_open(self):
        self.cursor.rowcount = 0
        with (
            patch.object(
                employee_sessions, "get_connection", return_value=self.database
            ),
            self.assertRaisesRegex(RuntimeError, "missing or already closed"),
        ):
            employee_sessions.end_employee_login(31)

        self.database.rollback.assert_called_once_with()
        self.database.commit.assert_not_called()

    def test_login_history_reads_latest_records_as_dictionaries(self):
        self.cursor.fetchall.return_value = [{"login_id": 31}]
        with patch.object(
            employee_sessions, "get_connection", return_value=self.database
        ):
            rows = employee_sessions.get_employee_login_history()

        self.assertEqual(rows, [{"login_id": 31}])
        self.assertEqual(self.database.cursor.call_args.kwargs, {"dictionary": True})
        query = self.cursor.execute.call_args.args[0]
        self.assertIn("FROM employe_login", query)
        self.assertIn("TIMESTAMPDIFF", query)
        self.assertIn("ORDER BY login_time DESC", query)
        self.assertEqual(self.cursor.execute.call_args.args[1], (500,))

    def test_login_history_rejects_non_positive_limit(self):
        with self.assertRaisesRegex(ValueError, "must be positive"):
            employee_sessions.get_employee_login_history(0)


if __name__ == "__main__":
    unittest.main()
