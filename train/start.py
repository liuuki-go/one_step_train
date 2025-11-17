
import argparse
import os
import re
import yaml
from ultralytics import YOLO


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

def train_with_cfg(data: str):
    model = YOLO("models/yolo11n.pt")
    train_results = model.train(
        cfg="train/config/train_conf.yaml",
        data=data,
    )
    return train_results


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument("--data")
    p.add_argument("--dataset")
    a = p.parse_args()
    data_arg = a.data
    if a.dataset:
        data_arg = os.path.join(a.dataset, "dataset_config.yaml")
    if os.path.exists(data_arg):
        _normalize_yaml(data_arg)
    if not data_arg:
        raise SystemExit("missing --dataset folder or --data yaml")
    train_with_cfg(data_arg)

