import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QPushButton, QLineEdit, QTextEdit, QSizePolicy, QLabel)
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    TITLE_NAME = "BSJ-icons 协议解析工具"
    TOOL_VERSION = "v1.0.0"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.TITLE_NAME)
        self.setGeometry(100, 100, 800, 650)
        # self.center_window()

        # 创建中央部件和主布局（垂直布局）
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 创建顶部区域（数据输入区域）
        self.top_group = QGroupBox("数据输入区域")
        top_layout = QVBoxLayout()
        self.top_input = QTextEdit()
        self.top_input.setPlaceholderText("请在此输入数据...（2929xxxxx0D）")
        top_layout.addWidget(self.top_input)
        self.top_group.setLayout(top_layout)
        main_layout.addWidget(self.top_group, stretch=3)

        # 创建中间区域（功能区域）
        self.middle_group = QGroupBox("功能区域")
        middle_layout = QHBoxLayout()

        # 添加三个按钮
        self.button1 = QPushButton("导入按钮1")
        self.button1.setFixedSize(100, 40)  # 设置按钮固定尺寸
        self.button2 = QPushButton("解析按钮2")
        self.button2.setFixedSize(100, 40)
        self.button3 = QPushButton("清除按钮3")
        self.button3.setFixedSize(100, 40)
        self.button4 = QPushButton("伪IP转换")
        self.button4.setFixedSize(100, 40)

        # 添加文本输入框
        self.middle_input = QLineEdit()
        self.middle_input.setPlaceholderText("参数输入")
        self.middle_input.setFixedWidth(150)  # 设置输入框固定宽度

        # 添加文本框（调整大小）
        self.middle_text = QTextEdit()
        self.middle_text.setPlaceholderText("伪IP转换结果显示...")
        self.middle_text.setReadOnly(True)  # 设置为只读
        self.middle_text.setMaximumSize(300, 150)  # 设置最大尺寸
        self.middle_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        middle_layout.addWidget(self.button1)
        middle_layout.addWidget(self.button2)
        middle_layout.addWidget(self.button3)
        middle_layout.addWidget(self.button4)
        middle_layout.addWidget(self.middle_input)
        middle_layout.addWidget(self.middle_text)

        self.middle_group.setLayout(middle_layout)
        main_layout.addWidget(self.middle_group, stretch=1)

        # 创建底部区域（解析区域）
        self.bottom_group = QGroupBox("解析结果区域")
        bottom_layout = QVBoxLayout()
        self.bottom_display = QTextEdit()
        self.bottom_display.setPlaceholderText("解析结果将显示在这里...")
        self.bottom_display.setReadOnly(True)  # 设置为只读
        bottom_layout.addWidget(self.bottom_display)
        self.bottom_group.setLayout(bottom_layout)
        main_layout.addWidget(self.bottom_group, stretch=5)

        # 状态栏
        self.statusBar().showMessage("就绪")

        # 版权信息-方案1
        self.status_label = QLabel()
        self.status_label.setText(f"© 2025 协议解析工具{self.TOOL_VERSION} - 版权所有")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.statusBar().addPermanentWidget(self.status_label)

    def center_window(self):
        # 获取主屏幕尺寸
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            # 计算窗口居中位置
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
