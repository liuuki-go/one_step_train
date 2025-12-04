import argparse
import os
import time
from ultralytics import YOLO #type: ignore





def train_with_cfg(data: str, export_path: str):
    model = YOLO("./models/yolo11n.pt")
    ts = time.strftime("%y-%m-%d_%H:%M", time.localtime())
    print(f"export_path: {export_path}")
    train_results = model.train(
        cfg="./train/config/train_conf.yaml",
        project=export_path,
        name=ts,
        data=data,
    )
    
    model.export(
    format="onnx",
    imgsz=640,
    dynamic=True,
    simplify=True,
    opset=18,
    )

    return train_results


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument("--dataset")
    p.add_argument("--export_path")
    a = p.parse_args()

    export_path = a.export_path or os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    if a.dataset:
        data_arg = os.path.join(a.dataset, "dataset_config.yaml")
        if os.path.exists(data_arg):
            train_with_cfg(data_arg, export_path)
            # _normalize_yaml(data_arg) 
        else:
            raise SystemExit("missing --dataset folder")
        

