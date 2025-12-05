import os
import re
import subprocess
from typing import List, Callable, Optional

def win_to_wsl_path(p: str) -> str:
    """将 Windows 路径转换为 WSL 的 `/mnt/<drive>/...` 形式。"""

    p = os.path.abspath(p)
    drive = p[0].lower()
    rest = p[2:].lstrip("\\/").replace("\\", "/")
    return f"/mnt/{drive}/{rest}"

def build_train_cmd(export_path: str,start_py: str, dataset_dir: str, env_name: str = "train", conda_base: Optional[str] = None) -> List[str]:
    """构建在 WSL 中执行训练的命令行。

    - 若提供 `conda_base`，优先使用该路径下的 `envs/<env_name>/bin/python` 或 `condabin/conda`。
    - 否则在常见路径下自动探测 `condabin/conda` 或使用 `micromamba`，最终回退到 `python3`。
    """
    sp = win_to_wsl_path(start_py)
    wd = os.path.dirname(sp)
    dd = win_to_wsl_path(dataset_dir)
    ep = win_to_wsl_path(export_path) 
    extra = f" --export_path \"{ep}\"" if ep else ""
    cmd = ""
    if conda_base:
        base = conda_base.rstrip("/")
        py = base + f"/envs/{env_name}/bin/python"
        cmd = (
            f"cd \"{wd}\"; "
            f"\"{py}\" \"{sp}\" --dataset \"{dd}\"{extra}"  # 直接用指定的py解释器运行脚本
        )
  
    return ["wsl", "bash", "-lc", cmd]

def run_stream(cmd: List[str], on_line: Callable[[str], None], stop_event=None) -> int:
    """以流式方式运行命令并逐行回调输出。返回进程退出码。"""
    ansi = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
    # 添加 CREATE_NO_WINDOW (0x08000000) 以防止弹出控制台窗口
    flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", creationflags=flags)
    
    while True:
        if stop_event and stop_event.is_set():
            p.terminate() # 尝试正常终止
            # 如果需要强制发送 Ctrl+C 信号，在 Windows 上对 CREATE_NEW_PROCESS_GROUP 创建的进程组可以使用 GenerateConsoleCtrlEvent
            # 但 wsl 进程可能需要特殊处理。terminate() 对于 wsl.exe 通常足够让它退出。
            # 如果 wsl 内部的训练脚本还在跑，wsl.exe 退出时通常也会带走子进程。
            # 如果不行，可以考虑 subprocess.run(["wsl", "--terminate", <distro>]) 但这里我们不知道 distro 名
            # 或者简单地 p.kill()
            break
            
        line = p.stdout.readline() if p.stdout else ""
        if not line and p.poll() is not None:
            break
        if line:
            s = line.replace("\r", "")
            s = ansi.sub("", s)
            on_line(s.rstrip())
            
    if stop_event and stop_event.is_set():
        return -1 # 手动停止
    return p.wait()
"""WSL 训练命令构建与流式输出工具。
- `win_to_wsl_path` 将 Windows 路径转换为 WSL 挂载路径。
- `build_train_cmd` 按是否提供 `conda_base` 构建可在 WSL 中执行的训练命令。
- `run_stream` 启动子进程并去除 ANSI 颜色码，逐行回调输出。
"""