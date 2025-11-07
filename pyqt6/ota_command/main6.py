import sys
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QRadioButton, QPushButton, QLineEdit, QLabel,
                             QTextEdit, QFileDialog, QButtonGroup, QStatusBar, QComboBox,
                             QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator, QFont


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app_version = "v1.0.0"  # 版本号
        self.copyright_info = "© 2023 公司名称 版权所有"  # 版权信息

        # 设备名称字典
        self.device_names = {
            "ZL_A08": 'ZL-A08',
            "ZL_A08_BD": r'ZL-A08_ML307R',
            "ZL_A08_EL_GX": r'ZL-A08_307H_DU',
            "TC10": 'TC10',
            "TC06_EL": 'TC06-EL-EG800K',
            "A12": r'ZL-A12_307H_DC',
            "TC02_4": 'TC02-4',
            "A01_BD_GJ_V10": r'ZT-A01-BD-GJ-EC800K',
            "A01_EL_GJ_V46": r'ZT-A01-EL-GJ-EC800K',
            "A01_BD_V08": r'ZT-A01-BD-CC1177W',
            "A01_BD": 'ZT-A01',
            "A01_EL": 'ZT-A01'
        }

        self.initUI()

    def initUI(self):
        # 设置窗口标题，包含版本号
        self.setWindowTitle(f'升级文件生成工具 {self.app_version}')
        self.setGeometry(100, 100, 900, 700)

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
        title_label = QLabel("升级文件生成工具")
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
        device_label = QLabel('设备名称:')
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
        self.upgrade_type_group.addButton(self.module_radio, 0)  # 模块值为0
        self.upgrade_type_group.addButton(self.mcu_radio, 1)  # 单片机值为1
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
        self.ota_edit.setPlaceholderText("请输入数字版本号")
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

        self.generate_btn = QPushButton('生成')
        self.generate_btn.setObjectName("actionButton")
        self.copy_btn = QPushButton('复制')
        self.copy_btn.setObjectName("actionButton")
        self.clear_btn = QPushButton('清除')
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

        # 设置状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 状态栏左侧显示临时消息
        self.status_bar.showMessage('就绪')

        # 状态栏右侧显示版权信息
        copyright_label = QLabel(self.copyright_info)
        copyright_label.setObjectName("copyrightLabel")  # 为版权信息标签添加特定ID
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

        /* 单选框样式 - 恢复蓝色主题 */
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

        /* -------------------状态栏样式------------------------- */
        QStatusBar {
            background-color: #34495e;
            color: #ecf0f1;  /* 设置状态栏默认文字颜色为浅灰色 */
            font-weight: 500;
        }

        /* 状态栏消息文字样式 */
        QStatusBar::item {
            border: none;
            background: transparent;
        }

        /* 状态栏临时消息样式 - 可以自定义颜色 */
        QStatusBar QLabel {
            color: #ecf0f1;  /* 默认颜色 */
            background-color: transparent;
            padding: 2px 5px;
        }

        /* 状态栏版权信息样式 */
        QLabel#copyrightLabel {
            color: #bdc3c7;  /* 版权信息使用更浅的颜色 */
            padding: 2px 5px;
        }
        """

    def show_status_message(self, message, color=None):
        """显示状态栏消息，可自定义颜色"""
        if color:
            # 创建带有颜色的HTML格式消息
            html_message = f'<span style="color: {color};">{message}</span>'
            self.status_bar.showMessage("")  # 先清空消息
            # 由于showMessage不支持HTML，我们需要使用其他方法
            # 这里我们使用一个技巧：通过设置样式表来改变颜色
            # 但更简单的方法是直接使用QLabel来显示消息
            self.status_bar.showMessage(message)
            # 应用临时颜色样式
            self.status_bar.setStyleSheet(f"QStatusBar {{ color: {color}; }}")
        else:
            # 恢复默认颜色
            self.status_bar.setStyleSheet("")
            self.status_bar.showMessage(message)

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
            self.show_status_message('已选择单文件模式', '#3498db')  # 蓝色消息
        else:
            self.upgrade_file2_btn.setEnabled(True)
            self.show_status_message('已选择双文件模式', '#3498db')  # 蓝色消息

    def select_file1(self):
        """选择升级文件1"""
        file_path, _ = QFileDialog.getOpenFileName(self, '选择升级文件1')
        if file_path:
            self.file1_path = Path(file_path)
            file_name = self.file1_path.name  # 使用Path.name获取文件名
            file_size = self.file1_path.stat().st_size  # 使用Path.stat().st_size获取文件大小
            # 格式化文件大小显示
            size_str = self.format_file_size(file_size)
            self.file1_info_label.setText(f'{file_name} ({size_str})')
            self.show_status_message(f'已选择文件1: {file_name}', '#2ecc71')  # 绿色消息

    def select_file2(self):
        """选择升级文件2"""
        file_path, _ = QFileDialog.getOpenFileName(self, '选择升级文件2')
        if file_path:
            self.file2_path = Path(file_path)
            file_name = self.file2_path.name  # 使用Path.name获取文件名
            file_size = self.file2_path.stat().st_size  # 使用Path.stat().st_size获取文件大小
            # 格式化文件大小显示
            size_str = self.format_file_size(file_size)
            self.file2_info_label.setText(f'{file_name} ({size_str})')
            self.show_status_message(f'已选择文件2: {file_name}', '#2ecc71')  # 绿色消息

    def format_file_size(self, size_bytes):
        """格式化文件大小显示"""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"

    def get_file_type_value(self):
        """获取文件类型的值"""
        return self.file_type_group.checkedId()

    def get_upgrade_type_value(self):
        """获取升级类型的值"""
        return self.upgrade_type_group.checkedId()

    def generate_output(self):
        """生成按钮点击事件"""
        output_text = "生成结果:\n"

        # 获取文件类型值
        file_type_value = self.get_file_type_value()
        file_type_text = "单文件" if file_type_value == 0 else "双文件"
        output_text += f"文件类型: {file_type_text} (值: {file_type_value})\n"

        # 文件信息
        if self.file1_path:
            file_size = self.file1_path.stat().st_size  # 使用Path.stat().st_size获取文件大小
            size_str = self.format_file_size(file_size)
            output_text += f"升级文件1: {self.file1_path.name} ({size_str})\n"  # 使用Path.name获取文件名
        else:
            output_text += "升级文件1: 未选择\n"

        if file_type_value == 1:  # 双文件
            if self.file2_path:
                file_size = self.file2_path.stat().st_size  # 使用Path.stat().st_size获取文件大小
                size_str = self.format_file_size(file_size)
                output_text += f"升级文件2: {self.file2_path.name} ({size_str})\n"  # 使用Path.name获取文件名
            else:
                output_text += "升级文件2: 未选择\n"

        # 设备名称 - 使用字典值
        device_key = self.device_combo.currentText()
        device_value = self.device_combo.currentData()
        output_text += f"设备名称: {device_value} (键: {device_key})\n"

        # 获取升级类型值
        upgrade_type_value = self.get_upgrade_type_value()
        upgrade_type_text = "模块" if upgrade_type_value == 0 else "单片机"
        output_text += f"升级类型: {upgrade_type_text} (值: {upgrade_type_value})\n"

        # OTA版本
        output_text += f"OTA版本: {self.ota_edit.text()}\n"

        self.display_text.setText(output_text)
        self.show_status_message('已生成输出结果', '#2ecc71')  # 绿色消息

    def copy_to_clipboard(self):
        """复制显示区域内容到剪贴板"""
        clipboard = QApplication.clipboard()
        text_to_copy = self.display_text.toPlainText()

        if text_to_copy.strip():  # 确保有内容可复制
            clipboard.setText(text_to_copy)
            self.show_status_message('内容已复制到剪贴板', '#2ecc71')  # 绿色消息
        else:
            self.show_status_message('没有内容可复制', '#e74c3c')  # 红色消息

    def clear_all(self):
        """清除所有输入和显示"""
        # 重置文件类型
        self.single_file_radio.setChecked(True)

        # 清除文件信息
        self.file1_info_label.setText('未选择文件')
        self.file2_info_label.setText('未选择文件')
        self.file1_path = None
        self.file2_path = None

        # 清除文本框和下拉框选择
        self.device_combo.setCurrentIndex(0)  # 重置为第一个选项
        self.ota_edit.clear()

        # 重置升级类型
        self.module_radio.setChecked(True)

        # 清除显示区域
        self.display_text.clear()

        self.show_status_message('已清除所有输入', '#f39c12')  # 橙色消息


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
    # status_bar带自定义的文字颜色方法
