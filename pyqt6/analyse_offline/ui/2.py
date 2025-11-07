import sys
import logging
import time
from pathlib import Path

import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLineEdit, QTextEdit,
                             QFileDialog, QFormLayout, QLabel, QCheckBox)
from PyQt6.QtCore import Qt, QObject, QRunnable, pyqtSignal
from PyQt6.QtGui import (QFont, QPalette, QColor, QIcon, QPixmap,
                         QPainter, QPen)

from analyse_offline.src.core.a08_analyze import analyze_excel_files


class TextEditLogger(logging.Handler):
    """将日志输出到QTextEdit组件的处理器"""

    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit

    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)


class TaskSignals(QObject):
    status_updated = pyqtSignal(int, str)


class MyTask(QRunnable):
    def __init__(self, task_id, folder_path, prefix, exclude_list):
        super().__init__()
        self.task_id = task_id
        self.signals = TaskSignals()
        self.folder_path = folder_path
        self.prefix = prefix
        self.exclude_list = exclude_list

    def run(self):
        pass

    def process_excel(self):
        """处理报表数据"""
        # 获取所有Excel文件
        files = list(Path(self.folder_path).glob("*.xlsx")) + list(Path(self.folder_path).glob("*.xls"))
        total = len(files)

        if total == 0:
            logger("💢 错误：未找到任何Excel（.xlsx和.xls）文件！")
            # self.finished.emit()
            return

        self.log.emit(f"💡 找到{total}个Excel文件，开始处理...\n")

        all_sum, all_offline_sum, result, excel_num = 0, 0, 0, 0
        start_time = time.time()

        # 处理每个文件（每个文件处理完后更新进度）
        for i, file in enumerate(files, 1):  # i从1开始计数
            try:
                # 读取Excel（实际使用时取消注释）
                df = pd.read_excel(file)

                # 关键：初始化filtered为原始DataFrame，确保它始终是DataFrame类型
                filtered = df.copy()  # 用copy()避免修改原始df

                # 1. 按设备前缀过滤（如果前缀不为空）
                if self.prefix:  # 注意：需确保self.prefix是字符串类型（如""表示空）
                    # 先判断"设备"列是否存在，避免KeyError
                    if "设备" not in filtered.columns:
                        self.log.emit(f"🤬 错误：Excel文件{file.name}中没有'设备'列！")
                        continue  # 跳过当前文件处理
                    # 安全转换为字符串并过滤（处理可能的NaN值）
                    filtered = filtered[
                        filtered["设备"].astype(str, errors="ignore").str.startswith(self.prefix, na=False)
                    ]

                # 2. 按排除客户过滤（如果排除列表不为空）
                if self.exclude_list:  # 注意：需确保self.exclude_list是列表类型（如[]表示空）
                    # 先判断"客户名称"列是否存在，避免KeyError
                    if "客户名称" not in filtered.columns:
                        self.log.emit(f"🤬 错误：Excel文件{file.name}中没有'客户名称'列！")
                        continue  # 跳过当前文件处理
                    filtered = filtered[~filtered["客户名称"].isin(self.exclude_list)]

                # 3. 统计（确保"设备状态"列存在）
                if "设备状态" not in filtered.columns:
                    self.log.emit(f"🤬 错误：Excel文件{file.name}中没有'设备状态'列！")
                    continue  # 跳过当前文件处理

                total_count = len(filtered)
                offline_count = (filtered["设备状态"] == "离线").sum()
                all_sum += total_count
                all_offline_sum += offline_count

                self.log.emit(f"序号{i}-处理完成 {file.name}：")
                self.log.emit(f"  符合条件设备：{total_count}")
                self.log.emit(f"  离线设备：{offline_count}\n")

                # 关键：当前文件处理完成后，计算并发送进度（已处理数/总数*100）
                current_progress = int((i / total) * 100)
                self.progress.emit(current_progress)

            except Exception as e:
                self.log.emit(f"处理 {file.name} 出错：{str(e)}\n")
                # 即使出错，也视为该文件已处理，更新进度
                current_progress = int((i / total) * 100)
                self.progress.emit(current_progress)
                continue

        end_time = time.time()
        elapsed_time = end_time - start_time
        # 计算小时、分钟和秒
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        # 格式化输出
        formatted_time = f"{int(hours)} 时 {int(minutes):02d} 分 {seconds:.2f} 秒"
        self.log.emit("ℹ️ 结束执行Excel分析任务...")

        # 添加分析分隔符
        self.log.emit("\n" + ">" * 50)
        self.log.emit("📊 数据分析结果...")
        self.log.emit(">" * 50)

        self.log.emit(f"设备总数：{all_sum}")
        self.log.emit(f"设备离线总数：{all_offline_sum}")

        if all_sum != 0:
            result = all_offline_sum / all_sum

        self.log.emit(f"设备离线率：{result * 100:.2f}%" if all_sum else "设备离线率：0.00%")
        self.log.emit(f"总耗时：{formatted_time}\n")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.folder_path = None
        self.TOOL_VERSION = "v1.0.0"
        self.log_file_handler = None
        self.init_ui()

    def init_ui(self):
        # 窗口基本设置
        self.setWindowTitle("A08离线率Excel表分析工具")
        self.setGeometry(100, 100, 900, 700)

        # 确保中文显示的字体设置
        font = QFont()
        font.setFamily("SimHei")
        self.setFont(font)

        # 中心部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 样式表 - 移除QGroupBox相关样式，优化直接布局的视觉效果
        central_widget.setStyleSheet("""
            QWidget {
                background-color: #f5f7fa;
            }
            /* 内容容器样式，替代原QGroupBox的视觉效果 */
            .content-container {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
            }
            QPushButton {
                background-color: #4285f4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                min-height: 34px;
                min-width: 80px;
                margin: 2px;
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #3367d6;
                box-shadow: 0 2px 8px rgba(66, 133, 244, 0.3);
            }
            QPushButton:pressed {
                background-color: #2850b8;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
            }
            QPushButton {
                icon-size: 18px;
                padding-left: 12px;
                padding-right: 16px;
            }
            QLineEdit {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 6px 10px;
                min-height: 30px;
            }
            QLineEdit:focus {
                border-color: #4285f4;
                outline: none;
            }
            QTextEdit {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 12px;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 9pt;
            }
            .section-title {
                font-size: 11pt;
                font-weight: bold;
                color: #333;
                margin-bottom: 8px;
            }
        """)

        # -------------------- 上部分：输入区域（无QGroupBox） --------------------
        # 输入区域标题
        input_title = QLabel("输入区域")
        input_title.setObjectName("section-title")
        main_layout.addWidget(input_title)

        # 输入内容容器（替代QGroupBox，使用样式类控制外观）
        input_container = QWidget()
        input_container.setObjectName("content-container")
        input_layout = QFormLayout(input_container)
        input_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        input_layout.setSpacing(12)
        input_layout.setContentsMargins(0, 0, 0, 0)  # 容器已有内边距，这里设为0

        # 文件夹选择按钮（带图标）
        self.folder_path = ""
        folder_layout = QHBoxLayout()

        self.folder_btn = QPushButton("选择文件夹")
        self.folder_btn.setIcon(self.get_icon("folder", "📂", Qt.GlobalColor.white))
        self.folder_btn.clicked.connect(self.select_folder)

        self.folder_label = QLabel("未选择文件夹")
        self.folder_label.setStyleSheet("color: #666; font-style: italic;")
        self.folder_label.setMinimumWidth(300)
        folder_layout.addWidget(self.folder_btn)
        folder_layout.addWidget(self.folder_label, 1)
        input_layout.addRow("文件夹路径：", folder_layout)

        # 字符串输入框
        self.string_input = QLineEdit()
        self.string_input.setPlaceholderText("请输入字符串数据")
        input_layout.addRow("设备名称开头：", self.string_input)

        # 列表输入框
        self.list_input = QLineEdit()
        # self.list_input.setPlaceholderText("请输入列表数据，用逗号分隔")
        holder_text = ("安吉租赁有限公司,亚民生旅业有限责任公司（民生）,上海东正汽车金融股份有限公司（东正）,浙江大搜车融资租赁有限公司,塔比星信息技术（深圳）有限公司,"
                       "广西通盛融资租赁有限公司,北京中交兴路车联网科技有限公司,WJJZ皖江金融租赁股份有限公司,华润集团")
        self.list_input.setPlaceholderText(holder_text)
        input_layout.addRow("过滤客户名称：", self.list_input)

        # 日志保存选项
        self.save_log_checkbox = QCheckBox("将日志保存为txt文件")
        self.save_log_checkbox.setChecked(False)
        self.save_log_checkbox.stateChanged.connect(self.update_log_handlers)
        input_layout.addRow(self.save_log_checkbox)

        # 按钮区域（带图标）
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 显示按钮
        self.display_btn = QPushButton("显示输入内容")
        self.display_btn.setIcon(self.get_icon("view-list", "📋", Qt.GlobalColor.white))
        self.display_btn.clicked.connect(self.display_inputs)

        # 清除按钮
        self.clear_btn = QPushButton("清除所有内容")
        self.clear_btn.setIcon(self.get_icon("edit-clear", "🗑️", Qt.GlobalColor.white))
        self.clear_btn.clicked.connect(self.clear_all)

        button_layout.addWidget(self.display_btn)
        button_layout.addWidget(self.clear_btn)
        input_layout.addRow(button_layout)

        # 上部分添加到主布局（比例1）
        main_layout.addWidget(input_container, 1)

        # -------------------- 下部分：显示区域（无QGroupBox） --------------------
        # 显示区域标题
        display_title = QLabel("显示区域")
        display_title.setObjectName("section-title")
        main_layout.addWidget(display_title)

        # 显示内容容器（替代QGroupBox）
        display_container = QWidget()
        display_container.setObjectName("content-container")
        display_layout = QVBoxLayout(display_container)
        display_layout.setContentsMargins(0, 0, 0, 0)  # 容器已有内边距
        display_layout.setSpacing(0)

        # 直接显示文本编辑框，无额外标题
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        display_layout.addWidget(self.text_display)

        # 下部分添加到主布局（比例3）
        main_layout.addWidget(display_container, 3)

        # # 状态栏
        self.statusBar().showMessage("就绪")

        # 版权信息-方案1
        self.status_label = QLabel()
        self.status_label.setText(f"© 2025 协议解析工具{self.TOOL_VERSION} - 版权所有")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.statusBar().addPermanentWidget(self.status_label)

        # 配置日志
        self.setup_logging()

    def get_icon(self, theme_name, fallback_text, icon_color=Qt.GlobalColor.white):
        """获取系统主题图标或创建指定颜色的文本图标"""
        icon = QIcon.fromTheme(theme_name)

        if icon.isNull():
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            painter.setFont(QFont("Arial", 12))
            painter.setPen(QPen(icon_color))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, fallback_text)
            painter.end()

            icon = QIcon(pixmap)

        return icon

    # 辅助方法：获取QLineEdit的值（优先用户输入，无输入则用placeholder）
    def get_input_value(self, line_edit):
        text = line_edit.text().strip()
        return text if text else line_edit.placeholderText()

    def setup_logging(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        if logger.hasHandlers():
            logger.handlers.clear()

        self.text_handler = TextEditLogger(self.text_display)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.text_handler.setFormatter(formatter)
        logger.addHandler(self.text_handler)

        self.log_file_handler = None
        logging.info("程序启动成功")

    def update_log_handlers(self):
        logger = logging.getLogger()

        if self.save_log_checkbox.isChecked() and not self.log_file_handler:
            log_file = Path(__file__).parent / "app2.log"
            self.log_file_handler = logging.FileHandler(log_file, encoding='utf-8')
            self.log_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(self.log_file_handler)
            logging.info(f"日志保存至：{log_file}")
        elif not self.save_log_checkbox.isChecked() and self.log_file_handler:
            logger.removeHandler(self.log_file_handler)
            self.log_file_handler.close()
            self.log_file_handler = None
            logging.info("已关闭日志保存")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹", "")
        if folder:
            self.folder_path = folder
            self.folder_label.setText(folder)
            self.folder_label.setToolTip(folder)
            logging.info(f"选择文件夹: {folder}")

    def display_inputs(self):
        self.text_display.clear()

        string_data = self.get_input_value(self.string_input)
        list_raw = self.get_input_value(self.list_input)
        list_data = [item.strip() for item in list_raw.split(',') if item.strip()]

        # 显示内容
        self.text_display.append("===== 输入内容 =====")
        self.text_display.append(f"文件夹路径: {self.folder_path if self.folder_path else '未选择'}")
        self.text_display.append(f"字符串变量: {string_data if string_data else '未输入'}")
        self.text_display.append(f"列表数据: {list_data if list_data else '未输入'}")
        self.text_display.append("\n===== 日志信息 =====")

        if self.save_log_checkbox.isChecked():
            content_lines = [
                "===== 输入内容 =====",
                f"文件夹路径: {self.folder_path or '未选择'}",
                f"字符串变量: {string_data}",
                f"列表数据: {list_data}",
                "\n===== 日志信息 ====="
            ]
            for line in content_lines:
                self.text_display.append(line)
                if line not in ["", "\n===== 日志信息 ====="]:
                    logging.info(line)

        # 记录"显示输入内容"操作日志
        analyze_excel_files(self.folder_path, string_data, list_data)

    def clear_all(self):
        self.folder_path = ""
        self.folder_label.setText("未选择文件夹")
        self.string_input.clear()
        self.list_input.clear()
        self.text_display.clear()
        logging.info(">" * 20 + "已清除所有输入内容和显示信息")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 全局字体设置
    font = QFont()
    font.setFamily("SimHei")
    font.setPointSize(10)
    app.setFont(font)

    # 调色板设置
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(245, 247, 250))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(51, 51, 51))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
