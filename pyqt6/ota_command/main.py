import sys

import traceback
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QRadioButton, QPushButton, QLineEdit, QLabel,
                             QTextEdit, QFileDialog, QButtonGroup, QStatusBar, QComboBox,
                             QSizePolicy, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator, QFont, QIcon

from ota_command.src.util.logutil import ota_command_logging


def custom_excepthook(cls, value, tb):
    """全局异常捕获：捕获未处理的系统级异常，如崩溃时的堆栈跟踪"""
    # 创建日志目录（使用Path对象）
    log_dir = Path.home() / "OTACommandLogs"  # c:\\Users\{用户名}
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

        # 开发环境弹窗提示（打包后不会执行弹框）
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


# 替换系统默认的异常处理器
sys.excepthook = custom_excepthook
logger = ota_command_logging()


class MainWindow(QMainWindow):
    """
    UI更美化（参数边框化）、status_bar文字显示并带emoji
    """
    def __init__(self):
        super().__init__()
        self.app_version = "v1.0.2"  # 版本号
        self.copyright_info = "© 2025 公司名称 版权所有"  # 版权信息

        # 设备名称字典
        self.device_names = {
            "ZL_A08": 'ZL-A08',
            "ZL_A08_BD": r'ZL-A08_ML307R',
            "ZL_A08_EL_GX": r'ZL-A08_307H_DU',
            "TC10": 'TC10',
            "TC06_EL": 'TC06-EL-EG800K',
            "A12": r'ZL-A12_307H_DC',
            "TC02_4": 'TC02-4',
            "A01_BD_GJ_V10+": r'ZT-A01-BD-GJ-EC800K',
            "A01_EL_GJ_V46+": r'ZT-A01-EL-GJ-EC800K',
            "A01_BD_V08-": r'ZT-A01-BD-CC1177W',
            "A01_BD": 'ZT-A01',
            "A01_EL": 'ZT-A01'
        }
        self.URL = r"http://lbsupgrade.lunz.cn:8080/LBSManagement/"
        self.COMMAND_HEAD = "AT^zr_cfg:ota@"
        self.command = ""
        self.initUI()

    def initUI(self):
        # 设置窗口标题，包含版本号
        self.setWindowTitle(f'OTA升级串口指令生成工具 {self.app_version}')
        self.setGeometry(100, 100, 900, 700)
        self.setWindowIcon(QIcon(self.load_resource("assets/icons/ota.ico")))

        # 设置应用样式
        self.setStyleSheet(self.getAppStyleSheet())

        # 创建中央部件
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 添加标题
        title_label = QLabel("OTA升级串口指令生成工具")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # 参数区域
        param_group = QGroupBox('参数设置')
        param_group.setObjectName("paramGroup")
        param_layout = QVBoxLayout(param_group)
        param_layout.setSpacing(10)
        param_layout.setContentsMargins(15, 15, 15, 15)

        # 文件类型
        file_type_layout = QHBoxLayout()
        file_type_label = QLabel('文件类型:')
        file_type_label.setObjectName("sectionLabel")
        self.single_file_radio = QRadioButton('单文件')
        self.double_file_radio = QRadioButton('双文件')

        # 创建按钮组并设置值
        self.file_type_group = QButtonGroup()
        self.file_type_group.addButton(self.single_file_radio, 0)  # 单文件值为0
        self.file_type_group.addButton(self.double_file_radio, 1)  # 双文件值为1
        self.single_file_radio.setChecked(True)

        file_type_layout.addWidget(file_type_label)
        file_type_layout.addWidget(self.single_file_radio)
        file_type_layout.addWidget(self.double_file_radio)
        file_type_layout.addStretch()

        # 升级文件1 - 单独一行
        upgrade_file1_layout = QHBoxLayout()
        upgrade_file1_label = QLabel('升级文件1:')
        upgrade_file1_label.setObjectName("sectionLabel")
        self.upgrade_file1_btn = QPushButton('选择文件')
        self.upgrade_file1_btn.setObjectName("fileButton")
        self.file1_info_label = QLabel('未选择文件')
        self.file1_info_label.setObjectName("fileInfoLabel")

        upgrade_file1_layout.addWidget(upgrade_file1_label)
        upgrade_file1_layout.addWidget(self.upgrade_file1_btn)
        upgrade_file1_layout.addWidget(self.file1_info_label)
        upgrade_file1_layout.addStretch()

        # 升级文件2 - 单独一行
        upgrade_file2_layout = QHBoxLayout()
        upgrade_file2_label = QLabel('升级文件2:')
        upgrade_file2_label.setObjectName("sectionLabel")
        self.upgrade_file2_btn = QPushButton('选择文件')
        self.upgrade_file2_btn.setObjectName("fileButton")
        self.upgrade_file2_btn.setEnabled(False)
        self.file2_info_label = QLabel('未选择文件')
        self.file2_info_label.setObjectName("fileInfoLabel")

        upgrade_file2_layout.addWidget(upgrade_file2_label)
        upgrade_file2_layout.addWidget(self.upgrade_file2_btn)
        upgrade_file2_layout.addWidget(self.file2_info_label)
        upgrade_file2_layout.addStretch()

        # 设备名称 - 改为下拉框
        device_layout = QHBoxLayout()
        device_label = QLabel('设备型号:')
        device_label.setObjectName("sectionLabel")
        self.device_combo = QComboBox()
        self.device_combo.setObjectName("comboBox")

        # 使用字典填充下拉框
        for key, value in self.device_names.items():
            # 显示键（变量名），存储值
            self.device_combo.addItem(key, value)

        # 设置下拉框不拉伸到最右边
        self.device_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        device_layout.addWidget(device_label)
        device_layout.addWidget(self.device_combo)
        # 添加一个弹性空间，使下拉框不会靠右
        device_layout.addStretch()

        # 升级类型
        upgrade_type_layout = QHBoxLayout()
        upgrade_type_label = QLabel('升级类型:')
        upgrade_type_label.setObjectName("sectionLabel")
        self.module_radio = QRadioButton('模块')
        self.mcu_radio = QRadioButton('单片机')

        # 创建按钮组并设置值
        self.upgrade_type_group = QButtonGroup()
        self.upgrade_type_group.addButton(self.module_radio, 1)  # 模块值为1
        self.upgrade_type_group.addButton(self.mcu_radio, 0)  # 单片机值为0
        self.module_radio.setChecked(True)

        upgrade_type_layout.addWidget(upgrade_type_label)
        upgrade_type_layout.addWidget(self.module_radio)
        upgrade_type_layout.addWidget(self.mcu_radio)
        upgrade_type_layout.addStretch()

        # OTA版本
        ota_layout = QHBoxLayout()
        ota_label = QLabel('OTA版本:')
        ota_label.setObjectName("sectionLabel")
        self.ota_edit = QLineEdit()
        self.ota_edit.setValidator(QIntValidator())
        self.ota_edit.setPlaceholderText("例如：312（10进制版本值0138转16进制）")
        self.ota_edit.setObjectName("otaEdit")  # 为OTA文本框添加特定ID

        ota_layout.addWidget(ota_label)
        ota_layout.addWidget(self.ota_edit)

        # 将各个布局添加到参数区域
        param_layout.addLayout(file_type_layout)
        param_layout.addLayout(upgrade_file1_layout)
        param_layout.addLayout(upgrade_file2_layout)
        param_layout.addLayout(device_layout)
        param_layout.addLayout(upgrade_type_layout)
        param_layout.addLayout(ota_layout)

        # 功能区域
        function_group = QGroupBox('功能操作')
        function_group.setObjectName("functionGroup")
        function_layout = QHBoxLayout(function_group)
        function_layout.setContentsMargins(15, 15, 15, 15)

        self.generate_btn = QPushButton('😁 生成')
        self.generate_btn.setObjectName("actionButton")
        self.copy_btn = QPushButton('🦄 复制串口指令')
        self.copy_btn.setObjectName("actionButton")
        self.clear_btn = QPushButton('🤡 清除所有')
        self.clear_btn.setObjectName("actionButton")

        function_layout.addWidget(self.generate_btn)
        function_layout.addWidget(self.copy_btn)
        function_layout.addWidget(self.clear_btn)
        function_layout.addStretch()

        # 显示区域
        display_group = QGroupBox('结果显示')
        display_group.setObjectName("displayGroup")
        display_layout = QVBoxLayout(display_group)
        display_layout.setContentsMargins(15, 15, 15, 15)

        self.display_text = QTextEdit()
        self.display_text.setReadOnly(True)
        self.display_text.setObjectName("displayText")

        display_layout.addWidget(self.display_text)

        # 将各个区域添加到主布局
        main_layout.addWidget(param_group)
        main_layout.addWidget(function_group)
        main_layout.addWidget(display_group)

        # 设置状态栏（底部）
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 状态栏左侧显示临时消息
        self.status_bar.showMessage('✅ 就绪')

        # 状态栏右侧显示版权信息
        copyright_label = QLabel(self.copyright_info)
        self.status_bar.addPermanentWidget(copyright_label)

        # 连接信号和槽
        self.connect_signals()

        # 存储文件路径
        self.file1_path = None
        self.file2_path = None

    def getAppStyleSheet(self):
        """返回应用的样式表"""
        return """
        /* 主窗口样式 */
        QMainWindow {
            background-color: #f0f0f0;
        }

        #centralWidget {
            background-color: #f5f5f5;
        }

        /* 标题样式 */
        #titleLabel {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
            margin-bottom: 10px;
        }

        /* 分组框样式 */
        QGroupBox {
            font-weight: bold;
            font-size: 14px;
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: white;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            color: #2c3e50;
        }

        #paramGroup {
            border-color: #3498db;
        }

        #functionGroup {
            border-color: #2ecc71;
        }

        #displayGroup {
            border-color: #e74c3c;
        }

        /* 标签样式 */
        QLabel#sectionLabel {
            font-weight: bold;
            color: #2c3e50;
            min-width: 80px;
            font-size: 10.5px;
            background-color: #ecf0f1;
            padding: 5px 8px;
            border-radius: 4px;
            border: 1px solid #bdc3c7;
        }

        QLabel#fileInfoLabel {
            color: #7f8c8d;
            font-style: italic;
            padding: 5px;
            background-color: #f8f9fa;
            border-radius: 3px;
            border: 1px solid #e9ecef;
        }

        /* 按钮样式 */
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            font-weight: bold;
            min-width: 80px;
        }

        QPushButton:hover {
            background-color: #2980b9;
        }

        QPushButton:pressed {
            background-color: #21618c;
        }

        QPushButton:disabled {
            background-color: #bdc3c7;
            color: #7f8c8d;
        }

        /* 文件选择按钮使用蓝色主题 */
        #fileButton {
            background-color: #3498db;
        }

        #fileButton:hover {
            background-color: #2980b9;
        }

        #fileButton:pressed {
            background-color: #21618c;
        }

        /* 功能按钮使用绿色主题 */
        #actionButton {
            background-color: #2ecc71;
        }

        #actionButton:hover {
            background-color: #27ae60;
        }

        #actionButton:pressed {
            background-color: #219653;
        }

        /* 单选框样式  */
        QRadioButton {
            spacing: 5px;
            color: #2c3e50;
        }

        QRadioButton::indicator {
            width: 13px;
            height: 13px;
        }

        QRadioButton::indicator:unchecked {
            border: 2px solid #bdc3c7;
            border-radius: 7px;
            background-color: white;
        }

        QRadioButton::indicator:checked {
            border: 2px solid #3498db;
            border-radius: 7px;
            background-color: #3498db;
        }

        /* 下拉框样式 */
        QComboBox {
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 5px;
            background-color: white;
            min-width: 200px;
        }

        QComboBox:hover {
            border: 1px solid #3498db;
        }

        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left-width: 1px;
            border-left-color: #bdc3c7;
            border-left-style: solid;
            border-top-right-radius: 3px;
            border-bottom-right-radius: 3px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #7f8c8d;
            width: 0px;
            height: 0px;
        }

        QComboBox QAbstractItemView {
            border: 1px solid #bdc3c7;
            selection-background-color: #3498db;
            background-color: white;
        }

        /* 文本框样式 - 优化OTA版本文本框 */
        QLineEdit {
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 5px;
            background-color: white;
            color: #2c3e50;  /* 设置输入文本颜色为深色 */
            font-weight: normal;
        }

        QLineEdit:focus {
            border: 1px solid #3498db;
            background-color: #f8f9fa;
        }

        QLineEdit[placeholderText] {
            color: #95a5a6;
        }

        /* 为OTA版本文本框添加特定样式 */
        #otaEdit {
            color: #2c3e50;
            font-weight: 500;
            background-color: #ffffff;
            border: 1px solid #bdc3c7;
        }

        #otaEdit:focus {
            border: 1px solid #3498db;
            background-color: #f8f9fa;
        }

        /* 文本编辑框样式 */
        QTextEdit {
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 8px;
            background-color: white;
            font-family: "Courier New", monospace;
            color: #2c3e50;  /* 确保显示区域文本颜色清晰 */
        }

        QTextEdit:focus {
            border: 1px solid #3498db;
        }

        #displayText {
            min-height: 150px;
        }

        /* 状态栏样式 */
        QStatusBar {
            background-color: #34495e;
            color: white;
        }

        QStatusBar QLabel {
            color: white;
        }
        """

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

    def connect_signals(self):
        """连接信号和槽函数"""
        self.single_file_radio.toggled.connect(self.on_file_type_changed)
        self.upgrade_file1_btn.clicked.connect(self.select_file1)
        self.upgrade_file2_btn.clicked.connect(self.select_file2)
        self.generate_btn.clicked.connect(self.generate_output)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.clear_btn.clicked.connect(self.clear_all)

    def on_file_type_changed(self):
        """文件类型单选框状态改变时的处理"""
        if self.single_file_radio.isChecked():
            self.upgrade_file2_btn.setEnabled(False)
            self.file2_info_label.setText('未选择文件')
            self.file2_path = None
            self.status_bar.showMessage('✅ 已选择单文件模式')
        else:
            self.upgrade_file2_btn.setEnabled(True)
            self.status_bar.showMessage('✅ 已选择双文件模式')

    def select_file1(self):
        """选择升级文件1"""
        file_path, _ = QFileDialog.getOpenFileName(self, '选择升级文件1')
        if file_path:
            self.file1_path = Path(file_path)
            file_name = self.file1_path.name  # 使用Path.name获取文件名
            # file_size = self.file1_path.stat().st_size  # 使用Path.stat().st_size获取文件大小
            # 格式化文件大小显示
            # size_str = self.format_file_size(file_size)
            self.file1_info_label.setText(f'{file_name}')
            self.status_bar.showMessage(f'✅ 已选择文件1: {file_name}')

    def select_file2(self):
        """选择升级文件2"""
        file_path, _ = QFileDialog.getOpenFileName(self, '选择升级文件2')
        if file_path:
            self.file2_path = Path(file_path)
            file_name = self.file2_path.name  # 使用Path.name获取文件名
            # file_size = self.file2_path.stat().st_size  # 使用Path.stat().st_size获取文件大小
            # 格式化文件大小显示
            # size_str = self.format_file_size(file_size)
            # self.file2_info_label.setText(f'{file_name} ({size_str})')
            self.file2_info_label.setText(f'{file_name}')
            self.status_bar.showMessage(f'✅ 已选择文件2: {file_name}')

    def format_file_size(self, size_bytes):
        """格式化文件大小显示"""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):2f} MB"

    def get_file_type_value(self) -> int:
        """获取文件类型的值"""
        return self.file_type_group.checkedId()

    def get_upgrade_type_value(self) -> int:
        """获取升级类型的值"""
        return self.upgrade_type_group.checkedId()

    def ota_command_generate(self, ota_id, dev_name_key, dev_name_val, ota_ver, f_size1, f_name1,
                             f_size2=0, f_name2=None, ota_time=0):
        """
        串口命令生成
        :param ota_id: 级类型，模块1，单片机0
        :param dev_name_key: 设备类型
        :param dev_name_val: 设备名称
        :param ota_ver: OTA版本值
        :param f_size1: 升级文件1大小，单位：byte
        :param f_name1: 升级文件1的文件名
        :param f_size2: 升级文件1大小，单位：byte
        :param f_name2: 升级文件2的文件名
        :param ota_time: ota升级时间
        """
        string_type = {"ZL_A08", "ZL_A08_BD", "ZL_A08_EL_GX", "A12"}
        frame_type = {"A01_BD_GJ_V10+", "A01_EL_GJ_V46+", "A01_BD_V08-", "A01_BD", "TC10", "TC02_4", "A01_EL"}

        if dev_name_key in string_type:  # 命令类型-字符串
            command = f"{self.COMMAND_HEAD}id:{ota_id};devname:{dev_name_val};softwarever:{ota_ver};updatetime:{ota_time};"
            command += f"size1:{f_size1};url1:{self.URL + f_name1};size2:{f_size2};url2:{(self.URL + f_name2) if f_name2 else None};"
            return command
        elif dev_name_key in frame_type:  # 命令类型-报文
            dev_name_val = str(dev_name_val).encode("utf-8")
            command = f"{self.COMMAND_HEAD}{ota_id:02X}{len(dev_name_val):02x}{dev_name_val.hex()}80{ota_ver:04X}{ota_time:08X}"

            # 单文件
            url1 = (self.URL + f_name1).encode("utf-8")
            command += f"{f_size1:08X}{len(url1):02X}{url1.hex()}"

            if f_size2 != 0:  # 双文件
                url2 = (self.URL + f_name2).encode("utf-8")
                command += f"{f_size2:08X}{len(url2):02X}{url2.hex()}"

            return command
        else:
            raise ValueError(f"暂不支持该设备型号的指令生成:{dev_name_key}")

    def generate_output(self):
        """生成按钮点击事件"""
        output_text = "生成结果:\n"

        # 获取文件类型值
        file_type_value = self.get_file_type_value()
        file_type_text = "[单文件]" if file_type_value == 0 else "双文件"
        output_text += f"[文件类型]: {file_type_text} (值: {file_type_value})\n"

        # 文件信息
        if self.file1_path:
            file1_size = self.file1_path.stat().st_size  # 使用Path.stat().st_size获取文件大小
            # size_str = self.format_file_size(file_size)
            file1_name = self.file1_path.name
            output_text += f"[升级文件1]: {file1_name} ({file1_size} bytes)\n"  # 使用Path.name获取文件名
        else:
            output_text += "[升级文件1]: 未选择\n"
            self.status_bar.showMessage('⚠️ 升级文件1: 未选择')
            return

        file2_size = 0
        file2_name = ""
        if file_type_value == 1:  # 双文件
            if self.file2_path:
                file2_size = self.file2_path.stat().st_size  # 使用Path.stat().st_size获取文件大小
                # size_str = self.format_file_size(file_size)
                file2_name = self.file2_path.name
                output_text += f"[升级文件2]: {file2_name} ({file2_size} bytes)\n"  # 使用Path.name获取文件名
            else:
                output_text += "[升级文件2]: 未选择\n"
                self.status_bar.showMessage('⚠️ 升级文件2: 未选择')
                return

        # 设备名称 - 使用字典值
        device_key = self.device_combo.currentText()
        device_value = self.device_combo.currentData()
        output_text += f"[设备名称]: {device_value} (设备型号: {device_key})\n"

        # 获取升级类型值
        upgrade_type_value = self.get_upgrade_type_value()
        upgrade_type_text = "[单片机]" if upgrade_type_value == 0 else "模块"
        output_text += f"[升级类型]: {upgrade_type_text} (值: {upgrade_type_value})\n"

        # OTA版本
        ota_ver = self.ota_edit.text()

        if ota_ver:
            output_text += f"[OTA版本]: {ota_ver}\n"
        else:
            self.status_bar.showMessage('⚠️ OTA版本: 不能为空')
            return

        self.display_text.setText(output_text)
        try:
            self.command = self.ota_command_generate(upgrade_type_value, device_key, device_value, int(ota_ver),
                                                     file1_size, file1_name, file2_size, file2_name, 0)
            self.display_text.append("ℹ️ 串口指令：\n")
            self.display_text.append(self.command)
        except Exception as e:
            self.display_text.append("ℹ️ 串口指令：None")
            self.status_bar.showMessage(f"⚠️ 错误: {str(e)}")
            return

        self.status_bar.showMessage('✅ 已生成输出结果')

    def copy_to_clipboard(self):
        """复制显示区域内容到剪贴板"""
        clipboard = QApplication.clipboard()
        # text_to_copy = self.display_text.toPlainText()
        text_to_copy = self.command
        if text_to_copy.strip():  # 确保有内容可复制
            clipboard.setText(text_to_copy)
            self.status_bar.showMessage('✅ 内容已复制到剪贴板')
        else:
            self.status_bar.showMessage('❌ 没有内容可复制')

    def clear_all(self):
        """清除所有输入和显示"""
        # 重置文件类型
        self.single_file_radio.setChecked(True)

        # 清除文件信息
        self.file1_info_label.setText('未选择文件')
        self.file2_info_label.setText('未选择文件')
        self.file1_path = None
        self.file2_path = None
        self.command = ""

        # 清除文本框和下拉框选择
        self.device_combo.setCurrentIndex(0)  # 重置为第一个选项
        self.ota_edit.clear()

        # 重置升级类型
        self.module_radio.setChecked(True)

        # 清除显示区域
        self.display_text.clear()

        self.status_bar.showMessage('✅ 已清除所有输入')


def main():
    app = QApplication(sys.argv)

    # 设置应用程序字体
    font = QFont("微软雅黑", 9)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
