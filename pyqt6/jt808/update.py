import sys
import os
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox,
                             QProgressDialog, QPushButton, QLabel, QVBoxLayout, QWidget)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

# 配置信息
VERSION = "1.0.0"  # 当前版本号
UPDATE_INFO_URL = "http://localhost:8080/pyqt6/jt808/get_version.json"  # 版本信息地址（包含最新版本和下载链接）


# 动态获取程序所在目录（用于保存下载文件）
def get_app_dir():
    if getattr(sys, 'frozen', False):
        # 打包后环境（EXE）
        return os.path.dirname(sys.executable)
    else:
        # 开发环境（脚本）
        return os.path.dirname(os.path.abspath(__file__))


# 下载目录：程序同级目录下的"downloads"文件夹（固定保存，不自动删除）
DOWNLOAD_DIR = os.path.join(get_app_dir(), "downloads")


class UpdateChecker(QThread):
    """检查更新的线程（获取新版本信息和下载链接）"""
    update_available = pyqtSignal(str, str, str)  # 新版本号, 描述, 下载链接
    no_update = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            # 获取服务器版本信息
            response = requests.get(UPDATE_INFO_URL, timeout=10)
            response.raise_for_status()
            update_info = response.json()

            # 数据放在data里
            version_info = update_info["data"]

            # 校验必要字段
            required_fields = ["latestVersion", "description", "downloadUrl"]
            if not all(field in version_info for field in required_fields):
                raise ValueError("版本信息缺少必要字段（version/package_url）")

            # 比较版本号
            if self.is_new_version(version_info["latestVersion"]):
                self.update_available.emit(
                    version_info["latestVersion"],
                    version_info.get("description", "无更新日志"),
                    version_info.get("downloadUrl", "")
                )
            else:
                self.no_update.emit()
        except Exception as e:
            self.error_occurred.emit(f"检查更新失败: {str(e)}")

    def is_new_version(self, server_version):
        """比较版本号（如1.0.0 < 1.0.1）"""
        local_parts = list(map(int, VERSION.split('.')))
        server_parts = list(map(int, server_version.split('.')))
        for local, server in zip(local_parts, server_parts):
            if server > local:
                return True
            elif server < local:
                return False
        return len(server_parts) > len(local_parts)


class FileDownloader(QThread):
    """文件下载线程（仅下载，不处理解压）"""
    progress_updated = pyqtSignal(int)
    download_finished = pyqtSignal(str)  # 下载完成的文件路径
    error_occurred = pyqtSignal(str)

    def __init__(self, download_url, save_dir):
        super().__init__()
        self.download_url = download_url
        self.save_dir = save_dir  # 保存目录

    def run(self):
        try:
            # 确保下载目录存在
            os.makedirs(self.save_dir, exist_ok=True)

            # 获取文件名（从URL中提取，如"v1.0.1.zip"）
            url_name = os.path.basename(self.download_url).split('?')  # 去掉URL参数
            print(url_name)
            file_name = url_name[1].split('=')[1]
            print(file_name)
            if not file_name:  # 若URL没有文件名，默认用"update_package.zip"
                file_name = "update_package.zip"
            save_path = os.path.abspath(os.path.join(self.save_dir, file_name))

            # 开始下载
            with requests.get(self.download_url, stream=True, timeout=60) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded_size = 0

                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if total_size > 0:
                                progress = int((downloaded_size / total_size) * 100)
                                self.progress_updated.emit(progress)

            # 校验文件是否存在且非空
            if not os.path.exists(save_path) or os.path.getsize(save_path) == 0:
                raise FileNotFoundError(f"下载失败，文件未生成或为空")

            self.download_finished.emit(save_path)
        except Exception as e:
            self.error_occurred.emit(f"下载失败: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.start_update_check_timer()  # 10秒后自动检查更新

    def init_ui(self):
        self.setWindowTitle("应用程序")
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        self.label = QLabel("欢迎使用本程序！\n程序启动后将在10秒后自动检查更新", alignment=Qt.AlignmentFlag.AlignCenter)
        self.check_btn = QPushButton("手动检查更新")
        self.check_btn.clicked.connect(self.check_for_updates)

        layout.addWidget(self.label)
        layout.addWidget(self.check_btn)

        self.setCentralWidget(central_widget)

    def start_update_check_timer(self):
        """10秒后自动检查更新"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_for_updates)
        self.update_timer.setSingleShot(True)
        self.update_timer.start(10000)  # 10秒延时

    def check_for_updates(self):
        """检查更新"""
        self.checker = UpdateChecker()
        self.checker.update_available.connect(self.on_update_available)
        self.checker.no_update.connect(self.on_no_update)
        self.checker.error_occurred.connect(self.on_update_error)
        self.checker.start()

    def on_update_available(self, new_version, description, download_url):
        """发现更新，提示用户是否下载"""
        reply = QMessageBox.question(
            self,
            "发现新版本",
            f"当前版本: {VERSION}\n最新版本: {new_version}\n\n更新说明:\n{description}\n\n是否下载更新包？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.start_download(download_url)

    def on_no_update(self):
        """无更新（仅手动检查时提示）"""
        if not self.update_timer.isActive():
            QMessageBox.information(self, "检查更新", f"当前已是最新版本: {VERSION}")

    def on_update_error(self, error_msg):
        QMessageBox.warning(self, "检查更新失败", error_msg)

    def start_download(self, download_url):
        """开始下载文件"""
        # 创建下载线程（指定保存目录为DOWNLOAD_DIR）
        self.downloader = FileDownloader(download_url, DOWNLOAD_DIR)

        # 显示进度对话框
        self.progress_dialog = QProgressDialog("正在下载更新包...", "取消", 0, 100, self)
        self.progress_dialog.setWindowTitle("下载中")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.canceled.connect(self.downloader.terminate)

        # 连接信号
        self.downloader.progress_updated.connect(self.progress_dialog.setValue)
        self.downloader.download_finished.connect(self.on_download_finished)
        self.downloader.error_occurred.connect(self.on_download_error)

        self.downloader.start()
        self.progress_dialog.exec()

    def on_download_finished(self, save_path):
        """下载完成，提示保存路径，并提供打开文件夹选项"""
        self.progress_dialog.close()

        # 显示下载位置，提供"打开文件夹"按钮
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("下载完成")
        msg_box.setText(f"更新包已成功下载至：\n{save_path}")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Open)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)

        # 点击"Open"按钮打开文件夹
        if msg_box.exec() == QMessageBox.StandardButton.Open:
            folder_path = os.path.dirname(save_path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))

    def on_download_error(self, error_msg):
        """下载失败提示"""
        self.progress_dialog.close()
        QMessageBox.warning(self, "下载失败", error_msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
