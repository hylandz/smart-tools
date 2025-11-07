import logging
from pathlib import Path
import sys

from jt808.src.util.logutil import setup_logging


def ota_command_logging():
    """初始化日志系统（支持开发/打包环境）"""
    # 日志目录配置
    log_dir = get_log_path()
    log_dir.mkdir(exist_ok=True, parents=True)

    # 创建日志记录器（带彩色输出）
    logger = logging.getLogger("OTACommandLogs")
    logger.setLevel(logging.DEBUG)

    # 格式化器配置
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 控制台处理器（开发环境）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 强制控制台编码
    if sys.platform == "win32":
        import ctypes
        ctypes.cdll.kernel32.SetConsoleOutputCP(65001)  # Windows控制台UTF-8
    logger.addHandler(console_handler)

    # 文件处理器（生产环境）
    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 错误日志专用处理器（追加模式）
    error_handler = logging.FileHandler(log_dir / "error.log", encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger


def get_log_path():
    """动态获取日志路径（兼容开发和打包环境）"""
    if getattr(sys, "frozen", False):
        # 打包后环境：用户目录+程序名
        return Path.home() / "OTACommandLogs"
    else:
        # 开发环境：项目根目录+logs
        return get_project_root() / "ota_command" / "ota_command-logs"


def get_project_root() -> Path:
    """通过标志性文件识别项目根目录"""
    current = Path(__file__).parent
    markers = [".git", "setup.py", "README.md", "requirements.txt"]

    while True:
        if any(Path(current / marker).exists() for marker in markers):
            return current
        if current.parent == current:  # 到达文件系统根目录
            raise RuntimeError("无法确定项目根目录")
        current = current.parent