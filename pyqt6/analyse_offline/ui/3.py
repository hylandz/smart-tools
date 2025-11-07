import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLineEdit, QTextEdit,
                             QFileDialog, QFormLayout, QLabel, QCheckBox)
from PyQt6.QtCore import Qt

from analyse_offline.src.core.a08_analyze import analyze_excel_files


class TextEditLogger(logging.Handler):
    """将日志输出到QTextEdit组件的处理器"""

    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit

    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.status_label = None
        self.TOOL_VERSION = "v1.0.0"
        self.text_handler = None
        self.text_display = None
        self.clear_btn = None
        self.display_btn = None
        self.save_log_checkbox = None
        self.list_input = None
        self.string_input = None
        self.folder_btn = None
        self.folder_path = None
        self.log_file_handler = None  # 日志文件处理器
        self.init_ui()

    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle("A08离线率Excel表分析工具")
        self.setGeometry(100, 100, 800, 600)

        # 创建中心部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # -------------------- 上部分：输入区域 --------------------
        input_widget = QWidget()
        input_layout = QFormLayout(input_widget)
        input_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        input_layout.setSpacing(15)

        # 文件夹选择按钮
        self.folder_path = ""
        self.folder_btn = QPushButton("选择文件夹")
        self.folder_btn.clicked.connect(self.select_folder)
        input_layout.addRow("文件夹路径：", self.folder_btn)

        # 字符串变量输入框
        self.string_input = QLineEdit()
        self.string_input.setPlaceholderText("请输入字符串数据")
        input_layout.addRow("设备名称开头：", self.string_input)

        # 列表数据输入框（用逗号分隔）
        self.list_input = QLineEdit()
        holder_text = ("安吉租赁有限公司,亚民生旅业有限责任公司（民生）,上海东正汽车金融股份有限公司（东正）,浙江大搜车融资租赁有限公司,塔比星信息技术（深圳）有限公司,"
                       "广西通盛融资租赁有限公司,北京中交兴路车联网科技有限公司,WJJZ皖江金融租赁股份有限公司,华润集团")

        # self.list_input.setPlaceholderText("请输入列表数据，用逗号分隔")
        self.list_input.setPlaceholderText(holder_text)
        input_layout.addRow("过滤客户名称：", self.list_input)

        # 日志保存选项 - 新增单选框
        self.save_log_checkbox = QCheckBox("将日志保存为txt文件")
        self.save_log_checkbox.setChecked(False)  # 默认不选中
        self.save_log_checkbox.stateChanged.connect(self.update_log_handlers)
        input_layout.addRow(self.save_log_checkbox)

        # 按钮区域（显示和清除按钮）
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        # 显示按钮
        self.display_btn = QPushButton("显示输入内容")
        self.display_btn.clicked.connect(self.display_inputs2)
        button_layout.addWidget(self.display_btn)

        # 清除按钮
        self.clear_btn = QPushButton("清除所有内容")
        self.clear_btn.clicked.connect(self.clear_all)
        button_layout.addWidget(self.clear_btn)

        input_layout.addRow(button_layout)

        # 将输入区域添加到主布局
        main_layout.addWidget(input_widget)

        # 添加分隔线
        line = QLabel("")
        line.setStyleSheet("background-color: #cccccc; height: 2px;")
        main_layout.addWidget(line)

        # -------------------- 下部分：显示区域 --------------------
        display_widget = QWidget()
        display_layout = QVBoxLayout(display_widget)

        # 显示区域标题
        display_label = QLabel("信息显示区域")
        display_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        display_layout.addWidget(display_label)

        # 创建文本编辑框用于显示信息
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)  # 设置为只读
        self.text_display.setStyleSheet("background-color: #f0f0f0;")
        display_layout.addWidget(self.text_display)

        # 将显示区域添加到主布局
        main_layout.addWidget(display_widget, 1)  # 1表示拉伸因子

        # 状态栏
        self.statusBar().showMessage("就绪")

        # 版权信息-方案1
        self.status_label = QLabel()
        self.status_label.setText(f"© 2025 协议解析工具{self.TOOL_VERSION} - 版权所有")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.statusBar().addPermanentWidget(self.status_label)

        # 配置日志系统
        self.setup_logging()

    # 辅助方法：获取QLineEdit的值（优先用户输入，无输入则用placeholder）
    def get_input_value(self, line_edit):
        text = line_edit.text().strip()
        return text if text else line_edit.placeholderText()

    def setup_logging(self):
        """配置日志系统，使其输出到文本编辑框"""
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # 清除已有的处理器，避免重复输出
        if logger.hasHandlers():
            logger.handlers.clear()

        # 创建文本框日志处理器并添加到日志记录器
        self.text_handler = TextEditLogger(self.text_display)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.text_handler.setFormatter(formatter)
        logger.addHandler(self.text_handler)

        # 初始不添加文件处理器，因为默认不选中
        self.log_file_handler = None

        # 记录程序启动信息
        logging.info("程序启动成功")

    def update_log_handlers(self):
        """根据复选框状态更新日志处理器"""
        logger = logging.getLogger()

        # 如果选中且文件处理器不存在，则添加文件处理器
        if self.save_log_checkbox.isChecked() and self.log_file_handler is None:
            # 日志文件保存在当前目录，名为app.log
            log_file = Path(__file__).parent / "app.log"
            self.log_file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            self.log_file_handler.setFormatter(formatter)
            logger.addHandler(self.log_file_handler)
            logging.info(f"已启用日志保存功能，日志文件路径：{log_file.resolve()}")

        # 如果未选中但文件处理器存在，则移除文件处理器
        elif not self.save_log_checkbox.isChecked() and self.log_file_handler is not None:
            logger.removeHandler(self.log_file_handler)
            self.log_file_handler.close()  # 关闭文件
            self.log_file_handler = None
            logging.info("已禁用日志保存功能")

    def select_folder(self):
        """选择文件夹并记录路径"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择文件夹", ""
        )
        if folder:
            self.folder_path = folder
            # 只显示文件夹名，不显示完整路径，避免按钮文字过长
            self.folder_btn.setText(f"已选择: {folder.split('/')[-1]}")
            logging.info(f"已选择文件夹: {folder}")

    def display_inputs(self):
        """显示所有输入的内容"""
        # 清空显示区域（保留日志）
        cursor = self.text_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        cursor.select(cursor.SelectionType.Document)
        cursor.removeSelectedText()

        # 获取输入内容
        string_data = self.string_input.text()
        list_data = self.list_input.text().split(',')
        # 清理列表数据中的空格
        list_data = [item.strip() for item in list_data if item.strip()]

        # 显示内容
        self.text_display.append("===== 输入内容 =====")
        self.text_display.append(f"文件夹路径: {self.folder_path if self.folder_path else '未选择'}")
        self.text_display.append(f"字符串变量: {string_data if string_data else '未输入'}")
        self.text_display.append(f"列表数据: {list_data if list_data else '未输入'}")
        self.text_display.append("\n===== 日志信息 =====")

        # 记录日志
        analyze_excel_files(self.folder_path, string_data, list_data)

    def display_inputs2(self):
        """显示输入内容（核心修改部分）"""
        # 清空显示区域
        self.text_display.clear()

        # 获取输入内容
        string_data = self.string_input.text()
        # list_data = self.list_input.text().split(',')
        list_data = self.get_input_value(self.list_input).split(',')
        list_data = [item.strip() for item in list_data if item.strip()]

        # 定义要显示的内容（同时通过日志输出）
        content_lines = [
            "===== 输入内容 =====",
            f"文件夹路径: {self.folder_path if self.folder_path else '未选择'}",
            f"字符串变量: {string_data if string_data else '未输入'}",
            f"列表数据: {list_data if list_data else '未输入'}",
            "\n===== 日志信息 ====="
        ]

        # 同时输出到界面和日志系统
        for line in content_lines:
            self.text_display.append(line)  # 显示在界面
            if line not in ["", "\n===== 日志信息 ====="]:  # 过滤不需要记录的分隔线
                logging.info(line)  # 通过日志系统记录（会保存到文件）

        # 记录"显示输入内容"操作日志
        analyze_excel_files(self.folder_path, string_data, list_data)

    def clear_all(self):
        """清除所有输入内容和显示区域"""
        # 重置文件夹选择
        self.folder_path = ""
        self.folder_btn.setText("选择文件夹")

        # 清空输入框
        self.string_input.clear()
        self.list_input.clear()

        # 清空显示区域
        self.text_display.clear()

        # 记录清除操作日志
        logging.info(">" * 20 + "已清除所有输入内容和显示信息")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
