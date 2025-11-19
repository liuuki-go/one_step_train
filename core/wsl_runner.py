import os
import re
import subprocess
import sys
from typing import List, Callable, Optional

def win_to_wsl_path(p: str) -> str:
    """将 Windows 路径转换为 WSL 的 `/mnt/<drive>/...` 形式。"""
    p = os.path.abspath(p)
    drive = p[0].lower()
    rest = p[2:].lstrip("\\/").replace("\\", "/")
    return f"/mnt/{drive}/{rest}"

def build_train_cmd(start_py: str, dataset_dir: str, env_name: str = "train", conda_base: Optional[str] = None, export_path: Optional[str] = None) -> List[str]:
    """构建在 WSL 中执行训练的命令行。

    - 若提供 `conda_base`，优先使用该路径下的 `envs/<env_name>/bin/python` 或 `condabin/conda`。
    - 否则在常见路径下自动探测 `condabin/conda` 或使用 `micromamba`，最终回退到 `python3`。
    """
    sp = win_to_wsl_path(start_py)
    dd = win_to_wsl_path(dataset_dir)
    ep = win_to_wsl_path(export_path) 
    extra = f" --export_path \"{ep}\"" if ep else ""
    if conda_base:
        base = conda_base.rstrip("/")
        py = base + f"/envs/{env_name}/bin/python"
        cb = base + "/condabin/conda"
        cmd = (
            f"if [ -x \"{py}\" ]; then \"{py}\" \"{sp}\" --dataset \"{dd}\"{extra}; "
            f"elif [ -x \"{cb}\" ]; then \"{cb}\" run -n {env_name} python \"{sp}\" --dataset \"{dd}\"{extra}; "    
            f"else python3 \"{sp}\" --dataset \"{dd}\"{extra}; fi"
        )
        return ["wsl", "bash", "-lc", cmd]
    sh = (
        "set -e; "
        "CONDA_BIN=''; for b in $HOME/enter $HOME/miniconda3 $HOME/anaconda3 $HOME/mambaforge $HOME/miniforge3 /opt/conda; do "
        "  if [ -x \"$b/condabin/conda\" ]; then CONDA_BIN=\"$b/condabin/conda\"; break; fi; "
        "done; "
        "if [ -n \"$CONDA_BIN\" ]; then \"$CONDA_BIN\" run -n " + env_name + f" python \"{sp}\" --dataset \"{dd}\"{extra}; "
        "else "
        "  if command -v micromamba >/dev/null 2>&1; then micromamba run -n " + env_name + f" python \"{sp}\" --dataset \"{dd}\"{extra}; "
        f"  else python3 \"{sp}\" --dataset \"{dd}\"{extra}; fi; "  
        "fi"
    )
    return ["wsl", "bash", "-lc", sh]

def run_stream(cmd: List[str], on_line: Callable[[str], None]) -> int:
    """以流式方式运行命令并逐行回调输出。返回进程退出码。"""
    ansi = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    while True:
        line = p.stdout.readline()
        if not line and p.poll() is not None:
            break
        if line:
            s = line.replace("\r", "")
            s = ansi.sub("", s)
            on_line(s.rstrip())
    return p.wait()
"""WSL 训练命令构建与流式输出工具。

- `win_to_wsl_path` 将 Windows 路径转换为 WSL 挂载路径。
- `build_train_cmd` 按是否提供 `conda_base` 构建可在 WSL 中执行的训练命令。
- `run_stream` 启动子进程并去除 ANSI 颜色码，逐行回调输出。
"""