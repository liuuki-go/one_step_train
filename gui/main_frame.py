import os
import sys
import yaml
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QStackedWidget
from PySide6.QtCore import QThread, Signal
from core.dataset_builder import build_yolo_dataset
from core.wsl_runner import build_train_cmd, run_stream
from gui.pages.monitor_widget import MonitorWidget
from gui.sys_settings_dialog import SystemSettingsDialog as SysSettingsDialog
from gui.pages.run_page import RunPageWidget
from gui.pages.build_page import BuildPageWidget
from gui.pages.config_page import ConfigPageWidget
from gui.components.app_menu import setup_menu
from gui.pages.one_click_page import OneClickPageWidget

class LogThread(QThread):
    line = Signal(str)
    done = Signal(int)
    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd
    def run(self):
        rc = run_stream(self.cmd, lambda s: self.line.emit(s))
        self.done.emit(rc)

class MainFrame(QMainWindow):
    """主框架：只负责页面路由与信号接线，业务逻辑下沉到各页面或 core 模块。"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("一键训练")
        self.resize(1200, 800)
        self._init_ui()
        self.dataset_root = None
        self.dataset_yaml = None
        self.log_thread = None
    
    def _on_page_changed(self, idx):
        self.console.setVisible(idx != 3)
    
    
    
    
    def _init_ui(self):
        cw = QWidget()
        self.setCentralWidget(cw)
        root = QHBoxLayout(cw)
        left_container = QWidget()
        left_container.setStyleSheet("QWidget{background:#f6f8fa;border-right:1px solid #e1e4e8;}")
        left = QVBoxLayout(left_container)
        center = QVBoxLayout()
        right = QVBoxLayout()
        left_container.setFixedWidth(160)
        root.addWidget(left_container, 1)
        root.addLayout(center, 2)
        root.addLayout(right, 1)
        setup_menu(self, self._open_sys_settings, self._set_lang)
        btn_one = QPushButton("一键训练")
        btn_build = QPushButton("数据集构建")
        btn_run = QPushButton("开始训练")
        btn_cfg = QPushButton("训练配置")
        st = self.style()
        btn_one.setIcon(st.standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        btn_build.setIcon(st.standardIcon(QtWidgets.QStyle.SP_DirIcon))
        btn_run.setIcon(st.standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        btn_cfg.setIcon(st.standardIcon(QtWidgets.QStyle.SP_FileDialogDetailedView))
        for b in (btn_one, btn_build, btn_run, btn_cfg):
            b.setCheckable(True)
            b.setStyleSheet(
                "QPushButton{font-size:16px;padding:12px 14px;text-align:left;border-radius:10px;}"
                "QPushButton:checked{background:#e6f0ff;color:#0366d6;}"
                "QPushButton:hover{background:#f0f6ff;}"
            )
        left.addWidget(btn_one)
        left.addWidget(btn_build)
        left.addWidget(btn_run)
        left.addWidget(btn_cfg)
        left.addStretch(1)
        group = QtWidgets.QButtonGroup(self)
        group.setExclusive(True)
        for i, b in enumerate((btn_one, btn_build, btn_run, btn_cfg)):
            group.addButton(b, i)
        btn_one.setChecked(True)
        group.idClicked.connect(lambda i: self.stack.setCurrentIndex(i))
        self.stack = QStackedWidget()
        center.addWidget(self.stack)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setLineWrapMode(QTextEdit.NoWrap)
        self.console.setStyleSheet('QTextEdit{font-family:Consolas, "Courier New", monospace; font-size:12px;}')
        center.addWidget(self.console)
        self.page_one = OneClickPageWidget()
        self.page_build = BuildPageWidget()
        self.page_run = RunPageWidget()
        self.page_cfg = ConfigPageWidget()
        self.stack.addWidget(self.page_one)
        self.stack.addWidget(self.page_build)
        self.stack.addWidget(self.page_run)
        self.stack.addWidget(self.page_cfg)
        # idClicked handles switching
        self.stack.currentChanged.connect(self._on_page_changed)
        self.monitor = MonitorWidget()
        right.addWidget(self.monitor)
        try:
            cfg = yaml.safe_load(open(os.path.join(os.getcwd(), "sys_config.yaml"), "r", encoding="utf-8")) or {}
            wsl = cfg.get("wsl", {})
            cp = None
            if isinstance(wsl, dict):
                cp = wsl.get("conda", {}).get("env_path") if isinstance(wsl.get("conda"), dict) else None
            # 运行页从配置读取 Conda 路径，无需预填
        except Exception:
            pass
        self.page_run.runRequested.connect(self._on_run_requested)
        self.page_build.datasetBuilt.connect(self._on_dataset_built)
        self.page_build.log.connect(self._append_log)
        self.page_one.oneClickRequested.connect(self._on_one_click)
    
    def _on_dataset_built(self, root: str, yaml_path: str):
        self.dataset_root = root
        self.dataset_yaml = yaml_path
        self._append_log(f"数据集构建完成 {root}")
    def _on_run_requested(self, dp: str, conda_base: str):
        use_dp = dp.strip() or (self.dataset_root or "")
        if not use_dp:
            self._append_log("缺少数据集文件夹")
            return
        start_py = os.path.join(os.getcwd(), "train", "start.py")
        cb = conda_base.strip() or None
        cmd = build_train_cmd(start_py, use_dp, conda_base=cb)
        self._append_log("启动训练")
        try:
            self._append_log("命令: " + " ".join(cmd))
        except Exception:
            pass
        self.log_thread = LogThread(cmd)
        self.log_thread.line.connect(self._append_log)
        self.log_thread.done.connect(lambda rc: self._append_log(f"训练结束 {rc}"))
        self.log_thread.start()
    def _on_one_click(self, src: str, cls: str, ratios: tuple, persist: bool, out_dir: str | None):
        """处理一键训练请求：构建数据集并启动训练（使用系统配置的 conda 路径回退）。"""
        if not src or not cls:
            self._append_log("参数不完整")
            return
        root, yaml_path = build_yolo_dataset(src, cls, ratios, persist, out_dir)
        self.dataset_root = root
        self.dataset_yaml = yaml_path
        self._append_log(f"数据集构建完成 {root}")
        start_py = os.path.join(os.getcwd(), "train", "start.py")
        cb = None
        try:
            cfg = yaml.safe_load(open(os.path.join(os.getcwd(), "sys_config.yaml"), "r", encoding="utf-8")) or {}
            wsl = cfg.get("wsl", {})
            if isinstance(wsl, dict):
                cb = wsl.get("conda", {}).get("env_path") if isinstance(wsl.get("conda"), dict) else None
        except Exception:
            cb = None
        cmd = build_train_cmd(start_py, root, conda_base=cb)
        self._append_log("启动训练")
        try:
            self._append_log("命令: " + " ".join(cmd))
        except Exception:
            pass
        self.log_thread = LogThread(cmd)
        self.log_thread.line.connect(self._append_log)
        self.log_thread.done.connect(lambda rc: self._append_log(f"训练结束 {rc}"))
        self.log_thread.start()
    
    def _set_lang(self, lang: str):
        if lang == "en":
            self.setWindowTitle("One-Click Train")
            pass
        else:
            self.setWindowTitle("一键训练")
            pass
    def _append_log(self, s: str):
        self.console.append(s)
    
    
    def _open_sys_settings(self):
        p = os.path.join(os.getcwd(), "sys_config.yaml")
        dlg = SysSettingsDialog(self, p)
        dlg.exec()
    

    def _on_page_changed(self, idx):
        self.console.setVisible(idx != 3)