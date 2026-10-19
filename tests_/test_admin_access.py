import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame, QLineEdit

import app
from gui.main_window import MainWindow
from services.authentication import (
    AuthenticatedAccount,
    authenticate_employee,
)


EMPLOYEE_CREDENTIALS = {
    "MAYURICAFE_EMPLOYEE_RECEPTIONIST_USERNAME": "aaray",
    "MAYURICAFE_EMPLOYEE_RECEPTIONIST_PASSWORD": "reception-secret",
    "MAYURICAFE_EMPLOYEE_RECEPTIONIST_ID": "1",
    "MAYURICAFE_EMPLOYEE_CASHIER_USERNAME": "diya",
    "MAYURICAFE_EMPLOYEE_CASHIER_PASSWORD": "cashier-secret",
    "MAYURICAFE_EMPLOYEE_CASHIER_ID": "2",
    "MAYURICAFE_EMPLOYEE_MANAGER_USERNAME": "tara",
    "MAYURICAFE_EMPLOYEE_MANAGER_PASSWORD": "manager-secret",
    "MAYURICAFE_EMPLOYEE_MANAGER_ID": "10",
}
ADMIN_CREDENTIALS = {
    "MAYURICAFE_ADMIN_ADITYA_USERNAME": "aditya",
    "MAYURICAFE_ADMIN_ADITYA_PASSWORD": "aditya-secret",
    "MAYURICAFE_ADMIN_PUSHPRAJ_USERNAME": "pushpraj",
    "MAYURICAFE_ADMIN_PUSHPRAJ_PASSWORD": "pushpraj-secret",
    "MAYURICAFE_ADMIN_DEEPAK_USERNAME": "deepak",
    "MAYURICAFE_ADMIN_DEEPAK_PASSWORD": "deepak-secret",
}


class AuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def _create_window(self):
        return MainWindow()

    def test_authentication_page_is_the_first_visible_workspace(self):
        window = self._create_window()
        window.resize(1280, 820)
        window.show()
        self.application.processEvents()

        self.assertIs(window.stack.currentWidget(), window.auth_page)
        card = window.auth_page.findChild(QFrame, "authenticationCard")
        self.assertEqual(card.maximumWidth(), 1200)
        self.assertGreater(card.width(), 1020)
        self.assertEqual(window.auth_page.employee_login_button.text(), "Login as Employee")
        self.assertEqual(window.auth_page.admin_login_button.text(), "Login as Admin")
        self.assertEqual(
            window.auth_page.employee_password.echoMode(),
            QLineEdit.EchoMode.Password,
        )
        self.assertEqual(
            window.auth_page.admin_password.echoMode(),
            QLineEdit.EchoMode.Password,
        )
        window.close()

    def test_admin_login_opens_admin_console(self):
        window = self._create_window()
        with (
            patch.dict(os.environ, ADMIN_CREDENTIALS, clear=True),
            patch("gui.main_window.connection.get_connection"),
            patch.object(window.admin_widget, "load") as load_admin,
        ):
            window._login_admin("aditya", "aditya-secret")

        load_admin.assert_called_once_with()
        self.assertEqual(window.authenticated_account.display_name, "Aditya")
        self.assertIs(window.stack.currentWidget(), window.admin_page)
        window.close()

    def test_employee_login_opens_employee_workspace_and_binds_employee_id(self):
        window = self._create_window()
        with (
            patch.dict(os.environ, EMPLOYEE_CREDENTIALS, clear=True),
            patch("gui.main_window.connection.get_connection"),
            patch(
                "gui.main_window.employee_sessions.start_employee_login",
                return_value=71,
            ) as start_session,
            patch("gui.main_window.employee_sessions.end_employee_login"),
            patch(
                "gui.main_window.get_employee_dashboard_stats",
                return_value={
                    "todays_bookings": 0,
                    "available_tables": 0,
                    "open_orders": 0,
                },
            ),
        ):
            window._login_employee("diya", "cashier-secret")

        self.assertEqual(window.authenticated_account.job_role, "Cashier")
        self.assertEqual(window.authenticated_account.employee_id, 2)
        self.assertEqual(window.booking_page.employee_id, 2)
        self.assertEqual(window.booking_page.employee_name, "Diya Patel")
        self.assertEqual(window.employee_greeting.text(), "Hello, Diya Patel")
        self.assertEqual(window._employee_login_id, 71)
        start_session.assert_called_once_with(2, "Diya Patel", "Cashier")
        self.assertIs(window.stack.currentWidget(), window.employee_page)
        with patch(
            "gui.main_window.employee_sessions.end_employee_login"
        ) as end_session:
            window.close()
        end_session.assert_called_once_with(71)

    def test_employee_logout_closes_the_recorded_session(self):
        window = self._create_window()
        window.authenticated_account = AuthenticatedAccount(
            "diya", "Diya Patel", "employee", 2, "Cashier"
        )
        window._employee_login_id = 71
        with patch(
            "gui.main_window.employee_sessions.end_employee_login"
        ) as end_session:
            window._logout()

        end_session.assert_called_once_with(71)
        self.assertIsNone(window.authenticated_account)
        self.assertIsNone(window._employee_login_id)
        self.assertIs(window.stack.currentWidget(), window.auth_page)
        window.close()

    def test_employee_session_recording_failure_prevents_login(self):
        window = self._create_window()
        with (
            patch.dict(os.environ, EMPLOYEE_CREDENTIALS, clear=True),
            patch("gui.main_window.connection.get_connection"),
            patch(
                "gui.main_window.employee_sessions.start_employee_login",
                side_effect=RuntimeError("write failed"),
            ),
            patch("gui.main_window.QMessageBox.critical") as show_error,
        ):
            window._login_employee("diya", "cashier-secret")

        show_error.assert_called_once()
        self.assertIsNone(window.authenticated_account)
        self.assertIs(window.stack.currentWidget(), window.auth_page)
        window.close()

    def test_only_receptionist_cashier_and_manager_accounts_authenticate(self):
        with patch.dict(os.environ, EMPLOYEE_CREDENTIALS, clear=True):
            self.assertEqual(
                authenticate_employee("aaray", "reception-secret").job_role,
                "Receptionist",
            )
            self.assertEqual(
                authenticate_employee("diya", "cashier-secret").job_role,
                "Cashier",
            )
            self.assertEqual(
                authenticate_employee("tara", "manager-secret").job_role,
                "Manager",
            )
            self.assertIsNone(authenticate_employee("chef", "other-secret"))

    def test_incorrect_credentials_are_rejected_before_database_connection(self):
        window = self._create_window()
        with (
            patch.dict(os.environ, ADMIN_CREDENTIALS, clear=True),
            patch("gui.main_window.connection.get_connection") as connect,
            patch("gui.main_window.QMessageBox.warning") as show_error,
        ):
            window._login_admin("aditya", "wrong-password")

        connect.assert_not_called()
        show_error.assert_called_once()
        self.assertIsNone(window.authenticated_account)
        self.assertIs(window.stack.currentWidget(), window.auth_page)
        window.close()

    def test_employee_and_admin_workspaces_are_role_restricted(self):
        window = self._create_window()
        window.authenticated_account = AuthenticatedAccount(
            "diya", "Diya Patel", "employee", 2, "Cashier"
        )
        with (
            patch("gui.main_window.QMessageBox.warning") as show_error,
            patch.object(window.admin_widget, "load") as load_admin,
        ):
            window._open_admin_workspace()

        show_error.assert_called_once()
        load_admin.assert_not_called()

        window.authenticated_account = AuthenticatedAccount(
            "aditya", "Aditya", "admin"
        )
        with patch("gui.main_window.QMessageBox.warning") as show_error:
            window._open_employee_workspace()
        show_error.assert_called_once()
        self.assertIsNot(window.stack.currentWidget(), window.employee_page)
        window.close()

    def test_database_failure_does_not_create_an_authenticated_session(self):
        window = self._create_window()
        with (
            patch.dict(os.environ, ADMIN_CREDENTIALS, clear=True),
            patch(
                "gui.main_window.connection.get_connection",
                side_effect=ConnectionError("database unavailable"),
            ),
            patch("gui.main_window.QMessageBox.critical") as show_error,
        ):
            window._login_admin("aditya", "aditya-secret")

        show_error.assert_called_once()
        self.assertIsNone(window.authenticated_account)
        self.assertIs(window.stack.currentWidget(), window.auth_page)
        window.close()

    def test_application_loads_all_local_dotenv_files_and_shows_login(self):
        application = unittest.mock.Mock()
        window = unittest.mock.Mock()
        with (
            patch("app.load_dotenv") as load_dotenv,
            patch("app.QApplication", return_value=application),
            patch("app.MainWindow", return_value=window),
        ):
            result = app.main()

        self.assertEqual(result, application.exec.return_value)
        self.assertEqual(
            [call.args[0].name for call in load_dotenv.call_args_list],
            [".env", ".env.employees", ".env.admins"],
        )
        window.show.assert_called_once_with()
        application.exec.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
