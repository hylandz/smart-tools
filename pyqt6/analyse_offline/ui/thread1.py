import sys
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QTextEdit)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont


# 1. 定义子线程类（用于执行耗时函数）
class WorkerThread(QThread):
    # 定义信号：用于向主线程发送消息（可自定义参数类型）
    update_signal = pyqtSignal(str)  # 发送字符串消息
    finish_signal = pyqtSignal()  # 通知任务完成

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func  # 目标函数
        self.args = args  # 函数参数
        self.kwargs = kwargs  # 关键字参数

    def run(self):
        """子线程入口：调用目标函数，并通过信号反馈结果"""
        try:
            # 调用目标函数（耗时操作）
            result = self.func(*self.args, **self.kwargs)
            # 发送结果到主线程
            self.update_signal.emit(f"函数执行结果：{result}")
        except Exception as e:
            # 异常信息也通过信号发送
            self.update_signal.emit(f"执行出错：{str(e)}")
        finally:
            # 通知任务完成
            self.finish_signal.emit()


# 2. 定义需要在子线程中调用的耗时函数
def long_running_function(n):
    """示例：耗时函数（模拟数据计算）"""
    total = 0
    for i in range(n):
        total += i
        # 模拟耗时（每步休眠0.1秒）
        time.sleep(0.1)
        # 可通过打印模拟中间过程（但不能直接更新UI）
        # print(f"计算中：{i}/{n}")
    return total


# 3. 主窗口（UI线程）
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.thread = None  # 子线程实例
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("PyQt6多线程示例")
        self.setGeometry(100, 100, 600, 400)

        # 字体设置
        font = QFont()
        font.setFamily("Microsoft YaHei")
        self.setFont(font)

        # 中心部件和布局
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        self.title_label = QLabel("多线程调用耗时函数演示")
        self.title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        layout.addWidget(self.title_label)

        # 日志显示区
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        layout.addWidget(self.log_edit)

        # 按钮：启动子线程
        self.start_btn = QPushButton("启动子线程执行耗时函数")
        self.start_btn.clicked.connect(self.start_thread)
        layout.addWidget(self.start_btn)

    def start_thread(self):
        """启动子线程，调用耗时函数"""
        # 防止重复启动线程
        if self.thread and self.thread.isRunning():
            self.log_edit.append("⚠️ 线程正在运行中，请勿重复启动！")
            return

        # 禁用按钮，避免重复点击
        self.start_btn.setEnabled(False)
        self.log_edit.append("▶️ 开始执行耗时函数...")

        # 创建子线程：传入目标函数和参数（计算1到100的和）
        self.thread = WorkerThread(long_running_function, 100)

        # 连接信号与槽：子线程的信号触发主线程的方法
        self.thread.update_signal.connect(self.update_log)  # 更新日志
        self.thread.finish_signal.connect(self.on_finish)  # 处理完成

        # 启动子线程（自动调用run()方法）
        self.thread.start()

    def update_log(self, message):
        """主线程槽函数：更新日志（UI操作必须在主线程）"""
        self.log_edit.append(message)

    def on_finish(self):
        """主线程槽函数：处理任务完成"""
        self.log_edit.append("✅ 耗时函数执行完毕！")
        # 恢复按钮状态
        self.start_btn.setEnabled(True)
        # 释放线程资源
        self.thread.deleteLater()
        self.thread = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
