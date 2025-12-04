import subprocess

def gpu_count():
    try:
        import pynvml as nvml
        nvml.nvmlInit()
        cnt = nvml.nvmlDeviceGetCount()
        try:
            nvml.nvmlShutdown()
        except Exception:
            pass
        return int(cnt)
    except Exception:
        pass
    try:
        r = subprocess.run([
            "nvidia-smi", "--query-gpu=name", "--format=csv,noheader"
        ], capture_output=True, text=True, timeout=2, creationflags=subprocess.CREATE_NO_WINDOW)
        if r.returncode == 0 and r.stdout.strip():
            return len([ln for ln in r.stdout.strip().splitlines() if ln.strip()])
    except Exception:
        pass
    return 0

def query_gpus():
    try:
        import pynvml as nvml
        nvml.nvmlInit()
        count = nvml.nvmlDeviceGetCount()
        out = []
        for i in range(count):
            h = nvml.nvmlDeviceGetHandleByIndex(i)
            try:
                name = nvml.nvmlDeviceGetName(h)
                name = name.decode() if isinstance(name, bytes) else str(name)
            except Exception:
                name = ""
            util = None
            mem_used = None
            mem_total = None
            temp = None
            try:
                u = nvml.nvmlDeviceGetUtilizationRates(h)
                util = float(u.gpu)
            except Exception:
                pass
            try:
                gi = nvml.nvmlDeviceGetMemoryInfo(h)
                mem_used = gi.used / (1024**2)
                mem_total = gi.total / (1024**2)
            except Exception:
                pass
            try:
                temp = nvml.nvmlDeviceGetTemperature(h, nvml.NVML_TEMPERATURE_GPU)
            except Exception:
                pass
            out.append({
                "index": i,
                "name": name,
                "utilization": util,
                "memory_used": mem_used,
                "memory_total": mem_total,
                "temperature": temp,
            })
        try:
            nvml.nvmlShutdown()
        except Exception:
            pass
        return out
    except Exception:
        pass

    try:
        r = subprocess.run([
            "nvidia-smi",
            "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
            "--format=csv,noheader,nounits"
        ], capture_output=True, text=True, timeout=2, creationflags=subprocess.CREATE_NO_WINDOW)
        if r.returncode == 0 and r.stdout.strip():
            lines = [ln.strip() for ln in r.stdout.strip().splitlines() if ln.strip()]
            out = []
            for i, ln in enumerate(lines):
                parts = [p.strip() for p in ln.split(',')]
                name = parts[0] if len(parts) >= 1 else ""
                util = float(parts[1]) if len(parts) >= 2 and parts[1] else None
                mu = float(parts[2]) if len(parts) >= 3 and parts[2] else None
                mt = float(parts[3]) if len(parts) >= 4 and parts[3] else None
                tp = float(parts[4]) if len(parts) >= 5 and parts[4] else None
                out.append({
                    "index": i,
                    "name": name,
                    "utilization": util,
                    "memory_used": mu,
                    "memory_total": mt,
                    "temperature": tp,
                })
            return out
    except Exception:
        pass
    return []
