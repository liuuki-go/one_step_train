from operator import ge
import psutil
import subprocess
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QGridLayout
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import QRectF
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QProgressBar
from core.monitor import get_cpu_name, cpu_temperature, cpu_load, memory_load, memory_data
import random 


class RingGauge(QWidget):
    '''
    环形进度条
    '''
    def __init__(self, color: QColor):
        super().__init__()
        self._value = 0.0
        self._color = color
        self.setMinimumSize(60, 60)
        self.setMaximumSize(60, 60)
    def setValue(self, v: float):
        self._value = max(0.0, min(100.0, float(v)))
        self.update()
    def setColor(self, color: QColor):
        self._color = color
        self.update()
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        r = min(w, h) - 8
        rect = QRectF((w - r) / 2, (h - r) / 2, r, r)
        base = QPen(QColor(225, 228, 232), 10)
        p.setPen(base)
        p.drawArc(rect, 0, 360 * 16)
        pen = QPen(self._color, 10)
        p.setPen(pen)
        span = int(self._value / 100.0 * 360 * 16)
        p.drawArc(rect, 90 * 16, -span)
        p.setPen(QPen(QColor(51, 51, 51)))
        p.drawText(self.rect(), QtCore.Qt.AlignCenter, f"{self._value:.1f}%")

class MetricBlock(QWidget):
    '''
    指标块组件
    '''
    def __init__(self, title: str, icon, caption: str):
        super().__init__()
        self.setStyleSheet("QWidget{background:#f6f8fa;border:1px solid #e1e4e8;border-radius:10px;} QLabel{color:#333;}")
        root = QHBoxLayout(self)
        left = QVBoxLayout()
        top = QHBoxLayout()
        self.icon = QLabel()
        self.icon.setPixmap(icon.pixmap(30, 30))
        self.icon.setStyleSheet("QLabel{border:0;}")
        self.title = QLabel(title)
        self.title.setStyleSheet("QLabel{font-size:15px;font-weight:700;border:0;background:#f6f8fa;}")
        top.addWidget(self.icon)
        top.addWidget(self.title)
        top.addStretch(1)
        self.detail = QLabel("")
        self.detail.setStyleSheet("QLabel{font-size:12px;padding:1 2px;border:0;background:#f6f8fa;}")
        left.addLayout(top)
        self.extra = QLabel("")
        self.extra.setStyleSheet("QLabel{font-size:12px;padding:1 2px;border:0;background:#f6f8fa;}")
        left.addWidget(self.extra)
        row_width = 120
        self.util_row = QHBoxLayout()
        self.util_label = QLabel("利用率")
        self.util_label.setStyleSheet("QLabel{font-size:12px;padding:1 2px;border:0;background:#f6f8fa;}")
        self.util_bar = QProgressBar()
        self.util_bar.setRange(0, 100)
        self.util_bar.setTextVisible(True)
        self.util_bar.setFixedWidth(row_width)
        self.util_row.addWidget(self.util_label)
        self.util_row.addWidget(self.util_bar)
        left.addLayout(self.util_row)
        self.temp_row = QHBoxLayout()
        self.temp_label = QLabel("温度")
        self.temp_label.setStyleSheet("QLabel{font-size:12px;padding:1 2px;border:0;background:#f6f8fa;}")
        self.temp_bar = QProgressBar()
        self.temp_bar.setRange(0, 85)
        self.temp_bar.setTextVisible(True)
        self.temp_bar.setFixedWidth(row_width)
        self.temp_row.addWidget(self.temp_label)
        self.temp_row.addWidget(self.temp_bar)
        left.addLayout(self.temp_row)
        left.addWidget(self.detail)
        left.addStretch(1)
        root.addLayout(left, 1)
        gauge_box = QVBoxLayout();gauge_box.setContentsMargins(0, 20, 0, 0)
        self.gauge = RingGauge(QColor(3, 102, 214))
        self.gauge_title = QLabel(caption)
        self.gauge_title.setStyleSheet("QLabel{color:#666;}")
        gauge_box.addWidget(self.gauge, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        gauge_box.addWidget(self.gauge_title, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        root.addLayout(gauge_box)

    def _bar_color(self, v: float) -> str:
        if v < 55:
            return "#00a35a"
        if v < 80:
            return "#ffbf00"
        return "#dc0000"

    def _bar_color_temp(self, v: float) -> str:
        if v < 50:
            return "#00a35a"
        if v < 75:
            return "#ffbf00"
        return "#dc0000"

class cpu_monitor_widget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("QWidget{background:#f6f8fa;border:1px solid #e1e4e8;border-radius:10px;} QLabel{color:#333;}")
        root = QHBoxLayout(self)
        left = QVBoxLayout()
        top = QHBoxLayout()
        self.icon = QLabel()
        self.icon.setPixmap(QIcon("gui/icon/monitor_icon/host_cpu.png").pixmap(30, 30))
        self.icon.setStyleSheet("QLabel{border:0;}")
        self.cpu_name = QLabel(get_cpu_name() or "CPU")
        self.cpu_name.setStyleSheet("QLabel{font-size:15px;font-weight:700;border:0;background:#f6f8fa;}")
        top.addWidget(self.icon)
        top.addWidget(self.cpu_name)
        top.addStretch(1)
        left.addLayout(top)
        row_width = 120
        self.avg_row = QHBoxLayout();self.avg_row.setContentsMargins(0, 0, 0, 0);self.avg_row.setSpacing(3)
        self.avg_label = QLabel("平均温度")
        self.avg_label.setStyleSheet("QLabel{font-size:12px;padding:1 2px;border:0;background:#f6f8fa;}")
        self.avg_bar = QProgressBar()
        self.avg_bar.setRange(0, 85)
        self.avg_bar.setTextVisible(True)
        self.avg_bar.setFixedWidth(row_width)
        self.avg_row.addWidget(self.avg_label)
        self.avg_row.addWidget(self.avg_bar)
        left.addLayout(self.avg_row)
        self.max_row = QHBoxLayout()
        self.max_label = QLabel("最大温度")
        self.max_label.setStyleSheet("QLabel{font-size:12px;padding:1 2px;border:0;background:#f6f8fa;}")
        self.max_bar = QProgressBar()
        self.max_bar.setRange(0, 85)
        self.max_bar.setTextVisible(True)
        self.max_bar.setFixedWidth(row_width)
        self.max_row.addWidget(self.max_label)
        self.max_row.addWidget(self.max_bar)
        left.addLayout(self.max_row)
        self.load_row = QHBoxLayout()
        self.load_label = QLabel("CPU负载")
        self.load_label.setStyleSheet("QLabel{font-size:12px;padding:1 2px;border:0;background:#f6f8fa;}")
        self.load_bar = QProgressBar()
        self.load_bar.setRange(0, 100)
        self.load_bar.setTextVisible(True)
        self.load_bar.setFixedWidth(row_width)
        lv = random.randint(0, 15)
        self.load_bar.setValue(lv)
        color = self._bar_color("load", lv)
        self.load_bar.setStyleSheet(f"QProgressBar{{border:0px solid #e1e4e8;border-radius:6px;height:12px;background:#f5f6f8;}} QProgressBar::chunk{{background:{color};border-radius:6px;}}")
        
        self.load_row.addWidget(self.load_label)
        self.load_row.addWidget(self.load_bar)
        left.addLayout(self.load_row)
        root.addLayout(left, 1)

        right = QVBoxLayout();right.setContentsMargins(0, 20, 0, 0)
        self.gauge = RingGauge(QColor(3, 102, 214))
        self.gauge_title = QLabel("利用率")
        self.gauge_title.setStyleSheet("QLabel{color:#666;}")
        right.addWidget(self.gauge, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        right.addWidget(self.gauge_title, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        root.addLayout(right)
    def _bar_color(self, kind: str, v: float) -> str:
        if kind == "temp":
            if v < 50:
                return "#00a35a"
            if v < 75:
                return "#ffbf00"
            return "#dc0000"
        if kind == "load":
            if v < 55:
                return "#00a35a"
            if v < 80:
                return "#ffbf00"
            return "#dc0000"
        return "#0366d6"
    def refresh(self):
        # 温度
        t = cpu_temperature() or {"core_avg": None, "core_max": None}
        avg = t.get("core_avg")
        mx = t.get("core_max")
        av = float(avg) if isinstance(avg, (int, float)) else 0.0
        mv = float(mx) if isinstance(mx, (int, float)) else 0.0
        self.avg_bar.setValue(int(max(0, min(100, av))))
        ac = self._bar_color("temp", av)
        self.avg_bar.setStyleSheet(f"QProgressBar{{border:0px solid #e1e4e8;border-radius:6px;height:12px;background:#f5f6f8;font-weight:550;}} QProgressBar::chunk{{background:{ac};border-radius:6px;}}")
        self.avg_bar.setFormat(f"{av:.1f}°C" if isinstance(avg, (int, float)) else "-")
        self.max_bar.setValue(int(max(0, min(100, mv))))
        mc = self._bar_color("temp", mv)
        self.max_bar.setStyleSheet(f"QProgressBar{{border:0px solid #e1e4e8;border-radius:6px;height:12px;background:#f5f6f8;font-weight:550;}} QProgressBar::chunk{{background:{mc};border-radius:6px;}}")
        self.max_bar.setFormat(f"{mv:.1f}°C" if isinstance(mx, (int, float)) else "-")
        # 负载
        ld = cpu_load()
        lv = float(ld) if isinstance(ld, (int, float)) else 0.0
        self.load_bar.setValue(int(max(0, min(100, lv))))
        color = self._bar_color("load", lv)
        self.load_bar.setStyleSheet(f"QProgressBar{{border:0px solid #e1e4e8;border-radius:6px;height:12px;background:#f5f6f8;}} QProgressBar::chunk{{background:{color};border-radius:6px;}}")
        self.load_label.setText("CPU负载")
        self.load_bar.setFormat(f"{lv:.1f}%" if isinstance(ld, (int, float)) else "-")
        try:
            self.gauge.setValue(lv)
            if lv < 50:
                self.gauge.setColor(QColor(0, 155, 85))
            elif lv < 80:
                self.gauge.setColor(QColor(255, 191, 0))
            else:
                self.gauge.setColor(QColor(220, 0, 0))
        except Exception:
            pass

class memory_monitor_widget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("QWidget{background:#fff;border:1px solid #e1e4e8;border-radius:10px;} QLabel{color:#333;}")
        root = QHBoxLayout(self)
        left = QVBoxLayout()
        top = QHBoxLayout()
        self.icon = QLabel()
        self.icon.setPixmap(QIcon("gui/icon/monitor_icon/host_memory.png").pixmap(30, 30))
        self.icon.setStyleSheet("QLabel{border:0;}")
        self.title = QLabel("Generic Memory")
        self.title.setStyleSheet("QLabel{font-size:15px;font-weight:700;border:0;background:#f6f8fa;}")
        top.addWidget(self.icon)
        top.addWidget(self.title)
        top.addStretch(1)
        left.addLayout(top)
        row_width = 120
        self.v_row = QHBoxLayout()
        self.v_label = QLabel("虚拟负载")
        self.v_label.setStyleSheet("QLabel{font-size:12px;padding:1 2px;border:0;background:#f6f8fa;}")
        self.v_bar = QProgressBar()
        self.v_bar.setRange(0, 100)
        self.v_bar.setTextVisible(True)
        self.v_bar.setFixedWidth(row_width)
        self.v_row.addWidget(self.v_label)
        self.v_row.addWidget(self.v_bar)
        left.addLayout(self.v_row)

        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(2)
        self.grid.setVerticalSpacing(1)
        h0 = QLabel("")
        h1 = QLabel("使用量")
        h2 = QLabel("可用量")
        for w in (h0, h1, h2):
            w.setStyleSheet("QLabel{font-size:12px;padding:1 2px;border:0;background:#f6f8fa;}")
        self.grid.addWidget(h0, 0, 0)
        self.grid.addWidget(h1, 0, 1)
        self.grid.addWidget(h2, 0, 2)
        r1 = QLabel("物理")
        r2 = QLabel("虚拟")
        for w in (r1, r2):
            w.setStyleSheet("QLabel{font-size:12px;padding:1 2px;border:0;background:#f6f8fa;}")
        self.grid.addWidget(r1, 1, 0)
        self.grid.addWidget(r2, 2, 0)
        self.p_used = QLabel("-")
        self.p_avail = QLabel("-")
        self.v_used = QLabel("-")
        self.v_avail = QLabel("-")
        for w in (self.p_used, self.p_avail, self.v_used, self.v_avail):
            w.setStyleSheet("QLabel{font-size:12px;padding:1 2px;border:0;background:#f6f8fa;}")
        self.grid.addWidget(self.p_used, 1, 1)
        self.grid.addWidget(self.p_avail, 1, 2)
        self.grid.addWidget(self.v_used, 2, 1)
        self.grid.addWidget(self.v_avail, 2, 2)
        left.addLayout(self.grid)
        root.addLayout(left, 1)

        right = QVBoxLayout();right.setContentsMargins(0, 20, 0, 0)
        self.gauge = RingGauge(QColor(3, 102, 214))
        self.gauge_title = QLabel("占用率")
        self.gauge_title.setStyleSheet("QLabel{color:#666;}")
        right.addWidget(self.gauge, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        right.addWidget(self.gauge_title, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        root.addLayout(right)
    def _color_for(self, v: float) -> QColor:
        if v < 75:
            return QColor(0, 155, 85)
        if v < 90:
            return QColor(255, 191, 0)
        return QColor(220, 0, 0)
    def refresh(self):
        ld = memory_load() or {"physical": None, "virtual": None}
        phy = ld.get("physical")
        vir = ld.get("virtual")
        pv = float(phy) if isinstance(phy, (int, float)) else 0.0
        vv = float(vir) if isinstance(vir, (int, float)) else 0.0
        self.gauge.setValue(pv)
        self.gauge.setColor(self._color_for(pv))
        self.v_bar.setValue(int(max(0, min(100, vv))))
        self.v_bar.setStyleSheet(f"QProgressBar{{border:0px solid #e1e4e8;border-radius:6px;height:12px;background:#f5f6f8;}} QProgressBar::chunk{{background:{'#00a35a' if vv<80 else ('#ffbf00' if vv<90 else '#dc0000')};border-radius:6px;}}")
        self.v_bar.setFormat(f"{vv:.1f}%" if isinstance(vir, (int, float)) else "-")
        dt = memory_data() or {}
        mu = dt.get("memory_used")
        ma = dt.get("memory_available")
        vu = dt.get("virtual_used")
        va = dt.get("virtual_available")
        self.p_used.setText(f"{float(mu):.2f}GB" if isinstance(mu, (int, float)) else "-")
        self.p_avail.setText(f"{float(ma):.2f}GB" if isinstance(ma, (int, float)) else "-")
        self.v_used.setText(f"{float(vu):.2f}GB" if isinstance(vu, (int, float)) else "-")
        self.v_avail.setText(f"{float(va):.2f}GB" if isinstance(va, (int, float)) else "-")

class gpu_monitor_widget(QWidget):


    pass

class MonitorWidget(QWidget):
    """系统监控组件：显示 CPU/内存与 GPU 指标。
    - 顶部数值为 GPU 利用率；环形仪表显示显存使用率
    - 支持 NVML 与 nvidia-smi 两种查询路径
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        st = self.style()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.cpu_block = cpu_monitor_widget()
        self.mem_block = memory_monitor_widget()
        self.container_layout.addWidget(self.cpu_block)
        self.container_layout.addWidget(self.mem_block)
        self.gpu_blocks = []
        self.scroll.setWidget(self.container)
        v.addWidget(self.scroll)
        self.cpu_data = []
        self.mem_data = []
        self.gpu_data = []
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)
        self._init_nvml()
        self._build_gpu_blocks()
    def _query_cpu_freq_windows(self):
        try:
            r = subprocess.run(["wmic", "cpu", "get", "CurrentClockSpeed"], capture_output=True, text=True, timeout=2)
            if r.returncode == 0 and r.stdout:
                for ln in r.stdout.splitlines():
                    ln = ln.strip()
                    if ln.isdigit():
                        return float(ln) / 1000.0
        except Exception:
            pass
        return None
    def _init_nvml(self):
        try:
            import pynvml as nvml
            nvml.nvmlInit()
            self.nvml = nvml
            self.gpu_count = self.nvml.nvmlDeviceGetCount()
            self.gpu_handles = [self.nvml.nvmlDeviceGetHandleByIndex(i) for i in range(self.gpu_count)]
        except Exception:
            self.nvml = None
            self.gpu_count = 0
    def _build_gpu_blocks(self):
        st = self.style()
        if self.nvml and self.gpu_count > 0:
            for i in range(self.gpu_count):
                blk = MetricBlock(f"显卡 {i}", QIcon("gui\icon\monitor_icon\gpu.png"), "显存占用")
                self.gpu_blocks.append(blk)
                self.container_layout.addWidget(blk)
                try:
                    nm = self.nvml.nvmlDeviceGetName(self.gpu_handles[i])
                    nm = nm.decode() if isinstance(nm, bytes) else str(nm)
                    blk.extra.setText(nm)
                except Exception:
                    pass
        else:
            blk = MetricBlock("显卡", QIcon("gui\icon\monitor_icon\gpu.png"), "显存占用")
            self.gpu_blocks.append(blk)
            self.container_layout.addWidget(blk)
    def _ensure_gpu_blocks(self):
        st = self.style()
        if self.nvml and self.gpu_count > 0 and len(self.gpu_blocks) != self.gpu_count:
            for b in self.gpu_blocks:
                b.setParent(None)
            self.gpu_blocks = []
            for i in range(self.gpu_count):
                blk = MetricBlock(f"显卡 {i}", QIcon("gui\icon\monitor_icon\gpu.png"), "显存占用")
                self.gpu_blocks.append(blk)
                self.container_layout.addWidget(blk)
                try:
                    nm = self.nvml.nvmlDeviceGetName(self.gpu_handles[i])
                    nm = nm.decode() if isinstance(nm, bytes) else str(nm)
                    blk.extra.setText(nm)
                except Exception:
                    pass
        elif (not self.nvml or self.gpu_count == 0) and len(self.gpu_blocks) == 0:
            blk = MetricBlock("显卡", QIcon("gui\icon\monitor_icon\gpu.png"), "显存占用")
            self.gpu_blocks.append(blk)
            self.container_layout.addWidget(blk)
    def _query_smi_all(self):
        try:
            r = subprocess.run([
                "nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits"
            ], capture_output=True, text=True, timeout=2)
            if r.returncode == 0 and r.stdout.strip():
                return [ln.strip() for ln in r.stdout.strip().splitlines() if ln.strip()]
        except Exception:
            return []
        return []
    def _query_smi_names(self):
        try:
            r = subprocess.run([
                "nvidia-smi", "--query-gpu=name", "--format=csv,noheader"
            ], capture_output=True, text=True, timeout=2)
            if r.returncode == 0 and r.stdout.strip():
                return [ln.strip() for ln in r.stdout.strip().splitlines() if ln.strip()]
        except Exception:
            return []
        return []
    def _query_smi_by_id(self, i: int):
        try:
            r = subprocess.run([
                "nvidia-smi", "-i", str(i), "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits"
            ], capture_output=True, text=True, timeout=2)
            if r.returncode == 0 and r.stdout.strip():
                parts = [p.strip() for p in r.stdout.strip().split(',')]
                if len(parts) >= 4:
                    return float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
        except Exception:
            return None
        return None
    def refresh(self):
        cpu = psutil.cpu_percent(interval=None)
        freq = psutil.cpu_freq(percpu=False).current / 1000.0
        vm = psutil.virtual_memory()
        mem = vm.percent
        gpu = None
        gpu_mem_used = None
        gpu_mem_total = None
        gpu_temp = None
        self.cpu_data.append(cpu)
        self.mem_data.append(mem)
        self.gpu_data.append(gpu if gpu is not None else 0)
        if len(self.cpu_data) > 100:
            self.cpu_data = self.cpu_data[-100:]
            self.mem_data = self.mem_data[-100:]
            self.gpu_data = self.gpu_data[-100:]
        cpu_temp = None
        try:
            ts = psutil.sensors_temperatures()
            for k, vs in ts.items():
                for v in vs:
                    if "cpu" in v.label.lower() or "package" in v.label.lower():
                        cpu_temp = v.current
                        break
        except Exception:
            cpu_temp = None
        mem_used = vm.used / (1024**3)
        mem_total = vm.total / (1024**3)
        # 更新CPU监控组件
        try:
            self.cpu_block.refresh()
        except Exception:
            pass
        try:
            self.mem_block.refresh()
        except Exception:
            pass
        self._ensure_gpu_blocks()
        if self.nvml and self.gpu_count > 0:
            for i, h in enumerate(self.gpu_handles):
                gu = gm_u = gm_t = gt = None
                try:
                    try:
                        nm = self.nvml.nvmlDeviceGetName(h)
                        nm = nm.decode() if isinstance(nm, bytes) else str(nm)
                        self.gpu_blocks[i].extra.setText(nm)
                    except Exception:
                        pass
                    u = self.nvml.nvmlDeviceGetUtilizationRates(h)
                    gi = self.nvml.nvmlDeviceGetMemoryInfo(h)
                    gu = float(u.gpu)
                    gm_u = gi.used / (1024**2)
                    gm_t = gi.total / (1024**2)
                    gt = self.nvml.nvmlDeviceGetTemperature(h, self.nvml.NVML_TEMPERATURE_GPU)
                except Exception:
                    pass
                if gu is None or gm_u is None or gm_t is None or gt is None:
                    smi = self._query_smi_by_id(i)
                    if smi is not None:
                        s_gu, s_gm_u, s_gm_t, s_gt = smi
                        if gu is None:
                            gu = s_gu
                        if gm_u is None:
                            gm_u = s_gm_u
                        if gm_t is None:
                            gm_t = s_gm_t
                        if gt is None:
                            gt = s_gt
                blk = self.gpu_blocks[i]
                mem_pct = 0.0
                if gm_u is not None and gm_t not in (None, 0):
                    mem_pct = float(gm_u) / float(gm_t) * 100.0
                gu_v = float(gu) if gu is not None else 0.0
                blk.util_bar.setValue(int(max(0, min(100, gu_v))))
                bc = blk._bar_color(gu_v)
                blk.util_bar.setStyleSheet(f"QProgressBar{{border:0px solid #e1e4e8;border-radius:6px;height:12px;background:#f5f6f8;}} QProgressBar::chunk{{background:{bc};border-radius:6px;}}")
                blk.util_bar.setFormat(f"{gu_v:.1f}%")
                tv = float(gt) if gt is not None else 0.0
                blk.temp_bar.setValue(int(max(0, min(85, tv))))
                tc = blk._bar_color_temp(tv)
                blk.temp_bar.setStyleSheet(f"QProgressBar{{border:0px solid #e1e4e8;border-radius:6px;height:12px;background:#f5f6f8;}} QProgressBar::chunk{{background:{tc};border-radius:6px;}}")
                blk.temp_bar.setFormat(f"{tv:.1f}°C" if gt is not None else "-")
                blk.gauge.setValue(mem_pct)
                blk.gauge.setColor(self._color_for("mem", mem_pct))
                det = []
                if gm_u is not None and gm_t is not None:
                    det.append(f"{gm_u:.0f}MB/{gm_t:.0f}MB")
                blk.detail.setText("  ".join(det))
            return
        if gpu is None:
            try:
                lines = self._query_smi_all()
                names = self._query_smi_names()
                while len(self.gpu_blocks) < len(lines):
                    nb = MetricBlock(f"显卡 {len(self.gpu_blocks)}", QIcon("gui\icon\monitor_icon\gpu.png"), "显存使用率")
                    self.gpu_blocks.append(nb)
                    self.container_layout.addWidget(nb)
                for i, ln in enumerate(lines):
                    parts = [p.strip() for p in ln.split(',')]
                    if len(parts) >= 4:
                        gu = float(parts[0])
                        gm_u = float(parts[1])
                        gm_t = float(parts[2])
                        gt = float(parts[3])
                        blk = self.gpu_blocks[i]
                        blk.title.setText(f"显卡 {i}")
                        if i < len(names):
                            blk.extra.setText(names[i])
                        mem_pct = 0.0
                        if gm_t not in (None, 0):
                            mem_pct = gm_u / gm_t * 100.0
                        blk.util_bar.setValue(int(max(0, min(100, gu))))
                        bc = blk._bar_color(gu)
                        blk.util_bar.setStyleSheet(f"QProgressBar{{border:0px solid #e1e4e8;border-radius:6px;height:12px;background:#f5f6f8;}} QProgressBar::chunk{{background:{bc};border-radius:6px;}}")
                        blk.util_bar.setFormat(f"{gu:.1f}%")
                        tv = float(gt) if gt is not None else 0.0
                        blk.temp_bar.setValue(int(max(0, min(85, tv))))
                        tc = blk._bar_color_temp(tv)
                        blk.temp_bar.setStyleSheet(f"QProgressBar{{border:0px solid #e1e4e8;border-radius:6px;height:12px;background:#f5f6f8;}} QProgressBar::chunk{{background:{tc};border-radius:6px;}}")
                        blk.temp_bar.setFormat(f"{tv:.1f}°C" if gt is not None else "-")
                        blk.gauge.setValue(mem_pct)
                        blk.gauge.setColor(self._color_for("mem", mem_pct))
                        det = [f"{gm_u:.0f}MB/{gm_t:.0f}MB"]
                        blk.detail.setText("  ".join(det))
            except Exception:
                pass
    def _color_for(self, kind: str, v: float) -> QColor:
        if kind in ("cpu", "mem"):
            if v < 50:
                return QColor(0, 155, 85)
            if v < 80:
                return QColor(255, 191, 0)
            return QColor(220, 0, 0)
        if kind == "gpu":
            if v > 80:
                return QColor(3, 102, 214)
            if v < 50:
                return QColor(0, 155, 85)
            return QColor(255, 191, 0)
        return QColor(3, 102, 214)