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

