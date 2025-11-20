from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QPushButton
import os
import sys
import yaml
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QStackedWidget, QSizePolicy
from PySide6.QtCore import QThread, Signal,Qt
from core.dataset_builder import build_yolo_dataset
from core.wsl_runner import build_train_cmd, run_stream
from gui.pages.monitor_widget import MonitorWidget
from gui.sys_settings_dialog import SystemSettingsDialog as SysSettingsDialog
from gui.pages.run_page import RunPageWidget
from gui.pages.build_page import BuildPageWidget
from gui.pages.config_page import ConfigPageWidget
from gui.components.app_menu import setup_menu
from gui.pages.one_click_page import OneClickPageWidget
from PySide6.QtGui import QIcon, QPixmap
from constants import SYS_SETTINGS_FILE


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
        self.setWindowTitle("oneST")  #设置程序标题
        self.setFixedSize(1500, 700)  #设置初始窗口大小
        self._init_ui()  
        self.dataset_root = None 
        self.dataset_yaml = None
        self.log_thread = None
        
    def _on_page_changed(self, idx):
        self.console.setVisible(idx != 3)
    
    def _set_run_button_loading(self, loading: bool):
        try:
            if loading:
                self.page_run.btn_run_train.setEnabled(False)
                self.page_run.btn_run_train.setText("训练中")
            else:
                self.page_run.btn_run_train.setEnabled(True)
                self.page_run.btn_run_train.setText("开始训练")
        except Exception:
            pass
    def _set_one_button_loading(self, loading: bool):
        try:
            if loading:
                self.page_one.btn_run_one.setEnabled(False)
                self.page_one.btn_run_one.setText("训练中")
            else:
                self.page_one.btn_run_one.setEnabled(True)
                self.page_one.btn_run_one.setText("一键训练")
        except Exception:
            pass

    def _on_train_done(self, rc: int):
        self._append_log(f"训练结束 {rc}")
        self._set_run_button_loading(False)
        self._set_one_button_loading(False)

    def _init_ui(self):
        """初始化用户界面，包括布局、组件和信号槽连接。"""
        cw = QWidget()
        cw.setStyleSheet("QWidget{background:#F8FAFC;}")
        self.setCentralWidget(cw) #设置主窗口的中心部件为cw
        root = QHBoxLayout(cw) #创建主水平布局
        left_container = QWidget() #创建左侧容器
        left_container.setStyleSheet("QWidget{background:#f6f8fa;border-right:2px solid #e1e4e8;}")
        left = QVBoxLayout(left_container)
        left.setContentsMargins(0, 0, 0, 0)

        
        function_title_container = QWidget()
        function_title_container.setStyleSheet("QWidget{background:#f6f8fa;border-right:0px solid #e1e4e8;}")
        function_title_layout = QHBoxLayout(function_title_container);function_title_layout.setSpacing(1);function_title_layout.setContentsMargins(0, 0, 0, 0) 
        lb_function_title_icon = QLabel()
        lb_f_icon=QPixmap("gui/icon/action_model_icon/子功能区.png").scaled(25, 25,Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        lb_function_title_icon.setPixmap(lb_f_icon);lb_function_title_icon.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lb_function_title = QLabel("功能区")
        lb_function_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lb_function_title.setStyleSheet("QLabel{font-size:20px;font-weight:bold;color:#24292f;margin:0px 0px 0px 5px;}")
        function_title_layout.addWidget(lb_function_title_icon)
        function_title_layout.addWidget(lb_function_title)
        function_title_layout.addStretch(1)

        #左侧功能栏
        left_functions_container = QWidget()
        left_functions_container.setStyleSheet("QWidget{background:#f6f8fa;border-right:2px solid #e1e4e8;}")
        left_functions_layout = QVBoxLayout(left_functions_container)

        # 工具区标题
        function_tools_container = QWidget()
        function_tools_container.setStyleSheet("QWidget{background:#f6f8fa;border-right:0px solid #e1e4e8;}")
        function_tools_layout = QHBoxLayout(function_tools_container);function_tools_layout.setSpacing(1);function_tools_layout.setContentsMargins(0, 0, 15, 0) 
        lb_tools_title_icon = QLabel()
        lb_t_icon=QPixmap("gui/icon/action_model_icon/tools.png").scaled(25, 25,Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        lb_tools_title_icon.setPixmap(lb_t_icon);lb_tools_title_icon.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lb_tools_title = QLabel("工具区")
        lb_tools_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lb_tools_title.setStyleSheet("QLabel{font-size:20px;font-weight:bold;color:#24292f;margin:0px 0px 0px 5px;}")
        function_tools_layout.addWidget(lb_tools_title_icon)
        function_tools_layout.addWidget(lb_tools_title)
        function_tools_layout.addStretch(1)

    

        #左侧工具栏
        left_tools_container = QWidget()
        left_tools_container.setStyleSheet("QWidget{background:#f6f8fa;border-right:2px solid #e1e4e8;}")
        left_tools_layout = QVBoxLayout(left_tools_container)
     
        left.addWidget(function_title_container)  # 加入功能栏标题
        left.addWidget(left_functions_container) # 加入功能栏区域
        left.addWidget(function_tools_container) # 加入工具区标题
        left.addWidget(left_tools_container) # 加入工具栏区域
        left.addStretch(1)




       
        center = QVBoxLayout()
        center.setContentsMargins(0, 0, 0, 0)
        center.setSpacing(0)
        right = QVBoxLayout()
        left_container.setFixedWidth(120)
        root.addWidget(left_container)
        root.addLayout(center, 7.5)
        root.addLayout(right, 2.5)
        
        setup_menu(self, self._open_sys_settings, self._set_lang)

        #设置左侧功能区的按钮和样式
        btn_one = QPushButton("一键训练"); btn_one.setIcon(QIcon("gui/icon/action_model_icon/one_step_train.png"))
        btn_build = QPushButton("构建数据"); btn_build.setIcon(QIcon("gui/icon/action_model_icon/build_dataset.png"))
        btn_run = QPushButton("开始训练") ;btn_run.setIcon(QIcon("gui/icon/action_model_icon/run_train.png"))
        btn_cfg = QPushButton("训练配置"); btn_cfg.setIcon(QIcon("gui/icon/action_model_icon/config.png"))
        for b in (btn_one, btn_build, btn_run, btn_cfg):
            b.setCheckable(True)
            b.setStyleSheet(
                "QPushButton{font-size:12px;padding:10px 10px;text-align:left;border-radius:10px;}"
                "QPushButton:checked{background:#e6f0ff;color:#0366d6;}"
                "QPushButton:hover{background:#f0f6ff;}"
            )
        left_functions_layout.addWidget(btn_one)
        left_functions_layout.addWidget(btn_build)
        left_functions_layout.addWidget(btn_run)
        left_functions_layout.addWidget(btn_cfg)
        left_functions_layout.addStretch(1)
        #设置左侧功能区按钮

        btn_tool_1 = QPushButton("btn_tool_1"); btn_tool_1.setIcon(QIcon("gui/icon/action_model_icon/one_step_train.png"))
        btn_tool_2 = QPushButton("btn_tool_2"); btn_tool_2.setIcon(QIcon("gui/icon/action_model_icon/build_dataset.png"))
        left_tools_layout.addWidget(btn_tool_1)
        left_tools_layout.addWidget(btn_tool_2)
        left_tools_layout.addStretch(1)

        
        #创建一个按钮组，用于管理左侧功能区的按钮，确保只能选中一个
        action_group = QtWidgets.QButtonGroup(self)
        action_group.setExclusive(True) #设置按钮组为"互斥"模式
        for i, b in enumerate[QPushButton]((btn_one, btn_build, btn_run, btn_cfg)):  
            action_group.addButton(b, i)

        btn_one.setChecked(True) #默认选中一键训练按钮
        action_group.idClicked.connect(lambda i: self.stack.setCurrentIndex(i))
    
        self.stack = QStackedWidget() #创建一个栈式窗口部件，用于切换不同的页面，QStackedWidget 是一个容器，可以包含多个子部件，但同一时间只显示一个
        self.console = QTextEdit()
        self.console.setReadOnly(True)    
        self.console.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.console.setStyleSheet('QTextEdit{font-family:Consolas, "Courier New", monospace; font-size:12px;border: 5px solid #FC5185;background-color: #ffffff;}')
        self.console.setFixedHeight(240)
        center.addWidget(self.stack)
        center.addItem(QtWidgets.QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        center.addWidget(self.console)


        #创建页面ui，每个页面都是一个QWidget
        self.page_one = OneClickPageWidget()
        self.page_build = BuildPageWidget()
        self.page_run = RunPageWidget()
        self.page_cfg = ConfigPageWidget()
        self.stack.addWidget(self.page_one) #索引0，一键训练页面
        self.stack.addWidget(self.page_build) #索引1，构建数据页面
        self.stack.addWidget(self.page_run) #索引2，开始训练页面
        self.stack.addWidget(self.page_cfg) #索引3，训练配置页面
        # idClicked handles switching
        self.stack.setCurrentIndex(0) #默认选中构建数据页面
        self.stack.currentChanged.connect(self._on_page_changed)
        
        #创建右侧监控器，用于显示训练进度和日志
        self.monitor = MonitorWidget()
        right.addWidget(self.monitor)
        try:
            cfg = yaml.safe_load(open(os.path.join(os.getcwd(), SYS_SETTINGS_FILE), "r", encoding="utf-8")) or {}
            wsl = cfg.get("wsl", {})
            cp = None
            if isinstance(wsl, dict):
                cp = wsl.get("conda", {}).get("env_path") if isinstance(wsl.get("conda"), dict) else None
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

    def _on_run_requested(self, dp: str, conda_base: str, export_path: str):
        start_py = os.path.join(os.getcwd(), "train", "start.py")
        cmd = build_train_cmd(start_py, dp, conda_base=conda_base, export_path=export_path)
        self._append_log("启动训练")
        try:
            self._append_log("命令: " + " ".join(cmd))
        except Exception:
            pass
        self._set_run_button_loading(True)
        self.log_thread = LogThread(cmd)
        self.log_thread.line.connect(self._append_log)
        self.log_thread.done.connect(self._on_train_done)
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
        self._set_one_button_loading(True)
        self.log_thread = LogThread(cmd)
        self.log_thread.line.connect(self._append_log)
        self.log_thread.done.connect(self._on_train_done)
        self.log_thread.start()

    def _limit_lines(self):
        """裁剪超出最大行数的内容，保留最后max_lines行"""
        # 断开信号避免递归触发
        # 设置触发行数（可根据需求调整，比如1000行）
        max_lines = 3000
        #设置保留行数
        save_lines = 2000
        self.console.textChanged.disconnect(self._limit_lines)
        # 获取所有行并分割
        text = self.console.toPlainText()
        lines = text.split('\n')
        
        # 若行数超过最大值，截取后max_lines行
        if len(lines) > max_lines:
            lines = lines[-save_lines:]  # 保留save_lines行
            new_text = '\n'.join(lines)
            self.console.setPlainText(new_text)
            # 滚动到最后一行（保持控制台最新内容可见）
            self.console.moveCursor(self.console.textCursor().End)
        
        # 重新连接信号
        self.console.textChanged.connect(self._limit_lines)
    
    def _set_lang(self, lang: str):
        if lang == "en":
            self.setWindowTitle("One-Click Train")
            pass
        else:
            self.setWindowTitle("一键训练")
            pass
    def _append_log(self, s: str):
        self.console.append(s)
        # 触发行数裁剪
        self._limit_lines()
    
    
    def _open_sys_settings(self):
        p = os.path.join(os.getcwd(), "sys_config.yaml")
        dlg = SysSettingsDialog(self, p)
        dlg.exec()
    

    def _on_page_changed(self, idx):
        self.console.setVisible(idx != 3)