import re
import yaml



def _to_wsl(p: str) -> str:
    if not isinstance(p, str):
        return p
    m = re.match(r"^([A-Za-z]):\\\\?", p)
    p2 = p
    if m:
        drive = m.group(1).lower()
        rest = p[len(m.group(0)):].replace("\\", "/")
        p2 = f"/mnt/{drive}/{rest}"
    elif re.match(r"^[A-Za-z]:/", p):
        drive = p[0].lower()
        rest = p[3:]
        p2 = f"/mnt/{drive}/{rest}"
    return p2

def _normalize_yaml(yaml_path: str) -> None:
    """
    归一化 YAML 文件，将 Windows 路径转换为 WSL 路径。
    """
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            d = yaml.safe_load(f) or {}
        if isinstance(d.get("path"), str):
            d["path"] = _to_wsl(d["path"])  # ensure posix path for WSL
        for k in ("train", "val", "test"):
            if isinstance(d.get(k), str):
                d[k] = _to_wsl(d[k])
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(d, f, allow_unicode=True, sort_keys=False)
    except Exception:
        pass