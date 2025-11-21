import psutil
import subprocess
import time
import os
import ctypes



LHM_EXE_PATH = r"core/LibreHardwareMonitor/LibreHardwareMonitor.exe" 
LHM_PROCESS_NAME = "LibreHardwareMonitor.exe"

class Monitor:
    def __init__(self):
        self.is_running = False
        self._start_lhm()

    def _is_admin(self):
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    def _start_lhm(self):
        """自动启动Libre Hardware Monitor，后台运行（无窗口）"""
        try:
            # 检查是否已启动，避免重复运行
            for proc in psutil.process_iter(["name"]):
                if proc.info["name"] == LHM_PROCESS_NAME:
                    print("Libre Hardware Monitor已后台运行")
                    self.is_running = True
                    return True
            # 启动exe，设置creationflags实现后台无窗口运行
            exe = os.path.abspath(LHM_EXE_PATH)
            if not self._is_admin():
                rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, None, None, 0)
                if rc <= 32:
                    raise OSError("elevation failed")
            else:
                subprocess.Popen(exe, creationflags=subprocess.CREATE_NO_WINDOW)
            print("正在启动Libre Hardware Monitor...")
            time.sleep(3)  # 等待3秒，让程序完成初始化（关键：否则COM接口调用失败）
            self.is_running = True
            return True
        except Exception as e:
            print(f"启动失败: {e}")
            self.is_running = False
            return False

