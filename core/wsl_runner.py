import os
import re
import subprocess
import sys
from typing import List, Callable, Optional

def win_to_wsl_path(p: str) -> str:
    p = os.path.abspath(p)
    drive = p[0].lower()
    rest = p[2:].lstrip("\\/").replace("\\", "/")
    return f"/mnt/{drive}/{rest}"

def build_train_cmd(start_py: str, dataset_dir: str, env_name: str = "train", conda_base: Optional[str] = None) -> List[str]:
    sp = win_to_wsl_path(start_py)
    dd = win_to_wsl_path(dataset_dir)
    if conda_base:
        base = conda_base.rstrip("/")
        py = base + f"/envs/{env_name}/bin/python"
        cb = base + "/condabin/conda"
        cmd = (
            f"if [ -x \"{py}\" ]; then \"{py}\" \"{sp}\" --dataset \"{dd}\"; "
            f"elif [ -x \"{cb}\" ]; then \"{cb}\" run -n {env_name} python \"{sp}\" --dataset \"{dd}\"; "
            f"else python3 \"{sp}\" --dataset \"{dd}\"; fi"
        )
        return ["wsl", "bash", "-lc", cmd]
    sh = (
        "set -e; "
        "CONDA_BIN=''; for b in $HOME/enter $HOME/miniconda3 $HOME/anaconda3 $HOME/mambaforge $HOME/miniforge3 /opt/conda; do "
        "  if [ -x \"$b/condabin/conda\" ]; then CONDA_BIN=\"$b/condabin/conda\"; break; fi; "
        "done; "
        "if [ -n \"$CONDA_BIN\" ]; then \"$CONDA_BIN\" run -n " + env_name + f" python \"{sp}\" --dataset \"{dd}\"; "
        "else "
        "  if command -v micromamba >/dev/null 2>&1; then micromamba run -n " + env_name + f" python \"{sp}\" --dataset \"{dd}\"; "
        f"  else python3 \"{sp}\" --dataset \"{dd}\"; fi; "
        "fi"
    )
    return ["wsl", "bash", "-lc", sh]

def run_stream(cmd: List[str], on_line: Callable[[str], None]) -> int:
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