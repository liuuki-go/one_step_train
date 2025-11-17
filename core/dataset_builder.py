import os
import shutil
import random
import yaml
import tempfile
from typing import List, Tuple
from .dataset_converter import load_classes, json_to_yolo_lines, pair_images_and_jsons

def _ensure_dirs(root: str):
    for split in ["train", "val", "test"]:
        os.makedirs(os.path.join(root, "images", split), exist_ok=True)
        os.makedirs(os.path.join(root, "labels", split), exist_ok=True)

def _write_label(label_path: str, lines: List[str]):
    with open(label_path, "w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")

def _split_indices(n: int, ratios: Tuple[int, int, int]) -> Tuple[List[int], List[int], List[int]]:
    a, b, c = ratios
    total = a + b + c
    if total == 0:
        raise ValueError("invalid ratios")
    idxs = list(range(n))
    random.shuffle(idxs)
    n_train = round(n * a / total)
    n_val = round(n * b / total)
    train = idxs[:n_train]
    val = idxs[n_train:n_train + n_val]
    test = idxs[n_train + n_val:]
    return train, val, test

def build_yolo_dataset(src_dir: str, classes_path: str, ratios: Tuple[int, int, int], persist: bool, output_dir: str = None, seed: int = 42):
    random.seed(seed)
    names = load_classes(classes_path)
    pairs = pair_images_and_jsons(src_dir)
    if not pairs:
        raise FileNotFoundError("no image-json pairs found")
    root = output_dir or tempfile.mkdtemp(prefix="yolo_ds_")
    _ensure_dirs(root)
    train_idx, val_idx, test_idx = _split_indices(len(pairs), ratios)
    for i, (img, js) in enumerate(pairs):
        lines = json_to_yolo_lines(js, names)
        base = os.path.splitext(os.path.basename(img))[0] + ".txt"
        if i in train_idx:
            dst_img = os.path.join(root, "images", "train", os.path.basename(img))
            dst_lbl = os.path.join(root, "labels", "train", base)
        elif i in val_idx:
            dst_img = os.path.join(root, "images", "val", os.path.basename(img))
            dst_lbl = os.path.join(root, "labels", "val", base)
        else:
            dst_img = os.path.join(root, "images", "test", os.path.basename(img))
            dst_lbl = os.path.join(root, "labels", "test", base)
        shutil.copy2(img, dst_img)
        _write_label(dst_lbl, lines)
    data_yaml = {
        "path": root.replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": names,
    }
    yaml_path = os.path.join(root, "dataset_config.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data_yaml, f, allow_unicode=True, sort_keys=False)
    if not persist and output_dir:
        pass
    return root, yaml_path