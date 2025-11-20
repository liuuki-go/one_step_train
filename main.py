import sys
from PySide6.QtWidgets import QApplication
from gui.main_frame import MainFrame
from PySide6.QtGui import QIcon



def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("gui/icon/system_icon.png"))
    w = MainFrame()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()