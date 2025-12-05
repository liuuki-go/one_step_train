from PySide6.QtWidgets import QPushButton


class ButtonStyleManager:
    # 初始化默认样式库（可自行扩展）

    _styles = {
        # 主样式（蓝色系）
        "primary": """
            QPushButton {
                background-color: #C2E2FA;
                color: #222831;
                font-family: "Microsoft YaHei UI";
                font-weight: bold;
                font-size: 16px;
                border-radius: 10px;
                min-width: 150px;
                min-height: 40px;
                border: none;
                padding:10px 10px;
            }
            QPushButton:hover {
                background-color: #578FCA;
            }
            QPushButton:checked {
                background-color: #e6f0ff;
                color: #0366d6;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled  {
                background-color: #E0E0E0;
                color: #A0A0A0;
            }
        """,
          "select_bt": """
            QPushButton {
                background-color: #F6F6F6;
                color: #222831;
                font-family: "Microsoft YaHei UI";
                font-weight: normal;
                font-size: 12px;
                border-radius: 10px;
                min-width: 80px;
                min-height: 20px;
                border: 2px solid #e1e4e8;
                padding:2px 2px;
            }
            QPushButton:hover {
                background-color: #CADEFC;
            }
            QPushButton:checked {
                background-color: #e6f0ff;
                color: #0366d6;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """,
        # 成功样式（绿色系）
        "success": """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                border-radius: 6px;
                min-width: 180px;
                min-height: 48px;
                border: none;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:pressed {
                background-color: #2E7D32;
            }
        """,
        # 危险样式（红色系）
        "danger": """
            QPushButton {
                background-color: #F44336;
                color: white;
                font-size: 14px;
                border-radius: 6px;
                min-width: 180px;
                min-height: 48px;
                border: none;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
            QPushButton:pressed {
                background-color: #B71C1C;
            }
        """,
        # 警告样式（黄色系）
        "warning": """
            QPushButton {
                background-color: #FFC107;
                color: #212121;
                font-size: 14px;
                border-radius: 6px;
                min-width: 180px;
                min-height: 48px;
                border: none;
            }
            QPushButton:hover {
                background-color: #FFA000;
            }
            QPushButton:pressed {
                background-color: #FF8F00;
            }
        """
    }

    @classmethod
    def get_style(cls, style_name: str) -> str:
        """根据样式名称获取对应的QSS"""
        if style_name not in cls._styles:
            raise ValueError(f"样式{style_name}不存在！可选样式：{list(cls._styles.keys())}")
        return cls._styles[style_name]

    @classmethod
    def add_style(cls, style_name: str, qss: str):
        """新增/覆盖样式"""
        cls._styles[style_name] = qss

class StyledButton(QPushButton):
    def __init__(self, text: str, style_name: str = "primary", parent=None):
        super().__init__(text, parent)
        # 设置样式
        self.set_style(style_name)

    def set_style(self, style_name: str):
        """切换按钮样式"""
        qss = ButtonStyleManager.get_style(style_name)
        self.setStyleSheet(qss)