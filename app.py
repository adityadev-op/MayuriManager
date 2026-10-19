from pathlib import Path

from PySide6.QtWidgets import QApplication
from dotenv import load_dotenv

from Database_ import connection
from gui.main_window import MainWindow
from gui.startup_splash import StartupSplash


def main():
    project_root = Path(__file__).resolve().parent
    load_dotenv(project_root / ".env")
    load_dotenv(project_root / ".env.employees")
    load_dotenv(project_root / ".env.admins")
    app = QApplication([])
    app.setApplicationName("MAYURICAFE")
    app.aboutToQuit.connect(connection.close_database_connection)

    window = MainWindow()
    splash = StartupSplash()

    def open_login_page():
        window.show()
        splash.close()

    splash.finished.connect(open_login_page)
    splash.showFullScreen()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
