import os
import sys
import re
import requests
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox, QProgressDialog,
                             QPushButton, QLabel, QVBoxLayout, QWidget, QToolButton,
                             QMenu, QHBoxLayout, QWidgetAction, QFrame)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QPoint, QSize
from PyQt6.QtGui import (QIcon, QPixmap, QPainter, QColor, QFont,
                         QDesktopServices, QActionGroup, QPen, QAction)
from PyQt6.QtCore import QUrl

# 配置信息
VERSION = "2.1.1"
UPDATE_INFO_URL = "http://localhost:8080/pyqt6/jt808/get_version.json"  # 需返回{version, description, package_url}
DEFAULT_DOWNLOAD_NAME = "JT808BSJParser"
CURRENT_VERSION_DESC = "修复0x8005和0x8001解析错误\n优化0x0704报文支持多个数据项解析\n使用多线程QRunnable执行报文解析"  # 当前版本描述


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
        self.setIcon(QIcon("assets/icons/notification.ico"))  # 替换为你的通知图标（建议32x32）
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
        self.set_menu_style()  # 应用菜单样式

    def init_title_bar(self):
        """将通知按钮添加到窗口右上角（模拟标题栏元素）"""
        title_bar = QWidget(self)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 10, 0)
        title_bar_layout.addStretch()  # 推到右侧
        title_bar_layout.addWidget(self.notification_btn)
        # 将标题栏控件放在窗口顶部
        self.setMenuWidget(title_bar)

    def set_menu_style(self):
        """设置菜单全局样式，提升美观度"""
        self.version_menu.setStyleSheet("""
            QMenu {
                background-color: #f5f5f5;  # 浅灰背景
                border: 1px solid #ddd;     # 边框
                border-radius: 4px;         # 圆角
                padding: 5px 0;             # 内边距
                font-family: "Microsoft YaHei", sans-serif;  # 支持中文
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 20px;  # 菜单项内边距（上下6px，左右20px）
                margin: 1px 0;      # 项间距
            }
            QMenu::item:selected {
                background-color: #e0e0e0;  # 选中背景
                color: #333;                # 选中文字色
            }
            QMenu::separator {
                height: 1px;
                background-color: #ddd;
                margin: 5px 0;
            }
        """)

    def show_version_menu(self):
        self.version_menu.clear()
        try:
            if not self.update_check_finished:
                # 检测中：显示加载提示（使用富文本加粗标题）
                self.add_menu_text("版本检查中", is_title=True)
                self.add_menu_text("请稍后点击重试")  # 普通文本，无需特殊标记
            else:
                if self.notification_btn.has_update and self.new_version:
                    # 有更新：突出显示新版本号
                    self.add_menu_text(f"发现新版本：V{self.new_version}", is_title=True, is_new=True)
                    self.version_menu.addSeparator()
                    # 美化版本描述（支持换行和缩进）
                    self.add_menu_text("更新内容：", is_subtitle=True)
                    self.add_menu_desc(self.new_desc)  # 专用方法处理描述
                    self.version_menu.addSeparator()
                    # 下载按钮（样式优化）
                    # 关键修改：用QWidgetAction包装QPushButton（支持样式表）
                    download_action = QWidgetAction(self.version_menu)
                    # 创建按钮控件
                    download_btn = QPushButton("📥 下载更新包")
                    # 给按钮设置样式（替代QAction的setStyleSheet）
                    download_btn.setStyleSheet("""
                                        QPushButton {
                                            color: #0066cc; 
                                            font-weight: bold;
                                            background: transparent;  # 透明背景，融入菜单
                                            border: none;
                                            text-align: left;         # 文字左对齐，和菜单其他项一致
                                            padding: 6px 20px;        # 和菜单项内边距匹配
                                        }
                                        QPushButton:hover {
                                            background-color: #e0e0e0;  #  hover时和菜单选中样式一致
                                        }
                                    """)
                    # 绑定点击事件
                    download_btn.clicked.connect(self.start_download)
                    # 将按钮设置为QWidgetAction的控件
                    download_action.setDefaultWidget(download_btn)
                    self.version_menu.addAction(download_action)
                else:
                    # 无更新：显示当前版本
                    self.add_menu_text(f"当前版本：V{VERSION}", is_title=True)
                    self.version_menu.addSeparator()
                    self.add_menu_text("版本信息：", is_subtitle=True)
                    self.add_menu_desc(self.current_desc)  # 专用方法处理描述

            self.version_menu.exec(self.notification_btn.mapToGlobal(QPoint(0, self.notification_btn.height())))
        except Exception as e:
            QMessageBox.warning(self, "操作失败", f"打开版本菜单出错：{str(e)}")

    def add_menu_text(self, text, is_title=False, is_subtitle=False, is_new=False):
        """添加带样式的文本项（标题/副标题/普通文本）"""
        action = QWidgetAction(self.version_menu)
        label = QLabel(text)

        # 设置字体和颜色
        font = QFont("Microsoft YaHei", 11 if is_title else 10)
        if is_title:
            font.setBold(True)
            label.setStyleSheet("color: #222;")
        if is_subtitle:
            font.setBold(True)
            label.setStyleSheet("color: #555; margin-top: 5px;")
        if is_new:
            label.setStyleSheet("color: #e63946;")  # 新版本用红色突出

        label.setFont(font)
        label.setContentsMargins(10, 2, 10, 2)  # 文本内边距
        action.setDefaultWidget(label)
        self.version_menu.addAction(action)

    def add_menu_desc(self, desc):
        """美化版本描述（支持多行、自动换行、缩进）"""
        action = QWidgetAction(self.version_menu)
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 5, 10, 5)  # 整体缩进

        # 按行拆分描述，逐行添加（支持空行）
        for line in desc.split('\n'):
            if not line.strip():  # 空行用分隔线替代
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.HLine)
                separator.setFrameShadow(QFrame.Shadow.Sunken)
                separator.setStyleSheet("margin: 3px 0; background-color: #f0f0f0;")
                layout.addWidget(separator)
            else:
                label = QLabel(f"• {line}")  # 每行前加项目符号
                label.setStyleSheet("color: #444; padding: 2px 0;")
                label.setFont(QFont("Microsoft YaHei", 10))
                layout.addWidget(label)

        layout.addStretch()
        action.setDefaultWidget(frame)
        self.version_menu.addAction(action)

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
            # print(f"尝试打开文件夹：{folder_str}")

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
