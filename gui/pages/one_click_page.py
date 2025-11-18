from PySide6 import QtWidgets
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QSpinBox, QCheckBox, QComboBox, QHBoxLayout

class OneClickPageWidget(QWidget):
    """一键训练页面：收集输入参数，发出 oneClickRequested 信号，由主框架执行构建与训练。"""
    oneClickRequested = Signal(str, str, tuple, bool, object)
    def __init__(self):
        super().__init__()
        form = QGridLayout(self)
        self.lbl_src = QLabel("标注文件夹")
        self.ed_src = QLineEdit()
        b1 = QPushButton("选择"); b1.clicked.connect(self._pick_src)
        form.addWidget(self.lbl_src, 0, 0)
        form.addWidget(self.ed_src, 0, 1)
        form.addWidget(b1, 0, 2)
        self.lbl_cls = QLabel("classes.txt")
        self.ed_cls = QLineEdit()
        b2 = QPushButton("选择"); b2.clicked.connect(self._pick_cls)
        form.addWidget(self.lbl_cls, 1, 0)
        form.addWidget(self.ed_cls, 1, 1)
        form.addWidget(b2, 1, 2)
        self.lbl_ratio = QLabel("比例 训练:推理:测试")
        self.sp_train = QSpinBox(); self.sp_train.setRange(0, 100); self.sp_train.setValue(8)
        self.sp_val = QSpinBox(); self.sp_val.setRange(0, 100); self.sp_val.setValue(1)
        self.sp_test = QSpinBox(); self.sp_test.setRange(0, 100); self.sp_test.setValue(1)
        hb = QHBoxLayout(); vb = QWidget(); vb.setLayout(hb)
        hb.addWidget(self.sp_train); hb.addWidget(QLabel(":")); hb.addWidget(self.sp_val); hb.addWidget(QLabel(":")); hb.addWidget(self.sp_test)
        form.addWidget(self.lbl_ratio, 2, 0)
        form.addWidget(vb, 2, 1)
        self.lbl_fmt = QLabel("数据集格式")
        self.cb_fmt = QComboBox(); self.cb_fmt.addItems(["YOLO"])  # 预留扩展
        form.addWidget(self.lbl_fmt, 3, 0)
        form.addWidget(self.cb_fmt, 3, 1)
        self.ck_persist = QCheckBox("持久化数据集")
        form.addWidget(self.ck_persist, 4, 0)
        self.lbl_out = QLabel("输出数据集路径")
        self.ed_out = QLineEdit()
        b3 = QPushButton("选择"); b3.clicked.connect(self._pick_out)
        form.addWidget(self.lbl_out, 5, 0)
        form.addWidget(self.ed_out, 5, 1)
        form.addWidget(b3, 5, 2)
        self.btn_run_one = QPushButton("一键训练")
        self.btn_run_one.clicked.connect(self._emit_one_click)
        form.addWidget(self.btn_run_one, 6, 1)
    def _pick_src(self):
        d = QFileDialog.getExistingDirectory(self, "选择标注文件夹")
        if d:
            self.ed_src.setText(d)
    def _pick_cls(self):
        p, _ = QFileDialog.getOpenFileName(self, "选择 classes.txt", filter="Text (*.txt)")
        if p:
            self.ed_cls.setText(p)
    def _pick_out(self):
        d = QFileDialog.getExistingDirectory(self, "选择输出数据集路径")
        if d:
            self.ed_out.setText(d)
    def _emit_one_click(self):
        src = self.ed_src.text().strip()
        cls = self.ed_cls.text().strip()
        ratios = (self.sp_train.value(), self.sp_val.value(), self.sp_test.value())
        persist = self.ck_persist.isChecked()
        out_dir = self.ed_out.text().strip() or None
        self.oneClickRequested.emit(src, cls, ratios, persist, out_dir)