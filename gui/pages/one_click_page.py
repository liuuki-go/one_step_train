from PySide6 import QtWidgets
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QSpinBox, QCheckBox, QComboBox, QHBoxLayout, QSpacerItem, QSizePolicy
from gui.style.ButtonStyleManager import StyledButton
from gui.style.CheckButtonStyleManager import StyledCheckBox
from PySide6.QtCore import Qt


class OneClickPageWidget(QWidget):
    oneClickRequested = Signal(str, str, tuple, bool, object, str, str)
    def __init__(self):
        super().__init__()
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 5)
        root.setSpacing(4)


        self.label_src = QLabel("标注数据文件夹：");self.label_src.setFixedWidth(120)
        self.ed_src = QLineEdit();self.ed_src.setText("C:/Users/zx123/Desktop/test")
        btn_src = StyledButton("选择文件夹", "select_bt"); btn_src.clicked.connect(self._pick_src)
        self.row_src = QWidget(); r0 = QtWidgets.QHBoxLayout(self.row_src); r0.setContentsMargins(0,0,0,0); r0.setSpacing(5)
        r0.addWidget(self.label_src); r0.addWidget(self.ed_src, 1); r0.addWidget(btn_src)
        root.addWidget(self.row_src)

        self.lbl_cls_b = QLabel("分类文本文件：");self.lbl_cls_b.setFixedWidth(120)
        self.ed_cls_b = QLineEdit(); self.ed_cls_b.setText("C:/Users/zx123/Desktop/classes.txt")
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
      

        # 持久化数据集布局
        self.ck_persist = StyledCheckBox("是否持久化数据集:"); self.ck_persist.setChecked(False); self.ck_persist.clicked.connect(self._on_persist_changed)
        self.row_persist = QWidget(); r4 = QtWidgets.QHBoxLayout(self.row_persist); r4.setContentsMargins(5,0,0,0)
        r4.addWidget(self.ck_persist)

        row_mix.addWidget(self.row_persist)
        row_mix.addWidget(self.row_fmt)
        row_mix.addWidget(self.row_ratio)
        row_mix.addStretch(1)
        root.addWidget(self.row_ratio_fmt_persist)



 


  

        self.ed_out = QLineEdit()
        self.btn_out = StyledButton("选择输出目录", "select_bt"); self.btn_out.clicked.connect(self._pick_out)
        self.row_out = QWidget(); r5 = QtWidgets.QHBoxLayout(self.row_out); r5.setContentsMargins(0,0,0,0); r5.setSpacing(5)
        r5.addWidget(self.ed_out, 1); r5.addWidget(self.btn_out)
        self.ed_out.setVisible(False)
        self.btn_out.setVisible(False)
        root.addWidget(self.row_out)


        self.lb_out_src = QLabel("结果输出路径：");self.lb_out_src.setFixedWidth(120)
        self.ed_out_src = QLineEdit()
        import os
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        self.ed_out_src.setText(desktop)
        btn_out_src = StyledButton("选择文件夹", "select_bt"); btn_out_src.clicked.connect(self._pick_out_src)
        self.row_out_src = QWidget(); r6 = QtWidgets.QHBoxLayout(self.row_out_src); r6.setContentsMargins(0,0,0,0); r6.setSpacing(5)
        r6.addWidget(self.lb_out_src); r6.addWidget(self.ed_out_src, 1); r6.addWidget(btn_out_src)
        root.addWidget(self.row_out_src)


        self.btn_run_one = StyledButton("一键训练", "primary")
        self.btn_run_one.setFixedSize(200, 50)
        self.btn_run_one.clicked.connect(self._emit_one_click)

        self.row_one_step_button = QWidget(); r6 = QtWidgets.QHBoxLayout(self.row_one_step_button); r6.setContentsMargins(0,5,0,5); r6.setSpacing(5)
        r6.addStretch(1); r6.addWidget(self.btn_run_one); r6.addStretch(1)
        self.row_one_step_button.setMinimumHeight(60)
        self.row_one_step_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        root.addWidget(self.row_one_step_button)
        
    
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
        self._validate_ratios()

    def _on_persist_changed(self):
        vis = self.ck_persist.isChecked()
        self.ed_out.setVisible(vis)
        self.btn_out.setVisible(vis)
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
            self.btn_run_one.setEnabled(False)
        else:
            self.lbl_error.setVisible(False)
            try:
                self.error_box.setFixedHeight(0)
            except Exception:
                pass
            self.btn_run_one.setEnabled(True)
            
    def _pick_src(self):
        d = QFileDialog.getExistingDirectory(self, "选择标注文件夹")
        if d:
            self.ed_src.setText(d)

    def _pick_out_src(self):
        d = QFileDialog.getExistingDirectory(self, "选择标注文件夹")
        if d:
            self.ed_out_src.setText(d)
    def _pick_cls(self):
        p, _ = QFileDialog.getOpenFileName(self, "选择 classes.txt", filter="Text (*.txt)")
        if p:
            self.ed_cls_b.setText(p)
    def _pick_out(self):
        d = QFileDialog.getExistingDirectory(self, "选择输出数据集路径")
        if d:
            self.ed_out.setText(d)
    def _emit_one_click(self):
        #判断输入合法性
        if not self.ed_src.text().strip():
            QtWidgets.QMessageBox.warning(self, "警告！", "标注数据集文件夹路径不可为空！请检查后再执行操作。")
            return
        if not self.ed_cls_b.text().strip():
            QtWidgets.QMessageBox.warning(self, "警告！", "类别文件路径不可为空！请检查后再执行操作。")
            return
        if self.ck_persist.isChecked() and not self.ed_out.text().strip():
            QtWidgets.QMessageBox.warning(self, "警告！", "已选择持久化数据集，输出数据集路径不可为空！请检查后再执行操作。")
            return
        if not self.ed_out_src.text().strip():
            QtWidgets.QMessageBox.warning(self, "警告！", "结果输出路径不可为空！请检查后再执行操作。")
            return
        
    

        self.btn_run_one.setEnabled(False); self.btn_run_one.setText("训练中")
        src = self.ed_src.text().strip()
        cls = self.ed_cls_b.text().strip()
        ratios = (self.sp_train_b.value(), self.sp_val_b.value(), self.sp_test_b.value())
        persist = self.ck_persist.isChecked()
        out_dir = self.ed_out.text().strip() or None
        out_src = self.ed_out_src.text().strip()
        fmt = self.cb_fmt.currentText()
        self.oneClickRequested.emit(src, cls, ratios, persist, out_dir,out_src,fmt)
        
  