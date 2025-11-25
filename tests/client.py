import random
import time
import sys
import os

# 定义彩色输出的ANSI转义码（兼容Linux/macOS/Windows 10+）
class Colors:
    GREEN = '\033[92m'    # INFO级别颜色
    YELLOW = '\033[93m'   # WARNING级别颜色
    BLUE = '\033[94m'     # 伪代码/指令颜色
    CYAN = '\033[96m'     # 标题/分隔符颜色
    WHITE = '\033[97m'    # 普通文本颜色
    RESET = '\033[0m'     # 重置颜色
    BOLD = '\033[1m'      # 加粗

# 生成模拟的时间戳（符合日志格式）
def get_timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

# 生成随机伪代码/终端指令片段
def generate_fake_code():
    # 伪关键字/指令库（偏运维/开发常用命令）
    keywords = [
        "import", "def", "class", "async", "await", "return",
        "sudo", "docker run", "kubectl apply", "git pull", "npm install", "pip install",
        "python", "go run", "gcc -o", "make", "tar -zxvf", "gzip", "rsync",
        "curl", "wget", "ping", "ssh", "netstat", "ps aux", "df -h", "free -m"
    ]
    # 伪变量/文件名/路径库
    variables = [
        "data_2025", "config.yaml", "payload.json", "response_0x7f", "socket_8080",
        "server-01", "client-192.168.1.10", "database_prod", "table_user", "cache_redis",
        "log/app.log", "error.log", "tmp/file.tmp", "/usr/local/bin", "/var/lib/docker"
    ]
    # 伪操作符/参数
    operators = ["--config", "--path", "--port", "--host", "--user", "--password", "-v", "-f", "-r", "-l"]
    # 伪数值
    values = [
        str(random.randint(0, 9999)), str(random.randint(1000, 65535)),  # 端口/数字
        f"0x{random.randint(0, 0xFF):x}", f"{random.randint(1, 100)}.{random.randint(0, 99)}%"
    ]

    # 随机组合代码/指令片段（长度更可控，更贴近真实命令）
    code_parts = [random.choice(keywords)]
    code_length = random.randint(1, 3)  # 缩短片段长度，更真实
    for _ in range(code_length):
        part_type = random.choice(["variable", "operator", "value"])
        if part_type == "variable":
            code_parts.append(random.choice(variables))
        elif part_type == "operator":
            code_parts.append(random.choice(operators))
        elif part_type == "value":
            code_parts.append(random.choice(values))
    return " ".join(code_parts)

# 生成模拟的INFO日志（主要输出）
def generate_info_log():
    info_actions = [
        "Processing request from client",
        "Reading configuration file",
        "Connecting to database server",
        "Loading cache data",
        "Validating input parameters",
        "Parsing JSON response",
        "Writing log to file",
        "Syncing data with remote server",
        "Initializing service module",
        "Checking system resource usage",
        "Updating package index",
        "Starting container instance",
        "Cloning git repository",
        "Compiling source code",
        "Testing network connectivity"
    ]
    details = [
        f"({random.choice(['ID:' + str(random.randint(1000, 9999)), 'IP:192.168.1.' + str(random.randint(1, 254)), 'Port:' + str(random.randint(1000, 65535))])})",
        f"path: {random.choice(['/etc/config', '/var/data', '/tmp'])}",
        f"timeout: {random.randint(5, 30)}s",
        f"size: {random.randint(1, 1024)}KB",
        f"version: v{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 99)}"
    ]
    return f"{random.choice(info_actions)} {random.choice(details)}"

# 生成模拟的WARNING日志（偶尔出现）
def generate_warning_log():
    warning_actions = [
        "Low disk space detected on partition",
        "Slow database query response time",
        "Invalid configuration parameter (ignored)",
        "Connection to cache server lost (retrying)",
        "Package version is deprecated",
        "Memory usage exceeds 80% threshold",
        "Network latency is high (>500ms)",
        "File permissions are not set correctly"
    ]
    details = [
        f"({random.choice(['/dev/sda1', '/dev/sdb2', '/mnt/data'])}), free space: {random.randint(1, 10)}GB",
        f"query: SELECT * FROM {random.choice(['user', 'order', 'product'])} WHERE id = {random.randint(1, 999)}",
        f"parameter: {random.choice(['max_connections', 'timeout', 'buffer_size'])} = {random.randint(0, 9999)}",
        f"server: {random.choice(['redis-01', 'memcached-02', 'cache-prod'])}:6379",
        f"package: {random.choice(['requests', 'numpy', 'docker'])} v{random.randint(0, 2)}.{random.randint(0, 9)}"
    ]
    return f"{random.choice(warning_actions)} {random.choice(details)}"

# 主循环：持续向下输出日志/伪代码
def main():
    # 初始标题
    print(f"{Colors.BOLD}{Colors.CYAN}=== 模拟服务器命令行执行日志 (Ctrl+C 终止) ==={Colors.RESET}\n")
    time.sleep(1)

    try:
        while True:
            # 输出类型权重：80% INFO日志，15% 伪代码，5% WARNING日志（核心调整）
            output_type = random.choices(
                ["info", "code", "warning"],
                weights=[0.8, 0.15, 0.05],
                k=1
            )[0]

            timestamp = get_timestamp()
            if output_type == "info":
                # 输出INFO日志（绿色）
                log = generate_info_log()
                print(f"{timestamp} {Colors.GREEN}[INFO]{Colors.RESET} {log}")
            elif output_type == "code":
                # 输出伪代码/指令（蓝色）
                code = generate_fake_code()
                print(f"{Colors.BLUE}$ {code}{Colors.RESET}")
            elif output_type == "warning":
                # 输出WARNING日志（黄色，加粗）
                log = generate_warning_log()
                print(f"{timestamp} {Colors.BOLD}{Colors.YELLOW}[WARNING]{Colors.RESET} {log}")

            # 控制输出速度（更贴近真实日志的间隔，随机波动）
            time.sleep(random.uniform(0.1, 0.5))

            # 强制刷新输出缓冲区，确保实时显示
            sys.stdout.flush()

    except KeyboardInterrupt:
        # 用户中断时的提示
        print(f"\n\n{Colors.BOLD}{Colors.CYAN}=== 执行终止 (用户手动中断) ==={Colors.RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()