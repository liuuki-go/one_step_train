from PySide6 import QtWidgets
from PySide6.QtCore import Signal, QEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
from tools.sys_config_tools import get_wsl_config
from PySide6.QtCore import Qt
from gui.style.ButtonStyleManager import StyledButton
from gui.components.log_panel import LogPanelWidget
import os

class RunPageWidget(QWidget):
    """训练运行页：采集数据集路径与 Conda 基路径，并发出运行请求。"""
    runRequested = Signal(str, str)
    stopRequested = Signal() # 新增停止信号

    def __init__(self):
        super().__init__()
        self.initUI()
        self.retranslateUi()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def initUI(self):
        #获取windows的用户目录桌面
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        root = QVBoxLayout(self)
        form = QGridLayout()
        #增加行间距
        form.setVerticalSpacing(15)
        # 数据集文件夹ui
        self.lbl_yaml = QLabel()
        self.ed_yaml = QLineEdit();self.ed_yaml.setText(os.path.join(desktop, self.tr("持久化")))
        self.b1 = StyledButton("", "select_bt"); self.b1.clicked.connect(self._pick_yaml_dir)
        form.addWidget(self.lbl_yaml, 0, 0)
        form.addWidget(self.ed_yaml, 0, 1)
        form.addWidget(self.b1, 0, 2)

        # 模型导出路径ui
        self.l_export_path = QLabel()
        self.ed_export_path = QLineEdit()
        #添加默认值
      
        self.ed_export_path.setText(desktop)
        self.b_export = StyledButton("", "select_bt"); self.b_export.clicked.connect(self._pick_export_path_dir)
        form.addWidget(self.l_export_path, 1, 0)
        form.addWidget(self.ed_export_path, 1, 1)
        form.addWidget(self.b_export, 1, 2)



        # 按钮容器
        btn_box = QtWidgets.QHBoxLayout()
        btn_box.setSpacing(20)
        btn_box.addStretch(1)

        # 开始训练按钮ui
        self.btn_run_train = StyledButton("", "primary")
        self.btn_run_train.setFixedSize(200, 50)
        self.btn_run_train.clicked.connect(self._emit_run)
        
        # 停止训练按钮ui
        self.btn_stop_train = StyledButton("", "primary") 
        self.btn_stop_train.setFixedSize(200, 50)
        self.btn_stop_train.clicked.connect(self._emit_stop)
        self.btn_stop_train.setEnabled(False) # 初始不可用

        btn_box.addWidget(self.btn_run_train)
        btn_box.addWidget(self.btn_stop_train)
        btn_box.addStretch(1)

        form.addLayout(btn_box, 2, 0, 1, 3) # 跨越3列
        root.addLayout(form)

        self.log_panel = LogPanelWidget("处理日志") # This will be updated in retranslateUi
        root.addWidget(self.log_panel)

    def retranslateUi(self):
        self.lbl_yaml.setText(self.tr("数据集文件夹："))
        self.b1.setText(self.tr("选择文件夹"))
        
        self.l_export_path.setText(self.tr("结果输出路径："))
        self.b_export.setText(self.tr("选择文件夹"))
        
        if self.btn_run_train.isEnabled():
            self.btn_run_train.setText(self.tr("开始训练"))
        else:
            self.btn_run_train.setText(self.tr("训练中"))
            
        self.btn_stop_train.setText(self.tr("停止训练"))
        
        self.log_panel.setTitle(self.tr("处理日志"))

    def _pick_yaml_dir(self):
        d = QFileDialog.getExistingDirectory(self, self.tr("选择数据集文件夹"))
        if d:
            self.ed_yaml.setText(d)
    def _pick_export_path_dir(self):
        d = QFileDialog.getExistingDirectory(self, self.tr("选择模型导出路径"))
        if d:
            self.ed_export_path.setText(d)

    def append_log(self, s: str):
        self.log_panel.append(s)

    def _emit_run(self):
        dp = self.ed_yaml.text().strip()
        export_path = self.ed_export_path.text().strip()
        if not dp or not export_path:
            QtWidgets.QMessageBox.warning(self, self.tr("警告"), self.tr("数据集文件夹与模型导出路径均不可为空！请检查后再执行操作。"))
            return
        
        #禁用开始训练的按钮
        self.btn_run_train.setEnabled(False);self.btn_run_train.setText(self.tr("训练中"))
        self.btn_stop_train.setEnabled(True) # 启用停止按钮
        self.runRequested.emit(dp,export_path)

    def _emit_stop(self):
        self.stopRequested.emit()
        self.btn_stop_train.setEnabled(False) # 防止重复点击
        self.append_log(self.tr("正在停止训练..."))