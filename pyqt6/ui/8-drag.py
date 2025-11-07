import sys
from PyQt6.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent


class FileDropTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 1. 启用控件的拖放功能
        self.setAcceptDrops(True)
        self.setPlaceholderText("拖拽文件到这里...")

    # 2. 拖拽进入事件：判断是否为文件，是则接受拖拽
    def dragEnterEvent(self, event: QDragEnterEvent):
        # 检查拖拽数据是否包含文件（MIME类型为text/uri-list）
        if event.mimeData().hasUrls():
            # 接受拖拽（否则控件不会响应后续的放下事件）
            event.acceptProposedAction()
        else:
            # 非文件数据，忽略
            super().dragEnterEvent(event)

    # 3. 拖拽移动事件：允许在控件内移动（直接接受即可）
    def dragMoveEvent(self, event: QDragMoveEvent):
        # 若已在dragEnterEvent中接受，这里直接接受
        event.acceptProposedAction()

    # 4. 放下事件：提取文件路径并处理
    def dropEvent(self, event: QDropEvent):
        # 获取拖拽的URL列表（文件路径以file:///开头）
        urls: list[QUrl] = event.mimeData().urls()
        if not urls:
            super().dropEvent(event)
            return

        # 转换URL为本地文件路径（过滤非本地文件，如网络文件）
        file_paths = []
        for url in urls:
            if url.isLocalFile():  # 确保是本地文件
                file_path = url.toLocalFile()  # 去除file:///前缀，得到真实路径
                file_paths.append(file_path)

        # 处理文件路径（这里示例：显示到文本框）
        if file_paths:
            self.clear()  # 清空现有内容
            self.append("拖拽的文件路径：\n")
            for path in file_paths:
                self.append(f"- {path}")
            event.acceptProposedAction()  # 确认处理完成
        else:
            super().dropEvent(event)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("文件拖拽示例")
        self.setGeometry(300, 300, 600, 400)

        # 布局
        layout = QVBoxLayout()
        # 添加支持拖拽的文本框
        self.drop_edit = FileDropTextEdit()
        layout.addWidget(self.drop_edit)

        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
