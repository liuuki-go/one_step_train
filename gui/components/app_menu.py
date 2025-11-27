
def setup_menu(main_window, on_sys_settings, on_lang_change):
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

    shift_admin_menu=sys_menu.addMenu("切换用户")
    shift_admin_menu.triggered.connect(on_shift_admin)
    return mb
def on_shift_admin():
    
    pass
    