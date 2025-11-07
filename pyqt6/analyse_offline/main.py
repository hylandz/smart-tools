import sys
import time
import traceback
from datetime import datetime

import pandas as pd
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLineEdit, QTextEdit,
                             QFileDialog, QFormLayout, QLabel, QProgressBar,
                             QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor

from analyse_offline.src.util.logutil import analyse_logging


def custom_excepthook(cls, value, tb):
    """全局异常捕获：捕获未处理的系统级异常，如崩溃时的堆栈跟踪"""
    # 创建日志目录（使用Path对象）
    log_dir = Path.home() / "AnalyseLogs"  # c:\\Users\{用户名}
    # log_dir = Path(__file__).parent / "ProtocolParserLogs" # 当前文件上一级目录(项目根路径)
    log_dir.mkdir(parents=True, exist_ok=True)  # 自动创建父目录

    # 生成日志文件路径
    # 固定日志文件名（按日期归档）
    log_file = log_dir / f"global-error_{datetime.now().strftime('%Y%m%d')}.log"

    # 写入错误详情
    with open(log_file, mode='a', encoding='utf-8') as f:
        f.write("\n\n======= [全局错误记录] =======\n")
        f.write(f"错误时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n")
        f.write(f"异常类型: {cls.__name__}\n")
        f.write(f"错误信息: {str(value)}\n")
        f.write("堆栈跟踪:\n")
        f.write(''.join(traceback.format_tb(tb)))
        f.write(">" * 50 + "\n")

        # 开发环境弹窗提示（打包后自动跳过）
        # if not getattr(sys, 'frozen', False):
        #     import tkinter.messagebox
        #     tkinter.messagebox.showerror("程序错误",f"发生未知错误，详细信息已保存至:\n{log_file}")
        # tkinter.messagebox.showerror("程序错误", f"发生未知错误，详细信息已保存至:\n{log_file}")
        # 使用PyQt6的QMessageBox显示错误（处理应用程序实例问题）
        try:
            # 尝试获取已存在的QApplication实例
            app = QApplication.instance()
            if app is None:
                # 如果没有实例，则创建一个新的QApplication
                app = QApplication(sys.argv)

            # 显示错误弹窗
            QMessageBox.critical(
                None,  # 父窗口为None（无父窗口）
                "程序错误",
                f"发生未知错误，详细信息已保存至:\n{log_file}"
            )

            # 如果是新创建的应用，需要执行一次应用循环（否则弹窗可能不显示）
            if app is None:
                sys.exit(app.exec())
        except Exception as e:
            # 极端情况下如果QMessageBox也失败，打印错误到控制台
            print(f"弹窗显示失败: {e}")
            print(f"错误日志已保存至: {log_file}")


# 设置全局异常捕获
sys.excepthook = custom_excepthook
logger = analyse_logging()


# 子线程：处理Excel分析（每个文件处理完后发送进度）
class ExcelThread(QThread):
    log = pyqtSignal(str)  # 日志信号
    progress = pyqtSignal(int)  # 进度信号（每个文件处理完后发送）
    finished = pyqtSignal()  # 全部完成信号

    def __init__(self, folder_path, prefix, exclude_list):
        super().__init__()
        self.folder_path = folder_path
        self.prefix = prefix
        self.exclude_list = exclude_list

    def process_excel(self):
        """处理报表数据"""
        # 获取所有Excel文件
        files = list(Path(self.folder_path).glob("*.xlsx")) + list(Path(self.folder_path).glob("*.xls"))
        total = len(files)

        if total == 0:
            self.log.emit("💢 错误：未找到任何Excel（.xlsx和.xls）文件！")
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
        # self.log.emit("=" * 50)

    def run(self):
        try:
            self.process_excel()
        except Exception as e:
            logger.error(str(e))
            self.log.emit(f"❌️ 报表分析报错：{str(e)}")
        finally:
            self.finished.emit()  # 全部完成


# 主窗口
class MainWindow(QMainWindow):
    TOOL_VERSION = "v1.1.4"

    def __init__(self):
        super().__init__()
        self.thread = None  # 线程对象
        self.init_ui()

    def init_ui(self):
        # 窗口基本设置
        self.setWindowTitle(f"设备离线数据分析工具_{self.TOOL_VERSION}")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(800, 600)
        self.setWindowIcon(QIcon(self.load_resource("assets/icons/logo.ico")))

        # 字体设置
        font = QFont()
        font.setFamily("Microsoft YaHei")
        font.setPointSize(10)
        self.setFont(font)

        # 中心部件和主布局
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # ----------------全局样式表----------------------------------
        central.setStyleSheet("""
            /* 主背景 */
            QWidget {
                background-color: #f0f2f5;
            }

            /* 卡片容器 */
            .card {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            }

            /* 标题样式 */
            .section-title {
                color: #1a1a1a;
                font-size: 14pt;
                font-weight: 600;
                margin-bottom: 15px;
                padding-bottom: 8px;
                border-bottom: 1px solid #f0f0f0;
            }

              /* -----------默认按钮基础样式（所有按钮的默认值）------------------- */
             QPushButton {
                color: white;                  /* 默认文字白色 */
                background-color: #2563eb;     /* 默认蓝色（主色调） */
                border: none;
                border-radius: 6px;
                padding: 8px 18px;
                font-size: 10pt;
                min-height: 36px;
                cursor: pointer;
                transition: all 0.2s ease;     /* 过渡动画 */
            }
            
            /* 默认按钮悬停效果 */
            QPushButton:hover {
                background-color: #1d4ed8;     /* 悬停时颜色加深 */
                transform: translateY(-1px);   /* 轻微上浮 */
                box-shadow: 0 3px 8px rgba(37, 99, 235, 0.2);  /* 淡蓝色阴影 */
            }
            /* -------------------- 按钮样式自定义（覆盖默认样式） -------------------- */
            /* 开始分析按钮（蓝色） */
            QPushButton#startBtn {
                background-color: #2c82e0;
            }
            QPushButton#startBtn:hover {
                background-color: #1e6cd3;
                transform: translateY(-1px);
                box-shadow: 0 3px 8px rgba(44, 130, 224, 0.2);
            }
            
            /* 保存日志按钮（紫色 - 新增独特颜色） */
            QPushButton#saveBtn {
                background-color: #7b68ee;  /* 主紫色 */
            }
            QPushButton#saveBtn:hover {
                background-color: #6a5acd;  /* 深紫色（悬停） */
                transform: translateY(-1px);
                box-shadow: 0 3px 8px rgba(123, 104, 238, 0.2);
            }
            
            /* 填充示例按钮（绿色） */
            QPushButton#fillExampleBtn {
                background-color: #4caf50;
            }
            QPushButton#fillExampleBtn:hover {
                background-color: #3d9140;
                transform: translateY(-1px);
                box-shadow: 0 3px 8px rgba(76, 175, 80, 0.2);
            }
            
            /* 清除按钮（红色） */
            QPushButton#clearBtn {
                background-color: #f56c6c;
            }
            QPushButton#clearBtn:hover {
                background-color: #e34c4c;
                transform: translateY(-1px);
                box-shadow: 0 3px 8px rgba(245, 108, 108, 0.2);
            }
           
            /* ------------------按钮禁用状态默认样式------------------- */
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                box-shadow: none;
                transform: none;
            }
            /* 开始按钮禁用 */
            QPushButton#startBtn:disabled {
                background-color: #cccccc;  /* 与普通按钮一致的灰色 */
                color: #666666;
                box-shadow: none;
                transform: none;
            }
            /* 保存按钮禁用 */
            QPushButton#saveBtn:disabled {
                background-color: #cccccc;  /* 与普通按钮一致的灰色 */
                color: #666666;
                box-shadow: none;
                transform: none;
            }
            /* 清除按钮禁用 */
            QPushButton#clearBtn:disabled {
                background-color: #cccccc;  /* 与普通按钮一致的灰色 */
                color: #666666;
                box-shadow: none;
                transform: none;
            }
            /* 填充示例按钮禁用 */
            QPushButton#fillExampleBtn:disabled {
                background-color: #cccccc;  /* 与普通按钮一致的灰色 */
                color: #666666;
                box-shadow: none;
                transform: none;
            }
            
            /* 日志区域样式 */
            QTextEdit {
                border: 1px solid #d0d7dc;
                border-radius: 6px;
                padding: 12px;
            }
            /* 输入框样式 */
            QLineEdit {
                background-color: white;
                border: 1px solid #d0d7dc;
                border-radius: 6px;
                padding: 8px 12px;
                min-height: 36px;
            }
            QLineEdit:focus {
                border-color: #2c82e0;
            }

            /* 日志显示区域 */
            QTextEdit {
                background-color: white;
                border: 1px solid #d0d7dc;
                border-radius: 6px;
                padding: 12px;
                font-family: "Consolas", "Microsoft YaHei", monospace;
            }

            /* 进度条样式#e8f5e9（绿色主题） */
            QProgressBar {
                height: 10px;
                border-radius: 5px;
                background-color: #e6e6e6;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 4px;
                transition: width 0.3s ease;  /* 平滑过渡动画 */
            }

            /* 进度文本样式 */
            .progress-label {
                color: #656d76;
                font-size: 9pt;
                min-width: 60px;
            }
            .progress-value {
                color: #2e7d32;
                font-size: 9pt;
                font-weight: 500;
                min-width: 50px;
                text-align: right;
            }
        """)

        # -------------------- 输入区域 --------------------
        input_card = QWidget()
        input_card.setObjectName("card")
        input_layout = QVBoxLayout(input_card)

        # 输入区域标题
        input_title = QLabel("分析参数设置")
        input_title.setObjectName("section-title")
        bold_font = QFont()
        bold_font.setFamily("Microsoft YaHei")
        bold_font.setPointSize(10)
        bold_font.setWeight(QFont.Weight.Bold)  # 代码设置加粗
        input_title.setFont(bold_font)
        input_layout.addWidget(input_title)

        # 表单布局
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # 文件夹选择
        self.folder_path = ""
        folder_layout = QHBoxLayout()

        self.folder_btn = QPushButton("选择文件夹")
        self.folder_btn.setIcon(self.get_icon("folder", "📂"))
        self.folder_btn.setIconSize(QSize(18, 18))
        self.folder_btn.clicked.connect(self.choose_folder)

        self.folder_label = QLabel("未选择文件夹")
        self.folder_label.setStyleSheet("color: #656d76; font-style: italic; margin-left: 10px;")
        self.folder_label.setMinimumWidth(300)
        folder_layout.addWidget(self.folder_btn)
        folder_layout.addWidget(self.folder_label, 1)
        form_layout.addRow("报表所在路径：", folder_layout)

        # 设备前缀
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("例如：5（设备名称以5开头）")
        form_layout.addRow("设备名称前缀：", self.prefix_input)

        # 排除客户
        self.exclude_input = QLineEdit()
        self.exclude_input.setPlaceholderText("支持一键填充和手动输入，例如：安吉,三亚民生（用英文逗号分隔）")
        form_layout.addRow("排除客户名称：", self.exclude_input)

        input_layout.addLayout(form_layout)

        # 分隔线
        line = QFrame()
        input_layout.addWidget(line)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 开始分析按钮
        self.start_btn = QPushButton("开始分析")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setIcon(self.get_icon("start", "▶️"))
        self.start_btn.setIconSize(QSize(18, 18))
        self.start_btn.clicked.connect(self.start_analysis)

        # 保存日志按钮
        self.save_btn = QPushButton("保存日志")
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.setIcon(self.get_icon("save", "💾"))
        self.save_btn.setIconSize(QSize(18, 18))
        self.save_btn.clicked.connect(self.save_log_to_txt)
        # 清除按钮
        self.clear_btn = QPushButton()
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.setText("清除所有")
        self.clear_btn.setIcon(self.get_icon("clear", "🗑️"))
        self.clear_btn.setIconSize(QSize(18, 18))
        self.clear_btn.clicked.connect(self.clear_all)

        # 填充示例按钮
        self.fill_example_btn = QPushButton("客户一键填充")
        self.fill_example_btn.setObjectName("fillExampleBtn")  # 绿色样式
        self.fill_example_btn.setIcon(self.get_icon("edit", "📋"))
        self.fill_example_btn.setIconSize(QSize(18, 18))
        self.fill_example_btn.clicked.connect(self.fill_exclude_example)  # 绑定事件

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.fill_example_btn)  # 新增按钮
        input_layout.addLayout(button_layout)

        main_layout.addWidget(input_card, 1)

        # -------------------- 显示区域 --------------------
        display_card = QWidget()
        display_card.setObjectName("card")
        display_layout = QVBoxLayout(display_card)

        # 显示区域标题
        display_title = QLabel("分析结果与日志")
        display_title.setObjectName("section-title")
        bold_font = QFont()
        bold_font.setFamily("Microsoft YaHei")
        bold_font.setPointSize(10)
        bold_font.setWeight(QFont.Weight.Bold)  # 代码设置加粗
        display_title.setFont(bold_font)
        display_layout.addWidget(display_title)

        # 进度条组合（左侧文字+中间进度条+右侧百分比）
        progress_container = QHBoxLayout()
        progress_container.setSpacing(10)
        progress_container.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # 左侧固定文字
        self.progress_text = QLabel("进度条：")
        self.progress_text.setObjectName("progress-label")
        progress_container.addWidget(self.progress_text)

        # 中间进度条
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        progress_container.addWidget(self.progress, 1)  # 占大部分空间

        # 右侧百分比显示
        self.progress_value = QLabel("0%")
        self.progress_value.setObjectName("progress-value")
        progress_container.addWidget(self.progress_value)

        display_layout.addLayout(progress_container)

        # 日志显示
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setPlaceholderText("分析结果将显示在这里...")
        display_layout.addWidget(self.log_display)

        # 版权信息-方案1
        # self.status_label = QLabel()
        # self.status_label.setText(f"© 2025 协议解析工具_v1.0.0 - 版权所有")
        # self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.statusBar().addPermanentWidget(self.status_label)

        main_layout.addWidget(display_card, 3)

    def get_icon(self, theme_name, fallback_text):
        """获取系统图标或生成文本图标"""
        icon = QIcon.fromTheme(theme_name)
        if icon.isNull():
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, fallback_text)
            painter.end()
            icon = QIcon(pixmap)
        return icon

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

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹", "")
        if folder:
            self.folder_path = folder
            self.folder_label.setText(folder)
            self.log_display.append(f"ℹ️ 已选择文件夹：{folder}")

    def start_analysis(self):
        # 检查输入
        if not self.folder_path:
            self.log_display.append("ℹ️ 请先选择文件夹！")
            return

        prefix = self.prefix_input.text().strip()
        # if not prefix:
        #     self.log_display.append("❌ 请输入设备前缀！")
        #     return

        exclude = [x.strip() for x in self.exclude_input.text().split(',') if x.strip()]

        # 禁用按钮
        self.start_btn.setEnabled(False)
        self.folder_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.fill_example_btn.setEnabled(False)  # 分析时禁用填充按钮
        self.prefix_input.setEnabled(False)
        self.exclude_input.setEnabled(False)

        # 初始化进度
        # self.log_display.clear()

        self.progress.setValue(0)
        self.progress_value.setText("0%")

        # 仅清空日志，但保留“选择文件夹”记录
        if self.folder_path:
            selected_log = f"📁 已选择文件夹：{self.folder_path}"
            self.log_display.clear()  # 清空所有
            self.log_display.append(selected_log)  # 重新添加选择文件夹日志
        # 添加分析分隔符
        self.log_display.append("\n" + "=" * 50)
        self.log_display.append("ℹ️ 开始执行Excel分析任务...")
        self.log_display.append("=" * 50 + "\n")

        if self.thread and self.thread.isRunning():
            return  # 避免重复启动线程
        # 启动子线程
        self.thread = ExcelThread(
            folder_path=self.folder_path,
            prefix=prefix,
            exclude_list=exclude
        )

        # 连接信号：每个文件处理完后更新进度
        self.thread.log.connect(self.log_display.append)
        self.thread.progress.connect(self.update_progress)  # 接收单个文件完成后的进度
        self.thread.finished.connect(self.on_finished)

        self.thread.start()  # 启动线程（执行run方法）

    def update_progress(self, value):
        """单个文件处理完成后更新进度条"""
        self.progress.setValue(value)
        self.progress_value.setText(f"{value}%")

    def on_finished(self):
        """所有文件处理完成后恢复状态"""
        # 确保进度条显示100%
        self.progress.setValue(100)
        self.progress_value.setText("100%")

        # 恢复按钮状态
        self.start_btn.setEnabled(True)
        self.folder_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.fill_example_btn.setEnabled(True)  # 恢复填充按钮可用
        self.prefix_input.setEnabled(True)
        self.exclude_input.setEnabled(True)

        self.log_display.append("✅ 分析任务已全部完成！")

    def save_log_to_txt(self):
        log_content = self.log_display.toPlainText()
        if not log_content.strip():
            self.log_display.append("ℹ️ 日志为空，无需保存！")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存日志", "", "文本文件 (*.txt);;所有文件 (*)"
        )

        if not file_path:
            return

        if not file_path.endswith(".txt"):
            file_path += ".txt"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(log_content)
            self.log_display.append(f"✅ 日志已保存至：{file_path}")
        except Exception as e:
            logger.error(str(e))
            self.log_display.append(f"❌ 保存失败：{str(e)}")

    def clear_all(self):
        """清除所有内容并重置进度"""
        self.folder_path = ""
        self.folder_label.setText("未选择文件夹")
        self.prefix_input.clear()
        self.exclude_input.clear()
        self.log_display.clear()
        self.progress.setValue(0)
        self.progress_value.setText("0%")
        self.log_display.append("✅️ 已清除所有输入内容和日志")

    def fill_exclude_example(self):
        """一键赋值：过滤客户"""
        example_str = ("安吉租赁有限公司,三亚民生旅业有限责任公司（民生）,上海东正汽车金融股份有限公司（东正）,浙江大搜车融资租赁有限公司,塔比星信息技术（深圳）有限公司,"
                       "广西通盛融资租赁有限公司,北京中交兴路车联网科技有限公司,WJJZ皖江金融租赁股份有限公司,华润集团")

        self.exclude_input.setText(example_str)
        self.log_display.append(f"ℹ️ 已填充示例排除值（🌹请🌹仔🌹细🌹核🌹对🌹）：\n{example_str}")  # 日志提示


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
