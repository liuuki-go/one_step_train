import os
import yaml

_cached_cfg = None

def _load_sys_cfg() -> dict:
    _path =  os.path.join(os.getcwd(), "sys_config.yaml")
    global _cached_cfg
    try:
        if _cached_cfg is None:
            with open(_path, "r", encoding="utf-8") as f:
                _cached_cfg = yaml.safe_load(f) or {}
    except Exception:
        _cached_cfg = {}
    return _cached_cfg

def get_wsl_config(yaml_path: str | None = None) -> dict:
    d = _load_sys_cfg()
    return d.get("wsl", {}) if isinstance(d, dict) else {}

def get_resource_path(relative_path):
    """
    获取资源文件的实际路径（适配打包后的情况），PyInstaller 在运行打包后的程序时，会设置sys._MEIPASS变量，指向临时解压目录的路径。
    :param relative_path: 资源文件的相对路径（相对于脚本或临时解压目录）
    :return: 资源文件的绝对路径
    """
    import sys
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS  # type: ignore[attr-defined] 打包后：临时解压目录
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 开发时：脚本所在目录
    return os.path.join(base_path, relative_path)

