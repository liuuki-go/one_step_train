import os
import sys
import subprocess
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    translations_dir = project_root / "resources" / "translations"
    translations_dir.mkdir(parents=True, exist_ok=True)
    
    ts_file = translations_dir / "en.ts"
    
    # Find all python files
    py_files = []
    for r, d, f in os.walk(project_root):
        if "venv" in r or ".git" in r or "__pycache__" in r:
            continue
        for file in f:
            if file.endswith(".py"):
                py_files.append(str(Path(r) / file))
    
    # Try to find pyside6-lupdate
    lupdate_cmd = "pyside6-lupdate"
    
    # Check relative to current python executable
    python_dir = os.path.dirname(sys.executable)
    # Common locations for scripts in python envs
    possible_paths = [
        os.path.join(python_dir, "Lib", "site-packages", "PySide6", "lupdate.exe"), # Direct executable
        os.path.join(python_dir, "Scripts", "pyside6-lupdate.exe"), # Wrapper
        os.path.join(python_dir, "bin", "pyside6-lupdate"),
        os.path.join(python_dir, "pyside6-lupdate") # Some envs might put it in root
    ]
    
    for p in possible_paths:
        if os.path.exists(p):
            lupdate_cmd = p
            print(f"Found lupdate at: {lupdate_cmd}")
            break
    
    # Construct command
    # Passing files directly to avoid .pro file parsing issues (which may require qmake/env vars)
    # Windows cmd limit is ~32k chars, we have ~35 files, so it's safe.
    
    cmd = [lupdate_cmd, "-target-language", "en"] + py_files + ["-ts", str(ts_file)]
    
    print(f"Running lupdate with {len(py_files)} files...")
    try:
        subprocess.run(cmd, check=True, shell=True)
        print(f"Successfully generated {ts_file}")
        print("Please open this file with Qt Linguist to translate strings.")
        print("After translation, run: pyside6-lrelease resources/translations/en.ts")
    except subprocess.CalledProcessError as e:
        print("Error running lupdate. Make sure PySide6 is installed and pyside6-lupdate is in your PATH.")
        print(f"Details: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
