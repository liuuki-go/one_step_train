import sys
from PySide6.QtWidgets import QApplication
from gui.main_frame import MainFrame


def main():
    app = QApplication(sys.argv)
    w = MainFrame()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()