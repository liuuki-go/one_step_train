from PySide6 import QtWidgets
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QSpinBox, QCheckBox, QComboBox, QHBoxLayout, QSpacerItem
from gui.style.ButtonStyleManager import StyledButton
from PySide6.QtCore import Qt

class OneClickPageWidget(QWidget):
    oneClickRequested = Signal(str, str, tuple, bool, object)
    def __init__(self):
        super().__init__()
        form = QGridLayout(self)
        form.setHorizontalSpacing(5)
        form.setVerticalSpacing(15)
        form.setColumnStretch(0, 0)
        form.setColumnStretch(1, 1)
        form.setColumnStretch(2, 0)
        self.label_src = QLabel("标注数据文件夹：")
        self.ed_src = QLineEdit()
        btn_src = StyledButton("选择文件夹", "select_bt"); btn_src.clicked.connect(self._pick_src)
        form.addWidget(self.label_src, 0, 0, 1, 1)
        form.addWidget(self.ed_src, 0, 1, 1, 1)
        form.addWidget(btn_src, 0, 2, 1, 1)
        self.lbl_cls_b = QLabel("分类文本文件：")
        self.ed_cls_b = QLineEdit()
        btn_cls = StyledButton("选择文件", "select_bt"); btn_cls.clicked.connect(self._pick_cls)
        form.addWidget(self.lbl_cls_b, 1, 0, 1, 1)
        form.addWidget(self.ed_cls_b, 1, 1, 1, 1)
        form.addWidget(btn_cls, 1, 2, 1, 1)
        self.lbl_ratio_b = QLabel("划分数据集比例：")
        self.sp_train_b = QSpinBox(); self.sp_train_b.setRange(0, 10); self.sp_train_b.setValue(9); self.sp_train_b.setFixedWidth(60)
        self.sp_val_b = QSpinBox(); self.sp_val_b.setRange(0, 10); self.sp_val_b.setValue(1); self.sp_val_b.setFixedWidth(60)
        self.sp_test_b = QSpinBox(); self.sp_test_b.setRange(0, 10); self.sp_test_b.setValue(0); self.sp_test_b.setFixedWidth(60)
        self.sp_train_b.valueChanged.connect(self._validate_ratios)
        self.sp_val_b.valueChanged.connect(self._validate_ratios)
        self.sp_test_b.valueChanged.connect(self._validate_ratios)
        hb = QHBoxLayout(); hb.setSpacing(5); hb.setContentsMargins(0, 0, 0, 0); hb.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title1 = QLabel("训练集:"); hb.addWidget(title1); hb.addWidget(self.sp_train_b); spacer1 = QSpacerItem(25, 20); hb.addItem(spacer1)
        title2 = QLabel("验证集:"); hb.addWidget(title2); hb.addWidget(self.sp_val_b); spacer2 = QSpacerItem(25, 20); hb.addItem(spacer2)
        title3 = QLabel("测试集:"); hb.addWidget(title3); hb.addWidget(self.sp_test_b)
        vb = QWidget(); vb.setLayout(hb)
        form.addWidget(self.lbl_ratio_b, 2, 0)
        form.addWidget(vb, 2, 1)
        self.lbl_error = QLabel()
        self.lbl_error.setStyleSheet("color:#d93025;font-size:12px;padding:6px 8px;background-color:#fff5f5;border:1px solid #ffd6d6;border-radius:6px;")
        self.lbl_error.setVisible(False)
        self.error_box = QWidget()
        self.error_box.setFixedHeight(38)
        err_layout = QHBoxLayout(self.error_box)
        err_layout.setContentsMargins(0, 0, 0, 0)
        err_layout.setSpacing(0)
        err_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        err_layout.addWidget(self.lbl_error)
        form.addWidget(self.error_box, 3, 0, 1, 3)
        self.lbl_fmt = QLabel("数据集格式：")
        self.cb_fmt = QComboBox(); self.cb_fmt.addItems(["YOLO"])
        form.addWidget(self.lbl_fmt, 4, 0)
        form.addWidget(self.cb_fmt, 4, 1)
        self.ck_persist = QCheckBox("持久化数据集")
        form.addWidget(self.ck_persist, 5, 1)
        self.lbl_out = QLabel("输出数据集路径：")
        self.ed_out = QLineEdit()
        btn_out = StyledButton("选择输出目录", "select_bt"); btn_out.clicked.connect(self._pick_out)
        form.addWidget(self.lbl_out, 6, 0)
        form.addWidget(self.ed_out, 6, 1)
        form.addWidget(btn_out, 6, 2)
        self.btn_run_one = StyledButton("一键训练", "primary")
        self.btn_run_one.setFixedSize(200, 50)
        self.btn_run_one.clicked.connect(self._emit_one_click)
        form.addWidget(self.btn_run_one, 7, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        self._validate_ratios()

    def _validate_ratios(self):
        train = self.sp_train_b.value()
        val = self.sp_val_b.value()
        test = self.sp_test_b.value()
        total = train + val + test
        if total != 10:
            self.lbl_error.setText("警告：比例总和需要为10，否则无法开启一键训练")
            self.lbl_error.setVisible(True)
            self.btn_run_one.setEnabled(False)
        else:
            self.lbl_error.setVisible(False)
            self.btn_run_one.setEnabled(True)
            
    def _pick_src(self):
        d = QFileDialog.getExistingDirectory(self, "选择标注文件夹")
        if d:
            self.ed_src.setText(d)
    def _pick_cls(self):
        p, _ = QFileDialog.getOpenFileName(self, "选择 classes.txt", filter="Text (*.txt)")
        if p:
            self.ed_cls_b.setText(p)
    def _pick_out(self):
        d = QFileDialog.getExistingDirectory(self, "选择输出数据集路径")
        if d:
            self.ed_out.setText(d)
    def _emit_one_click(self):
        self.btn_run_one.setEnabled(False); self.btn_run_one.setText("训练中")
        src = self.ed_src.text().strip()
        cls = self.ed_cls_b.text().strip()
        ratios = (self.sp_train_b.value(), self.sp_val_b.value(), self.sp_test_b.value())
        persist = self.ck_persist.isChecked()
        out_dir = self.ed_out.text().strip() or None
        self.oneClickRequested.emit(src, cls, ratios, persist, out_dir)