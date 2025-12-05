

from PySide6.QtWidgets import QRadioButton


class QRadioButtonStyleManager:
    # 初始化默认样式库（可自行扩展）

    _styles = {
        # 主样式（蓝色系）
        "primary": """
            QRadioButton {
                color: black;
                font-size: 12px;
              
            }
            /* 指示器（圆圈）的通用大小 */
            QRadioButton::indicator {
                width: 10px;  /* 增大圆圈尺寸，更醒目 */
                height: 10px;
                margin: 0;
                padding: 0;
            }
            /* 未选中时：显示空心圆圈 */
            QRadioButton::indicator:unchecked {
                border: 1px solid #333;  /* 黑色边框（和文本配色一致） */
                border-radius: 5px;         /* 半径=宽度的一半，保证是正圆 */
              
            }
            /* 选中时的指示器样式（核心突出效果） */
            QRadioButton::indicator:checked {
                border: 0px solid #000000; /* 黑色边框（和文本呼应） */
                border-radius: 5px;
                background-color: #000000; /* 黑色填充，直观区分选中状态 */
            }
        """,
         
    
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

class StyledRadioButton(QRadioButton):
    def __init__(self, text: str, style_name: str = "primary", parent=None):
        super().__init__(text, parent)
        # 设置样式
        self.set_style(style_name)

    def set_style(self, style_name: str):
        """切换按钮样式"""
        qss = QRadioButtonStyleManager.get_style(style_name)
        self.setStyleSheet(qss)