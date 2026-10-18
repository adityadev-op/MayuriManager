import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import app
from gui.main_window import MainWindow


class AdminAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def _create_window(self):
        with patch("gui.main_window.connection.set_password_prompt"):
            return MainWindow()

    def test_admin_workspace_is_denied_when_password_is_not_configured(self):
        window = self._create_window()
        with (
            patch.dict(os.environ, {"MAYURICAFE_ADMIN_PASSWORD": ""}),
            patch("gui.main_window.QMessageBox.critical") as show_error,
            patch("gui.main_window.QInputDialog.getText") as prompt_password,
            patch.object(window.admin_widget, "load") as load_admin,
        ):
            window._open_admin_workspace()

        show_error.assert_called_once()
        prompt_password.assert_not_called()
        load_admin.assert_not_called()
        self.assertIsNot(window.stack.currentWidget(), window.admin_page)

    def test_admin_workspace_rejects_incorrect_password(self):
        window = self._create_window()
        with (
            patch.dict(os.environ, {"MAYURICAFE_ADMIN_PASSWORD": "correct-secret"}),
            patch(
                "gui.main_window.QInputDialog.getText",
                return_value=("incorrect-secret", True),
            ),
            patch("gui.main_window.QMessageBox.warning") as show_error,
            patch.object(window.admin_widget, "load") as load_admin,
        ):
            window._open_admin_workspace()

        show_error.assert_called_once()
        load_admin.assert_not_called()
        self.assertIsNot(window.stack.currentWidget(), window.admin_page)

    def test_admin_workspace_opens_only_after_correct_password(self):
        window = self._create_window()
        with (
            patch.dict(os.environ, {"MAYURICAFE_ADMIN_PASSWORD": "correct-secret"}),
            patch(
                "gui.main_window.QInputDialog.getText",
                return_value=("correct-secret", True),
            ),
            patch.object(window.admin_widget, "load") as load_admin,
        ):
            window._open_admin_workspace()

        load_admin.assert_called_once_with()
        self.assertIs(window.stack.currentWidget(), window.admin_page)

    def test_application_loads_admin_password_from_local_environment_file(self):
        application = unittest.mock.Mock()
        window = unittest.mock.Mock()
        with (
            patch.dict(os.environ),
            patch("app.QApplication", return_value=application),
            patch("app.MainWindow", return_value=window),
            patch("app.connection.get_connection") as connect_database,
            patch.object(application, "exec", return_value=0) as run_event_loop,
        ):
            os.environ.pop("MAYURICAFE_ADMIN_PASSWORD", None)
            app.main()
            self.assertTrue(os.environ.get("MAYURICAFE_ADMIN_PASSWORD"))

        connect_database.assert_called_once_with()
        window.show.assert_called_once_with()
        run_event_loop.assert_called_once_with()

    def test_application_does_not_open_when_database_connection_fails(self):
        application = unittest.mock.Mock()
        window = unittest.mock.Mock()
        with (
            patch("app.QApplication", return_value=application),
            patch("app.MainWindow", return_value=window),
            patch(
                "app.connection.get_connection",
                side_effect=ConnectionError("Unable to connect"),
            ) as connect_database,
            patch("app.QMessageBox.critical") as show_error,
            patch.object(application, "exec", return_value=0) as run_event_loop,
        ):
            result = app.main()

        self.assertEqual(result, 1)
        connect_database.assert_called_once_with()
        show_error.assert_called_once()
        window.show.assert_not_called()
        run_event_loop.assert_not_called()


if __name__ == "__main__":
    unittest.main()
