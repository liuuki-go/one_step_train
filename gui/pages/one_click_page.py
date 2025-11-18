from PySide6 import QtWidgets
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QSpinBox, QCheckBox, QComboBox, QHBoxLayout,QSpacerItem
from PySide6.QtCore import Qt
class OneClickPageWidget(QWidget):
    """一键训练页面：收集输入参数，发出 oneClickRequested 信号，由主框架执行构建与训练。"""
    oneClickRequested = Signal(str, str, tuple, bool, object)
    def __init__(self):
        super().__init__()
        form = QGridLayout(self)
        form.setHorizontalSpacing(5)
        form.setVerticalSpacing(10)
        # 标注数据文件夹
        self.label_src = QLabel("标注数据文件夹：")
        self.ed_src = QLineEdit()
        select_label_src_bt = QPushButton("选择文件夹"); select_label_src_bt.clicked.connect(self._pick_src)
        form.addWidget(self.label_src, 0, 0,1,1)
        form.addWidget(self.ed_src, 0, 1,1,1)
        form.addWidget(select_label_src_bt, 0, 2,1,1)
   
        # 分类文本文件
        self.lbl_cls_b = QLabel("分类文本文件：")
        self.ed_cls_b = QLineEdit()
        b2 = QPushButton("选择文件"); b2.clicked.connect(self._pick_cls)
        form.addWidget(self.lbl_cls_b, 1, 0,1,1)
        form.addWidget(self.ed_cls_b, 1, 1,1,1)
        form.addWidget(b2, 1, 2,1,1)
        
        # 比例 训练:推理:测试
        self.lbl_ratio_b = QLabel("划分数据集比例：")
        self.sp_train_b = QSpinBox(); self.sp_train_b.setRange(0, 10); self.sp_train_b.setValue(9);self.sp_train_b.setFixedWidth(60)
        self.sp_val_b = QSpinBox(); self.sp_val_b.setRange(0, 10); self.sp_val_b.setValue(1);self.sp_val_b.setFixedWidth(60)
        self.sp_test_b = QSpinBox(); self.sp_test_b.setRange(0, 10); self.sp_test_b.setValue(0);self.sp_test_b.setFixedWidth(60)
        hb = QHBoxLayout();hb.setSpacing(5);hb.setContentsMargins(0, 0, 0, 0);hb.setAlignment(Qt.AlignmentFlag.AlignLeft) 
        
        title1 = QLabel("训练集:"); hb.addWidget(title1); hb.addWidget(self.sp_train_b);spacer1 = QSpacerItem(25, 20);hb.addItem(spacer1)
        title2 = QLabel("验证集:"); hb.addWidget(title2); hb.addWidget(self.sp_val_b);spacer2 = QSpacerItem(25, 20);hb.addItem(spacer2)
        title3 = QLabel("测试集:"); hb.addWidget(title3); hb.addWidget(self.sp_test_b)
        vb = QWidget(); vb.setLayout(hb)
        form.addWidget(self.lbl_ratio_b, 2, 0)
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