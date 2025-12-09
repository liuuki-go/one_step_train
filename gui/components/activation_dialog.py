from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QHBoxLayout, QMessageBox, QApplication)
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QClipboard
from core.activation import get_machine_code, verify_activation_code, save_activation_status
import sys
import datetime

class ActivationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("软件激活"))
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowCloseButtonHint)
        
        # Disable close button (X) behavior effectively by overriding closeEvent if needed,
        # but for now we just handle rejection.
        
        layout = QVBoxLayout()
        
        # Instructions
        layout.addWidget(QLabel(self.tr("本软件未激活或许可已过期。")))
        layout.addWidget(QLabel(self.tr("请联系管理员获取激活码。")))
        
        # Machine Code Section
        layout.addSpacing(10)
        layout.addWidget(QLabel(self.tr("机器码:")))
        
        self.machine_code = get_machine_code()
        self.machine_code_display = QLineEdit(self.machine_code)
        self.machine_code_display.setReadOnly(True)
        self.machine_code_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.machine_code_display.setStyleSheet("font-size: 14px; font-weight: bold; color: #333; background: #f0f0f0;")
        layout.addWidget(self.machine_code_display)
        
        # Copy Button
        copy_btn = QPushButton(self.tr("复制机器码"))
        copy_btn.clicked.connect(self.copy_machine_code)
        layout.addWidget(copy_btn)
        
        # Activation Code Input
        layout.addSpacing(20)
        layout.addWidget(QLabel(self.tr("激活码:")))
        self.activation_input = QLineEdit()
        self.activation_input.setPlaceholderText(self.tr("在此输入激活码"))
        layout.addWidget(self.activation_input)
        
        # Buttons
        layout.addSpacing(20)
        btn_layout = QHBoxLayout()
        
        exit_btn = QPushButton(self.tr("退出"))
        exit_btn.clicked.connect(self.handle_exit)
        exit_btn.setStyleSheet("background-color: #ffcccc;")
        
        activate_btn = QPushButton(self.tr("激活"))
        activate_btn.clicked.connect(self.handle_activate)
        activate_btn.setStyleSheet("background-color: #ccffcc; font-weight: bold;")
        
        btn_layout.addWidget(exit_btn)
        btn_layout.addWidget(activate_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def copy_machine_code(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.machine_code)
        QMessageBox.information(self, self.tr("复制成功"), self.tr("机器码已复制到剪贴板！"))
        
    def handle_activate(self):
        code = self.activation_input.text().strip()
        if not code:
            QMessageBox.warning(self, self.tr("输入错误"), self.tr("请输入激活码。"))
            return
            
        valid, duration, msg = verify_activation_code(code, self.machine_code)
        
        if valid:
            if save_activation_status(duration, code):
                # Format the expiration date for display
                import datetime
                expire_time = datetime.datetime.now() + datetime.timedelta(seconds=duration)
                expire_str = expire_time.strftime("%Y-%m-%d %H:%M:%S")
                
                QMessageBox.information(self, self.tr("激活成功"), self.tr("激活成功！\n有效期至: {}").format(expire_str))
                self.accept() # Close dialog and return QDialog.Accepted
            else:
                QMessageBox.critical(self, self.tr("错误"), self.tr("激活状态保存失败，请检查权限。"))
        else:
            QMessageBox.critical(self, self.tr("激活失败"), self.tr("无效的激活码。\n原因: {}").format(self.tr(msg)))
            
    def handle_exit(self):
        sys.exit(0)
        
    def closeEvent(self, event):
        # Prevent closing by X unless we are exiting app or activated
        # But QDialog exec() returns Rejected if closed by X.
        # We will handle the result in main.
        event.accept()
