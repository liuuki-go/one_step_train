from PySide6 import QtWidgets
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PySide6.QtWidgets import QSizePolicy, QFrame, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from gui.style.ButtonStyleManager import StyledButton

class LogPanelWidget(QWidget):
    def __init__(self, title: str = "处理日志"):
        super().__init__()
        self.setStyleSheet("")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.console.setFrameStyle(QFrame.NoFrame)
        self.console.setStyleSheet('QTextEdit{font-family:Consolas, "Courier New", monospace; font-size:11px;background-color: #ffffff;padding:0px;} QTextEdit::viewport{background:#ffffff;}')
        self.console.setPlaceholderText(title)
        self.console.setFixedHeight(250)
        self.console.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.console_frame = QFrame()
        self.console_frame.setStyleSheet('QFrame{background:#ffffff;border: 2px solid #9aa0a6;border-radius:8px;}')
        frame_layout = QtWidgets.QVBoxLayout(self.console_frame)
        frame_layout.setContentsMargins(4,4,4,4)
        frame_layout.setSpacing(0)
        frame_layout.addWidget(self.console)
        eff = QGraphicsDropShadowEffect(self)
        eff.setBlurRadius(12)
        eff.setOffset(0, 2)
        eff.setColor(QColor(0,0,0,40))
        self.console_frame.setGraphicsEffect(eff)
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setContentsMargins(0,0,0,0)
        btn_row.setSpacing(8)
        self.btn_clear = StyledButton("清空日志", "select_bt")
        self.btn_save = StyledButton("保存日志", "select_bt")
        self.btn_clear.clicked.connect(self.clear)
        self.btn_save.clicked.connect(self.save)
        layout.addWidget(self.console_frame)
        btn_row.addWidget(self.btn_clear)
        btn_row.addWidget(self.btn_save)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self.console.textChanged.connect(self._limit_lines)

    def append(self, s: str):
        self.console.append(s)

    def clear(self):
        try:
            self.console.clear()
        except Exception:
            pass

    def save(self):
        try:
            import os
            default = os.path.join(os.path.join(os.environ.get('USERPROFILE', os.getcwd())), 'Desktop', 'oneST-log.txt')
            fn, _ = QtWidgets.QFileDialog.getSaveFileName(self, "保存日志", default, "Text Files (*.txt);;All Files (*.*)")
            if fn:
                with open(fn, 'w', encoding='utf-8') as f:
                    f.write(self.console.toPlainText())
        except Exception:
            pass

    def _limit_lines(self):
        max_lines = 3000
        save_lines = 2000
        try:
            self.console.textChanged.disconnect(self._limit_lines)
        except Exception:
            pass
        text = self.console.toPlainText()
        lines = text.split('\n')
        if len(lines) > max_lines:
            lines = lines[-save_lines:]
            self.console.setPlainText('\n'.join(lines))
            self.console.moveCursor(self.console.textCursor().End)
        self.console.textChanged.connect(self._limit_lines)