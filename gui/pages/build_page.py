from PySide6 import QtWidgets
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QSpinBox, QCheckBox, QHBoxLayout, QSpacerItem
from gui.style.ButtonStyleManager import StyledButton
from core.dataset_builder import build_yolo_dataset
from PySide6.QtCore import Qt



class BuildPageWidget(QWidget):
    """数据集构建页：采集构建参数，调用构建函数，发出结果与日志。"""
    datasetBuilt = Signal(str, str)
    log = Signal(str)
    def __init__(self):
        super().__init__()
        form = QGridLayout(self)
        form.setHorizontalSpacing(5)
        form.setVerticalSpacing(15)
        form.setColumnStretch(0, 0)
        form.setColumnStretch(1, 1)
        form.setColumnStretch(2, 0)
        # 标注数据文件夹
        self.label_src = QLabel("标注数据文件夹：")
        self.ed_src = QLineEdit()
        select_label_src_bt = StyledButton("选择文件夹", "select_bt"); select_label_src_bt.clicked.connect(self._pick_src_b)
        form.addWidget(self.label_src, 0, 0,1,1)
        form.addWidget(self.ed_src, 0, 1,1,1)
        form.addWidget(select_label_src_bt, 0, 2,1,1)
   
        # 分类文本文件
        self.lbl_cls_b = QLabel("分类文本文件：")
        self.ed_cls_b = QLineEdit()
        b2 = StyledButton("选择文件", "select_bt"); b2.clicked.connect(self._pick_cls_b)
        form.addWidget(self.lbl_cls_b, 1, 0,1,1)
        form.addWidget(self.ed_cls_b, 1, 1,1,1)
        form.addWidget(b2, 1, 2,1,1)
        
        # 比例 训练:推理:测试
        self.lbl_ratio_b = QLabel("划分数据集比例：")
        self.sp_train_b = QSpinBox(); self.sp_train_b.setRange(0, 10); self.sp_train_b.setValue(9);self.sp_train_b.setFixedWidth(60)
        self.sp_val_b = QSpinBox(); self.sp_val_b.setRange(0, 10); self.sp_val_b.setValue(1);self.sp_val_b.setFixedWidth(60)
        self.sp_test_b = QSpinBox(); self.sp_test_b.setRange(0, 10); self.sp_test_b.setValue(0);self.sp_test_b.setFixedWidth(60)
        
        # 连接值变化信号到验证函数
        self.sp_train_b.valueChanged.connect(self._validate_ratios)
        self.sp_val_b.valueChanged.connect(self._validate_ratios)
        self.sp_test_b.valueChanged.connect(self._validate_ratios)
        
        hb = QHBoxLayout();hb.setSpacing(5);hb.setContentsMargins(0, 0, 0, 0);hb.setAlignment(Qt.AlignmentFlag.AlignLeft) 
        
        title1 = QLabel("训练集:"); hb.addWidget(title1); hb.addWidget(self.sp_train_b);spacer1 = QSpacerItem(25, 20);hb.addItem(spacer1)
        title2 = QLabel("验证集:"); hb.addWidget(title2); hb.addWidget(self.sp_val_b);spacer2 = QSpacerItem(25, 20);hb.addItem(spacer2)
        title3 = QLabel("测试集:"); hb.addWidget(title3); hb.addWidget(self.sp_test_b)
        vb = QWidget(); vb.setLayout(hb)
        form.addWidget(self.lbl_ratio_b, 2, 0)
        form.addWidget(vb, 2, 1)
        
        # 错误提示标签
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
        
        
        #输出数据集路径
        self.lbl_out_b = QLabel("输出数据集路径：")
        self.ed_out_b = QLineEdit()
        b3 = StyledButton("选择输出目录", "select_bt"); b3.clicked.connect(self._pick_out_b)
        form.addWidget(self.lbl_out_b, 4, 0)
        form.addWidget(self.ed_out_b, 4, 1)
        form.addWidget(b3, 4, 2)
        self.btn_build = StyledButton("构建数据集", "primary")
        self.btn_build.setFixedSize(200, 50)
        self.btn_build.clicked.connect(self._do_build)
        form.addWidget(self.btn_build, 5, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 初始化验证
        self._validate_ratios()
        
    def _validate_ratios(self):
        """验证比例设置是否有效"""
        train = self.sp_train_b.value()
        val = self.sp_val_b.value()
        test = self.sp_test_b.value()
        total = train + val + test
        # 检查总和是否为0或大于10
        if total != 10:
            self.lbl_error.setText(f"警告：比例总和需要为10，否则无法开启构建，当前总和为{total}")
            self.lbl_error.setVisible(True)
            self.btn_build.setEnabled(False)
        else:
            self.lbl_error.setVisible(False)
            self.btn_build.setEnabled(True)
            
    def _pick_src_b(self):
        d = QFileDialog.getExistingDirectory(self, "选择标注文件夹")
        if d:
            self.ed_src.setText(d)
    def _pick_cls_b(self):
        p, _ = QFileDialog.getOpenFileName(self, "选择 classes.txt", filter="Text (*.txt)")
        if p:
            self.ed_cls_b.setText(p)
    def _pick_out_b(self):
        d = QFileDialog.getExistingDirectory(self, "选择输出数据集路径")
        if d:
            self.ed_out_b.setText(d)
    def _do_build(self):
        self.btn_build.setEnabled(False); self.btn_build.setText("构建中")
        src = self.ed_src.text().strip()
        cls = self.ed_cls_b.text().strip()
        if not src or not cls:
            self.log.emit("参数不完整")
            self.btn_build.setEnabled(True); self.btn_build.setText("构建数据集")
            return
        ratios = (self.sp_train_b.value(), self.sp_val_b.value(), self.sp_test_b.value())
        persist = True
        out_dir = self.ed_out_b.text().strip()
        if not out_dir:
            self.log.emit("必须选择输出数据集路径")
            self.btn_build.setEnabled(True); self.btn_build.setText("构建数据集")
            return
        root, yaml_path = build_yolo_dataset(src, cls, ratios, persist, out_dir)
        self.datasetBuilt.emit(root, yaml_path)
        self.log.emit(f"数据集构建完成 {root}")
        self.btn_build.setEnabled(True); self.btn_build.setText("构建数据集")