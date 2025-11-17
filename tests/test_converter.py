import os
import json
import sys
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "core")))
from core.dataset_converter import json_to_yolo_lines

root = os.path.abspath(os.path.join(os.getcwd(), "参考"))
js = os.path.join(root, "_0T0_E95_NG1_39_1752505815.json")
tx = os.path.join(root, "_0T0_E95_NG1_39_1752505815.txt")

with open(js, "r", encoding="utf-8") as f:
    data = json.load(f)
labels = []
for s in data.get("shapes", []):
    if s.get("shape_type") == "rectangle":
        lab = s.get("label")
        if lab not in labels:
            labels.append(lab)

pred = json_to_yolo_lines(js, labels)

with open(tx, "r", encoding="utf-8") as f:
    exp = [line.strip() for line in f if line.strip()]

assert len(pred) == len(exp)

def floats(s):
    parts = s.split()
    return [float(x) for x in parts[1:5]]

for i in range(len(exp)):
    a = floats(pred[i])
    b = floats(exp[i])
    for x, y in zip(a, b):
        assert abs(x - y) < 1e-3

print("ok")