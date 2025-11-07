import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QMessageBox, QMenuBar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 从应用中获取名称和版本号，设置到窗口标题
        app = QApplication.instance()
        window_title = f"{app.applicationName()} v{app.applicationVersion()}"
        self.setWindowTitle(window_title)
        self.resize(600, 400)

        # 创建菜单栏和“关于”选项
        menubar = self.menuBar()
        help_menu = menubar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def show_about_dialog(self):
        # 弹出“关于”对话框，展示应用信息
        app = QApplication.instance()
        about_text = f"{app.applicationName()}\n版本：{app.applicationVersion()}\n\n智能协议解析工具，高效处理协议数据。"
        QMessageBox.about(self, "关于软件", about_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("智能协议解析工具")
    app.setApplicationVersion("2.3")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
