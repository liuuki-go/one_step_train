import os
import yaml

_cached_cfg = None

def _load_sys_cfg() -> dict:
    # 优先加载当前目录下的配置文件（用户配置）
    local_path = os.path.join(os.getcwd(), "sys_config.yaml")
    # 备用：打包在资源中的配置文件（默认配置）
    bundled_path = get_resource_path("sys_config.yaml")
    
    global _cached_cfg
    try:
        if _cached_cfg is None:
            # 如果本地有配置，优先使用
            if os.path.exists(local_path):
                with open(local_path, "r", encoding="utf-8") as f:
                    _cached_cfg = yaml.safe_load(f) or {}
            # 否则使用默认配置
            elif os.path.exists(bundled_path):
                with open(bundled_path, "r", encoding="utf-8") as f:
                    _cached_cfg = yaml.safe_load(f) or {}
            else:
                _cached_cfg = {}
    except Exception:
        _cached_cfg = {}
    return _cached_cfg

def get_wsl_config(yaml_path: str | None = None) -> dict:
    d = _load_sys_cfg()
    return d.get("wsl", {}) if isinstance(d, dict) else {}

def get_resource_path(relative_path):
    """
    获取资源文件的实际路径（适配打包后的情况）。
    优先查找可执行文件所在目录（Exposed Resources），
    其次查找 PyInstaller 的临时解压目录（Bundled Resources）。
    :param relative_path: 资源文件的相对路径
    :return: 资源文件的绝对路径
    """
    import sys
    
    # 1. 优先检查当前工作目录/可执行文件目录（适配 OneDir 模式下的外部资源）
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        p = os.path.join(base_path, relative_path)
        if os.path.exists(p):
            return p
    
    # 2. 检查 PyInstaller 的临时/内部目录
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 开发时
        
    return os.path.join(base_path, relative_path)

