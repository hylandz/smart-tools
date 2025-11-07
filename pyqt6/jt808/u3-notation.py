import os
import sys
import re
import requests
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox, QProgressDialog,
                             QPushButton, QLabel, QVBoxLayout, QWidget, QToolButton,
                             QMenu, QHBoxLayout)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QPoint, QSize
from PyQt6.QtGui import (QIcon, QPixmap, QPainter, QColor, QFont,
                         QDesktopServices, QActionGroup, QAction, QPen)
from PyQt6.QtCore import QUrl

# 配置信息
VERSION = "2.1.1"
UPDATE_INFO_URL = "http://localhost:8080/pyqt6/jt808/get_version.json"  # 需返回{version, description, package_url}
DEFAULT_DOWNLOAD_NAME = "JT808BSJParser"
CURRENT_VERSION_DESC = "当前版本：V1.0.0\n功能：基础数据解析，支持JT808协议基础帧解析,优化0x0704报文支持多个数据项解析"  # 当前版本描述


# 路径处理（使用Path）
def get_app_dir() -> Path:
    return Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent


DOWNLOAD_DIR: Path = get_app_dir().joinpath("downloads")


# 1. 版本检查线程
class UpdateChecker(QThread):
    update_available = pyqtSignal(str, str, str)  # 新版本号, 新描述, 下载链接
    no_update = pyqtSignal(str)  # 当前版本描述
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            # 可根据需要改为POST（添加data参数）
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
                self.no_update.emit(version_info["description"])  # 无更新时返回服务器上的当前版本描述
        except Exception as e:
            self.error_occurred.emit(f"检查失败：{str(e)}")
            # 出错时仍显示本地当前版本描述
            self.no_update.emit(CURRENT_VERSION_DESC)

    def is_new_version(self, server_version):
        """比较版本号（如1.0.0 < 2.1.1）"""
        local = list(map(int, VERSION.split('.')))
        server = list(map(int, server_version.split('.')))
        return server > local  # 直接列表比较（Python支持按元素大小比较）


# 2. 下载线程
class FileDownloader(QThread):
    progress_updated = pyqtSignal(int)
    download_finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, url, save_dir: Path):
        super().__init__()
        self.url = url
        self.save_dir = save_dir

    def _get_valid_filename(self) -> str:
        """从URL提取文件名（如"filename=xxx.zip"截取xxx.zip）"""
        # 优先从URL参数提取filename（如"?filename=xxx.zip"）
        if "filename=" in self.url:
            filename_part = self.url.split("filename=")[-1].split('&')[0]  # 取=后到&前的部分
            return re.sub(r'[/:*?"<>|]', '_', filename_part)

        # 否则从路径提取
        filename = Path(self.url).name.split('?')[0]
        return filename if filename else f"{DEFAULT_DOWNLOAD_NAME}_v{VERSION}.zip"

    def run(self):
        try:
            self.save_dir.mkdir(parents=True, exist_ok=True)
            filename = self._get_valid_filename()
            save_path = self.save_dir / filename
            print(filename)
            with requests.get(self.url, stream=True, timeout=60) as r:
                r.raise_for_status()
                total = int(r.headers.get('content-length', 0))
                downloaded = 0

                with save_path.open('wb') as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total:
                                self.progress_updated.emit(int(downloaded / total * 100))

            if not save_path.exists() or save_path.stat().st_size == 0:
                raise FileNotFoundError("文件下载不完整")

            self.download_finished.emit(str(save_path))
        except Exception as e:
            self.error_occurred.emit(f"下载失败：{str(e)}")


# 3. 带红点的通知按钮（核心UI组件）
class NotificationButton(QToolButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon("assets/icons/notification.png"))  # 替换为你的通知图标（建议32x32）
        self.setIconSize(QSize(24, 24))
        self.setStyleSheet("""
            QToolButton {
                border: none;
                padding: 4px;
                margin: 2px;
            }
            QToolButton:hover {
                background-color: rgba(200, 200, 200, 50);
                border-radius: 4px;
            }
        """)  # 扁平样式，模拟标题栏元素
        self.has_update = False  # 是否有更新（控制红点显示）
        self.setToolTip("版本信息")

    def set_has_update(self, has_update: bool):
        """设置是否有更新，触发重绘（显示/隐藏红点）"""
        self.has_update = has_update
        self.update()  # 触发paintEvent重绘

    def paintEvent(self, event):
        """重写绘制事件，在图标右上角绘制红点"""
        super().paintEvent(event)  # 先绘制原始图标

        if self.has_update:
            # 绘制红点（位置：图标右上角，大小8x8）
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 抗锯齿
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 0, 0))  # 红色
            # 位置：右上角，留出2px边距
            painter.drawEllipse(self.width() - 10, 2, 8, 8)


# 4. 主窗口
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.new_version = None  # 新版本号
        self.new_desc = None  # 新版本描述
        self.download_url = None  # 下载链接
        self.current_desc = "正在检查版本更新..."  # 当前版本描述（默认提示）
        self.update_check_finished = False  # 版本检测是否完成（标记状态）
        self.init_ui()
        self.start_update_check()

    def init_ui(self):
        self.setWindowTitle("JT808协议解析工具")
        self.setGeometry(100, 100, 800, 600)

        # 标题栏右侧添加通知按钮（核心）
        self.notification_btn = NotificationButton(self)
        self.notification_btn.clicked.connect(self.show_version_menu)  # 点击弹出菜单
        # 将按钮放在窗口右上角（通过布局实现）
        self.init_title_bar()

        # 主内容区
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(QLabel("欢迎使用JT808协议解析工具", alignment=Qt.AlignmentFlag.AlignCenter))
        self.setCentralWidget(central_widget)

        # 创建版本菜单（点击图标时显示）
        self.version_menu = QMenu(self)

    def init_title_bar(self):
        """将通知按钮添加到窗口右上角（模拟标题栏元素）"""
        title_bar = QWidget(self)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 10, 0)
        title_bar_layout.addStretch()  # 推到右侧
        title_bar_layout.addWidget(self.notification_btn)
        # 将标题栏控件放在窗口顶部
        self.setMenuWidget(title_bar)

    def start_update_check(self):
        """启动版本检查（10秒后自动检查）"""
        QTimer.singleShot(10000, self.check_update)

    def check_update(self):
        """检查更新并更新通知图标状态"""
        self.checker = UpdateChecker()
        self.checker.update_available.connect(self.on_update_available)
        self.checker.no_update.connect(self.on_no_update)
        self.checker.error_occurred.connect(self.on_update_error)
        self.checker.start()

    def on_update_available(self, new_version, new_desc, download_url):
        """有新版本：显示红点"""
        self.new_version = new_version
        self.new_desc = new_desc
        self.download_url = download_url
        self.notification_btn.set_has_update(True)  # 显示红点
        self.update_check_finished = True  # 标记检测完成

    def on_no_update(self, current_desc):
        """无新版本：隐藏红点，保存当前版本描述"""
        self.current_desc = current_desc
        self.notification_btn.set_has_update(False)  # 隐藏红点
        self.update_check_finished = True  # 标记检测完成

    def on_update_error(self, error_msg):
        """检查出错：隐藏红点，记录错误"""
        print(f"版本检查错误：{error_msg}")
        self.current_desc = f"版本检查失败：{error_msg}\n当前版本：V{VERSION}"
        self.notification_btn.set_has_update(False)
        self.update_check_finished = True  # 标记检测完成（即使出错也算完成）

    def show_version_menu(self):
        """点击通知图标时显示菜单"""
        # 清空旧菜单
        self.version_menu.clear()

        try:
            if not self.update_check_finished:
                # 版本检测未完成：显示"正在检查"提示
                self.version_menu.addAction("正在检查版本更新...")
                self.version_menu.addAction("请稍后点击重试")
            else:
                # 检测完成：根据是否有更新显示内容
                if self.notification_btn.has_update and self.new_version:
                    # 有更新
                    self.version_menu.addAction(f"发现新版本：V{self.new_version}")
                    self.version_menu.addSeparator()
                    for line in self.new_desc.split('\n'):
                        self.version_menu.addAction(line).setEnabled(False)
                    self.version_menu.addSeparator()
                    download_action = QAction("下载更新包", self)
                    download_action.triggered.connect(self.start_download)
                    self.version_menu.addAction(download_action)
                else:
                    # 无更新（确保self.current_desc已初始化）
                    self.version_menu.addAction(f"当前版本：V{VERSION}")
                    self.version_menu.addSeparator()
                    for line in self.current_desc.split('\n'):
                        self.version_menu.addAction(line).setEnabled(False)

            # 显示菜单
            self.version_menu.exec(self.notification_btn.mapToGlobal(QPoint(0, self.notification_btn.height())))

        except Exception as e:
            # 捕获所有异常，避免闪退（关键！）
            QMessageBox.warning(
                self,
                "操作失败",
                f"打开版本菜单出错：{str(e)}\n请稍后重试"
            )

    def start_download(self):
        """开始下载更新包"""
        if not self.download_url:
            QMessageBox.warning(self, "错误", "下载链接无效")
            return

        self.downloader = FileDownloader(self.download_url, DOWNLOAD_DIR)
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
        # msg = QMessageBox(self)
        # msg.setWindowTitle("下载完成")
        # msg.setText(f"更新包已保存至：\n{save_path}")
        # msg.addButton("打开文件夹", QMessageBox.ButtonRole.AcceptRole)
        # msg.addButton("确定", QMessageBox.ButtonRole.RejectRole)
        # if msg.exec() == 0:  # 点击"打开文件夹"
        #     print("打开文件夹")
        #     QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(save_path).parent)))
        # 1. 构建弹窗，保留"打开文件夹"按钮
        msg = QMessageBox(self)
        msg.setWindowTitle("下载完成")
        msg.setText(f"更新包已保存至：\n{save_path}")

        # 添加按钮："打开文件夹"（AcceptRole）和"确定"（RejectRole）
        open_btn = msg.addButton("打开文件夹", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("确定", QMessageBox.ButtonRole.RejectRole)

        # 2. 显示弹窗，等待用户点击
        msg.exec()

        # 3. 如果用户点击了"打开文件夹"，执行打开逻辑
        if msg.clickedButton() == open_btn:
            self.open_folder(save_path)  # 提取为单独方法，便于维护

    def open_folder(self, save_path):
        """单独的文件夹打开逻辑，包含多重尝试和错误处理"""
        folder_str = ""
        try:
            # 解析并验证路径
            save_path_obj = Path(save_path)
            folder_path = save_path_obj.parent.resolve()  # 绝对路径

            if not folder_path.exists():
                raise FileNotFoundError(f"文件夹不存在：{folder_path}")
            if not folder_path.is_dir():
                raise NotADirectoryError(f"不是有效文件夹：{folder_path}")

            folder_str = str(folder_path)
            print(f"尝试打开文件夹：{folder_str}")

            # 方案1：QDesktopServices（跨平台）
            if QDesktopServices.openUrl(QUrl.fromLocalFile(folder_str)):
                return

            # 方案2：Windows专用os.startfile
            if sys.platform.startswith('win32'):
                os.startfile(folder_str)
                return

            # 方案3：Linux/macOS系统命令
            import subprocess
            cmd = 'xdg-open' if sys.platform.startswith('linux') else 'open'
            subprocess.run([cmd, folder_str], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return

        except Exception as e:
            # 打开失败时，显示详细错误和路径
            QMessageBox.warning(
                self,
                "打开失败",
                f"无法打开文件夹，请手动访问：\n{folder_str}\n\n错误原因：{str(e)}"
            )

    def on_download_error(self, error_msg):
        self.progress_dialog.close()
        QMessageBox.warning(self, "下载失败", error_msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
