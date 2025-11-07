import sys
import time

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QProgressBar, QVBoxLayout, QPushButton, QApplication, QLabel, QHBoxLayout


class WorkerThread(QThread):
    # 自定义的信号
    progress_updated = pyqtSignal(int)

    def run(self):
        for i in range(1, 101):
            time.sleep(0.1)
            # 发送信号，类似按钮的点击
            self.progress_updated.emit(i)


class MyWindow(QWidget):
    """
    自定义信号与槽用例Demo
    """
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("自定义信号示例")
        self.setGeometry(100, 100, 900, 700)
        layout = QVBoxLayout()

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # progress_container = QHBoxLayout()
        # progress_container.setSpacing(10)
        # progress_container.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        #
        # # 左侧固定文字
        # self.progress_text = QLabel("进度条：")
        # self.progress_text.setObjectName("progress-label")
        # progress_container.addWidget(self.progress_text)
        #
        # # 中间进度条
        # self.progress_bar = QProgressBar()
        # self.progress_bar.setValue(0)
        # self.progress_bar.setTextVisible(False)
        # progress_container.addWidget(self.progress_bar, 1)  # 占大部分空间
        #
        # # 右侧百分比显示
        # self.progress_value = QLabel("0%")
        # self.progress_value.setObjectName("progress-value")
        # progress_container.addWidget(self.progress_value)
        #
        # layout.addLayout(progress_container)

        self.btn = QPushButton("Start Missoin")
        layout.addWidget(self.btn)

        self.setLayout(layout)

        # 创建工作线程
        self.woker = WorkerThread()
        # 自定义的信号与槽连接
        self.woker.progress_updated.connect(self.update_progress)

        # 按钮点击触发任务
        self.btn.clicked.connect(self.start_task)

    def start_task(self):
        self.btn.setEnabled(False)  # 禁用按钮
        self.woker.start()  # 启动线程

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        # self.progress_value.setText(f"{value}%")
        if value == 100:
            self.btn.setEnabled(True)  # 任务完成，启用按钮


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())
