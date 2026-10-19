import os
import unittest
from unittest.mock import Mock, patch

from Database_ import connection


class PersistentConnectionTests(unittest.TestCase):
    def setUp(self):
        self.previous_connection = connection._database_connection
        connection._database_connection = None

    def tearDown(self):
        connection._database_connection = self.previous_connection

    def test_reuses_one_connection_until_explicit_shutdown(self):
        database = Mock()
        database.is_connected.return_value = True

        with patch.object(connection, "connect_to_database", return_value=database) as connect:
            first = connection.get_connection()
            second = connection.get_connection()

            self.assertIs(first, database)
            self.assertIs(second, database)
            connect.assert_called_once_with()
            database.close.assert_not_called()

            connection.close_database_connection()

        database.close.assert_called_once_with()
        self.assertIsNone(connection._database_connection)

    def test_reconnects_persistent_connection_after_connection_loss(self):
        database = Mock()
        database.ping.side_effect = connection.Error("connection lost")
        connection._database_connection = database
        replacement = Mock()
        replacement.is_connected.return_value = True

        with patch.object(
            connection, "connect_to_database", return_value=replacement
        ) as connect:
            self.assertIs(connection.get_connection(), replacement)

        database.ping.assert_called_once_with(reconnect=True, attempts=1, delay=0)
        connect.assert_called_once_with()

    def test_connect_uses_the_password_from_environment(self):
        database = Mock()
        database.is_connected.return_value = True
        cursor = database.cursor.return_value
        cursor.fetchone.return_value = ("MAYURICAFE",)

        with (
            patch.dict(os.environ, {"MAYURICAFE_MYSQL_PASSWORD": "configured"}),
            patch.object(
                connection.mysql.connector, "connect", return_value=database
            ) as connect,
        ):
            self.assertIs(connection.connect_to_database(), database)

        self.assertEqual(connect.call_args.kwargs["password"], "configured")
        cursor.close.assert_called_once_with()

    def test_connect_reports_missing_environment_password_without_prompting(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            self.assertRaisesRegex(ConnectionError, "MAYURICAFE_MYSQL_PASSWORD"),
            patch.object(connection.mysql.connector, "connect") as connect,
        ):
            connection.connect_to_database()

        connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
