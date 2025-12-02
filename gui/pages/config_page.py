import os
import yaml
from PySide6 import QtWidgets
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QScrollArea, QFormLayout

class ConfigPageWidget(QWidget):
    """训练配置页：加载 YAML，生成编辑器，支持保存与导出。"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        form_top = QGridLayout()
        self.lbl_cfg_path = QLabel("train_conf.yaml")
        self.ed_cfg_path = QLineEdit(os.path.join(os.getcwd(), "train", "config", "train_conf.yaml"))
        b0 = QPushButton("选择"); b0.clicked.connect(self._pick_cfg)
        form_top.addWidget(self.lbl_cfg_path, 0, 0)
        form_top.addWidget(self.ed_cfg_path, 0, 1)
        form_top.addWidget(b0, 0, 2)
        layout.addLayout(form_top)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.cfg_panel = QWidget()
        self.form_all = QFormLayout(self.cfg_panel)
        self.scroll_area.setWidget(self.cfg_panel)
        layout.addWidget(self.scroll_area)
        btns = QtWidgets.QHBoxLayout()
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
        try:
            self._on_load_cfg_clicked()
        except Exception:
            pass
    def _pick_cfg(self):
        p, _ = QFileDialog.getOpenFileName(self, "选择配置", filter="YAML (*.yaml)")
        if p:
            self.ed_cfg_path.setText(p)
    def _make_editor(self, key, val):
        if isinstance(val, bool):
            w = QtWidgets.QCheckBox(); w.setChecked(val); return w
        if isinstance(val, int):
            w = QtWidgets.QSpinBox(); w.setRange(-10**9, 10**9); w.setValue(val); return w
        if isinstance(val, float):
            w = QtWidgets.QDoubleSpinBox(); w.setRange(-1e9, 1e9); w.setDecimals(6); w.setValue(val); return w
        if isinstance(val, (list, dict)) or val is None:
            w = QtWidgets.QLineEdit(yaml.safe_dump(val, allow_unicode=True, sort_keys=False) if not isinstance(val, str) else str(val)); return w
        return QtWidgets.QLineEdit(str(val))
    def _on_load_cfg_clicked(self):
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
    def _on_save_cfg_clicked(self):
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
                    QtWidgets.QMessageBox.warning(self, "错误", f"字段 {k} 无法解析为有效结构")
                    return
            else:
                out[k] = w.text()
        with open(p, "w", encoding="utf-8") as f:
            yaml.safe_dump(out, f, allow_unicode=True, sort_keys=False)
        QtWidgets.QMessageBox.information(self, "成功", "配置已保存")
    def _on_export_cfg_clicked(self):
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
                    QtWidgets.QMessageBox.warning(self, "错误", f"字段 {k} 无法解析为有效结构")
                    return
            else:
                d[k] = w.text()
        tgt, _ = QFileDialog.getSaveFileName(self, "导出配置", filter="YAML (*.yaml)")
        if not tgt:
            return
        with open(tgt, "w", encoding="utf-8") as f:
            yaml.safe_dump(d, f, allow_unicode=True, sort_keys=False)
        QtWidgets.QMessageBox.information(self, "成功", "配置已导出")