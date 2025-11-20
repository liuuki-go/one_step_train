# custom_checkbox.py
from PySide6.QtWidgets import QCheckBox
from PySide6.QtCore import Qt

class CheckBoxStyleManager:
    """勾选框样式管理器，与按钮primary样式视觉统一"""
    # 仅维护与按钮风格一致的primary样式
    _styles = {
        "primary": """
            QCheckBox {
                color: #222831;          
                font-family: "Microsoft YaHei UI";  
                font-weight: bold;        
                font-size: 12px;          
                padding: 2px 1px;         
                spacing: 5px;            
            }

            /* 勾选框指示器（未选中） */
            QCheckBox::indicator {
                width: 22px;              
                height: 22px;             
                border-radius: 6px;       
                border: none;             
                /* 新增：未选中状态的图标 */
                image: url(gui/icon/action_model_icon/uncheck.png); 
            }

            /* 指示器悬停状态 */
            QCheckBox::indicator:hover {
                background-color: #578FCA;
                width: 22px;              
                height: 22px;             
                border-radius: 6px;       
                border: none;    
                /* image: url(gui/icon/action_model_icon/uncheck_hover.png); */
            }

            /* 指示器选中状态（已有的选中图标） */
            QCheckBox::indicator:checked {
                background-color: #e6f0ff;
                image: url(gui/icon/action_model_icon/checked.png); 
            }

            /* 指示器按下状态（与按钮pressed色一致） */
            QCheckBox::indicator:pressed {
                background-color: #0D47A1;
            }
        """
    }

    @classmethod
    def get_style(cls, style_name: str) -> str:
        """根据样式名称获取QSS"""
        if style_name not in cls._styles:
            raise ValueError(f"样式{style_name}不存在！可选样式：{list(cls._styles.keys())}")
        return cls._styles[style_name]

    @classmethod
    def add_style(cls, style_name: str, qss: str):
        """新增/覆盖样式（后续扩展用）"""
        cls._styles[style_name] = qss

class StyledCheckBox(QCheckBox):
    """自定义样式勾选框，默认使用primary样式"""
    def __init__(self, text: str, style_name: str = "primary", parent=None):
        super().__init__(text, parent)
        # 应用样式
        self.set_style(style_name)

    def set_style(self, style_name: str):
        """切换勾选框样式"""
        qss = CheckBoxStyleManager.get_style(style_name)
        self.setStyleSheet(qss)