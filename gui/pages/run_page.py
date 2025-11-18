from PySide6 import QtWidgets
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from tools.sys_config_tools import get_wsl_config

class RunPageWidget(QWidget):
    """训练运行页：采集数据集路径与 Conda 基路径，并发出运行请求。"""
    runRequested = Signal(str, str)
    def __init__(self):
        super().__init__()
        form = QGridLayout(self)
        self.lbl_yaml = QLabel("数据集文件夹")
        self.ed_yaml = QLineEdit()
        b1 = QPushButton("选择"); b1.clicked.connect(self._pick_yaml_dir)
        form.addWidget(self.lbl_yaml, 0, 0)
        form.addWidget(self.ed_yaml, 0, 1)
        form.addWidget(b1, 0, 2)
        self.btn_run_train = QPushButton("开始训练")
        self.btn_run_train.clicked.connect(self._emit_run)
        form.addWidget(self.btn_run_train, 2, 1)
    def _pick_yaml_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择数据集文件夹")
        if d:
            self.ed_yaml.setText(d)
    def _emit_run(self):
        dp = self.ed_yaml.text().strip()
        cfg = get_wsl_config()
        conda_base = ""
        try:
            if isinstance(cfg.get("conda"), dict):
                conda_base = str(cfg["conda"].get("env_path", "")).strip()
        except Exception:
            conda_base = ""
        self.runRequested.emit(dp, conda_base)