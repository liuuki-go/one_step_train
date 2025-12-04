
from PySide6.QtWidgets import QPushButton,QInputDialog,QLineEdit,QMessageBox

def setup_menu(main_window, on_sys_settings, on_lang_change,btn_cfg:QPushButton):
    mb = main_window.menuBar()
    mb.setStyleSheet("QMenuBar{background:#f8f8f8;border-bottom:1px solid #d0d0d0;} QMenuBar::item{padding:6px 12px;}")
    lang_menu = mb.addMenu("语言")
    act_zh = lang_menu.addAction("中文")
    act_en = lang_menu.addAction("English")
    act_zh.triggered.connect(lambda: on_lang_change("zh"))
    act_en.triggered.connect(lambda: on_lang_change("en"))


    sys_menu = mb.addMenu("系统设置")
    act_sys = sys_menu.addAction("打开设置")
    act_sys.triggered.connect(on_sys_settings)

    shift_admin_action = mb.addAction("切换用户")
    shift_admin_action.triggered.connect(lambda: on_shift_admin(btn_cfg,shift_admin_action))


def on_shift_admin(btn_cfg:QPushButton,shift_admin_action):  
    ADMIN_PASSWORD="123456"
    #弹出小框，提示输入密码：
    password, ok = QInputDialog.getText(
        None,
        "管理员验证",
        "请输入管理员密码：",
        QLineEdit.EchoMode.Password,  # 密码模式，输入内容会隐藏为星号
        ""
    )
     # 判断用户是否点击了确认按钮
    if ok:
        # 验证密码
        if password == ADMIN_PASSWORD:
            btn_cfg.setEnabled(True)
            shift_admin_action.setVisible(False)

        else:
            btn_cfg.setEnabled(False)
            QMessageBox.warning(None, "验证失败", "密码错误，请重试！")
   

    
    pass
    