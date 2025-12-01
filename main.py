import sys
from PySide6.QtWidgets import QApplication
from gui.main_frame import MainFrame
from PySide6.QtGui import QIcon
from core.monitor import Monitor
from core.monitor import shutdown as monitor_shutdown
import os
import ctypes

"""
本文件负责应用入口、管理员权限自提升以及隐藏控制台窗口：

1) 管理员权限自提升（_ensure_admin）：
   - 使用 ShellExecuteW 的 "runas" 动词请求 UAC 提升；
   - 以当前 Python 解释器（sys.executable）重新启动本脚本，并附加标记 "--elevated"；
   - 原进程在发起提升后立即退出，避免重复启动造成闪烁；
   - 新进程检测到 "--elevated" 标记后不再自提升，直接进入主流程。

2) 隐藏控制台窗口（main）：
   - 对于从命令行启动的 python.exe，会附带一个控制台窗口；
   - 通过 GetConsoleWindow() 获取控制台句柄，调用 ShowWindow(hwnd, 0) 将其隐藏；
   - 隐藏只是将窗口不可见，不会关闭进程或影响后续 GUI 运行。
"""







def main():
    """主函数，启动Libre Hardware Monitor并初始化GUI"""
    # 隐藏控制台窗口：
    # - 某些场景从命令行启动会出现黑色控制台；用户只需看到 GUI，因此将其隐藏。
    # - 如果没有控制台（例如以 pythonw.exe 启动），GetConsoleWindow 会返回 0，这里安全忽略。
    # try:
    #     hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    #     if hwnd:
    #         ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE = 0，将控制台窗口隐藏
    # except Exception:
    #     pass
    monitor = Monitor()
    if not monitor.is_running:
        print("Libre Hardware Monitor启动失败，程序退出")
        

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("gui/icon/system_icon.png"))
    try:
        app.aboutToQuit.connect(monitor_shutdown)
    except Exception:
        pass
    w = MainFrame()
    w.show()
    sys.exit(app.exec())

def _ensure_admin():
    try:
        # 防重复：提升后的新进程会带上 "--elevated" 标记，避免再次自提升导致循环
        if "--elevated" in sys.argv:
            return
        # 判断当前是否管理员上下文；非管理员则发起 UAC 提升
        if not bool(ctypes.windll.shell32.IsUserAnAdmin()):
            exe = sys.executable  # 使用当前 Python 解释器启动（可为 python.exe 或打包后的 exe）
            script = os.path.abspath(__file__)  # 当前入口脚本绝对路径
            params = f'"{script}" --elevated'  # 传入标记，提升后不再重复自提升
            # ShellExecuteW 参数说明：
            # - 第1参：父窗口句柄（None）
            # - 动词："runas"（请求管理员权限）
            # - 文件：解释器路径（exe）
            # - 参数：脚本路径 + 标记
            # - 目录：None（使用默认）
            # - 显示：1（SW_SHOWNORMAL，不影响随后在 main 中隐藏控制台）
            ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
            # 关键：发起提升后立刻退出当前进程，避免原进程继续运行造成 GUI 闪烁
            sys.exit(0)
    except Exception:
        pass

if __name__ == "__main__":
    # 入口：如非管理员则尝试自提升；已提升或带标记时直接进入主流程
    # if "--elevated" not in sys.argv:
    #     _ensure_admin()
    main()
