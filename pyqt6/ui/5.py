import sys

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel, QApplication, QTextEdit


class MyWindow(QWidget):
    """
    带参数的信号与槽用例demo
    """
    def __init__(self):
        super().__init__()
        self.label = None
        self.edit = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("带参数的信号与槽")
        self.setGeometry(300, 300, 300, 300)

        # 布局
        layout = QVBoxLayout()

        self.label1 = QLabel("请输入文本...")
        layout.addWidget(self.label1)
        self.edit = QLineEdit()
        layout.addWidget(self.edit)

        self.label2 = QLabel("文本显示")
        layout.addWidget(self.label2)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text, stretch=2)

        self.setLayout(layout)

        # 连接信号与槽：textChanged信号（传递str参数） -> 自定义槽函数
        self.edit.textChanged.connect(self.update_text)

    def update_text(self, content):
        """
        槽函数接收参数（与信号的参数类型匹配）
        """
        self.text.setText(content)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())
