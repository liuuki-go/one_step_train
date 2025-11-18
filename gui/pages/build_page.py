from PySide6 import QtWidgets
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QSpinBox, QCheckBox, QHBoxLayout
from core.dataset_builder import build_yolo_dataset

class BuildPageWidget(QWidget):
    """数据集构建页：采集构建参数，调用构建函数，发出结果与日志。"""
    datasetBuilt = Signal(str, str)
    log = Signal(str)
    def __init__(self):
        super().__init__()
        form = QGridLayout(self)
        self.lbl_src_b = QLabel("标注文件夹")
        self.ed_src_b = QLineEdit()
        b1 = QPushButton("选择"); b1.clicked.connect(self._pick_src_b)
        form.addWidget(self.lbl_src_b, 0, 0)
        form.addWidget(self.ed_src_b, 0, 1)
        form.addWidget(b1, 0, 2)
        self.lbl_cls_b = QLabel("classes.txt")
        self.ed_cls_b = QLineEdit()
        b2 = QPushButton("选择"); b2.clicked.connect(self._pick_cls_b)
        form.addWidget(self.lbl_cls_b, 1, 0)
        form.addWidget(self.ed_cls_b, 1, 1)
        form.addWidget(b2, 1, 2)
        self.lbl_ratio_b = QLabel("比例 训练:推理:测试")
        self.sp_train_b = QSpinBox(); self.sp_train_b.setRange(0, 100); self.sp_train_b.setValue(8)
        self.sp_val_b = QSpinBox(); self.sp_val_b.setRange(0, 100); self.sp_val_b.setValue(1)
        self.sp_test_b = QSpinBox(); self.sp_test_b.setRange(0, 100); self.sp_test_b.setValue(1)
        hb = QHBoxLayout(); vb = QWidget(); vb.setLayout(hb)
        hb.addWidget(self.sp_train_b); hb.addWidget(QLabel(":")); hb.addWidget(self.sp_val_b); hb.addWidget(QLabel(":")); hb.addWidget(self.sp_test_b)
        form.addWidget(self.lbl_ratio_b, 2, 0)
        form.addWidget(vb, 2, 1)
        self.ck_persist_b = QCheckBox("持久化数据集")
        self.ck_persist_b.setChecked(True)
        self.ck_persist_b.setEnabled(False)
        form.addWidget(self.ck_persist_b, 3, 0)
        self.lbl_out_b = QLabel("输出数据集路径")
        self.ed_out_b = QLineEdit()
        b3 = QPushButton("选择"); b3.clicked.connect(self._pick_out_b)
        form.addWidget(self.lbl_out_b, 4, 0)
        form.addWidget(self.ed_out_b, 4, 1)
        form.addWidget(b3, 4, 2)
        self.btn_build = QPushButton("构建数据集")
        self.btn_build.clicked.connect(self._do_build)
        form.addWidget(self.btn_build, 5, 1)
    def _pick_src_b(self):
        d = QFileDialog.getExistingDirectory(self, "选择标注文件夹")
        if d:
            self.ed_src_b.setText(d)
    def _pick_cls_b(self):
        p, _ = QFileDialog.getOpenFileName(self, "选择 classes.txt", filter="Text (*.txt)")
        if p:
            self.ed_cls_b.setText(p)
    def _pick_out_b(self):
        d = QFileDialog.getExistingDirectory(self, "选择输出数据集路径")
        if d:
            self.ed_out_b.setText(d)
    def _do_build(self):
        src = self.ed_src_b.text().strip()
        cls = self.ed_cls_b.text().strip()
        if not src or not cls:
            self.log.emit("参数不完整")
            return
        ratios = (self.sp_train_b.value(), self.sp_val_b.value(), self.sp_test_b.value())
        persist = True
        out_dir = self.ed_out_b.text().strip()
        if not out_dir:
            self.log.emit("必须选择输出数据集路径")
            return
        root, yaml_path = build_yolo_dataset(src, cls, ratios, persist, out_dir)
        self.datasetBuilt.emit(root, yaml_path)
        self.log.emit(f"数据集构建完成 {root}")