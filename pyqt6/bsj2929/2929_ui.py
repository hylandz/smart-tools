import json
import logging
import sys
import tkinter
import traceback
from datetime import datetime
from pathlib import Path

from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QPushButton, QTextEdit, QLabel, QFileDialog,
                             QMessageBox)
from PyQt6.QtCore import Qt

from bsj2929.src.protocols.bsj_2929_parse import parse_2929, imei2ip
from bsj2929.src.util.logutil29 import my_logging


def custom_excepthook(cls, value, tb):
    """全局异常捕获：捕获未处理的系统级异常，如崩溃时的堆栈跟踪"""
    # 创建日志目录（使用Path对象）
    log_dir = Path.home() / "BSJ2929ParserLogs"  # c:\\Users\{用户名}
    # log_dir = Path(__file__).parent / "ProtocolParserLogs" # 当前文件上一级目录(项目根路径)
    log_dir.mkdir(parents=True, exist_ok=True)  # 自动创建父目录

    # 生成日志文件路径
    # 固定日志文件名（按日期归档）
    log_file = log_dir / f"global-error_{datetime.now().strftime('%Y%m%d')}.log"

    # 写入错误详情
    with open(log_file, mode='a', encoding='utf-8') as f:
        f.write("\n\n======= [错误记录] =======\n")
        f.write(f"错误时间: {datetime.now().strftime("%Y%m%d %H:%M:%S")}\n")
        f.write(f"异常类型: {cls.__name__}\n")
        f.write(f"错误信息: {str(value)}\n")
        f.write("堆栈跟踪:\n")
        f.write(''.join(traceback.format_tb(tb)))
        f.write("=" * 50 + "\n")

    # 开发环境弹窗提示（打包后自动跳过）
    # if not getattr(sys, 'frozen', False):
    #     import tkinter.messagebox
    #     tkinter.messagebox.showerror("程序错误",f"发生未知错误，详细信息已保存至:\n{log_file}")
    tkinter.messagebox.showerror("程序错误", f"发生未知错误，详细信息已保存至:\n{log_file}")


# 设置全局异常捕获
sys.excepthook = custom_excepthook
logger = my_logging()


class MainWindow(QMainWindow):
    TITLE_NAME = "BSJ-2929 协议解析工具"
    TOOL_VERSION = "v1.1.4"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.TITLE_NAME)
        self.setGeometry(100, 100, 800, 650)
        # self.center_window()
        self.setWindowIcon(QIcon(self.load_resource("assets/icons/app.ico")))
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
        self.import_btn = QPushButton("导入协议文件")
        self.import_btn.setFixedSize(100, 40)  # 设置按钮固定尺寸
        self.import_btn.clicked.connect(self.import_file)
        middle_layout.addWidget(self.import_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.parse_btn = QPushButton("解析协议")
        self.parse_btn.setFixedSize(100, 40)
        self.parse_btn.clicked.connect(self.parse_protocol)
        middle_layout.addWidget(self.parse_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.clean_btn = QPushButton("清除内容")
        self.clean_btn.setFixedSize(100, 40)
        self.clean_btn.clicked.connect(self.clear_all)
        middle_layout.addWidget(self.clean_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.fake_ip_btn = QPushButton("IMEI转伪IP")
        self.fake_ip_btn.setFixedSize(100, 40)
        self.fake_ip_btn.clicked.connect(self.change_ip)
        middle_layout.addWidget(self.fake_ip_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # 添加文本输入框
        # self.middle_input = QLineEdit()
        # self.middle_input.setPlaceholderText("参数输入")
        # self.middle_input.setFixedWidth(150)  # 设置输入框固定宽度
        #
        # # 添加文本框（调整大小）
        # self.middle_text = QTextEdit()
        # self.middle_text.setPlaceholderText("伪IP转换结果显示...")
        # self.middle_text.setReadOnly(True)  # 设置为只读
        # self.middle_text.setMaximumSize(300, 150)  # 设置最大尺寸
        # self.middle_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # middle_layout.addWidget(self.middle_input)
        # middle_layout.addWidget(self.middle_text)

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

    def load_resource(self, relative_path):
        """安全加载资源文件（自动处理打包后路径）"""
        if hasattr(sys, 'frozen'):
            # 打包后环境
            base_path = Path(sys._MEIPASS)
        else:
            # 开发环境
            base_path = Path(__file__).parent

        # 使用pathlib构建跨平台路径
        path = Path(base_path) / relative_path

        # 验证路径是否存在
        if not path.exists():
            logger.error(f"加载资源路径失败：{path}")
            raise FileNotFoundError(f"资源文件不存在: {path}")

        # logger.info(f"加载资源路径成功：{path}")
        return str(path)  # 转换为str以兼容PyQt方法

    def import_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择协议文件", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            file = Path(file_path)
            if file.suffix.lower() == ".txt":
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.top_input.setText(f.read())
                    self.statusBar().showMessage(f"已加载: {file_path}")
                except Exception as e:
                    # logger.error(e)
                    self.statusBar().showMessage(f"错误: {str(e)}")
            else:
                # logger.error("选择的文件类型错误。当前只支持.txt格式")
                QMessageBox.warning(self, "格式错误", "请选择.txt格式的文件！")

    def parse_protocol(self):
        raw_data = self.top_input.toPlainText().strip()
        if not raw_data:
            self.statusBar().showMessage("错误：无输入数据")
            return

        # 示例解析逻辑（可根据实际协议修改）
        parsed_data = []
        lines = raw_data.splitlines()
        for i, line in enumerate(lines):
            is_valid, msg, r = parse_2929(line)
            if is_valid:
                data = json.dumps(r, ensure_ascii=False, indent=2)
                parsed_data.append(data)
            else:
                parsed_data.append(msg)
        # 生成解析报告
        self.show_datas(parsed_data)

    def show_datas(self, parsed_data: list) -> None:
        # 生成解析报告
        report = ""
        for index, item in enumerate(parsed_data, start=1):
            report += "*" * 20 + f"第{index}条" + "*" * 20 + "\n"
            report += item + "\n"

        self.bottom_display.setText(report)
        self.statusBar().showMessage(f"解析完成，共发现 {len(parsed_data)} 条记录")

    def clear_all(self):
        self.top_input.clear()
        self.bottom_display.clear()
        self.statusBar().showMessage("内容已清空")

    def change_ip(self):
        raw_data = self.top_input.toPlainText().strip()
        if not raw_data:
            self.statusBar().showMessage("错误：无输入数据")
            return
        lines = raw_data.splitlines()
        parsed_data = []
        for i, line in enumerate(lines):
            try:
                f_ip = imei2ip(line)
                parsed_data.append(f_ip.hex())
            except Exception as e:
                logging.error(e)
                parsed_data.append(str(e))
        # 生成解析报告
        self.show_datas(parsed_data)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置全局字体
    default_font = QFont()
    default_font.setPointSize(10)  # 设置字体大小为12pt
    # 可选：设置字体家族
    # default_font.setFamily("Consolas")  # 例如设置为黑体，解决中文显示问题
    app.setFont(default_font)  # 将字体应用到整个应用程序

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
