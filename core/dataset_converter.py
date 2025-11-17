import os
import json
import math
from typing import List, Tuple, Dict

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}

def load_classes(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def _normalize_bbox(points: List[List[float]], iw: int, ih: int) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x_min = min(xs)
    x_max = max(xs)
    y_min = min(ys)
    y_max = max(ys)
    x_center = ((x_min + x_max) / 2.0) / float(iw)
    y_center = ((y_min + y_max) / 2.0) / float(ih)
    w = (x_max - x_min) / float(iw)
    h = (y_max - y_min) / float(ih)
    return x_center, y_center, w, h

def json_to_yolo_lines(json_path: str, classes: List[str]) -> List[str]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    iw = int(data.get("imageWidth"))
    ih = int(data.get("imageHeight"))
    lines = []
    for s in data.get("shapes", []):
        if s.get("shape_type") != "rectangle":
            continue
        label = s.get("label")
        if label not in classes:
            raise ValueError(f"label not in classes: {label}")
        cls_idx = classes.index(label)
        x, y, w, h = _normalize_bbox(s.get("points", []), iw, ih)
        line = f"{cls_idx} {x:.6f} {y:.6f} {w:.6f} {h:.6f}"
        lines.append(line)
    return lines

def pair_images_and_jsons(root: str) -> List[Tuple[str, str]]:
    pairs = []
    for dirpath, _, filenames in os.walk(root):
        base_map: Dict[str, Dict[str, str]] = {}
        for name in filenames:
            p = os.path.join(dirpath, name)
            stem, ext = os.path.splitext(name)
            if ext.lower() in IMAGE_EXTS:
                base_map.setdefault(stem, {}).update({"img": p})
            elif ext.lower() == ".json":
                base_map.setdefault(stem, {}).update({"json": p})
        for stem, d in base_map.items():
            img = d.get("img")
            js = d.get("json")
            if img and js:
                pairs.append((img, js))
    return pairs