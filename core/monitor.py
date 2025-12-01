import psutil
import subprocess
import time
import os
import ctypes
import threading

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
        try:
            # Check if LHM is already running
            for proc in psutil.process_iter(["name"]):
                if proc.info["name"] == LHM_PROCESS_NAME:
                    self.is_running = True
                    return True
            exe = os.path.abspath(LHM_EXE_PATH)
            if not self._is_admin():
                rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, None, None, 0)
                if rc <= 32:
                    raise OSError("elevation failed")
            else:
                subprocess.Popen(exe, creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(2)
            self.is_running = True
            return True
        except Exception:
            self.is_running = False
            return False

_CLIENT = None
_CLIENT_LOCK = threading.RLock()
_SAMPLER_THREAD = None
_SAMPLER_PERIOD = 3.0
_PSUTIL_LAST = None
_STOP_EVENT = threading.Event()

def _get_client():
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    try:
        import clr
        dll_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "LibreHardwareMonitor"))
        dll = os.path.join(dll_dir, "LibreHardwareMonitorLib.dll")
        from System.Reflection import Assembly
        Assembly.LoadFrom(dll)
        from LibreHardwareMonitor.Hardware import Computer, HardwareType, SensorType
        c = Computer()
        c.IsCpuEnabled = True
        c.IsMemoryEnabled = True
        c.Open()
        _CLIENT = (c, HardwareType, SensorType)
        _ensure_sampler()
        return _CLIENT
    except Exception:
        return None

def _update_all_once():
    if _CLIENT is None:
        return
    c, _, _ = _CLIENT
    try:
        for hw in list(c.Hardware):
            hw.Update()
            for shw in list(hw.SubHardware):
                shw.Update()
    except Exception:
        pass

def _ensure_sampler():
    global _SAMPLER_THREAD, _PSUTIL_LAST
    if _SAMPLER_THREAD is not None:
        return
    def _loop():
        global _PSUTIL_LAST
        try:
            _PSUTIL_LAST = psutil.cpu_percent(interval=_SAMPLER_PERIOD)
        except Exception:
            _PSUTIL_LAST = None
        while not _STOP_EVENT.is_set():
            try:
                with _CLIENT_LOCK:
                    _update_all_once()
                try:
                    _PSUTIL_LAST = psutil.cpu_percent(interval=None)
                except Exception:
                    pass
            except Exception:
                pass
            time.sleep(_SAMPLER_PERIOD)
    t = threading.Thread(target=_loop, name="lhm-sampler", daemon=True)
    _SAMPLER_THREAD = t
    t.start()

def shutdown():
    try:
        _STOP_EVENT.set()
    except Exception:
        pass
    try:
        if _SAMPLER_THREAD is not None:
            _SAMPLER_THREAD.join(timeout=_SAMPLER_PERIOD + 1.0)
    except Exception:
        pass
    try:
        if _CLIENT is not None:
            c, _, _ = _CLIENT
            try:
                c.Close()
            except Exception:
                pass
    except Exception:
        pass
    try:
        with _CLIENT_LOCK:
            globals()["_CLIENT"] = None
            globals()["_SAMPLER_THREAD"] = None
    except Exception:
        pass

def get_cpu_name():
    cl = _get_client()
    if cl is None:
        return None
    c, HT, _ = cl
    # 名称无需刷新，直接读取
    for hw in list(c.Hardware):
        if hw.HardwareType == HT.Cpu:
            return str(hw.Name)
    return None

def cpu_temperature():
    cl = _get_client()
    if cl is None:
        return None
    c, HT, ST = cl
    # 读取聚合与核心温度，不进行阻塞刷新
    avg = None
    mx = None
    cores = []
    def _scan(hw):
        nonlocal avg, mx, cores
        for s in list(hw.Sensors):
            if s.SensorType == ST.Temperature and s.Value is not None:
                n = str(s.Name)
                v = float(s.Value)
                if n.lower().strip() == "core average":
                    avg = v
                elif n.lower().strip() == "core max":
                    mx = v
                elif n.startswith("CPU Core") or ("Core" in n and "#" in n):
                    cores.append(v)
    for hw in list(c.Hardware):
        if hw.HardwareType == HT.Cpu:
            with _CLIENT_LOCK:
                _scan(hw)
                for shw in list(hw.SubHardware):
                    _scan(shw)
            break
    if avg is None and cores:
        avg = sum(cores) / len(cores)
    if mx is None and cores:
        try:
            mx = max(cores)
        except Exception:
            mx = None
    return {"core_avg": avg, "core_max": mx}

def cpu_load():
    cl = _get_client()
    if cl is None:
        return None
    cpu_util = psutil.cpu_percent(interval=None)
    c, HT, ST = cl
    total = None
    total = None
    per_core = []
    for hw in list(c.Hardware):
        if hw.HardwareType == HT.Cpu:
            with _CLIENT_LOCK:
                for s in list(hw.Sensors):
                    if s.SensorType == ST.Load and s.Value is not None:
                        n = str(s.Name)
                        v = float(s.Value)
                        if "Total" in n:
                            total = v
                        elif "Core" in n:
                            per_core.append(v)
                for shw in list(hw.SubHardware):
                    for s in list(shw.Sensors):
                        if s.SensorType == ST.Load and s.Value is not None:
                            n = str(s.Name)
                            v = float(s.Value)
                            if "Total" in n:
                                total = v
                            elif "Core" in n:
                                per_core.append(v)
            break
    if (total is None or (isinstance(total, float) and total == 0.0)) and per_core:
        total = sum(per_core) / len(per_core)
    if total is None or (isinstance(total, float) and total == 0.0):
        total = _PSUTIL_LAST
   

    return total, cpu_util

def cpu_clocks():
    cl = _get_client()
    if cl is None:
        return None
    c, HT, ST = cl
    cores = []
    cores = []
    for hw in list(c.Hardware):
        if hw.HardwareType == HT.Cpu:
            with _CLIENT_LOCK:
                for s in list(hw.Sensors):
                    if s.SensorType == ST.Clock and s.Value is not None:
                        n = str(s.Name)
                        if "Core" in n:
                            cores.append(float(s.Value))
                for shw in list(hw.SubHardware):
                    for s in list(shw.Sensors):
                        if s.SensorType == ST.Clock and s.Value is not None:
                            n = str(s.Name)
                            if "Core" in n:
                                cores.append(float(s.Value))
            break
    if not cores:
        return {"cores": [], "average": None}
    return {"cores": cores, "average": sum(cores) / len(cores)}

def cpu_power():
    cl = _get_client()
    if cl is None:
        return None
    c, HT, ST = cl
    pkg = None
    for hw in list(c.Hardware):
        if hw.HardwareType == HT.Cpu:
            with _CLIENT_LOCK:
                for s in list(hw.Sensors):
                    if s.SensorType == ST.Power and s.Value is not None:
                        n = str(s.Name)
                        if "Package" in n:
                            pkg = float(s.Value)
                for shw in list(hw.SubHardware):
                    for s in list(shw.Sensors):
                        if s.SensorType == ST.Power and s.Value is not None:
                            n = str(s.Name)
                            if "Package" in n:
                                pkg = float(s.Value)
            break
    return pkg

def memory_load():
    cl = _get_client()
    if cl is None:
        return None
    c, HT, ST = cl
    phy = None
    vmem = None
    for hw in list(c.Hardware):
        if hw.HardwareType == HT.Memory or str(hw.Name).lower().startswith("generic memory"):
            with _CLIENT_LOCK:
                for s in list(hw.Sensors):
                    if s.SensorType == ST.Load and s.Value is not None:
                        n = str(s.Name)
                        v = float(s.Value)
                        if "Virtual" in n:
                            vmem = v
                        elif "Memory" in n:
                            phy = v
                for shw in list(hw.SubHardware):
                    for s in list(shw.Sensors):
                        if s.SensorType == ST.Load and s.Value is not None:
                            n = str(s.Name)
                            v = float(s.Value)
                            if "Virtual" in n:
                                vmem = v
                            elif "Memory" in n:
                                phy = v
            if (phy is None and vmem is None):
                with _CLIENT_LOCK:
                    _update_all_once()
                    for s in list(hw.Sensors):
                        if s.SensorType == ST.Load and s.Value is not None:
                            n = str(s.Name)
                            v = float(s.Value)
                            if "Virtual" in n:
                                vmem = v
                            elif "Memory" in n:
                                phy = v
                    for shw in list(hw.SubHardware):
                        for s in list(shw.Sensors):
                            if s.SensorType == ST.Load and s.Value is not None:
                                n = str(s.Name)
                                v = float(s.Value)
                                if "Virtual" in n:
                                    vmem = v
                                elif "Memory" in n:
                                    phy = v
            break
    return {"physical": phy, "virtual": vmem}

def memory_data():
    cl = _get_client()
    if cl is None:
        return None
    c, HT, ST = cl
    used = avail = vused = vavail = None
    for hw in list(c.Hardware):
        if hw.HardwareType == HT.Memory or str(hw.Name).lower().startswith("generic memory"):
            with _CLIENT_LOCK:
                for s in list(hw.Sensors):
                    if s.SensorType == ST.Data and s.Value is not None:
                        n = str(s.Name)
                        v = float(s.Value)
                        if "Virtual Memory Used" in n:
                            vused = v
                        elif "Virtual Memory Available" in n:
                            vavail = v
                        elif "Memory Used" in n:
                            used = v
                        elif "Memory Available" in n:
                            avail = v
                for shw in list(hw.SubHardware):
                    for s in list(shw.Sensors):
                        if s.SensorType == ST.Data and s.Value is not None:
                            n = str(s.Name)
                            v = float(s.Value)
                            if "Virtual Memory Used" in n:
                                vused = v
                            elif "Virtual Memory Available" in n:
                                vavail = v
                            elif "Memory Used" in n:
                                used = v
                            elif "Memory Available" in n:
                                avail = v
            if used is None and avail is None and vused is None and vavail is None:
                with _CLIENT_LOCK:
                    _update_all_once()
                    for s in list(hw.Sensors):
                        if s.SensorType == ST.Data and s.Value is not None:
                            n = str(s.Name)
                            v = float(s.Value)
                            if "Virtual Memory Used" in n:
                                vused = v
                            elif "Virtual Memory Available" in n:
                                vavail = v
                            elif "Memory Used" in n:
                                used = v
                            elif "Memory Available" in n:
                                avail = v
                    for shw in list(hw.SubHardware):
                        for s in list(shw.Sensors):
                            if s.SensorType == ST.Data and s.Value is not None:
                                n = str(s.Name)
                                v = float(s.Value)
                                if "Virtual Memory Used" in n:
                                    vused = v
                                elif "Virtual Memory Available" in n:
                                    vavail = v
                                elif "Memory Used" in n:
                                    used = v
                                elif "Memory Available" in n:
                                    avail = v
            break
    return {
        "memory_used": used,
        "memory_available": avail,
        "virtual_used": vused,
        "virtual_available": vavail,
    }


if __name__ == "__main__":
    m = Monitor()
    print(get_cpu_name())
    print(cpu_temperature())
    print(cpu_load())
    print(cpu_clocks())
    print(cpu_power())
    print(memory_load())
    print(memory_data())
