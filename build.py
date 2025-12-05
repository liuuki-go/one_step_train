import PyInstaller.__main__
import os
import shutil
import sys
import glob

def build():
    # 确保清理旧的构建文件
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")

    # 定义资源文件映射 (源路径, 目标路径)
    # 注意：对于 OneDir 模式，为了方便用户修改，我们将 models, train/config, start.py, sys_config.yaml
    # 移出内部 bundle，改为在构建后复制到 exe 同级目录。
    datas = [
        ("gui/icon", "gui/icon"),
        ("core/LibreHardwareMonitor", "core/LibreHardwareMonitor"),
        # ("train/config", "train/config"), # 外部暴露
        # ("models", "models"),             # 外部暴露
        # ("start.py", "."),                # 外部暴露
        # ("sys_config.yaml", "."),         # 外部暴露

    ]

    # 构建 --add-data 参数
    add_data_args = []
    sep = ";" if os.name == 'nt' else ":"
    for src, dst in datas:
        if os.path.exists(src):
            add_data_args.append(f"--add-data={src}{sep}{dst}")
        else:
            print(f"Warning: Resource {src} not found, skipping.")

    # ---------------------------------------------------------
    # 处理 Conda 环境下的 DLL 缺失问题 (特别是 _ctypes 依赖的 libffi)
    # ---------------------------------------------------------
    add_binary_args = []
    paths_args = []
    
    # 尝试定位 Conda 的 Library/bin 目录
    conda_bin_path = os.path.join(sys.prefix, 'Library', 'bin')
    if os.path.exists(conda_bin_path):
        print(f"Detected Conda environment, adding binary path: {conda_bin_path}")
        # 添加搜索路径
        paths_args.append(f"--paths={conda_bin_path}")
        
        # 显式添加关键 DLL
        # libffi (ctypes), libssl/libcrypto (ssl/hashlib), zlib, sqlite3
        # 注意: conda-forge 的 libffi 可能命名为 ffi-8.dll
        dll_patterns = [
            "libffi-*.dll", "ffi-*.dll", 
            "libssl-*.dll", "libcrypto-*.dll",
            "zlib.dll", "sqlite3.dll"
        ]
        for pattern in dll_patterns:
            for dll_path in glob.glob(os.path.join(conda_bin_path, pattern)):
                dll_name = os.path.basename(dll_path)
                print(f"Adding binary: {dll_name}")
                add_binary_args.append(f"--add-binary={dll_path}{sep}.")

    # 检查 sys.prefix 下的 python3.dll (有时需要显式添加)
    python3_dll = os.path.join(sys.prefix, 'python3.dll')
    if os.path.exists(python3_dll):
        print(f"Adding python3.dll from {python3_dll}")
        add_binary_args.append(f"--add-binary={python3_dll}{sep}.")

    # ---------------------------------------------------------

    # PyInstaller 参数
    args = [
        "main.py",                      # 入口脚本
        "--name=OneST",        # 生成的 exe 名称
        "--noconsole",                  # 不显示控制台窗口
        "--onedir",                     # 多文件/目录打包 (方便修改资源)
        "--clean",                      # 清理缓存
        "--icon=gui/icon/system_icon.png", # 应用图标
        
        # 隐式导入
        "--hidden-import=pythonnet",
        "--hidden-import=clr",
        "--hidden-import=psutil",
        "--hidden-import=yaml",
        "--hidden-import=PySide6",
        "--hidden-import=ctypes",       # 显式添加 ctypes
        "--hidden-import=_ctypes",      # 显式添加 _ctypes
        "--hidden-import=tensorrt",          # 显式添加 tensorrt
  
        
    ] + add_data_args + add_binary_args + paths_args

    print("Starting build with args:", args)
    PyInstaller.__main__.run(args)

    # ---------------------------------------------------------
    # 后处理：复制需要暴露给用户的资源文件到 dist/one_step_train/ 根目录
    # ---------------------------------------------------------
    print("Build complete. Copying exposed resources...")
    dist_dir = os.path.join("dist", "one_step_train")
    
    # 需要复制的文件/文件夹列表 (源路径 -> 目标相对路径)
    exposed_resources = [
        ("sys_config.yaml", "sys_config.yaml"),
        ("start.py", "start.py"),
        ("models", "models"),
        ("train/config", "train/config"),
        ("yolo11n.pt", "yolo11n.pt"),
    ]

    for src, dst_rel in exposed_resources:
        dst = os.path.join(dist_dir, dst_rel)
        if os.path.exists(src):
            print(f"Copying {src} -> {dst}")
            if os.path.isfile(src):
                # 确保目标文件夹存在
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(src, dst)
            else:
                # 目录复制 (Python 3.8+ 支持 dirs_exist_ok)
                if os.path.exists(dst):
                    shutil.rmtree(dst) # 先删除旧的，保证干净
                shutil.copytree(src, dst)
        else:
            print(f"Warning: Exposed resource {src} not found!")


if __name__ == "__main__":
    build()
