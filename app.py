from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from dotenv import load_dotenv

from Database_ import connection
from gui.main_window import MainWindow


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

    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
