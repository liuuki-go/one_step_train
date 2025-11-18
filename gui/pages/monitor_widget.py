import psutil
import subprocess
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import QRectF

class RingGauge(QWidget):
    def __init__(self, color: QColor):
        super().__init__()
        self._value = 0.0
        self._color = color
        self.setMinimumSize(100, 100)
        self.setMaximumSize(120, 120)
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
    def __init__(self, title: str, icon, caption: str):
        super().__init__()
        self.setStyleSheet("QWidget{background:#fff;border:1px solid #e1e4e8;border-radius:10px;} QLabel{color:#333;}")
        root = QHBoxLayout(self)
        left = QVBoxLayout()
        top = QHBoxLayout()
        self.icon = QLabel()
        self.icon.setPixmap(icon.pixmap(18, 18))
        self.title = QLabel(title)
        self.title.setStyleSheet("QLabel{font-weight:600;}")
        top.addWidget(self.icon)
        top.addWidget(self.title)
        top.addStretch(1)
        self.value = QLabel("-")
        self.value.setStyleSheet("QLabel{font-size:18px;padding:0 8px;}")
        self.detail = QLabel("")
        self.detail.setStyleSheet("QLabel{color:#666;padding:0 8px 8px;}")
        left.addLayout(top)
        left.addWidget(self.value)
        left.addWidget(self.detail)
        left.addStretch(1)
        root.addLayout(left, 1)
        gauge_box = QVBoxLayout()
        self.gauge = RingGauge(QColor(3, 102, 214))
        self.gauge_title = QLabel(caption)
        self.gauge_title.setStyleSheet("QLabel{color:#666;}")
        gauge_box.addWidget(self.gauge, alignment=QtCore.Qt.AlignCenter)
        gauge_box.addWidget(self.gauge_title, alignment=QtCore.Qt.AlignCenter)
        root.addLayout(gauge_box)

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
        self.cpu_block = MetricBlock("CPU", st.standardIcon(QtWidgets.QStyle.SP_ComputerIcon), "CPU使用率")
        self.mem_block = MetricBlock("内存", st.standardIcon(QtWidgets.QStyle.SP_DriveHDIcon), "内存使用率")
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
                blk = MetricBlock(f"GPU {i}", st.standardIcon(QtWidgets.QStyle.SP_MediaVolume), "显存使用率")
                self.gpu_blocks.append(blk)
                self.container_layout.addWidget(blk)
        else:
            blk = MetricBlock("GPU", st.standardIcon(QtWidgets.QStyle.SP_MediaVolume), "显存使用率")
            self.gpu_blocks.append(blk)
            self.container_layout.addWidget(blk)
    def _ensure_gpu_blocks(self):
        st = self.style()
        if self.nvml and self.gpu_count > 0 and len(self.gpu_blocks) != self.gpu_count:
            for b in self.gpu_blocks:
                b.setParent(None)
            self.gpu_blocks = []
            for i in range(self.gpu_count):
                blk = MetricBlock(f"GPU {i}", st.standardIcon(QtWidgets.QStyle.SP_MediaVolume), "显存使用率")
                self.gpu_blocks.append(blk)
                self.container_layout.addWidget(blk)
        elif (not self.nvml or self.gpu_count == 0) and len(self.gpu_blocks) == 0:
            blk = MetricBlock("GPU", st.standardIcon(QtWidgets.QStyle.SP_MediaVolume), "显存使用率")
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
        self.cpu_block.value.setText(f"CPU利用率：{cpu:.1f}%")
        self.cpu_block.gauge.setValue(cpu)
        self.cpu_block.gauge.setColor(self._color_for("cpu", cpu))
        cores = psutil.cpu_count(logical=True) or 0
        freq = None
        try:
            freq = self._query_cpu_freq_windows()
            if freq is None:
                fr = psutil.cpu_freq()
                if fr:
                    freq = fr.current / 1000.0
        except Exception:
            freq = None
        freq_txt = f"{freq:.2f}GHz" if isinstance(freq, float) else "-"
        self.cpu_block.detail.setText(f"核心数 {cores} | 频率 {freq_txt}")
        self.mem_block.value.setText(f"内存使用率：{mem:.1f}%")
        self.mem_block.gauge.setValue(mem)
        self.mem_block.gauge.setColor(self._color_for("mem", mem))
        self.mem_block.detail.setText(f"{mem_used:.2f}GB / {mem_total:.2f}GB")
        self._ensure_gpu_blocks()
        if self.nvml and self.gpu_count > 0:
            for i, h in enumerate(self.gpu_handles):
                gu = gm_u = gm_t = gt = None
                try:
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
                blk.value.setText(f"GPU利用率：{gu_v:.1f}%")
                blk.gauge.setValue(mem_pct)
                blk.gauge.setColor(self._color_for("mem", mem_pct))
                det = []
                if gm_u is not None and gm_t is not None:
                    det.append(f"{gm_u:.0f}MB/{gm_t:.0f}MB")
                if gt is not None:
                    det.append(f"{gt:.0f}°C")
                blk.detail.setText("  ".join(det))
            return
        if gpu is None:
            try:
                lines = self._query_smi_all()
                while len(self.gpu_blocks) < len(lines):
                    st = self.style()
                    nb = MetricBlock(f"GPU {len(self.gpu_blocks)}", st.standardIcon(QtWidgets.QStyle.SP_MediaVolume), "显存使用率")
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
                        blk.title.setText(f"GPU {i}")
                        mem_pct = 0.0
                        if gm_t not in (None, 0):
                            mem_pct = gm_u / gm_t * 100.0
                        blk.value.setText(f"GPU利用率：{gu:.1f}%")
                        blk.gauge.setValue(mem_pct)
                        blk.gauge.setColor(self._color_for("mem", mem_pct))
                        det = [f"{gm_u:.0f}MB/{gm_t:.0f}MB", f"{gt:.0f}°C"]
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