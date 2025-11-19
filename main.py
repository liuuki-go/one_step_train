import sys
from PySide6.QtWidgets import QApplication
from gui.main_frame import MainFrame
from PySide6.QtGui import QIcon
from qt_material import apply_stylesheet
import qdarkstyle


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("gui/icon/system_icon.png"))
    # Apply a built-in theme
    # apply_stylesheet(app, theme='light_lightgreen.xml', invert_secondary=True)
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyside6())
    w = MainFrame()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()