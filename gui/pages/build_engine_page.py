from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import Signal, QThread, QEvent
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QFileDialog, QGroupBox, QSpinBox, QMessageBox)
from gui.style.ButtonStyleManager import StyledButton
from gui.components.log_panel import LogPanelWidget
from core.wsl_runner import run_stream
import sys
import os
import re

def check_tensor_version():
    #检查版本
    try:
        import tensorrt as trt
        return trt.__version__
    except ImportError:
        return "未安装TensorRT"

class BuildThread(QThread):
    log_signal = Signal(str)
    finished_signal = Signal(int)

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd
        self._is_running = True

    def run(self):
        try:
            rc = run_stream(self.cmd, self.log_signal.emit)
            self.finished_signal.emit(rc)
        except Exception as e:
            self.log_signal.emit(f"Error: {str(e)}")
            self.finished_signal.emit(-1)

    def stop(self):
        self._is_running = False

class BuildEnginePageWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.build_thread = None
        self.initUI()
        self.retranslateUi()
    
    def initUI(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        self.lb_rt_version = QLabel() # Text set in retranslateUi
        root.addWidget(self.lb_rt_version)
        
        # 1. ONNX Path
        self.gb_input = QGroupBox() # Title set in retranslateUi
        self.gb_input.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        layout_input = QVBoxLayout(self.gb_input)

        row_onnx = QWidget()
        layout_onnx = QHBoxLayout(row_onnx)
        layout_onnx.setContentsMargins(0, 0, 0, 0)
        self.lbl_onnx = QLabel()
        self.ed_onnx = QLineEdit()
        self.btn_onnx = StyledButton("", "select_bt") # Text set in retranslateUi
        self.btn_onnx.clicked.connect(self._pick_onnx)
        layout_onnx.addWidget(self.lbl_onnx)
        layout_onnx.addWidget(self.ed_onnx)
        layout_onnx.addWidget(self.btn_onnx)
        layout_input.addWidget(row_onnx)
        root.addWidget(self.gb_input)

        # 2. Output & Parameters
        self.gb_params = QGroupBox() # Title set in retranslateUi
        self.gb_params.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        layout_params = QVBoxLayout(self.gb_params)

        # Engine Path
        row_out_dir = QWidget()
        layout_out_dir = QHBoxLayout(row_out_dir)
        layout_out_dir.setContentsMargins(0, 0, 0, 0)
        self.lbl_out_dir = QLabel()
        self.ed_out_dir = QLineEdit()
        self.btn_out_dir = StyledButton("", "select_bt")
        self.btn_out_dir.clicked.connect(self._pick_out_dir)
        layout_out_dir.addWidget(self.lbl_out_dir)
        layout_out_dir.addWidget(self.ed_out_dir)
        layout_out_dir.addWidget(self.btn_out_dir)
        layout_params.addWidget(row_out_dir)

        # Output Filename
        row_out_name = QWidget()
        layout_out_name = QHBoxLayout(row_out_name)
        layout_out_name.setContentsMargins(0, 0, 0, 0)
        self.lbl_out_name = QLabel()
        self.ed_out_name = QLineEdit()
        self.ed_out_name.setText("best.engine")
        # Placeholder set in retranslateUi
        layout_out_name.addWidget(self.lbl_out_name)
        layout_out_name.addWidget(self.ed_out_name)
        layout_params.addWidget(row_out_name)

        # Image Size & Memory
        row_opts = QWidget()
        layout_opts = QHBoxLayout(row_opts)
        layout_opts.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_size = QLabel()
        self.sp_size = QSpinBox()
        self.sp_size.setRange(64, 4096)
        self.sp_size.setValue(960)
        self.sp_size.setSingleStep(32)

        self.lbl_max_mem = QLabel()
        self.sp_max_mem = QSpinBox()
        self.sp_max_mem.setRange(1, 128)
        self.sp_max_mem.setValue(30) # Default 30 as requested

        self.lbl_min_mem = QLabel()
        self.sp_min_mem = QSpinBox()
        self.sp_min_mem.setRange(1, 128)
        self.sp_min_mem.setValue(16) # Default 16 as requested

        layout_opts.addWidget(self.lbl_size)
        layout_opts.addWidget(self.sp_size)
        layout_opts.addSpacing(20)
        layout_opts.addWidget(self.lbl_max_mem)
        layout_opts.addWidget(self.sp_max_mem)
        layout_opts.addSpacing(20)
        layout_opts.addWidget(self.lbl_min_mem)
        layout_opts.addWidget(self.sp_min_mem)
        layout_opts.addStretch()
        
        layout_params.addWidget(row_opts)
        root.addWidget(self.gb_params)

        # 3. Action Buttons
        row_actions = QWidget()
        layout_actions = QHBoxLayout(row_actions)
        layout_actions.setContentsMargins(0, 10, 0, 10)
        
        self.btn_build = StyledButton("", "primary")
        self.btn_build.setFixedSize(200, 50)
        self.btn_build.clicked.connect(self._start_build)
        
        layout_actions.addStretch()
        layout_actions.addWidget(self.btn_build)
        layout_actions.addStretch()
        root.addWidget(row_actions)

        # 4. Log Panel
        self.log_panel = LogPanelWidget("构建日志")
        root.addWidget(self.log_panel)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        version_text = check_tensor_version()
        if version_text == "未安装TensorRT":
            version_text = self.tr("未安装TensorRT")
        self.lb_rt_version.setText(self.tr("TensorRT版本：") + f"{version_text}")
        
        self.gb_input.setTitle(self.tr("输入设置"))
        self.lbl_onnx.setText(self.tr("ONNX路径："))
        self.btn_onnx.setText(self.tr("选择文件"))
        
        self.gb_params.setTitle(self.tr("构建参数"))
        self.lbl_out_dir.setText(self.tr("输出目录："))
        self.btn_out_dir.setText(self.tr("选择目录"))
        self.lbl_out_name.setText(self.tr("文件名称："))
        self.ed_out_name.setPlaceholderText(self.tr("例如: best.engine (不能包含中文)"))
        
        self.lbl_size.setText(self.tr("图像大小："))
        self.lbl_max_mem.setText(self.tr("最大内存(GB)："))
        self.lbl_min_mem.setText(self.tr("最小内存(GB)："))
        
        self.btn_build.setText(self.tr("开始构建"))
        self.log_panel.setTitle(self.tr("构建日志"))

    def _pick_onnx(self):
        f, _ = QFileDialog.getOpenFileName(self, self.tr("选择ONNX模型"), filter="ONNX Files (*.onnx)")
        if f:
            self.ed_onnx.setText(f)
            # Auto set output dir if empty
            if not self.ed_out_dir.text():
                self.ed_out_dir.setText(os.path.dirname(f))

    def _pick_out_dir(self):
        d = QFileDialog.getExistingDirectory(self, self.tr("选择输出目录"))
        if d:
            self.ed_out_dir.setText(d)

    def _start_build(self):
        onnx_path = self.ed_onnx.text().strip()
        out_dir = self.ed_out_dir.text().strip()
        out_name = self.ed_out_name.text().strip()
        
        if not onnx_path or not os.path.exists(onnx_path):
            QMessageBox.warning(self, self.tr("错误"), self.tr("请选择有效的ONNX文件！"))
            return
        if not out_dir:
            QMessageBox.warning(self, self.tr("错误"), self.tr("请选择输出目录！"))
            return
        if not out_name:
            QMessageBox.warning(self, self.tr("错误"), self.tr("请输入文件名称！"))
            return

        # Check for Chinese characters in filename
        if re.search(r'[\u4e00-\u9fa5]', out_name):
            QMessageBox.warning(self, self.tr("错误"), self.tr("文件名称不能包含中文！"))
            return

        engine_path = os.path.join(out_dir, out_name)

        # Disable UI
        self.btn_build.setEnabled(False)
        self.btn_build.setText(self.tr("构建中..."))
        self.gb_input.setEnabled(False)
        self.gb_params.setEnabled(False)
        self.log_panel.clear()

        # Construct command
        script_path = os.path.abspath(os.path.join("core", "build_engine.py"))
        cmd = [
            sys.executable, 
            script_path,
            "--onnx", onnx_path,
            "--engine", engine_path,
            "--img_size", str(self.sp_size.value()),
            "--max_mem", str(self.sp_max_mem.value()),
            "--min_mem", str(self.sp_min_mem.value())
        ]

        self.log_panel.append(self.tr("执行命令：") + f" {' '.join(cmd)}")

        self.build_thread = BuildThread(cmd)
        self.build_thread.log_signal.connect(self.log_panel.append)
        self.build_thread.finished_signal.connect(self._on_finished)
        self.build_thread.start()

    def _on_finished(self, rc):
        self.btn_build.setEnabled(True)
        self.btn_build.setText(self.tr("开始构建"))
        self.gb_input.setEnabled(True)
        self.gb_params.setEnabled(True)
        
        if rc == 0:
            QMessageBox.information(self, self.tr("完成"), self.tr("模型构建成功！"))
            self.log_panel.append(self.tr("构建成功！"))
        else:
            QMessageBox.critical(self, self.tr("失败"), self.tr("模型构建失败，请查看日志。"))
            self.log_panel.append(self.tr("构建失败，错误码：") + f" {rc}")
