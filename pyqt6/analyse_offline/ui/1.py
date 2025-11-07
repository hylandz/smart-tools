import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QTextEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("修改保存按钮颜色示例")
        self.setGeometry(100, 100, 600, 400)

        # 字体设置
        font = QFont()
        font.setFamily("Microsoft YaHei")
        self.setFont(font)

        # 中心部件和布局
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 样式表：保存按钮使用紫色系
        central.setStyleSheet("""
            /* 通用按钮基础样式 */
            QPushButton {
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 18px;
                font-size: 10pt;
                min-height: 36px;
                cursor: pointer;
                transition: all 0.2s ease;
            }

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

            /* 统一禁用状态样式 */
            QPushButton:disabled {
                background-color: #cccccc;
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
        """)

        # 日志显示区
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.append("日志内容示例...")
        main_layout.addWidget(self.log_display)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        # 开始分析按钮
        self.start_btn = QPushButton("开始分析")
        self.start_btn.setObjectName("startBtn")
        button_layout.addWidget(self.start_btn)

        # 保存日志按钮（紫色）
        self.save_btn = QPushButton("保存日志")
        self.save_btn.setObjectName("saveBtn")  # 绑定紫色样式
        self.save_btn.setIcon(QIcon.fromTheme("document-save", QIcon()))
        button_layout.addWidget(self.save_btn)

        # 填充示例按钮
        self.fill_btn = QPushButton("填充示例")
        self.fill_btn.setObjectName("fillExampleBtn")
        button_layout.addWidget(self.fill_btn)

        # 清除按钮
        self.clear_btn = QPushButton("清除所有")
        self.clear_btn.setObjectName("clearBtn")
        button_layout.addWidget(self.clear_btn)

        main_layout.addLayout(button_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
