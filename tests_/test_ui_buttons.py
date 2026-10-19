import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, Qt
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QScrollArea

from gui.branding import LOGO_PATH
from gui.main_window import MainWindow
from gui.startup_splash import STARTUP_VIDEO_PATH, StartupSplash


class PremiumButtonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_primary_button_remains_visible_and_changes_on_hover(self):
        window = MainWindow()
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

    def test_authentication_page_offers_employee_and_admin_sign_in(self):
        window = MainWindow()
        self.assertIs(window.stack.currentWidget(), window.auth_page)
        self.assertEqual(window.auth_page.employee_login_button.text(), "Login as Employee")
        self.assertEqual(window.auth_page.admin_login_button.text(), "Login as Admin")
        window.close()

    def test_brand_logo_is_visible_in_shared_header(self):
        window = MainWindow()

        self.assertTrue(LOGO_PATH.is_file())
        self.assertFalse(window.brand_logo.pixmap().isNull())
        self.assertEqual(window.brand_logo.accessibleName(), "Mayuri Cafe logo")
        self.assertIsNotNone(window.findChild(type(window.brand_logo), "brandLogo"))
        window.close()

    def test_startup_splash_plays_the_bundled_video_and_finishes_at_end(self):
        splash = StartupSplash()
        finished_calls = []
        splash.finished.connect(lambda: finished_calls.append(True))

        self.assertTrue(STARTUP_VIDEO_PATH.is_file())
        self.assertEqual(
            splash.video_path,
            STARTUP_VIDEO_PATH,
        )
        self.assertEqual(
            splash.player.videoOutput(),
            splash.video_widget,
        )

        splash._on_media_status_changed(QMediaPlayer.MediaStatus.EndOfMedia)
        splash._on_media_status_changed(QMediaPlayer.MediaStatus.EndOfMedia)
        self.assertEqual(finished_calls, [True])
        splash.close()

    def test_startup_video_and_login_share_the_main_window(self):
        window = MainWindow()
        window.show_startup_video()

        self.assertIs(window.stack.currentWidget(), window.startup_page)
        self.assertIs(window.startup_page.window(), window)
        self.assertFalse(window.startup_page.isWindow())

        window.startup_page.finished.emit()
        self.assertIs(window.stack.currentWidget(), window.auth_page)
        window.close()

    def test_startup_splash_can_be_skipped_with_escape(self):
        splash = StartupSplash()
        finished_calls = []
        splash.finished.connect(lambda: finished_calls.append(True))

        QTest.keyClick(splash.video_widget, Qt.Key.Key_Escape)

        self.assertEqual(finished_calls, [True])
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

        window._show_page(window.employee_page)
        self.assertIs(window.stack.currentWidget(), window.employee_page)
        self.assertIsNotNone(window._page_animation)
        self.assertGreater(window.employee_page.x(), 0)
        self.assertIsNotNone(window.employee_page.graphicsEffect())
        QTest.qWait(520)
        self.assertEqual(window.employee_page.pos().x(), 0)
        self.assertEqual(window.employee_page.pos().y(), 0)
        self.assertIsNone(window.employee_page.graphicsEffect())

        window._show_page(window.booking_page)
        self.assertGreater(window.booking_page.x(), 0)
        window._show_page(window.admin_page)
        self.assertIs(window.stack.currentWidget(), window.admin_page)
        QTest.qWait(400)
        self.assertEqual(window.admin_page.pos().x(), 0)
        self.assertEqual(window.admin_page.pos().y(), 0)
        self.assertIsNone(window.admin_page.graphicsEffect())
        window.close()

    def test_employee_dashboard_keeps_text_at_its_minimum_height(self):
        window = MainWindow()
        window.resize(1280, 820)
        window.show()
        window.stack.setCurrentWidget(window.employee_page)
        self.application.processEvents()

        self.assertIsInstance(window.employee_page, QScrollArea)
        title = window.findChild(QLabel, "employeeBookingTitle")
        description = window.findChild(QLabel, "employeeBookingDescription")
        self.assertGreaterEqual(title.height(), title.minimumSizeHint().height())
        self.assertGreaterEqual(
            description.height(),
            description.minimumSizeHint().height(),
        )
        self.assertGreater(window.employee_page.verticalScrollBar().maximum(), 0)
        window.close()

    def test_admin_employee_performance_rows_keep_text_readable(self):
        window = MainWindow()
        window.resize(1200, 768)
        window.show()
        window.stack.setCurrentWidget(window.admin_page)
        self.application.processEvents()
        rows = [
            {
                "employee_name": f"Employee {index}",
                "total_billed": 500,
                "bill_count": 6 - index,
            }
            for index in range(5)
        ]
        window.admin_widget._render_dashboard_employees(rows)
        self.application.processEvents()

        admin = window.admin_widget
        self.assertGreater(admin.dashboard_employee_scroll.verticalScrollBar().maximum(), 0)
        for index in range(admin.dashboard_employee_rows.count()):
            row = admin.dashboard_employee_rows.itemAt(index).widget()
            for label in row.findChildren(QLabel):
                self.assertGreaterEqual(
                    label.height(),
                    label.minimumSizeHint().height(),
                )
        window.close()

    def test_authentication_heading_is_ready_without_a_prelogin_splash(self):
        window = MainWindow()
        window.show()
        self.application.processEvents()

        self.assertEqual(window.stack.currentWidget(), window.auth_page)
        title = window.auth_page.findChild(QLabel, "authTitle")
        self.assertEqual(title.text(), "Sign in to MAYURICAFE")
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
