import sys
import time
import logging
from typing import Any, Callable, Optional
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton,
                             QTextEdit, QVBoxLayout)
from PyQt6.QtCore import QRunnable, QThreadPool, pyqtSignal, QObject, QThread


# ------------------------------------------------------
# 1. 全局日志配置（程序启动时初始化，支持多线程安全）
# ------------------------------------------------------
def setup_global_logging(
        log_file: str = "task_log.log",
        level: int = logging.INFO,
        fmt: str = "%(asctime)s - %(levelname)s - %(threadName)s - 任务%(task_id)s - %(message)s"
):
    """
    配置全局日志，支持多线程输出到控制台和文件
    :param log_file: 日志文件路径
    :param level: 日志级别（DEBUG/INFO/WARNING/ERROR）
    :param fmt: 日志格式（默认包含时间、级别、线程名、任务ID）
    """
    # 清除已有处理器（避免重复输出）
    logging.root.handlers = []

    # 配置日志格式
    formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    # 全局配置
    logging.basicConfig(
        level=level,
        handlers=[console_handler, file_handler]
    )


# ------------------------------------------------------
# 2. 任务信号类（用于线程间通信，传递状态/结果/异常）
# ------------------------------------------------------
class TaskSignals(QObject):
    """
    任务信号集合：
    - started: 任务开始（传递任务ID）
    - progress: 任务进度（传递任务ID、进度值0-100、描述）
    - finished: 任务完成（传递任务ID、结果）
    - error: 任务出错（传递任务ID、错误信息、异常对象）
    """
    started = pyqtSignal(int)
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(int, object)  # Any表示任意类型的结果
    error = pyqtSignal(int, str, Exception)


# ------------------------------------------------------
# 3. QRunnable 任务基类（封装日志、异常捕获和信号发射）
# ------------------------------------------------------
class LoggedRunnable(QRunnable):
    def __init__(self, task_id: int, *args, **kwargs):
        """
        带日志和信号的任务基类
        :param task_id: 任务唯一标识（用于日志和信号）
        :param args: 任务所需的位置参数
        :param kwargs: 任务所需的关键字参数
        """
        super().__init__()
        self.task_id = task_id
        self.args = args  # 任务参数（传递给实际处理逻辑）
        self.kwargs = kwargs
        self.signals = TaskSignals()  # 信号实例
        self.log_extra = {"task_id": self.task_id}  # 日志上下文（含任务ID）
        self.setAutoDelete(True)  # 任务完成后自动销毁

    def run(self) -> None:
        """任务主逻辑（自动调用，封装了日志和异常捕获）"""
        try:
            # 1. 任务开始：日志+信号
            logging.info("任务启动", extra=self.log_extra)
            self.signals.started.emit(self.task_id)

            # 2. 执行实际任务（需子类实现或通过回调函数定义）
            result = self._run_task(*self.args, **self.kwargs)

            # 3. 任务完成：日志+信号
            logging.info(f"任务完成，结果：{result}", extra=self.log_extra)
            self.signals.finished.emit(self.task_id, result)

        except Exception as e:
            # 4. 异常捕获：日志（含堆栈）+ 信号
            logging.error(
                f"任务执行失败：{str(e)}",
                exc_info=True,  # 输出完整堆栈跟踪
                extra=self.log_extra
            )
            self.signals.error.emit(self.task_id, str(e), e)

    def _run_task(self, *args, **kwargs) -> Any:
        """
        实际任务逻辑（必须重写或通过回调函数实现）
        :return: 任务执行结果（会通过finished信号传递）
        """
        # 示例：默认模拟一个耗时任务（子类应重写此方法）
        for i in range(1, 101, 20):
            time.sleep(0.5)  # 模拟耗时
            progress = i
            self.signals.progress.emit(self.task_id, progress, f"处理中：{i}%")
        return f"默认任务完成（参数：{args}, {kwargs}）"


# ------------------------------------------------------
# 4. 示例：自定义任务（继承基类并重写业务逻辑）
# ------------------------------------------------------
class MyCustomTask(LoggedRunnable):
    """自定义任务示例：处理数据并返回结果"""

    def _run_task(self, data: list, multiplier: int, *args, **kwargs) -> dict:
        """
        实际业务逻辑：处理数据列表，乘以倍率后返回统计结果
        :param data: 待处理数据列表
        :param multiplier: 倍率
        :return: 包含处理后数据和统计信息的字典
        """
        # 模拟分步处理并发送进度
        total = len(data)

        for i, num in enumerate(data):
            processed = num * multiplier
            progress = int((i + 1) / total * 100)
            self.signals.progress.emit(
                self.task_id,
                progress,
                f"处理第{i + 1}/{total}个数据（{num} → {processed}）"
            )
            time.sleep(0.3)  # 模拟处理耗时

        # 计算结果
        processed_data = [num * multiplier for num in data]
        return {
            "original": data,
            "processed": processed_data,
            "sum": sum(processed_data),
            "multiplier": multiplier
        }


# ------------------------------------------------------
# 5. 主窗口（展示如何使用任务和处理信号）
# ------------------------------------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool.globalInstance()
        self.init_ui()
        # logging.info(f"主线程启动，线程池最大线程数：{self.thread_pool.maxThreadCount()}")

    def init_ui(self):
        self.setWindowTitle("带日志的 QRunnable 模板")
        self.setGeometry(300, 300, 600, 500)

        # 布局
        layout = QVBoxLayout()

        # 日志/状态显示区域
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        layout.addWidget(self.status_display)

        # 控制按钮
        self.btn_run_default = QPushButton("运行默认任务（5个）")
        self.btn_run_default.clicked.connect(self.run_default_tasks)

        self.btn_run_custom = QPushButton("运行自定义数据处理任务")
        self.btn_run_custom.clicked.connect(self.run_custom_task)

        layout.addWidget(self.btn_run_default)
        layout.addWidget(self.btn_run_custom)

        self.setLayout(layout)


    def run_default_tasks(self):
        """运行5个默认任务（测试基础功能）"""
        for task_id in range(1, 6):
            task = LoggedRunnable(
                task_id=task_id,
                msg=f"默认任务参数_{task_id}"  # 传递自定义参数
            )
            # 关联信号到UI更新函数
            self._connect_task_signals(task)
            # 提交到线程池
            self.thread_pool.start(task)

    def run_custom_task(self):
        """运行自定义数据处理任务（测试业务逻辑）"""
        task = MyCustomTask(
            task_id=100,  # 任务ID（可自定义规则）
            data=[1, 2, 3, 4, 5],  # 待处理数据
            multiplier=3  # 倍率参数
        )
        self._connect_task_signals(task)
        self.thread_pool.start(task)

    def _connect_task_signals(self, task: LoggedRunnable):
        """统一关联任务信号与UI更新函数"""
        task.signals.started.connect(self._on_task_started)
        task.signals.progress.connect(self._on_task_progress)
        task.signals.finished.connect(self._on_task_finished)
        task.signals.error.connect(self._on_task_error)

    # --------------------------
    # UI更新槽函数（主线程执行）
    # --------------------------
    def _on_task_started(self, task_id: int):
        self.status_display.append(f"[任务{task_id}] 开始执行")

    def _on_task_progress(self, task_id: int, progress: int, desc: str):
        self.status_display.append(f"[任务{task_id}] 进度：{progress}% | {desc}")

    def _on_task_finished(self, task_id: int, result: Any):
        self.status_display.append(f"[任务{task_id}] 执行完成，结果：{result}\n")

    def _on_task_error(self, task_id: int, err_msg: str, exc: Exception):
        self.status_display.append(f"[任务{task_id}] 执行失败：{err_msg}\n")


# ------------------------------------------------------
# 程序入口
# ------------------------------------------------------
if __name__ == "__main__":
    # 初始化日志
    setup_global_logging(
        log_file="my_task_log.log",
        level=logging.INFO  # 开发时可改为logging.DEBUG
    )

    # 启动应用
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())