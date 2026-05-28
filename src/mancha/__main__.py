import sys
from PySide6.QtWidgets import QApplication
from mancha.widgets.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Mancha")
    app.setApplicationVersion("0.5.0")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
