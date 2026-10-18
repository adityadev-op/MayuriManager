from pathlib import Path

from PySide6.QtWidgets import QApplication
from dotenv import load_dotenv

from Database_ import connection
from gui.main_window import MainWindow


def main():
    load_dotenv(Path(__file__).resolve().parent / ".env")
    app = QApplication([])
    app.setApplicationName("MAYURICAFE")
    app.aboutToQuit.connect(connection.close_database_connection)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
