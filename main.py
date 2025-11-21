import sys
from PySide6.QtWidgets import QApplication
from gui.main_frame import MainFrame
from PySide6.QtGui import QIcon
from core.monitor import Monitor







def main():
    """主函数，启动Libre Hardware Monitor并初始化GUI"""
    monitor = Monitor()
    if not monitor.is_running:
        print("Libre Hardware Monitor启动失败，程序退出")
        

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("gui/icon/system_icon.png"))
    w = MainFrame()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()