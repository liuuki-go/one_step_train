import os
import sys
import yaml
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFileDialog, QLineEdit, QSpinBox, QCheckBox, QComboBox, QTextEdit, QStackedWidget, QScrollArea, QFormLayout, QMessageBox, QDoubleSpinBox, QDialog, QListWidget, QListWidgetItem
from PySide6.QtCore import QThread, Signal
from core.dataset_builder import build_yolo_dataset
from core.wsl_runner import build_train_cmd, run_stream
from gui.monitor_widget import MonitorWidget

class LogThread(QThread):
    line = Signal(str)
    done = Signal(int)
    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd
    def run(self):
        rc = run_stream(self.cmd, lambda s: self.line.emit(s))
        self.done.emit(rc)

class MainFrame(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("一键训练")
        self.resize(1200, 800)
        self._init_ui()
        self.dataset_root = None
        self.dataset_yaml = None
        self.log_thread = None
    def _on_load_cfg_clicked(self):
        try:
            self._load_cfg_full()
        except Exception:
            pass
    def _on_save_cfg_clicked(self):
        try:
            self._save_cfg_full()
        except Exception:
            pass
    def _on_export_cfg_clicked(self):
        try:
            self._export_cfg()
        except Exception:
            pass
    def _on_page_changed(self, idx):
        self.console.setVisible(idx != 3)
    def _make_editor(self, key, val):
        if isinstance(val, bool):
            w = QCheckBox()
            w.setChecked(val)
            return w
        if isinstance(val, int):
            w = QSpinBox()
            w.setRange(-1000000, 1000000)
            w.setValue(val)
            return w
        if isinstance(val, float):
            w = QDoubleSpinBox()
            w.setRange(-1e9, 1e9)
            w.setDecimals(6)
            w.setSingleStep(0.1)
            w.setValue(val)
            return w
        if isinstance(val, (list, dict)) or val is None:
            w = QLineEdit(yaml.safe_dump(val, allow_unicode=True, sort_keys=False) if not isinstance(val, str) else str(val))
            return w
        w = QLineEdit(str(val))
        return w
    def _load_cfg_full(self):
        p = self.ed_cfg_path.text().strip()
        if not p:
            return
        with open(p, "r", encoding="utf-8") as f:
            d = yaml.safe_load(f) or {}
        while self.form_all.rowCount():
            self.form_all.removeRow(0)
        self.cfg_editors.clear()
        for k, v in d.items():
            w = self._make_editor(k, v)
            self.form_all.addRow(QLabel(k), w)
            self.cfg_editors[k] = w
    def _save_cfg_full(self):
        p = self.ed_cfg_path.text().strip()
        if not p:
            return
        with open(p, "r", encoding="utf-8") as f:
            d = yaml.safe_load(f) or {}
        out = {}
        for k, old in d.items():
            w = self.cfg_editors.get(k)
            if w is None:
                out[k] = old
                continue
            if isinstance(old, bool):
                out[k] = bool(w.isChecked())
            elif isinstance(old, int):
                out[k] = int(w.value())
            elif isinstance(old, float):
                out[k] = float(w.value())
            elif isinstance(old, (list, dict)) or old is None:
                try:
                    out[k] = yaml.safe_load(w.text())
                except Exception:
                    QMessageBox.warning(self, "错误", f"字段 {k} 无法解析为有效结构")
                    return
            else:
                out[k] = w.text()
        with open(p, "w", encoding="utf-8") as f:
            yaml.safe_dump(out, f, allow_unicode=True, sort_keys=False)
        QMessageBox.information(self, "成功", "配置已保存")
    def _export_cfg(self):
        p = self.ed_cfg_path.text().strip()
        if not p:
            return
        with open(p, "r", encoding="utf-8") as f:
            d = yaml.safe_load(f) or {}
        for k in list(d.keys()):
            w = self.cfg_editors.get(k)
            if w is None:
                continue
            if isinstance(d[k], bool):
                d[k] = bool(w.isChecked())
            elif isinstance(d[k], int):
                d[k] = int(w.value())
            elif isinstance(d[k], float):
                d[k] = float(w.value())
            elif isinstance(d[k], (list, dict)) or d[k] is None:
                try:
                    d[k] = yaml.safe_load(w.text())
                except Exception:
                    QMessageBox.warning(self, "错误", f"字段 {k} 无法解析为有效结构")
                    return
            else:
                d[k] = w.text()
        tgt, _ = QFileDialog.getSaveFileName(self, "导出配置", filter="YAML (*.yaml)")
        if not tgt:
            return
        with open(tgt, "w", encoding="utf-8") as f:
            yaml.safe_dump(d, f, allow_unicode=True, sort_keys=False)
        QMessageBox.information(self, "成功", "配置已导出")
    def _init_ui(self):
        cw = QWidget()
        self.setCentralWidget(cw)
        root = QHBoxLayout(cw)
        left_container = QWidget()
        left_container.setStyleSheet("QWidget{background:#f6f8fa;border-right:1px solid #e1e4e8;}")
        left = QVBoxLayout(left_container)
        center = QVBoxLayout()
        right = QVBoxLayout()
        left_container.setFixedWidth(160)
        root.addWidget(left_container, 1)
        root.addLayout(center, 2)
        root.addLayout(right, 1)
        mb = self.menuBar()
        mb.setStyleSheet("QMenuBar{background:#f8f8f8;border-bottom:1px solid #d0d0d0;} QMenuBar::item{padding:6px 12px;}")
        lang_menu = mb.addMenu("语言")
        act_zh = lang_menu.addAction("中文")
        act_en = lang_menu.addAction("English")
        act_zh.triggered.connect(lambda: self._set_lang("zh"))
        act_en.triggered.connect(lambda: self._set_lang("en"))
        sys_menu = mb.addMenu("系统设置")
        act_sys = sys_menu.addAction("打开设置")
        act_sys.triggered.connect(self._open_sys_settings)
        btn_one = QPushButton("一键训练")
        btn_build = QPushButton("数据集构建")
        btn_run = QPushButton("开始训练")
        btn_cfg = QPushButton("训练配置")
        st = self.style()
        btn_one.setIcon(st.standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        btn_build.setIcon(st.standardIcon(QtWidgets.QStyle.SP_DirIcon))
        btn_run.setIcon(st.standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        btn_cfg.setIcon(st.standardIcon(QtWidgets.QStyle.SP_FileDialogDetailedView))
        for b in (btn_one, btn_build, btn_run, btn_cfg):
            b.setCheckable(True)
            b.setStyleSheet(
                "QPushButton{font-size:16px;padding:12px 14px;text-align:left;border-radius:10px;}"
                "QPushButton:checked{background:#e6f0ff;color:#0366d6;}"
                "QPushButton:hover{background:#f0f6ff;}"
            )
        left.addWidget(btn_one)
        left.addWidget(btn_build)
        left.addWidget(btn_run)
        left.addWidget(btn_cfg)
        left.addStretch(1)
        group = QtWidgets.QButtonGroup(self)
        group.setExclusive(True)
        for i, b in enumerate((btn_one, btn_build, btn_run, btn_cfg)):
            group.addButton(b, i)
        btn_one.setChecked(True)
        group.idClicked.connect(lambda i: self.stack.setCurrentIndex(i))
        self.stack = QStackedWidget()
        center.addWidget(self.stack)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setLineWrapMode(QTextEdit.NoWrap)
        self.console.setStyleSheet('QTextEdit{font-family:Consolas, "Courier New", monospace; font-size:12px;}')
        center.addWidget(self.console)
        self.page_one = self._build_one_page()
        self.page_build = self._build_build_page()
        self.page_run = self._build_run_page()
        self.page_cfg = self._build_cfg_page()
        self.stack.addWidget(self.page_one)
        self.stack.addWidget(self.page_build)
        self.stack.addWidget(self.page_run)
        self.stack.addWidget(self.page_cfg)
        # idClicked handles switching
        self.stack.currentChanged.connect(self._on_page_changed)
        self.monitor = MonitorWidget()
        right.addWidget(self.monitor)
        try:
            cfg = yaml.safe_load(open(os.path.join(os.getcwd(), "sys_config.yaml"), "r", encoding="utf-8")) or {}
            wsl = cfg.get("wsl", {})
            cp = None
            if isinstance(wsl, dict):
                cp = wsl.get("conda", {}).get("env_path") if isinstance(wsl.get("conda"), dict) else None
            if isinstance(cp, str) and cp:
                self.ed_conda.setText(cp)
        except Exception:
            pass
    def _build_one_page(self):
        w = QWidget()
        form = QGridLayout(w)
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
        self.cb_fmt = QComboBox(); self.cb_fmt.addItems(["YOLO"])
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
        self.btn_run_one.clicked.connect(self._run_one)
        form.addWidget(self.btn_run_one, 6, 1)
        return w
    def _build_build_page(self):
        w = QWidget()
        form = QGridLayout(w)
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
        return w
    def _build_run_page(self):
        w = QWidget()
        form = QGridLayout(w)
        self.lbl_yaml = QLabel("数据集文件夹")
        self.ed_yaml = QLineEdit()
        b1 = QPushButton("选择"); b1.clicked.connect(self._pick_yaml_dir)
        form.addWidget(self.lbl_yaml, 0, 0)
        form.addWidget(self.ed_yaml, 0, 1)
        form.addWidget(b1, 0, 2)
        self.lbl_conda = QLabel("Conda基路径(WSL)")
        self.ed_conda = QLineEdit("/home/meineng/enter")
        form.addWidget(self.lbl_conda, 1, 0)
        form.addWidget(self.ed_conda, 1, 1)
        self.btn_run_train = QPushButton("开始训练")
        self.btn_run_train.clicked.connect(self._run_train)
        form.addWidget(self.btn_run_train, 2, 1)
        return w
    def _build_cfg_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        form_top = QGridLayout()
        self.lbl_cfg_path = QLabel("train_conf.yaml")
        self.ed_cfg_path = QLineEdit(os.path.join(os.getcwd(), "train", "config", "train_conf.yaml"))
        b0 = QPushButton("选择"); b0.clicked.connect(self._pick_cfg)
        form_top.addWidget(self.lbl_cfg_path, 0, 0)
        form_top.addWidget(self.ed_cfg_path, 0, 1)
        form_top.addWidget(b0, 0, 2)
        layout.addLayout(form_top)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.cfg_panel = QWidget()
        self.form_all = QFormLayout(self.cfg_panel)
        self.scroll.setWidget(self.cfg_panel)
        layout.addWidget(self.scroll)
        btns = QHBoxLayout()
        self.btn_load_cfg = QPushButton("加载配置")
        self.btn_save_cfg = QPushButton("保存配置")
        self.btn_export_cfg = QPushButton("导出配置")
        self.btn_load_cfg.clicked.connect(self._on_load_cfg_clicked)
        self.btn_save_cfg.clicked.connect(self._on_save_cfg_clicked)
        self.btn_export_cfg.clicked.connect(self._on_export_cfg_clicked)
        btns.addWidget(self.btn_load_cfg)
        btns.addWidget(self.btn_save_cfg)
        btns.addWidget(self.btn_export_cfg)
        layout.addLayout(btns)
        self.cfg_editors = {}
        return w
    def _set_lang(self, lang: str):
        if lang == "en":
            self.setWindowTitle("One-Click Train")
            pass
        else:
            self.setWindowTitle("一键训练")
            pass
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
    def _append_log(self, s: str):
        self.console.append(s)
    def _run_one(self):
        src = self.ed_src.text().strip()
        cls = self.ed_cls.text().strip()
        if not src or not cls:
            self._append_log("参数不完整")
            return
        ratios = (self.sp_train.value(), self.sp_val.value(), self.sp_test.value())
        persist = self.ck_persist.isChecked()
        out_dir = self.ed_out.text().strip() if persist else None
        root, yaml_path = build_yolo_dataset(src, cls, ratios, persist, out_dir)
        self.dataset_root = root
        self.dataset_yaml = yaml_path
        start_py = os.path.join(os.getcwd(), "train", "start.py")
        cmd = build_train_cmd(start_py, root)
        self._append_log("启动训练")
        try:
            self._append_log("命令: " + " ".join(cmd))
        except Exception:
            pass
        self.log_thread = LogThread(cmd)
        self.log_thread.line.connect(self._append_log)
        self.log_thread.done.connect(lambda rc: self._append_log(f"训练结束 {rc}"))
        self.log_thread.start()
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
            self._append_log("参数不完整")
            return
        ratios = (self.sp_train_b.value(), self.sp_val_b.value(), self.sp_test_b.value())
        persist = self.ck_persist_b.isChecked()
        out_dir = self.ed_out_b.text().strip() if persist else None
        root, yaml_path = build_yolo_dataset(src, cls, ratios, persist, out_dir)
        self.dataset_root = root
        self.dataset_yaml = yaml_path
        self._append_log(f"数据集构建完成 {root}")
    def _pick_yaml_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择数据集文件夹")
        if d:
            self.ed_yaml.setText(d)
    def _run_train(self):
        dp = self.ed_yaml.text().strip() or (self.dataset_root or "")
        if not dp:
            self._append_log("缺少数据集文件夹")
            return
        start_py = os.path.join(os.getcwd(), "train", "start.py")
        conda_base = self.ed_conda.text().strip() or None
        cmd = build_train_cmd(start_py, dp, conda_base=conda_base)
        self._append_log("启动训练")
        try:
            self._append_log("命令: " + " ".join(cmd))
        except Exception:
            pass
        self.log_thread = LogThread(cmd)
        self.log_thread.line.connect(self._append_log)
        self.log_thread.done.connect(lambda rc: self._append_log(f"训练结束 {rc}"))
        self.log_thread.start()
    def _open_sys_settings(self):
        p = os.path.join(os.getcwd(), "sys_config.yaml")
        dlg = SystemSettingsDialog(self, p)
        dlg.exec()
    def _pick_cfg(self):
        p, _ = QFileDialog.getOpenFileName(self, "选择配置", filter="YAML (*.yaml)")
        if p:
            self.ed_cfg_path.setText(p)

class SystemSettingsDialog(QDialog):
    def __init__(self, parent, path: str):
        super().__init__(parent)
        self.setWindowTitle("系统设置")
        self.resize(800, 500)
        self.path = path
        self.data = {}
        root = QHBoxLayout(self)
        self.left = QListWidget()
        self.left.setFixedWidth(180)
        self.mid = QListWidget()
        self.mid.setFixedWidth(200)
        self.right = QScrollArea()
        self.right.setWidgetResizable(True)
        self.panel = QWidget()
        self.form = QFormLayout(self.panel)
        self.right.setWidget(self.panel)
        self.right.setStyleSheet(
            "QScrollArea{background:#0d0f13;border:1px solid #22262e;}"
            "QWidget{background:#0d0f13;}"
        )
        self.setStyleSheet(
            "QDialog{background:#0f1115;color:#e6edf3;}"
            "QListWidget{background:#0d0f13;border:1px solid #22262e;color:#e6edf3;}"
            "QLabel{color:#c9d1d9;}"
            "QLineEdit, QSpinBox, QDoubleSpinBox{background:#0d0f13;border:1px solid #30363d;color:#e6edf3;padding:4px;border-radius:6px;}"
            "QPushButton{background:#1f6feb;color:#fff;border:none;padding:6px 10px;border-radius:6px;}"
            "QPushButton:hover{background:#388bfd;}"
        )
        btns = QHBoxLayout()
        self.btn_close = QPushButton("关闭")
        self.btn_close.clicked.connect(self.close)
        root.addWidget(self.left)
        root.addWidget(self.mid)
        root.addWidget(self.right, 1)
        root.addLayout(btns)
        self.row_paths = []
        self._load()
        self.left.currentRowChanged.connect(self._switch)
        self.mid.currentRowChanged.connect(self._switch2)
        if self.left.count():
            self.left.setCurrentRow(0)
            self._switch(0)
    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = yaml.safe_load(f) or {}
        except Exception:
            self.data = {}
        self.left.clear()
        for k in self.data.keys():
            self.left.addItem(QListWidgetItem(str(k)))
    def _make_editor(self, val):
        if isinstance(val, bool):
            w = QCheckBox(); w.setChecked(val); return w
        if isinstance(val, int):
            w = QSpinBox(); w.setRange(-10**9, 10**9); w.setValue(val); return w
        if isinstance(val, float):
            w = QDoubleSpinBox(); w.setRange(-1e9, 1e9); w.setDecimals(6); w.setValue(val); return w
        if isinstance(val, (list, dict)) or val is None:
            w = QLineEdit(yaml.safe_dump(val, allow_unicode=True, sort_keys=False) if not isinstance(val, str) else str(val)); return w
        return QLineEdit(str(val))
    def _switch(self, idx: int):
        try:
            self._apply_current()
        except Exception:
            pass
        while self.form.rowCount():
            self.form.removeRow(0)
        if idx < 0:
            return
        key = self.left.item(idx).text()
        section = self.data.get(key, {})
        if not isinstance(section, dict):
            section = {key: section}
        self._populate_mid(section)
        if self.mid.count():
            self.mid.setCurrentRow(0)
    def _populate_mid(self, section: dict):
        self.mid.clear()
        for k in section.keys():
            self.mid.addItem(QListWidgetItem(str(k)))
        self._current_section = section
    def _switch2(self, idx: int):
        try:
            self._apply_current()
        except Exception:
            pass
        while self.form.rowCount():
            self.form.removeRow(0)
        if idx < 0:
            return
        left_idx = self.left.currentRow()
        if left_idx < 0:
            return
        left_key = self.left.item(left_idx).text()
        mid_key = self.mid.item(idx).text()
        section2 = self._current_section.get(mid_key, {}) if isinstance(self._current_section, dict) else {}
        path = [mid_key]
        if isinstance(section2, dict):
            # render scalar children directly as third-level
            scalar_items = {k: v for k, v in section2.items() if not isinstance(v, dict)}
            nested_items = {k: v for k, v in section2.items() if isinstance(v, dict)}
            if scalar_items:
                self.form.addRow(QLabel(f"{left_key} / {mid_key}"), QLabel(""))
                for k, v in scalar_items.items():
                    ed = self._make_editor(v)
                    ed.setProperty("yaml_path", path + [k])
                    self.form.addRow(QLabel(str(k)), ed)
            if nested_items:
                self._populate_form(nested_items, level=2, parent_path=path)
        else:
            self._populate_form({mid_key: section2}, level=2, parent_path=[mid_key])
    def _populate_form(self, d: dict, level: int, parent_path=None):
        if parent_path is None:
            parent_path = []
        for k, v in d.items():
            if isinstance(v, dict) and level < 3:
                # if children are scalars, render them directly as third-level
                if all(not isinstance(sv, dict) for sv in v.values()):
                    self.form.addRow(QLabel(str(k)), QLabel(""))
                    for sk, sv in v.items():
                        ed = self._make_editor(sv)
                        ed.setProperty("yaml_path", parent_path + [k, sk])
                        self.form.addRow(QLabel(str(sk)), ed)
                else:
                    self.form.addRow(QLabel(str(k)), QLabel(""))
                    self._populate_form(v, level + 1, parent_path + [k])
            else:
                ed = self._make_editor(v)
                ed.setProperty("yaml_path", parent_path + [k])
                self.form.addRow(QLabel(str(k)), ed)
    def _get_by_path(self, d, path):
        cur = d
        for k in path:
            if not isinstance(cur, dict) or k not in cur:
                return None
            cur = cur[k]
        return cur
    def _set_by_path(self, d, path, value):
        cur = d
        for k in path[:-1]:
            if k not in cur or not isinstance(cur[k], dict):
                cur[k] = {}
            cur = cur[k]
        cur[path[-1]] = value
    def _collect(self) -> dict:
        idx = self.left.currentRow()
        if idx < 0:
            return {}
        key = self.left.item(idx).text()
        section = self.data.get(key, {})
        out = yaml.safe_load(yaml.safe_dump(section, allow_unicode=True, sort_keys=False)) if isinstance(section, dict) else {}
        i = 0
        while i < self.form.rowCount():
            lab = self.form.itemAt(i, QFormLayout.LabelRole).widget()
            fld = self.form.itemAt(i, QFormLayout.FieldRole).widget()
            if isinstance(fld, QLabel) and lab and lab.text():
                i += 1
                continue
            path = fld.property("yaml_path") or []
            old = self._get_by_path(section, path)
            if isinstance(old, bool):
                val = bool(fld.isChecked())
            elif isinstance(old, int):
                val = int(fld.value())
            elif isinstance(old, float):
                val = float(fld.value())
            elif isinstance(old, (list, dict)) or old is None:
                try:
                    val = yaml.safe_load(fld.text())
                except Exception:
                    val = fld.text()
            else:
                val = fld.text()
            self._set_by_path(out, path, val)
            i += 1
        return {key: out}
    def _apply_current(self):
        idx = self.left.currentRow()
        if idx is None or idx < 0:
            return
        key = self.left.item(idx).text()
        upd = self._collect().get(key, {})
        if isinstance(upd, dict):
            self.data[key] = upd
    def closeEvent(self, e):
        try:
            self._apply_current()
            if self.path:
                with open(self.path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(self.data, f, allow_unicode=True, sort_keys=False)
        except Exception:
            pass
        e.accept()
    def _on_page_changed(self, idx):
        self.console.setVisible(idx != 3)