from PySide6.QtCore import QTranslator, QCoreApplication, QObject
from tools.sys_config_tools import get_resource_path, _load_sys_cfg, save_sys_cfg
import os

class LanguageManager(QObject):
    _instance = None
    _translator = None
    _current_lang = "zh"

    def __init__(self):
        super().__init__()
        self._load_config()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_config(self):
        cfg = _load_sys_cfg()
        self._current_lang = cfg.get("gui", {}).get("languages", {}).get("language", "zh")



    def current_lang(self):
        return self._current_lang

    def install(self, app, lang=None):
        """
        Install the translator for the specified language.
        lang: "zh" (default, no translator) or "en" (English).
        If lang is None, it uses the persisted language.
        """
        if lang is None:
            lang = self._current_lang
        
        # Save to config if changed
        if lang != self._current_lang:
            self._current_lang = lang
            cfg = _load_sys_cfg()
            cfg["gui"]["languages"]["language"] = lang
            save_sys_cfg(cfg)

        if self._translator:
            app.removeTranslator(self._translator)
            self._translator = None
        
        if lang == "en":
            self._translator = QTranslator()
            # Try loading from various potential locations
            # 1. resources/translations/en.qm (relative to CWD)
            # 2. gui/resources/translations/en.qm (if packaged)
            
            paths_to_try = [
                os.path.join(os.getcwd(), "resources", "translations", "en.qm"),
                get_resource_path("resources/translations/en.qm"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resources", "translations", "en.qm")
            ]
            
            loaded = False
            for p in paths_to_try:
                if os.path.exists(p):
                    if self._translator.load(p):
                        app.installTranslator(self._translator)
                        loaded = True
                        print(f"Loaded translation from {p}")
                        break
            
            if not loaded:
                print(f"Warning: Could not load English translation. Checked: {paths_to_try}")
        
        # Note: QCoreApplication.installTranslator automatically sends a QEvent.LanguageChange 
        # to all top-level widgets, which then propagates it.
