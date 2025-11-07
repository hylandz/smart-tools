import json
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QPushButton,
    QVBoxLayout, QWidget, QFileDialog, QLabel, QSizePolicy, QHBoxLayout, QMessageBox
)

from PyQt6.QtCore import Qt, QObject, pyqtSignal, QRunnable, QThreadPool

from jt808.src.protocols.jt808_parse import parse_jt808
from jt808.src.util.logutil import setup_logging


def custom_excepthook(cls, value, tb):
    """全局异常捕获：捕获未处理的系统级异常，如崩溃时的堆栈跟踪"""
    # 创建日志目录（使用Path对象）
    log_dir = Path.home() / "BSJ808ParserLogs"  # c:\\Users\{用户名}
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
        # tkinter.messagebox.showerror("程序错误", f"发生未知错误，详细信息已保存至:\n{log_file}")
        # 使用PyQt6的QMessageBox显示错误（处理应用程序实例问题）
        try:
            # 尝试获取已存在的QApplication实例
            application = QApplication.instance()
            if application is None:
                # 如果没有实例，则创建一个新的QApplication
                application = QApplication(sys.argv)

            # 显示错误弹窗,用pyqt6自带的，其他包会增加打包内存
            QMessageBox.critical(
                None,  # 父窗口为None（无父窗口）
                "程序错误",
                f"发生未知错误，详细信息已保存至:\n{log_file}"
            )

            # 如果是新创建的应用，需要执行一次应用循环（否则弹窗可能不显示）
            if application is None:
                sys.exit(app.exec())
        except Exception as e:
            # 极端情况下如果QMessageBox也失败，打印错误到控制台
            print(f"弹窗显示失败: {e}")
            print(f"错误日志已保存至: {log_file}")
            logger.error(f"弹窗显示失败: {e}")


# 设置全局异常捕获
sys.excepthook = custom_excepthook
logger = setup_logging()


class TaskSignals(QObject):
    """
    1. 定义任务信号（用于向主线程发送消息）
    """
    status_updated = pyqtSignal(int, object)
    error = pyqtSignal(int, str, Exception)
    finished = pyqtSignal(int)


class ParseTask(QRunnable):
    """
    2. 子类化QRunnable，定义任务
    """

    def __init__(self, task_id, data):
        super().__init__()
        self.task_id = task_id
        self.hex_str = data
        self.signals = TaskSignals()  # 信号实例

    def run(self):
        # 任务逻辑
        try:
            is_valid, msg, parse_data = parse_jt808(self.hex_str)
            if is_valid:
                result = json.dumps(parse_data, ensure_ascii=False, indent=2)
            else:
                result = msg
            self.signals.status_updated.emit(self.task_id, result)
        except Exception as e:
            self.signals.error.emit(self.task_id, str(e), e)
        finally:
            self.signals.finished.emit(self.task_id)


class ProtocolParser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.completed_tasks = 0
        self.total_tasks = 0
        self.parse_btn = None
        self.result_text = None
        self.input_text = None
        self.copyright_info = "© 2025 公司名称 版权所有"  # 版权信息
        self.app_version = "v2.1.1"
        self.thread_pool = QThreadPool.globalInstance()
        self.init_ui()

    def init_ui(self):
        # 资源加载示例：窗口图标
        # self.setWindowIcon(QIcon(self.load_resource("assets/logo.png")))

        # 资源加载示例：按钮图标
        # self.import_btn.setIcon(QIcon(self.load_resource("assets/import_icon.svg")))

        # 资源加载示例：背景图片
        # self.setStyleSheet("""
        #             QMainWindow {
        #                 background-image: url(assets/background.png);
        #                 background-repeat: no-repeat;
        #                 background-position: center;
        #             }
        #         """)

        self.setWindowTitle(f"JT808-BSJ 协议解析工具 {self.app_version}")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon(self.load_resource("assets/icons/app.ico")))

        # 创建主部件和布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)  # 竖直布局

        # 协议输入区域
        input_label = QLabel("协议输入:")
        layout.addWidget(input_label)

        self.input_text = QTextEdit()
        # font1 = QFont()
        # font1.setPointSize(10)
        # font1.setFamily("Consolas")
        # self.input_text.setFont(font1)
        self.input_text.setPlaceholderText("请输入协议数据或点击导入文件...")
        layout.addWidget(self.input_text, stretch=3)

        # 按钮区域,使用尺寸策略 + 样式表
        btn_layout = QHBoxLayout()  # 改水平布局
        btn_layout.setSpacing(15)  # 按钮间距
        btn_layout.setContentsMargins(0, 10, 0, 10)  # 上下左右边距
        # btn_layout.addStretch(1)  # 顶部弹性空间

        # 导入按钮 - 尺寸策略 + 样式
        self.import_btn = QPushButton("📁 导入协议文件")
        # 设置尺寸策略：水平方向优先扩展，垂直方向固定
        self.import_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.import_btn.setMinimumSize(150, 40)  # 最小尺寸
        self.import_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border-radius: 8px;
                        padding: 8px;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                    QPushButton:disabled {
                                background-color: #cccccc;
                                color: #666666;
                                box-shadow: none;
                                transform: none;
                            }
                """)
        self.import_btn.clicked.connect(self.import_file)
        btn_layout.addWidget(self.import_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # 解析按钮
        self.parse_btn = QPushButton("🔍 解析协议")
        self.parse_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.parse_btn.setMinimumSize(150, 40)
        self.parse_btn.setStyleSheet("""
                            QPushButton {
                                background-color: #008CBA;
                                color: white;
                                border-radius: 8px;
                                padding: 8px;
                                font-size: 14px;
                            }
                            QPushButton:hover {
                                background-color: #007B9C;
                            }
                            QPushButton:disabled {
                                background-color: #cccccc;
                                color: #666666;
                                box-shadow: none;
                                transform: none;
                            }
                        """)
        btn_layout.addWidget(self.parse_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        self.parse_btn.clicked.connect(self.parse_protocol)

        # 清空按钮
        self.clear_btn = QPushButton("🗑️ 清空内容")
        self.clear_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.clear_btn.setMinimumSize(150, 40)
        self.clear_btn.setStyleSheet("""
                            QPushButton {
                                background-color: #f44336;
                                color: white;
                                border-radius: 8px;
                                padding: 8px;
                                font-size: 14px;
                            }
                            QPushButton:hover {
                                background-color: #d32f2f;
                            }
                            QPushButton:disabled {
                                background-color: #cccccc;
                                color: #666666;
                                box-shadow: none;
                                transform: none;
                            }
                        """)
        self.clear_btn.clicked.connect(self.clear_all)
        btn_layout.addWidget(self.clear_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # # 测试按钮
        # seltest_btn = QPushButton("❤️异常测试，别点我")
        # self.test_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        # self.test_btn.setMinimumSize(150, 40)
        # self.test_btn.setStyleSheet("""
        #                    QPushButton {
        #                        background-color: #4CAF50;
        #                        color: white;
        #                        border-radius: 8px;
        #                        padding: 8px;
        #                        font-size: 14px;
        #                    }
        #                    QPushButton:hover {
        #                        background-color: #45a049;
        #                    }
        #                """)
        # self.test_btn.clicked.connect(self.test_error)
        # btn_layout.addWidget(self.test_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        btn_layout.addStretch(1)  # 底部弹性空间
        layout.addLayout(btn_layout)

        # 结果显示区域
        result_label = QLabel("解析结果:")
        layout.addWidget(result_label)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("解析结果将显示在这里...")
        layout.addWidget(self.result_text, stretch=5)

        # 添加版权信息 - 方案2
        # self.copyright_label = QLabel("© 2025 协议解析工具 - 版权所有")
        # self.copyright_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.copyright_label.setStyleSheet("""
        #             QLabel {
        #                 color: #808080;
        #                 font-size: 12px;
        #                 padding: 5px;
        #             }
        #         """)
        # layout.addWidget(self.copyright_label)
        # # 设置主布局边距
        # layout.setContentsMargins(15, 15, 15, 15)

        # 状态栏
        self.statusBar().showMessage("就绪")

        # 版权信息-方案1
        status_label = QLabel()
        status_label.setText(self.copyright_info)
        status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.statusBar().addPermanentWidget(status_label)

    @staticmethod
    def set_font_size(widget, size, family="Consolas"):
        """通用设置字体大小的方法"""
        font = QFont()
        font.setPointSize(size)
        font.setFamily(family)
        widget.setFont(font)

    @staticmethod
    def load_resource(relative_path):
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
                        self.input_text.setText(f.read())
                    self.statusBar().showMessage(f"已加载: {file_path}")
                except Exception as e:
                    logger.error(e)
                    self.statusBar().showMessage(f"错误: {str(e)}")
            else:
                logger.error("选择的文件类型错误。当前只支持.txt格式")
                QMessageBox.warning(self, "格式错误", "请选择.txt格式的文件！")

    def parse_protocol(self):
        self.result_text.clear()
        # 获取数据
        raw_data = self.input_text.toPlainText().strip()
        if not raw_data:
            self.statusBar().showMessage("错误：无输入数据")
            return

        batch_data = raw_data.splitlines()
        self.total_tasks = len(batch_data)
        self.completed_tasks = 0

        # 解析总条数大于20使用多线程
        if self.total_tasks > 10:
            # 禁用按钮，记录任务总数（用于判断是否全部完成）
            self.parse_btn.setEnabled(False)
            self.clear_btn.setEnabled(False)
            self.import_btn.setEnabled(False)
            # 3. 为每个数据包创建一个任务，提交到线程池
            for i, data in enumerate(batch_data):
                task_id = i + 1  # 任务ID从1开始
                task = ParseTask(task_id=task_id, data=data)

                # 关联信号
                task.signals.status_updated.connect(self.update_ui_status)
                task.signals.finished.connect(self.on_batch_task_finished)
                task.signals.error.connect(self.on_batch_task_error)

                # 提交任务
                QThreadPool.globalInstance().start(task)
        else:
            # 直接调用解析方法
            parsed_data = []
            report = ""
            for i, line in enumerate(batch_data):
                is_valid, msg, data = parse_jt808(line)  # 解析报文
                if is_valid:
                    result = json.dumps(data, ensure_ascii=False, indent=2)
                    parsed_data.append(result)
                else:
                    parsed_data.append(msg)

            # 生成解析报告
            for index, item in enumerate(parsed_data, start=1):
                report += "=" * 20 + f"第{index}条" + "=" * 20 + "\n"
                report += item + "\n"

            self.result_text.setText(report)
            self.statusBar().showMessage(f"解析完成，共发现 {len(parsed_data)} 条记录")

    def on_batch_task_finished(self, task_id):
        self.completed_tasks += 1
        # 所有任务完成，启用按钮
        if self.completed_tasks == self.total_tasks:
            time.sleep(0.5)
            self.parse_btn.setEnabled(True)
            self.import_btn.setEnabled(True)
            self.clear_btn.setEnabled(True)
            self.statusBar().showMessage(f"解析完成，共发现 {self.completed_tasks} 条记录")

    def update_ui_status(self, task_id, result):
        """
        多线程并行解析，结果是无序的
        """
        # 生成解析报告
        report = ">" * 20 + f"第{task_id}条" + ">" * 20 + "\n"
        report += result + "\n"
        # self.result_text.setText(report)
        self.result_text.append(report)

    def on_batch_task_error(self, task_id, msg, error):
        logger.error(f"task_id={task_id}, error={msg}")
        self.statusBar().showMessage(f"解析异常：{msg}")

    def clear_all(self):
        self.input_text.clear()
        self.result_text.clear()
        self.statusBar().showMessage("内容已清空")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 设置全局字体
    default_font = QFont()
    default_font.setPointSize(10)  # 设置字体大小为12pt
    # 可选：设置字体家族
    default_font.setFamily("Consolas")  # 例如设置为黑体，解决中文显示问题
    app.setFont(default_font)  # 将字体应用到整个应用程序

    window = ProtocolParser()
    window.show()
    sys.exit(app.exec())
