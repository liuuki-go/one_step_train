from PySide6 import QtWidgets
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from tools.sys_config_tools import get_wsl_config
from PySide6.QtCore import Qt
from gui.style.ButtonStyleManager import StyledButton
from gui.components.log_panel import LogPanelWidget
class RunPageWidget(QWidget):
    """训练运行页：采集数据集路径与 Conda 基路径，并发出运行请求。"""
    runRequested = Signal(str, str)
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        form = QGridLayout()
        #增加行间距
        form.setVerticalSpacing(15)
        # 数据集文件夹ui
        self.lbl_yaml = QLabel("数据集文件夹：")
        self.ed_yaml = QLineEdit()
        b1 = StyledButton("选择文件夹", "select_bt"); b1.clicked.connect(self._pick_yaml_dir)
        form.addWidget(self.lbl_yaml, 0, 0)
        form.addWidget(self.ed_yaml, 0, 1)
        form.addWidget(b1, 0, 2)

        # 模型导出路径ui
        self.l_export_path = QLabel("结果输出路径：")
        self.ed_export_path = QLineEdit()
        #添加默认值
        #获取windows的用户目录桌面
        import os
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        self.ed_export_path.setText(desktop)
        b_export = StyledButton("选择文件夹", "select_bt"); b_export.clicked.connect(self._pick_export_path_dir)
        form.addWidget(self.l_export_path, 1, 0)
        form.addWidget(self.ed_export_path, 1, 1)
        form.addWidget(b_export, 1, 2)



        # 开始训练按钮ui
        self.btn_run_train = StyledButton("开始训练", "primary")
        #设置大小
        self.btn_run_train.setFixedSize(200, 50)
        #设置居中
        # self.btn_run_train.set(Qt.AlignmentFlag.AlignCenter)
        self.btn_run_train.clicked.connect(self._emit_run)
        form.addWidget(self.btn_run_train, 2, 1,alignment=Qt.AlignmentFlag.AlignCenter)
        root.addLayout(form)

        self.log_panel = LogPanelWidget("处理日志")
        root.addWidget(self.log_panel)

    def _pick_yaml_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择数据集文件夹")
        if d:
            self.ed_yaml.setText(d)
    def _pick_export_path_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择模型导出路径")
        if d:
            self.ed_export_path.setText(d)

    def append_log(self, s: str):
        self.log_panel.append(s)

    def _emit_run(self):
        dp = self.ed_yaml.text().strip()
        export_path = self.ed_export_path.text().strip()
        if not dp or not export_path:
            QtWidgets.QMessageBox.warning(self, "警告", "数据集文件夹与模型导出路径均不可为空！请检查后再执行操作。")
            return
        
        #禁用开始训练的按钮
        self.btn_run_train.setEnabled(False);self.btn_run_train.setText("训练中")
        self.runRequested.emit(dp,export_path)