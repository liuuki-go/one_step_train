from PySide6 import QtWidgets
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QSpinBox, QCheckBox, QComboBox, QHBoxLayout, QSpacerItem, QSizePolicy
from gui.style.ButtonStyleManager import StyledButton
from PySide6.QtCore import Qt
from gui.components.log_panel import LogPanelWidget



class BuildPageWidget(QWidget):
    """数据集构建页：采集构建参数，调用构建函数，发出结果与日志。"""
    datasetBuilt = Signal(str, str, list, str, str)
    log = Signal(str)
    def __init__(self):
        super().__init__()
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 5)
        root.setSpacing(4)


        self.label_src = QLabel("标注数据文件夹：");self.label_src.setFixedWidth(120)
        self.ed_src = QLineEdit();self.ed_src.setText("C:/Users/Administrator/Desktop/test")
        btn_src = StyledButton("选择文件夹", "select_bt"); btn_src.clicked.connect(self._pick_src)
        self.row_src = QWidget(); r0 = QtWidgets.QHBoxLayout(self.row_src); r0.setContentsMargins(0,0,0,0); r0.setSpacing(5)
        r0.addWidget(self.label_src); r0.addWidget(self.ed_src, 1); r0.addWidget(btn_src)
        root.addWidget(self.row_src)

        self.lbl_cls_b = QLabel("分类文本文件：");self.lbl_cls_b.setFixedWidth(120)
        self.ed_cls_b = QLineEdit(); self.ed_cls_b.setText("C:/Users/Administrator/Desktop/classes.txt")
        btn_cls = StyledButton("选择文件", "select_bt"); btn_cls.clicked.connect(self._pick_cls)
        self.row_cls = QWidget(); r1 = QtWidgets.QHBoxLayout(self.row_cls); r1.setContentsMargins(0,0,0,0); r1.setSpacing(5)
        r1.addWidget(self.lbl_cls_b); r1.addWidget(self.ed_cls_b, 1); r1.addWidget(btn_cls)
        root.addWidget(self.row_cls)

        # 数据集划分比例、格式、持久化, 放到一个行中显示
        #显示行
        self.row_ratio_fmt_persist = QWidget(); row_mix = QtWidgets.QHBoxLayout(self.row_ratio_fmt_persist); row_mix.setContentsMargins(0,0,0,0); row_mix.setSpacing(100)
        # 数据集划分比例布局
        self.lbl_ratio_b = QLabel("划分数据集比例(训练集:验证集:测试集):");self.lbl_ratio_b.setFixedWidth(220)
        self.sp_train_b = QSpinBox(); self.sp_train_b.setRange(0, 10); self.sp_train_b.setValue(9); self.sp_train_b.setFixedWidth(60)
        self.sp_val_b = QSpinBox(); self.sp_val_b.setRange(0, 10); self.sp_val_b.setValue(1); self.sp_val_b.setFixedWidth(60)
        self.sp_test_b = QSpinBox(); self.sp_test_b.setRange(0, 10); self.sp_test_b.setValue(0); self.sp_test_b.setFixedWidth(60)
        self.sp_train_b.valueChanged.connect(self._validate_ratios)
        self.sp_val_b.valueChanged.connect(self._validate_ratios)
        self.sp_test_b.valueChanged.connect(self._validate_ratios)
        ratio_box = QWidget(); hb = QtWidgets.QHBoxLayout(ratio_box); hb.setContentsMargins(0,0,0,0); hb.setSpacing(5)
        hb.addWidget(self.sp_train_b);hb.addWidget(QLabel(":"))
        # hb.addItem(QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        hb.addWidget(self.sp_val_b);hb.addWidget(QLabel(":"))
        hb.addWidget(self.sp_test_b)
        hb.addStretch(1)
        self.row_ratio = QWidget(); r2 = QtWidgets.QHBoxLayout(self.row_ratio); r2.setContentsMargins(0,0,0,0); r2.setSpacing(0)

        r2.addWidget(self.lbl_ratio_b); r2.addWidget(ratio_box, 1)
    
    


        self.lbl_fmt = QLabel("数据集格式：")
        self.cb_fmt = QComboBox(); self.cb_fmt.addItems(["TXT"]);self.cb_fmt.addItems(["COCO"]);self.cb_fmt.setCurrentIndex(0)
        self.cb_fmt.setFixedWidth(70)
        self.row_fmt = QWidget(); r3 = QtWidgets.QHBoxLayout(self.row_fmt); r3.setContentsMargins(0,0,0,0); r3.setSpacing(5)
        r3.addWidget(self.lbl_fmt); r3.addWidget(self.cb_fmt, 1)
        r3.addStretch(1)
      
        row_mix.addWidget(self.row_fmt)
        row_mix.addWidget(self.row_ratio)
        row_mix.addStretch(1)
        root.addWidget(self.row_ratio_fmt_persist)


        self.ed_out = QLineEdit(); self.ed_out.setText("C:/Users/Administrator/Desktop/持久化")
        self.btn_out = StyledButton("选择输出目录", "select_bt"); self.btn_out.clicked.connect(self._pick_out)
        self.row_out = QWidget(); r5 = QtWidgets.QHBoxLayout(self.row_out); r5.setContentsMargins(0,0,0,0); r5.setSpacing(5)
        r5.addWidget(self.ed_out, 1); r5.addWidget(self.btn_out)
        root.addWidget(self.row_out)

    
        self.lbl_error = QLabel()
        self.lbl_error.setStyleSheet("color:#141311;font-size:12px;padding:6px 8px;background-color:#AEE38A;border:1px solid #AEE38A;border-radius:6px;")
        self.lbl_error.setVisible(False)
        self.error_box = QWidget()
        self.error_box.setFixedHeight(38)
        err_layout = QHBoxLayout(self.error_box)
        err_layout.setContentsMargins(0, 0, 0, 0)
        err_layout.setSpacing(0)
        err_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        err_layout.addWidget(self.lbl_error)
        root.addWidget(self.error_box)
       

        
        self.btn_build = StyledButton("开始构建", "primary")
        self.btn_build.setFixedSize(200, 50)
        self.btn_build.clicked.connect(self._do_build)

        self.row_one_step_button = QWidget(); r6 = QtWidgets.QHBoxLayout(self.row_one_step_button); r6.setContentsMargins(0,5,0,5); r6.setSpacing(5)
        r6.addStretch(1); r6.addWidget(self.btn_build); r6.addStretch(1)
        self.row_one_step_button.setMinimumHeight(60)
        self.row_one_step_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        root.addWidget(self.row_one_step_button)

        self.log_panel = LogPanelWidget("处理日志")
        root.addWidget(self.log_panel)
        self._validate_ratios()

    def append_log(self, s: str):
        self.log_panel.append(s)
        
    def _validate_ratios(self):
        train = self.sp_train_b.value()
        val = self.sp_val_b.value()
        test = self.sp_test_b.value()
        total = train + val + test
        if total != 10:
            self.lbl_error.setText(f"温馨提示：比例总和需要为10，否则无法开启一键训练,当前总和为{total}")
            self.lbl_error.setVisible(True)
            try:
                self.error_box.setFixedHeight(38)
            except Exception:
                pass
            self.btn_build.setEnabled(False)
        else:
            self.lbl_error.setVisible(False)
            try:
                self.error_box.setFixedHeight(0)
            except Exception:
                pass
            self.btn_build.setEnabled(True)

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
            
    def _do_build(self):

        if not self.ed_src.text().strip():
            QtWidgets.QMessageBox.warning(self, "警告！", "标注数据集文件夹路径不可为空！请检查后再执行操作。")
            return
        if not self.ed_cls_b.text().strip():
            QtWidgets.QMessageBox.warning(self, "警告！", "类别文件路径不可为空！请检查后再执行操作。")
            return
        if not self.ed_out.text().strip():
            QtWidgets.QMessageBox.warning(self, "警告！", "结果输出路径不可为空！请检查后再执行操作。")
            return

        self.btn_build.setEnabled(False); self.btn_build.setText("构建中")
        src = self.ed_src.text().strip()
        cls = self.ed_cls_b.text().strip()
        ratios = (self.sp_train_b.value(), self.sp_val_b.value(), self.sp_test_b.value())
        out_dir = self.ed_out.text().strip() or None
        fmt = self.cb_fmt.currentText().strip()
        self.datasetBuilt.emit(src, cls, ratios, out_dir, fmt)
        # root, yaml_path = build_yolo_dataset(src, cls, ratios, persist, out_dir)
        self.btn_build.setEnabled(True); self.btn_build.setText("构建数据集")