import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow


class PremiumButtonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_primary_button_remains_visible_and_changes_on_hover(self):
        window = MainWindow()
        window.stack.setCurrentWidget(window.roles_page)
        window.show()
        self.application.processEvents()

        button = next(
            item
            for item in window.findChildren(type(window.theme_button))
            if item.objectName() == "primaryButton" and item.isVisible()
        )
        normal_image = button.grab().toImage()
        QTest.mouseMove(button, QPoint(button.width() // 2, button.height() // 2))
        self.application.processEvents()
        hover_image = button.grab().toImage()

        self.assertTrue(button.isVisible())
        self.assertTrue(button.underMouse())
        self.assertIsNone(button.graphicsEffect())
        self.assertTrue(
            any(
                normal_image.pixel(x, y) != hover_image.pixel(x, y)
                for x in range(normal_image.width())
                for y in range(normal_image.height())
            )
        )
        window.close()

    def test_welcome_screen_has_local_navigation_and_quick_guide(self):
        window = MainWindow()
        self.assertEqual(window.home_page.objectName(), "welcomePage")
        self.assertEqual(window.enter_cafe_button.text(), "Enter Cafe")
        self.assertEqual(window.quick_guide_button.text(), "Quick Guide")

        window.enter_cafe_button.click()
        self.assertIs(window.stack.currentWidget(), window.roles_page)

        with patch("gui.main_window.QMessageBox.information") as show_guide:
            window.quick_guide_button.click()
        show_guide.assert_called_once()
        self.assertIn("Employee", show_guide.call_args.args[2])
        self.assertIn("Admin", show_guide.call_args.args[2])
        window.close()

    def test_complex_panels_switch_without_widget_graphics_effects(self):
        window = MainWindow()

        self.assertIsNone(window.booking_page.graphicsEffect())
        self.assertIsNone(window.admin_page.graphicsEffect())
        self.assertIsNone(window.booking_page.stage_stack.widget(0).graphicsEffect())

        window._show_page(window.booking_page)
        self.assertIs(window.stack.currentWidget(), window.booking_page)
        window.booking_page._show_stage(1)
        self.assertEqual(window.booking_page.stage_stack.currentIndex(), 1)
        self.assertIsNone(window.booking_page.stage_stack.widget(1).graphicsEffect())

        window._show_page(window.admin_page)
        self.assertIs(window.stack.currentWidget(), window.admin_page)
        self.assertIsNone(window.admin_page.graphicsEffect())
        window.close()

    def test_theme_toggle_updates_icon_accessibility_and_welcome_theme(self):
        window = MainWindow()
        window._toggle_theme()

        self.assertTrue(window.is_dark)
        self.assertEqual(window.theme_button.text(), "☾")
        self.assertEqual(
            window.theme_button.accessibleName(),
            "Switch to light theme",
        )
        self.assertIn("#1c1714", window.styleSheet())
        window.close()


if __name__ == "__main__":
    unittest.main()
