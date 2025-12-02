import yaml
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QDialog, QHBoxLayout, QListWidget, QListWidgetItem, QScrollArea, QWidget, QFormLayout, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, QMessageBox

class SystemSettingsDialog(QDialog):
    """系统设置对话框：
    - 左列顶层键；中列二级键；右侧表单渲染第三级及以下标量字段
    - 切换分组前缓存当前编辑；关闭即保存到 `sys_config.yaml`
    """
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
        btns = QtWidgets.QHBoxLayout()
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
            lab = self.form.itemAt(i, QFormLayout.ItemRole.LabelRole).widget()
            fld = self.form.itemAt(i, QFormLayout.ItemRole.FieldRole).widget()
            if isinstance(fld, QLabel) and lab and lab.text():  #type: ignore
                i += 1
                continue
            if fld is None:
                i += 1
                continue
            path = fld.property("yaml_path") or []
            old = self._get_by_path(section, path)
            if isinstance(old, bool):
                val = bool(fld.isChecked()) #type: ignore
            elif isinstance(old, int):
                val = int(fld.value()) #type: ignore
            elif isinstance(old, float):
                val = float(fld.value()) #type: ignore
            elif isinstance(old, (list, dict)) or old is None:
                try:
                    val = yaml.safe_load(fld.text()) #type: ignore
                except Exception:
                    val = fld.text() #type: ignore
            else:
                val = fld.text() #type: ignore
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