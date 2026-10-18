from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from dotenv import load_dotenv

from Database_ import connection
from gui.main_window import MainWindow
from gui.startup_splash import StartupSplash


def main():
    load_dotenv(Path(__file__).resolve().parent / ".env")
    app = QApplication([])
    app.setApplicationName("MAYURICAFE")
    app.aboutToQuit.connect(connection.close_database_connection)

    window = MainWindow()
    try:
        connection.get_connection()
    except ConnectionError as error:
        QMessageBox.critical(
            window,
            "Database connection failed",
            f"Could not connect to the MAYURICAFE database: {error}",
        )
        return 1

    splash = StartupSplash()

    def finish_startup():
        splash.close()
        window.show()

    splash.logo_animation.finished.connect(finish_startup)
    splash.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
