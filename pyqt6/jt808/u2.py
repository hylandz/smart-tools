import sys
import os
import re
from pathlib import Path

import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox,
                             QProgressDialog, QPushButton, QLabel, QVBoxLayout, QWidget)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

# 配置信息
VERSION = "2.1.0"
UPDATE_INFO_URL = "http://localhost:8080/pyqt6/jt808/get_version.json"
DEFAULT_DOWNLOAD_NAME = "软件更新包"  # 当无法提取文件名时的默认名


# 用Path获取程序所在目录（兼容开发/打包环境）
def get_app_dir() -> Path:
    if getattr(sys, 'frozen', False):
        # 打包后环境（EXE）：获取EXE所在目录
        return Path(sys.executable).parent
    else:
        # 开发环境（脚本）：获取当前脚本所在目录
        return Path(__file__).parent


# 下载目录：程序同级目录下的"downloads"文件夹（用Path定义）
DOWNLOAD_DIR: Path = get_app_dir().joinpath("downloads")


class UpdateChecker(QThread):
    update_available = pyqtSignal(str, str, str)
    no_update = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            response = requests.get(UPDATE_INFO_URL, timeout=10)

            response.raise_for_status()
            update_info = response.json()

            # 数据放在data里
            version_info = update_info["data"]

            # 校验必要字段
            required_fields = ["latestVersion", "description", "downloadUrl"]
            if not all(field in version_info for field in required_fields):
                raise ValueError("版本信息缺少必要字段（latestVersion/downloadUrl）")

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
        local_parts = list(map(int, VERSION.split('.')))
        server_parts = list(map(int, server_version.split('.')))
        for local, server in zip(local_parts, server_parts):
            if server > local:
                return True
            elif server < local:
                return False
        return len(server_parts) > len(local_parts)


class FileDownloader(QThread):
    progress_updated = pyqtSignal(int)
    download_finished = pyqtSignal(str)  # 传递字符串路径（方便UI显示）
    error_occurred = pyqtSignal(str)

    def __init__(self, download_url, save_dir, default_name=DEFAULT_DOWNLOAD_NAME):
        super().__init__()
        self.download_url = download_url
        self.save_dir = save_dir  # 接收Path对象
        self.default_name = default_name  # 自定义默认名

    def _get_valid_filename(self, url) -> str:
        """生成合法文件名（返回字符串，后续用Path拼接）"""
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        print(parsed_url)
        raw_filename = Path(parsed_url.query).name  # 用Path提取文件名（自动忽略路径部分）
        filename = raw_filename[raw_filename.find("=") + 1:]
        print(filename)
        if not filename:
            version_match = re.search(r'v?(\d+\.\d+\.\d+)', url)
            version_suffix = f"_v{version_match.group(1)}" if version_match else ""
            filename = f"{self.default_name}{version_suffix}.zip"

        # 过滤非法字符（替换为下划线）
        invalid_chars = r'[\/:*?"<>|]'
        valid_filename = re.sub(invalid_chars, '_', filename)

        # 处理重复文件
        base, ext = valid_filename.rsplit('.', 1) if '.' in valid_filename else (valid_filename, '')
        counter = 1
        final_filename = valid_filename
        while (self.save_dir / final_filename).exists():  # 用Path的/运算符拼接路径
            final_filename = f"{base}_{counter}.{ext}" if ext else f"{base}_{counter}"
            counter += 1

        return final_filename

    def run(self):
        try:
            # 用Path的mkdir方法创建目录（parents=True允许创建父目录，exist_ok=True忽略已存在）
            self.save_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名并拼接完整路径（Path对象）
            file_name = self._get_valid_filename(self.download_url)
            save_path: Path = self.save_dir / file_name  # 用/运算符拼接路径，更简洁

            # 下载文件（save_path.open()直接支持Path对象）
            with requests.get(self.download_url, stream=True, timeout=60) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded_size = 0

                with save_path.open('wb') as f:  # Path对象直接调用open()
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if total_size > 0:
                                progress = int((downloaded_size / total_size) * 100)
                                self.progress_updated.emit(progress)

            # 校验文件（用Path的exists()和stat().st_size）
            if not save_path.exists() or save_path.stat().st_size == 0:
                raise FileNotFoundError(f"下载失败，文件未生成或为空（路径：{save_path}）")

            # 转换为字符串传递给UI（方便显示）
            self.download_finished.emit(str(save_path))
        except Exception as e:
            self.error_occurred.emit(f"下载失败: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.start_update_check_timer()

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
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_for_updates)
        self.update_timer.setSingleShot(True)
        self.update_timer.start(10000)

    def check_for_updates(self):
        self.checker = UpdateChecker()
        self.checker.update_available.connect(self.on_update_available)
        self.checker.no_update.connect(self.on_no_update)
        self.checker.error_occurred.connect(self.on_update_error)
        self.checker.start()

    def on_update_available(self, new_version, description, download_url):
        reply = QMessageBox.question(
            self,
            "发现新版本",
            f"当前版本: {VERSION}\n最新版本: {new_version}\n\n更新说明:\n{description}\n\n是否下载更新包？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.start_download(download_url)

    def on_no_update(self):
        if not self.update_timer.isActive():
            QMessageBox.information(self, "检查更新", f"当前已是最新版本: {VERSION}")

    def on_update_error(self, error_msg):
        QMessageBox.warning(self, "检查更新失败", error_msg)

    def start_download(self, download_url):
        self.downloader = FileDownloader(download_url, DOWNLOAD_DIR)
        self.progress_dialog = QProgressDialog("正在下载更新包...", "取消", 0, 100, self)
        self.progress_dialog.setWindowTitle("下载中")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.canceled.connect(self.downloader.terminate)

        self.downloader.progress_updated.connect(self.progress_dialog.setValue)
        self.downloader.download_finished.connect(self.on_download_finished)
        self.downloader.error_occurred.connect(self.on_download_error)

        self.downloader.start()
        self.progress_dialog.exec()

    def on_download_finished(self, save_path):
        self.progress_dialog.close()
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("下载完成")
        msg_box.setText(f"更新包已成功下载至：\n{save_path}")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Open)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)
        if msg_box.exec() == QMessageBox.StandardButton.Open:
            folder_path = os.path.dirname(save_path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))

    def on_download_error(self, error_msg):
        self.progress_dialog.close()
        QMessageBox.warning(self, "下载失败", error_msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
