import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QGroupBox, QLineEdit, QPushButton, QTextEdit, QLabel, QHBoxLayout, QSizePolicy)
from PyQt6.QtCore import Qt


class ProtocolParserTool(QMainWindow):
    TOOL_VERSION = "v1.0.0"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("协议解析工具")
        self.setGeometry(100, 100, 800, 600)  # 调整整体窗口高度为500

        # 创建主控件和主布局（垂直布局）
        main_widget = QWidget()  # 主控件
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()  # 主布局

        # 协议输入区域 - 设置固定高度
        input_group = QGroupBox("协议输入")
        input_layout = QVBoxLayout()

        # self.protocol_input = QLineEdit()
        self.protocol_input = QTextEdit()
        self.protocol_input.setPlaceholderText("请输入协议数据")

        input_layout.addWidget(self.protocol_input)
        input_group.setLayout(input_layout)
        input_group.setMaximumHeight(200)  # 限制输入区域最大高度

        # 按钮区域
        btn_group = QGroupBox("功能区域")
        # 按钮区域布局：使用尺寸策略 + 样式表
        btn_layout = QHBoxLayout()  # 改水平布局
        btn_layout.setSpacing(15)  # 按钮间距
        btn_layout.setContentsMargins(0, 10, 0, 10)  # 上下左右边距
        btn_layout.addStretch(1)  # 顶部弹性空间

        # 解析按钮
        parse_button = QPushButton("💡解析协议")
        parse_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        parse_button.setMinimumSize(150, 40)
        parse_button.clicked.connect(self.parse_protocol)
        btn_layout.addWidget(parse_button, alignment=Qt.AlignmentFlag.AlignLeft)

        # 清除按钮
        clean_btn = QPushButton("❤️ 清除按钮")
        clean_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        clean_btn.setMinimumSize(150, 40)
        clean_btn.clicked.connect(self.clear_all)

        btn_layout.addWidget(clean_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        btn_group.setLayout(btn_layout)

        # 解析结果展示区域
        result_group = QGroupBox("解析结果")  # 组合框
        result_layout = QVBoxLayout()  # 布局
        # 部件
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        #
        result_layout.addWidget(self.result_display)
        result_group.setLayout(result_layout)

        # 状态栏
        self.statusBar().showMessage("就绪")

        # 版权信息-方案1
        self.status_label = QLabel()
        self.status_label.setText(f"© 2025 协议解析工具{self.TOOL_VERSION} - 版权所有")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.statusBar().addPermanentWidget(self.status_label)

        # 调整布局比例
        main_layout.addWidget(input_group, stretch=3)  # 输入区域占比小
        main_layout.addWidget(btn_group, stretch=1)  # 按钮不拉伸
        main_layout.addWidget(result_group, stretch=5)  # 结果区域占比大

        main_widget.setLayout(main_layout)

    def parse_protocol(self):
        raw_data = self.protocol_input.toPlainText().strip()
        if not raw_data:
            self.statusBar().showMessage("错误：无输入数据")
            return

        self.result_display.setText("解析结果：\n")
        for i, item in enumerate(raw_data):
            self.result_display.append(f"字段 {i + 1}: {item}")

    def clear_all(self):
        self.protocol_input.clear()
        self.protocol_input.clear()
        self.statusBar().showMessage("内容已清空")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProtocolParserTool()
    window.show()
    sys.exit(app.exec())
