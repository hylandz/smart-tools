import sys
from PyQt6.QtWidgets import (QMainWindow, QApplication, QLabel, QPushButton, QMessageBox, QVBoxLayout)
from PyQt6.QtCore import Qt, QSize


class CenteredWindow(QMainWindow):
    """
    信号与槽用例demo
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("信号与槽用例demo")
        # self.setFixedSize(400, 300)  # 设置固定窗口大小
        self.setGeometry(100, 100, 300, 200)
        # self.center_window()

        layout = QVBoxLayout()

        # 创建按钮
        self.loginBtn = QPushButton("点击我", self)
        self.loginBtn.setGeometry(100, 80, 100, 40)
        layout.addWidget(self.loginBtn)

        # 创建按钮
        self.resetBtn = QPushButton("重置我", self)
        self.resetBtn.setGeometry(200, 80, 100, 40)
        layout.addWidget(self.resetBtn)

        self.setLayout(layout)
        # 连接信号与槽
        # self.loginBtn.clicked.connect(lambda: self.show_info("hahahahahah"))  # 按钮点击信号（无参数） -> 通过lambda传递参数给show_info
        self.loginBtn.clicked.connect(self.show_msg2)
        self.loginBtn.clicked.connect(self.show_msg2)  # 一个信号可以连接多个槽

        # 多个信号连接同一个槽(login+reset按钮2个信号连接show_mag3)
        connrction = self.loginBtn.clicked.connect(self.show_msg3)
        # 断开连接（方式1：通过信号断开）
        self.loginBtn.clicked.disconnect(self.show_msg3)  # 这里使用disconnect断开信号连接
        # 方式2：通过连接对象断开（PyQt6支持）
        # connrction.disconnect()
        self.resetBtn.clicked.connect(self.show_msg3)

    def show_msg(self):
        QMessageBox.information(self, "提示1", "按钮被点击了！")

    def show_info(self, msg):
        QMessageBox.information(self, "提示1", msg)

    def show_msg2(self):
        QMessageBox.warning(self, "提示2", "按钮再被点击了！")

    def show_msg3(self):
        QMessageBox.critical(self, "提示3", "lalalalalal")

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
    window = CenteredWindow()
    window.show()
    sys.exit(app.exec())
