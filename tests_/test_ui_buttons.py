import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from gui.branding import LOGO_PATH
from gui.main_window import MainWindow
from gui.startup_splash import StartupSplash


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

    def test_brand_logo_is_visible_in_shared_header(self):
        window = MainWindow()

        self.assertTrue(LOGO_PATH.is_file())
        self.assertFalse(window.brand_logo.pixmap().isNull())
        self.assertEqual(window.brand_logo.accessibleName(), "Mayuri Cafe logo")
        self.assertIsNotNone(window.findChild(type(window.brand_logo), "brandLogo"))
        window.close()

    def test_startup_splash_animates_the_brand_logo(self):
        splash = StartupSplash()

        self.assertEqual(splash.logo_animation.duration(), 850)
        self.assertEqual(splash.logo.accessibleName(), "Mayuri Cafe logo")
        self.assertFalse(splash.logo.pixmap().isNull())
        self.assertEqual(splash.logo_animation.endValue().width(), 300)
        splash.show()
        self.application.processEvents()
        self.assertTrue(splash.logo_animation.state())
        splash.close()

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

    def test_page_transitions_slide_and_finish_at_normal_position(self):
        window = MainWindow()
        window.show()
        self.application.processEvents()

        window._show_page(window.roles_page)
        self.assertIs(window.stack.currentWidget(), window.roles_page)
        self.assertIsNotNone(window._page_animation)
        self.assertGreater(window.roles_page.x(), 0)
        self.assertIsNone(window.roles_page.graphicsEffect())
        QTest.qWait(520)
        self.assertEqual(window.roles_page.pos().x(), 0)
        self.assertEqual(window.roles_page.pos().y(), 0)

        window._show_page(window.booking_page)
        self.assertGreater(window.booking_page.x(), 0)
        window._show_page(window.admin_page)
        self.assertIs(window.stack.currentWidget(), window.admin_page)
        QTest.qWait(520)
        self.assertEqual(window.admin_page.pos().x(), 0)
        self.assertEqual(window.admin_page.pos().y(), 0)
        self.assertEqual(window.roles_page.pos().x(), 0)
        window.close()

    def test_welcome_headline_appears_with_typewriter_animation(self):
        window = MainWindow()
        window.show()
        self.application.processEvents()

        self.assertEqual(window.welcome_title.accessibleName(), "Welcome to MAYURICAFE")
        self.assertGreaterEqual(
            window.welcome_title.height(),
            window.welcome_title.fontMetrics().height(),
        )
        QTest.qWait(180)
        visible_text = window.welcome_title.text()
        self.assertGreater(len(visible_text), 0)
        self.assertLess(len(visible_text), len("Welcome to MAYURICAFE"))

        QTest.qWait(1200)
        self.assertEqual(window.welcome_title.text(), "Welcome to MAYURICAFE")
        self.assertFalse(window._welcome_typing_timer.isActive())
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
