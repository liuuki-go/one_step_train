from PySide6 import QtWidgets
from PySide6.QtCore import Signal, QThread
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QCheckBox, QButtonGroup, 
                               QFileDialog, QGroupBox, QMessageBox)
from gui.style.ButtonStyleManager import StyledButton
from gui.style.CheckButtonStyleManager import StyledCheckBox
from gui.style.RadioButtonStyleManager import StyledRadioButton
from core.label_processor import LabelProcessor
import os

class ProcessorThread(QThread):
    finished_signal = Signal(bool, str)

    def __init__(self, processor, mode, **kwargs):
        super().__init__()
        self.processor = processor
        self.mode = mode
        self.kwargs = kwargs

    def run(self):
        try:
            success = False
            if self.mode == "delete":
                success = self.processor.delete_labels(**self.kwargs)
            elif self.mode == "export":
                success = self.processor.export_labels(**self.kwargs)
            elif self.mode == "replace":
                success = self.processor.replace_labels(**self.kwargs)
            elif self.mode == "blank":
                success = self.processor.export_blank_images(**self.kwargs)
            
            msg = "处理完成" if success else "处理失败或被中断"
            self.finished_signal.emit(success, msg)
        except Exception as e:
            self.finished_signal.emit(False, str(e))

class LabelProcessorPageWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.processor_thread = None
        self.processor = None
        
        # 主布局
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # GroupBox 样式
        groupbox_style = """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
            }
        """
        

        # 1. 顶部：源目录设置
        self.gb_source = QGroupBox("数据源设置")
        self.gb_source.setStyleSheet(groupbox_style)
        layout_source = QVBoxLayout(self.gb_source)
        
        # 源目录行
        row_src = QWidget()
        layout_src_row = QHBoxLayout(row_src)
        layout_src_row.setContentsMargins(0, 0, 0, 0)
        self.lbl_src = QLabel("处理目录：")
        self.ed_src = QLineEdit()
        self.btn_src = StyledButton("选择目录", "select_bt")
        self.btn_src.clicked.connect(self._pick_src)
        
        layout_src_row.addWidget(self.lbl_src)
        layout_src_row.addWidget(self.ed_src)
        layout_src_row.addWidget(self.btn_src)
        
        # 递归选项
        self.ck_recursive = StyledCheckBox("递归处理子目录")
        self.ck_recursive.setChecked(True)
        
        layout_source.addWidget(row_src)
        layout_source.addWidget(self.ck_recursive)
        
        root.addWidget(self.gb_source)

        # 2. 中部：功能选择与参数配置
        self.gb_func = QGroupBox("功能选择")
        self.gb_func.setStyleSheet(groupbox_style)
        layout_func = QVBoxLayout(self.gb_func)
        
        # 功能单选按钮
        row_radios = QWidget()
        layout_radios = QHBoxLayout(row_radios)
        layout_radios.setContentsMargins(0, 0, 0, 0)
        
        self.bg_mode = QButtonGroup(self)
        self.rb_delete = StyledRadioButton("删除标签")
        self.rb_export = StyledRadioButton("导出标签")
        self.rb_replace = StyledRadioButton("替换标签")
        self.rb_blank = StyledRadioButton("导出空白图")
        
        
        self.bg_mode.addButton(self.rb_delete, 0)
        self.bg_mode.addButton(self.rb_export, 1)
        self.bg_mode.addButton(self.rb_replace, 2)
        self.bg_mode.addButton(self.rb_blank, 3)
        
        self.rb_delete.setChecked(True)
        
        layout_radios.addWidget(self.rb_delete)
        layout_radios.addWidget(self.rb_export)
        layout_radios.addWidget(self.rb_replace)
        layout_radios.addWidget(self.rb_blank)
        layout_radios.setSpacing(5)
        layout_radios.addStretch()
        
        layout_func.addWidget(row_radios)
        
        # 功能说明
        self.lbl_desc = QLabel()
        self.lbl_desc.setStyleSheet("color: #666; font-style: italic;")
        layout_func.addWidget(self.lbl_desc)
        
        # 参数配置区域
        self.gb_params = QGroupBox("参数配置")
        # 内部参数配置框不需要加粗加大，保持默认或跟随父级样式（这里不设置样式）
        layout_params = QVBoxLayout(self.gb_params)
        
        # 通用参数行：输出目录 (用于导出和空白图)
        self.row_out = QWidget()
        layout_out = QHBoxLayout(self.row_out)
        layout_out.setContentsMargins(0, 0, 0, 0)
        self.lbl_out = QLabel("输出目录：")
        self.ed_out = QLineEdit()
        self.btn_out = StyledButton("选择目录", "select_bt")
        self.btn_out.clicked.connect(self._pick_out)
        layout_out.addWidget(self.lbl_out)
        layout_out.addWidget(self.ed_out)
        layout_out.addWidget(self.btn_out)
        layout_params.addWidget(self.row_out)
        
        # 标签设置区域
        self.gb_labels = QWidget()
        layout_labels = QVBoxLayout(self.gb_labels)
        layout_labels.setContentsMargins(0, 0, 0, 0)
        
        # 目标标签 (删除/导出)
        self.row_target_labels = QWidget()
        layout_target = QHBoxLayout(self.row_target_labels)
        layout_target.setContentsMargins(0, 0, 0, 0)
        self.lbl_target = QLabel("目标标签：")
        self.ed_target = QLineEdit()
        self.ed_target.setPlaceholderText("多个标签请用逗号分隔")
        layout_target.addWidget(self.lbl_target)
        layout_target.addWidget(self.ed_target)
        layout_labels.addWidget(self.row_target_labels)
        
        # 替换标签设置
        self.row_replace_labels = QWidget()
        layout_replace = QHBoxLayout(self.row_replace_labels)
        layout_replace.setContentsMargins(0, 0, 0, 0)
        self.lbl_old = QLabel("原标签名：")
        self.ed_old = QLineEdit()
        self.lbl_new = QLabel("新标签名：")
        self.ed_new = QLineEdit()
        layout_replace.addWidget(self.lbl_old)
        layout_replace.addWidget(self.ed_old)
        layout_replace.addWidget(self.lbl_new)
        layout_replace.addWidget(self.ed_new)
        layout_labels.addWidget(self.row_replace_labels)
        
        layout_params.addWidget(self.gb_labels)
        
        # 备份选项 (删除/替换)
        self.ck_backup = StyledCheckBox("备份原文件")
        self.ck_backup.stateChanged.connect(self._update_ui_state)
        layout_params.addWidget(self.ck_backup)
        
        # 备份目录
        self.row_backup = QWidget()
        layout_backup = QHBoxLayout(self.row_backup)
        layout_backup.setContentsMargins(0, 0, 0, 0)
        self.lbl_backup = QLabel("备份目录：")
        self.ed_backup = QLineEdit()
        self.btn_backup = StyledButton("选择目录", "select_bt")
        self.btn_backup.clicked.connect(self._pick_backup)
        layout_backup.addWidget(self.lbl_backup)
        layout_backup.addWidget(self.ed_backup)
        layout_backup.addWidget(self.btn_backup)
        layout_params.addWidget(self.row_backup)
        
        layout_func.addWidget(self.gb_params)
        root.addWidget(self.gb_func)
        
        # 3. 底部：操作按钮
        row_actions = QWidget()
        layout_actions = QHBoxLayout(row_actions)
        layout_actions.setContentsMargins(0, 5, 0, 5)
        
        self.btn_start = StyledButton("开始处理", "primary")
        self.btn_start.setFixedSize(200, 50)
        self.btn_start.clicked.connect(self._start_process)
        
     
        
        layout_actions.addStretch()
        layout_actions.addWidget(self.btn_start)
        layout_actions.addStretch()
        
        root.addWidget(row_actions)
        root.addStretch() # 底部填充
        
        # 移除日志面板
        
        # 连接信号
        self.bg_mode.idClicked.connect(self._update_ui_state)
        
        # 初始化状态
        self._update_ui_state()

    def _update_ui_state(self):
        mode = self.bg_mode.checkedId()
        # 0: delete, 1: export, 2: replace, 3: blank

        # 输出目录显示
        self.row_out.setVisible(mode in [1, 3])
        
        # 备份目录显示
        self.row_backup.setVisible(self.ck_backup.isChecked())

        # 标签设置显示
        if mode == 3: # blank
            self.gb_labels.setVisible(False)
        else:
            self.gb_labels.setVisible(True)
            if mode == 2: # replace
                self.row_target_labels.setVisible(False)
                self.row_replace_labels.setVisible(True)
            else: # delete, export
                self.row_target_labels.setVisible(True)
                self.row_replace_labels.setVisible(False)
        
        # 备份选项显示 (仅删除和替换可用)
        self.ck_backup.setVisible(mode in [0, 2])
        if mode not in [0, 2]:
             self.row_backup.setVisible(False)
        elif mode in [0, 2] and self.ck_backup.isChecked():
             self.row_backup.setVisible(True)

        # 功能说明更新
        descs = {
            0: "• 删除JSON文件中指定名称的标签\n• 如果删除后JSON文件没有其他标签，则删除整个JSON文件\n• 支持同时删除多个标签 (用逗号分隔)\n• 可选择是否备份原文件",
            1: "• 导出包含指定标签的JSON文件和对应图片\n• 将匹配的文件复制到指定的输出目录\n• 支持同时匹配多个标签 (用逗号分隔)\n• 自动查找同名的图片文件",
            2: "• 将JSON文件中的指定标签名称替换为新名称\n• 精确匹配标签名称进行替换\n• 可选择是否备份原文件\n• 批量处理所有匹配的文件",
            3: "• 导出没有JSON文件或JSON文件为空的图片\n• 将符合条件的图片复制到指定的输出目录\n• 支持常见图片格式 (jpg, png, bmp等)\n• 自动保持目录结构"
        }
        self.lbl_desc.setText(descs.get(mode, ""))

    def _pick_src(self):
        d = QFileDialog.getExistingDirectory(self, "选择处理目录")
        if d:
            self.ed_src.setText(d)

    def _pick_out(self):
        d = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if d:
            self.ed_out.setText(d)

    def _pick_backup(self):
        d = QFileDialog.getExistingDirectory(self, "选择备份目录")
        if d:
            self.ed_backup.setText(d)

    def _start_process(self):
        # 参数验证
        src_dir = self.ed_src.text().strip()
        if not src_dir or not os.path.exists(src_dir):
            QMessageBox.warning(self, "错误", "请选择有效的处理目录！")
            return

        mode = self.bg_mode.checkedId()
        kwargs = {}
        mode_str = ""

        # 初始化处理器
        backup_enabled = self.ck_backup.isChecked() if mode in [0, 2] else False
        backup_dir = self.ed_backup.text().strip() if backup_enabled else ""
        
        if backup_enabled and not backup_dir:
            QMessageBox.warning(self, "错误", "开启备份时必须选择备份目录！")
            return

        self.processor = LabelProcessor(
            source_dir=src_dir,
            recursive=self.ck_recursive.isChecked(),
            backup_enabled=backup_enabled,
            backup_dir=backup_dir
        )

        if mode == 0: # delete
            mode_str = "delete"
            targets = [t.strip() for t in self.ed_target.text().split(",") if t.strip()]
            if not targets:
                QMessageBox.warning(self, "错误", "请输入要删除的标签！")
                return
            kwargs['target_labels'] = targets

        elif mode == 1: # export
            mode_str = "export"
            targets = [t.strip() for t in self.ed_target.text().split(",") if t.strip()]
            out_dir = self.ed_out.text().strip()
            if not targets:
                QMessageBox.warning(self, "错误", "请输入要导出的标签！")
                return
            if not out_dir:
                QMessageBox.warning(self, "错误", "请选择输出目录！")
                return
            kwargs['target_labels'] = targets
            kwargs['output_dir'] = out_dir

        elif mode == 2: # replace
            mode_str = "replace"
            old_l = self.ed_old.text().strip()
            new_l = self.ed_new.text().strip()
            if not old_l or not new_l:
                QMessageBox.warning(self, "错误", "请输入原标签名和新标签名！")
                return
            kwargs['old_label'] = old_l
            kwargs['new_label'] = new_l

        elif mode == 3: # blank
            mode_str = "blank"
            out_dir = self.ed_out.text().strip()
            if not out_dir:
                QMessageBox.warning(self, "错误", "请选择输出目录！")
                return
            kwargs['output_dir'] = out_dir

        # 启动线程
        self.processor_thread = ProcessorThread(self.processor, mode_str, **kwargs)
        # 不再连接日志信号
        self.processor_thread.finished_signal.connect(self._on_process_finished)
        
        self.btn_start.setEnabled(False)
        self.btn_start.setText("处理中...")
        self.gb_source.setEnabled(False) # 锁定输入
        self.gb_func.setEnabled(False)
        
        self.processor_thread.start()

    def _on_process_finished(self, success, msg):
        self.btn_start.setEnabled(True)
        self.btn_start.setText("开始处理")
        self.gb_source.setEnabled(True) # 恢复输入
        self.gb_func.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "提示", "操作已完成！")
        else:
            QMessageBox.critical(self, "错误", f"操作失败：{msg}")
