from PySide6.QtWidgets import QPushButton
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget
from PySide6.QtCore import QThread, Signal,Qt
from core.dataset_builder import build_yolo_dataset
from core.wsl_runner import build_train_cmd, run_stream
from gui.pages.monitor_widget import MonitorWidget
from gui.components.sys_settings_dialog import SystemSettingsDialog as SysSettingsDialog
from gui.pages.run_page import RunPageWidget
from gui.pages.build_page import BuildPageWidget
from gui.pages.config_page import ConfigPageWidget
from gui.pages.label_processor_page import LabelProcessorPageWidget
from gui.pages.build_engine_page import BuildEnginePageWidget

from gui.components.app_menu import setup_menu
from gui.pages.one_click_page import OneClickPageWidget
from PySide6.QtGui import QIcon, QPixmap
from tools.sys_config_tools import get_wsl_config
from tools.sys_config_tools import get_resource_path


from threading import Event
import os
import shutil

class LogThread(QThread):
    line = Signal(str)
    done = Signal(int)
    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd
        self.stop_event = Event()
        
    def run(self):
        rc = run_stream(self.cmd, lambda s: self.line.emit(s), stop_event=self.stop_event)
        self.done.emit(rc)
    
    def stop(self):
        self.stop_event.set()

class MainFrame(QMainWindow):
    """主框架：只负责页面路由与信号接线，业务逻辑下沉到各页面或 core 模块。"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("oneST")  #设置程序标题
        self.resize(1220, 650)  #设置初始窗口大小
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self._init_ui()  
        self.dataset_root = None 
        self.dataset_yaml = None
        self.log_thread = None
        self._is_closing = False
        
    # def _on_page_changed(self, idx):
    #     pass
    
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
        self._emit_log_to_current(f"训练结束 {rc}")
        self._set_run_button_loading(False)
        self._set_one_button_loading(False)
        try:
            # 训练结束时，禁用停止按钮
            if hasattr(self.page_run, "btn_stop_train"):
                self.page_run.btn_stop_train.setEnabled(False)
        except Exception:
            pass

    def _on_stop_requested(self):
        """处理停止训练请求"""
        if self.log_thread and self.log_thread.isRunning():
            self._emit_log_to_current("正在发送停止信号...")
            self.log_thread.stop()
        else:
            self._emit_log_to_current("当前没有正在运行的训练任务。")

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




        center_container = QWidget()
        center_container.setStyleSheet("QWidget{background:#F8FAFC;border-right:0px solid #e1e4e8;}")
        center = QVBoxLayout(center_container)
        center.setContentsMargins(0, 0, 0, 0)
        center.setSpacing(0)
        right_container = QWidget()
        right_container.setStyleSheet("QWidget{background:#F8FAFC;border-right:0px solid #e1e4e8;}")
        right = QVBoxLayout(right_container)
        left_container.setFixedWidth(120)
        root.addWidget(left_container)
        root.addWidget(center_container, 70)
        root.addWidget(right_container, 30)
        
        

        #设置左侧功能区的按钮和样式
        btn_one = QPushButton("一键训练"); btn_one.setIcon(QIcon(get_resource_path("gui/icon/action_model_icon/one_step_train.png")))
        btn_build = QPushButton("构建数据"); btn_build.setIcon(QIcon(get_resource_path("gui/icon/action_model_icon/build_dataset.png")))
        btn_run = QPushButton("开始训练") ;btn_run.setIcon(QIcon(get_resource_path("gui/icon/action_model_icon/run_train.png")))
        self.btn_cfg = QPushButton("训练配置"); self.btn_cfg.setIcon(QIcon(get_resource_path("gui/icon/action_model_icon/config.png")));self.btn_cfg.setEnabled(False)
        for b in (btn_one, btn_build, btn_run, self.btn_cfg):
            b.setCheckable(True)
            b.setStyleSheet(
                "QPushButton{font-size:12px;padding:10px 10px;text-align:left;border-radius:10px;}"
                "QPushButton:checked{background:#e6f0ff;color:#0366d6;}"
                "QPushButton:hover{background:#f0f6ff;}"
            )
        left_functions_layout.addWidget(btn_one)
        left_functions_layout.addWidget(btn_build)
        left_functions_layout.addWidget(btn_run)
        left_functions_layout.addWidget(self.btn_cfg)
        left_functions_layout.addStretch(1)
        #设置左侧工具区按钮
        
        btn_tool_1 = QPushButton("标签处理"); btn_tool_1.setIcon(QIcon(get_resource_path("gui/icon/action_model_icon/one_step_train.png")))
        btn_tool_2 = QPushButton("模型转换"); btn_tool_2.setIcon(QIcon(get_resource_path("gui/icon/action_model_icon/build_dataset.png")))
        for b in (btn_tool_1, btn_tool_2):
            b.setCheckable(True)
            b.setStyleSheet(
                "QPushButton{font-size:12px;padding:10px 10px;text-align:left;border-radius:10px;}"
                "QPushButton:checked{background:#e6f0ff;color:#0366d6;}"
                "QPushButton:hover{background:#f0f6ff;}"
        )
        left_tools_layout.addWidget(btn_tool_1)
        left_tools_layout.addWidget(btn_tool_2)
        left_tools_layout.addStretch(1)

        #设置菜单
        setup_menu(self, self._open_sys_settings, self._set_lang,self.btn_cfg)

        
        #创建一个按钮组，用于管理左侧功能区的按钮，确保只能选中一个
        action_group = QtWidgets.QButtonGroup(self)
        action_group.setExclusive(True) #设置按钮组为"互斥"模式
        for i, b in enumerate[QPushButton]((btn_one, btn_build, btn_run, self.btn_cfg, btn_tool_1, btn_tool_2)):  
            action_group.addButton(b, i)

        btn_one.setChecked(True) #默认选中一键训练按钮
        action_group.idClicked.connect(lambda i: self.stack.setCurrentIndex(i))
    
        self.stack = QStackedWidget() #创建一个栈式窗口部件，用于切换不同的页面，QStackedWidget 是一个容器，可以包含多个子部件，但同一时间只显示一个
        center.addWidget(self.stack)


        #创建页面ui，每个页面都是一个QWidget
        self.page_one = OneClickPageWidget()
        self.page_build = BuildPageWidget()
        self.page_run = RunPageWidget()
        self.page_cfg = ConfigPageWidget()
        self.stack.addWidget(self.page_one) #索引0，一键训练页面
        self.stack.addWidget(self.page_build) #索引1，构建数据页面
        self.stack.addWidget(self.page_run) #索引2，开始训练页面
        self.stack.addWidget(self.page_cfg) #索引3，训练配置页面
        self.stack.addWidget(LabelProcessorPageWidget()) #索引4，标签处理页面
        self.stack.addWidget(BuildEnginePageWidget()) #索引5，模型转换页面
        # idClicked handles switching
        self.stack.setCurrentIndex(0) #默认选中构建数据页面
        # self.stack.currentChanged.connect(self._on_page_changed)
        
        #创建右侧监控器，用于显示训练进度和日志
        self.monitor = MonitorWidget(); self.monitor.setStyleSheet("background-color: #F8FAFC;")
        right.addWidget(self.monitor)
        self.page_run.runRequested.connect(self._on_run_requested)
        self.page_run.stopRequested.connect(self._on_stop_requested) # 连接停止信号
        self.page_build.datasetBuilt.connect(self._on_dataset_built)
        self.page_build.log.connect(lambda s: getattr(self.page_build, "append_log", lambda x: None)(s))
        self.page_one.oneClickRequested.connect(self._on_one_click)
        self.page_one.stopRequested.connect(self._on_stop_requested) # 连接停止信号
    


    def _on_dataset_built(self, src: str, cls: str, ratios: tuple, out_dir: str, fmt: str, persist: bool = False):
        # if fmt == "TXT":
        dataset_root, yaml_path = build_yolo_dataset(src, cls, ratios, persist, out_dir)
        # elif fmt == "COCO":
           # dataset_root, yaml_path = build_coco_dataset(src, cls, ratios, persist, out_dir)
        #    pass

        self._emit_log_to_current(f"数据集构建完成 {dataset_root}")
        return dataset_root, yaml_path



    def _on_run_requested(self, dataset_root: str, export_path: str):
        # 启动训练
        start_py = get_resource_path("start.py") # 训练脚本路径
        cfg = get_wsl_config()
        conda_base = ""
        try:
            if isinstance(cfg.get("conda"), dict):
                conda_base = str(cfg["conda"].get("env_path", "")).strip()
            if not conda_base:
                QtWidgets.QMessageBox.warning(self, "警告", "Conda 环境路径不能为空。请检查配置文件是否正确或联系管理员。")
                return
        except Exception:
            QtWidgets.QMessageBox.warning(self, "警告", "获取 Conda 环境路径失败。请检查配置文件是否正确或联系管理员。")
            return
        self._emit_log_to_current(f"conda 环境路径 {conda_base}")
        cmd = build_train_cmd(export_path,start_py, dataset_root, conda_base=conda_base)
        
        self._emit_log_to_current("启动训练")
        try:
            self._emit_log_to_current("命令: " + " ".join(cmd))
            self._set_one_button_loading(True)
            self.log_thread = LogThread(cmd)
            self.log_thread.line.connect(self._emit_log_to_current)
            self.log_thread.done.connect(self._on_train_done)
            self.log_thread.start()
        except Exception as e:
            self._set_one_button_loading(False)
            return
        

        
    def _on_one_click(self, src: str, cls: str, ratios: tuple, persist: bool, out_dir: str, export_path: str, fmt: str = "TXT"):
        """处理一键训练请求：构建数据集并启动训练（使用系统配置的 conda 路径回退）。"""
        # 构建数据集
        dataset_root, yaml_path = self._on_dataset_built(src, cls, ratios, out_dir, fmt, persist)
        if persist:
            self._emit_log_to_current(f"数据集构建完成 {dataset_root}")
        
        # 启动训练
        self._on_run_requested(dataset_root, export_path)


  
        
   

    # 日志裁剪逻辑已在各页面的日志组件中实现
    
    def _set_lang(self, lang: str):
        if lang == "en":
            pass
        else:
            pass
    def _emit_log_to_current(self, s: str):
        try:
            w = self.stack.currentWidget()
            fn = getattr(w, "append_log", None)
            if callable(fn):
                fn(s)
        except Exception:
            pass
    
    
    def _open_sys_settings(self):
        # 确定本地配置文件路径
        local_path = os.path.join(os.getcwd(), "sys_config.yaml")
        # 确定打包的默认配置文件路径
        bundled_path = get_resource_path("sys_config.yaml")
        
        # 如果本地文件不存在，且打包文件存在，则复制一份到本地
        if not os.path.exists(local_path) and os.path.exists(bundled_path):
            try:
                shutil.copy(bundled_path, local_path)
            except Exception:
                pass # 如果写入失败（如权限问题），可能只能使用临时路径了
        
        # 如果本地文件现在存在了，就用本地的；否则回退到打包路径（只读或临时）
        p = local_path if os.path.exists(local_path) else bundled_path
        
        dlg = SysSettingsDialog(self, p)
        dlg.exec()
    
    def closeEvent(self, e):
        self._is_closing = True
        self.hide()
        try:
            if self.log_thread is not None:
                try:
                    self.log_thread.line.disconnect(self._emit_log_to_current)
                except Exception:
                    pass
                try:
                    self.log_thread.done.disconnect(self._on_train_done)
                except Exception:
                    pass
                try:
                    self.log_thread.quit()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            app = QtWidgets.QApplication.instance()
            if app is not None:
                QtCore.QTimer.singleShot(0, app.quit)
        except Exception:
            pass
        e.accept()
