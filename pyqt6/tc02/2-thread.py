import sys
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QPushButton, QLabel,
                             QFrame, QFileDialog)
from PyQt6.QtCore import Qt, QEasingCurve, QPropertyAnimation, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QDragEnterEvent, QDropEvent, QIcon


# --------------------------
# 1. 工具类：拖拽文本框（独立功能模块）
# --------------------------
class DraggableTextEdit(QTextEdit):
    """支持文件拖拽、文本输入的自定义文本框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_settings()
        self.init_animation()

    def init_settings(self):
        """初始化基础设置"""
        self.setAcceptDrops(True)
        self.setPlaceholderText("请输入十六进制协议文本（每行一条数据）\n或直接拖拽 .txt/.hex/.log 文件到此处...")
        self.setMinimumHeight(120)
        self.setObjectName("inputText")

    def init_animation(self):
        """初始化拖拽动画"""
        self.drag_anim = QPropertyAnimation(self, b"geometry")
        self.drag_anim.setDuration(200)
        self.drag_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件：提示可接收"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            orig_geo = self.geometry()
            self.drag_anim.setStartValue(orig_geo)
            self.drag_anim.setEndValue(orig_geo.adjusted(-2, -2, 2, 2))
            self.drag_anim.start()
        super().dragEnterEvent(event)

    def dragLeaveEvent(self, event):
        """拖拽离开事件：恢复原状"""
        orig_geo = self.geometry()
        self.drag_anim.setStartValue(self.geometry())
        self.drag_anim.setEndValue(orig_geo)
        self.drag_anim.start()
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        """放下事件：读取文件内容（修正URL残留问题）"""
        orig_geo = self.geometry()
        self.drag_anim.setStartValue(self.geometry())
        self.drag_anim.setEndValue(orig_geo)
        self.drag_anim.start()

        if event.mimeData().hasUrls():
            # 关键修正：拖入文件时先清空文本框，避免URL残留
            self.clear()
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                self._load_file(file_path)
                break
            event.acceptProposedAction()
        else:
            # 非文件拖放（如纯文本），保留默认处理
            super().dropEvent(event)

    def _load_file(self, file_path: str):
        """加载文件内容到文本框（支持多行数据）"""
        supported_types = ('.txt', '.hex', '.log')
        if not file_path.endswith(supported_types):
            # 错误信息不包含URL，仅提示类型问题
            self.setText(f"不支持的文件类型！仅支持 {', '.join(supported_types)}")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            # 仅显示文件内容，不包含路径
            self.setText(content)
            raw_data_list = [line.strip() for line in content.splitlines() if line.strip()]
            # 占位符提示文件信息（不显示在正文）
            self.setPlaceholderText(f"已加载文件：{file_path}（共{len(raw_data_list)}条数据）")
        except Exception as e:
            # 错误信息不包含URL，仅提示读取失败
            self.setText(f"文件读取失败：{str(e)}")


# --------------------------
# 2. 业务类：协议解析器（独立业务模块）
# --------------------------
class ProtocolParser:
    """协议解析核心逻辑（与UI、线程解耦）"""
    @staticmethod
    def validate_hex(hex_str: str) -> tuple[bool, str, str]:
        """验证十六进制字符串有效性"""
        clean_hex = hex_str.replace(" ", "").replace("\n", "").upper()
        if not clean_hex:
            return False, clean_hex, "数据为空"
        if not all(c in "0123456789ABCDEF" for c in clean_hex):
            return False, clean_hex, "包含非十六进制字符（仅允许0-9、A-F）"
        if len(clean_hex) % 2 != 0:
            return False, clean_hex, "字符串长度为奇数，不符合十六进制格式"
        if len(clean_hex) < 4:
            return False, clean_hex, "数据长度过短，无法构成完整协议帧"
        return True, clean_hex, "验证通过"

    @staticmethod
    def parse(hex_str: str) -> dict:
        """解析十六进制协议为字典（可根据实际协议修改）"""
        protocol_data = {
            "basic": {
                "input": hex_str,
                "hex_len": len(hex_str),
                "byte_len": len(hex_str) // 2,
                "status": "success",  # success/warning/failed
                "msg": ""
            },
            "frame_header": {
                "hex": hex_str[:2],
                "desc": "帧起始标识（0x7E）",
                "valid": hex_str.startswith("7E")
            },
            "address": {
                "hex": hex_str[2:6] if len(hex_str) >= 6 else "",
                "dec": int(hex_str[2:6], 16) if len(hex_str) >= 6 else 0,
                "desc": "目标设备地址"
            },
            "data_len": {
                "hex": hex_str[6:8] if len(hex_str) >= 8 else "",
                "dec": int(hex_str[6:8], 16) if len(hex_str) >= 8 else 0,
                "desc": "数据段字节数"
            },
            "data": {
                "hex": "",
                "ascii": "",
                "desc": "业务数据内容"
            },
            "checksum": {
                "hex": "",
                "dec": 0,
                "calculated": "",
                "valid": False,
                "desc": "CRC校验和（帧头-数据段字节和）"
            },
            "frame_tail": {
                "hex": hex_str[-2:] if len(hex_str) >= 2 else "",
                "desc": "帧结束标识（0x7E）",
                "valid": hex_str.endswith("7E")
            }
        }

        # 解析数据段
        data_len = protocol_data["data_len"]["dec"]
        if len(hex_str) >= 8 + 2 * data_len:
            data_start = 8
            data_end = 8 + 2 * data_len
            protocol_data["data"]["hex"] = hex_str[data_start:data_end]
            try:
                data_bytes = bytes.fromhex(hex_str[data_start:data_end])
                protocol_data["data"]["ascii"] = ''.join([
                    chr(b) if 32 <= b <= 126 else '.' for b in data_bytes
                ])
            except:
                protocol_data["data"]["ascii"] = "解析失败"

        # 解析校验和
        if len(hex_str) >= 8 + 2 * data_len + 4:
            cs_start = 8 + 2 * data_len
            cs_end = cs_start + 4
            protocol_data["checksum"]["hex"] = hex_str[cs_start:cs_end]
            protocol_data["checksum"]["dec"] = int(hex_str[cs_start:cs_end], 16) if hex_str[cs_start:cs_end] else 0
            calc_bytes = bytes.fromhex(hex_str[:cs_start])
            protocol_data["checksum"]["calculated"] = hex(sum(calc_bytes))[2:].upper().zfill(4)
            protocol_data["checksum"]["valid"] = protocol_data["checksum"]["calculated"] == protocol_data["checksum"]["hex"]

        # 状态判断
        if not protocol_data["frame_header"]["valid"] or not protocol_data["frame_tail"]["valid"]:
            protocol_data["basic"]["status"] = "failed"
            protocol_data["basic"]["msg"] = "帧头/帧尾无效（需以0x7E开头和结尾）"
        elif not protocol_data["checksum"]["valid"] and protocol_data["checksum"]["hex"]:
            protocol_data["basic"]["status"] = "warning"
            protocol_data["basic"]["msg"] = f"校验和不匹配（实际：{protocol_data['checksum']['hex']}，计算：{protocol_data['checksum']['calculated']}）"

        return protocol_data

    @staticmethod
    def to_formatted_json(data: dict) -> str:
        """将解析结果转为格式化JSON字符串"""
        return json.dumps(data, indent=4, ensure_ascii=False)


# --------------------------
# 3. 多线程类：解析工作线程（独立线程模块）
# --------------------------
class ParseWorker(QThread):
    """解析工作线程：独立执行批量解析，通过信号传递结果"""
    # 信号定义（参数：当前进度、总进度）
    progress_signal = pyqtSignal(int, int)
    # 信号定义（参数：单条结果的HTML模块）
    result_module_signal = pyqtSignal(str)
    # 信号定义（参数：解析完成状态）
    finish_signal = pyqtSignal(bool)

    def __init__(self, data_list: list):
        super().__init__()
        self.data_list = data_list  # 待解析数据列表
        self.is_running = True  # 线程运行标志（用于终止线程）

    def run(self):
        """线程执行逻辑：逐条解析数据"""
        total_count = len(self.data_list)
        for idx, raw_data in enumerate(self.data_list, 1):
            # 检查是否需要终止线程（如用户点击清除）
            if not self.is_running:
                self.finish_signal.emit(False)
                return

            # 1. 发送进度信号
            self.progress_signal.emit(idx, total_count)

            # 2. 验证+解析单条数据
            is_valid, clean_hex, msg = ProtocolParser.validate_hex(raw_data)
            if not is_valid:
                # 生成失败模块，发送信号
                fail_module = self._generate_fail_module(idx, raw_data, msg)
                self.result_module_signal.emit(fail_module)
                continue

            try:
                parse_result = ProtocolParser.parse(clean_hex)
                json_str = ProtocolParser.to_formatted_json(parse_result)
                # 生成成功/警告模块，发送信号
                success_module = self._generate_success_module(idx, clean_hex, parse_result, json_str)
                self.result_module_signal.emit(success_module)
            except Exception as e:
                # 生成异常模块，发送信号
                fail_module = self._generate_fail_module(idx, raw_data, f"解析异常：{str(e)}")
                self.result_module_signal.emit(fail_module)

            # 短暂休眠，降低CPU占用（可选）
            self.msleep(10)

        # 解析完成，发送成功信号
        self.finish_signal.emit(True)

    def stop(self):
        """终止线程运行"""
        self.is_running = False

    def _generate_success_module(self, idx: int, raw_hex: str, parse_data: dict, json_str: str) -> str:
        """生成单条成功/警告的HTML模块"""
        # 长数据截断
        if len(raw_hex) > 120:
            display_hex = f"{raw_hex[:50]}...{raw_hex[-30:]}"
        else:
            display_hex = raw_hex

        # 状态标识
        status_icon = "✅" if parse_data["basic"]["status"] == "success" else "⚠️"
        status_text = "解析成功" if parse_data["basic"]["status"] == "success" else "解析警告"
        status_color = "#10b981" if parse_data["basic"]["status"] == "success" else "#f59e0b"

        # 基础信息表格
        basic_info = f"""
            <h4 style='color: #1e293b; margin-top: 0; font-size: 14px;'>
                第{idx}条数据 {status_icon} {status_text}
            </h4>
            <table style='width: 100%; border-collapse: separate; border-spacing: 0 8px; margin-bottom: 15px;'>
                <tr>
                    <td style='width: 130px; color: #64748b; font-weight: 500;'>原始数据</td>
                    <td style='color: #1e293b;'>{display_hex}</td>
                </tr>
                <tr>
                    <td style='color: #64748b; font-weight: 500;'>数据长度</td>
                    <td style='color: #1e293b;'>{parse_data['basic']['hex_len']} 字符 / {parse_data['basic']['byte_len']} 字节</td>
                </tr>
                <tr>
                    <td style='color: #64748b; font-weight: 500;'>帧头校验</td>
                    <td style='color: {"#10b981" if parse_data["frame_header"]["valid"] else "#ef4444"};'>
                        {"✅ 通过" if parse_data["frame_header"]["valid"] else "❌ 失败"} 
                        （{parse_data["frame_header"]["hex"]} - {parse_data["frame_header"]["desc"]}）
                    </td>
                </tr>
                <tr>
                    <td style='color: #64748b; font-weight: 500;'>帧尾校验</td>
                    <td style='color: {"#10b981" if parse_data["frame_tail"]["valid"] else "#ef4444"};'>
                        {"✅ 通过" if parse_data["frame_tail"]["valid"] else "❌ 失败"} 
                        （{parse_data["frame_tail"]["hex"]} - {parse_data["frame_tail"]["desc"]}）
                    </td>
                </tr>
                <tr>
                    <td style='color: #64748b; font-weight: 500;'>校验和校验</td>
                    <td style='color: {
                        "#10b981" if parse_data["checksum"]["valid"] else 
                        "#f59e0b" if parse_data["checksum"]["hex"] else 
                        "#94a3b8"
                    };'>
                        {
                            "✅ 通过" if parse_data["checksum"]["valid"] else 
                            f"⚠️ 不匹配 （实际：{parse_data['checksum']['hex']}，计算：{parse_data['checksum']['calculated']}）" 
                            if parse_data["checksum"]["hex"] else "ℹ️ 数据不足"
                        }
                    </td>
                </tr>
            </table>
        """

        # JSON详情
        json_info = f"""
            <div>
                <h5 style='color: #1e293b; margin-top: 0; font-size: 13px;'>解析详情（JSON格式）</h5>
                <div class='json-container'>
                    <pre style='font-family: Consolas, monospace; font-size: 12px; margin: 0;'>{json_str}</pre>
                </div>
            </div>
        """

        # 警告提示
        warning_msg = f"""
            <p style='color: {status_color}; margin-top: 10px; font-size: 13px;'>
                {status_icon} 提示：{parse_data['basic']['msg']}
            </p>
        """ if parse_data["basic"]["msg"] else ""

        # 卡片模块
        card_border_color = "#10b981" if parse_data["basic"]["status"] == "success" else "#f59e0b"
        return f"""
            <div class='result-card' style='border-left-color: {card_border_color};'>
                {basic_info}
                {json_info}
                {warning_msg}
            </div>
            <div class='result-divider'></div>
        """

    def _generate_fail_module(self, idx: int, raw_data: str, error_msg: str) -> str:
        """生成单条解析失败的HTML模块"""
        display_data = raw_data[:100] + "..." + raw_data[-20:] if len(raw_data) > 120 else raw_data
        return f"""
            <div class='result-card' style='border-left-color: #ef4444;'>
                <h4 style='color: #ef4444; margin-top: 0; font-size: 14px;'>
                    第{idx}条数据 ❌ 解析失败
                </h4>
                <table style='width: 100%; border-collapse: separate; border-spacing: 0 8px; margin-bottom: 15px;'>
                    <tr>
                        <td style='width: 130px; color: #64748b; font-weight: 500;'>原始数据</td>
                        <td style='color: #ef4444;'>{display_data}</td>
                    </tr>
                    <tr>
                        <td style='color: #64748b; font-weight: 500;'>失败原因</td>
                        <td style='color: #ef4444;'>{error_msg}</td>
                    </tr>
                </table>
            </div>
            <div class='result-divider'></div>
        """


# --------------------------
# 4. 界面类：主窗口（UI模块+多线程调度）
# --------------------------
class ProtocolAnalyzerWindow(QMainWindow):
    """工具主窗口（整合UI与多线程调度）"""
    def __init__(self):
        super().__init__()
        self.parser = ProtocolParser()
        self.parse_worker = None  # 解析工作线程实例
        self.result_modules = []  # 存储所有结果模块
        self.init_window()
        self.init_ui_components()
        self.init_layout()
        self.apply_style()

    def init_window(self):
        """初始化窗口基础属性"""
        self.setWindowTitle("智能协议解析工具 v2.2（多线程版）")
        self.resize(1000, 750)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setObjectName("centralWidget")

    def init_ui_components(self):
        """初始化所有UI组件"""
        # 1. 输入区域组件
        self.input_frame = QFrame()
        self.input_frame.setObjectName("contentFrame")
        self.input_title = QLabel("数据输入区")
        self.input_title.setObjectName("sectionTitle")
        self.input_hint = QLabel("支持手动输入十六进制文本（每行一条）或拖拽文件（.txt/.hex/.log）")
        self.input_hint.setObjectName("sectionHint")
        self.input_text = DraggableTextEdit()

        # 2. 按钮区域组件
        self.btn_frame = QFrame()
        self.btn_frame.setObjectName("contentFrame")
        self.btn_frame.setMinimumHeight(80)
        self.parse_btn = QPushButton("🔍 解析数据")
        self.parse_btn.setObjectName("primaryBtn")
        self.import_btn = QPushButton("📁 导入文件")
        self.import_btn.setObjectName("secondaryBtn")
        self.clear_btn = QPushButton("🗑️ 清除内容")
        self.clear_btn.setObjectName("dangerBtn")

        # 3. 结果区域组件
        self.result_frame = QFrame()
        self.result_frame.setObjectName("contentFrame")
        self.result_title = QLabel("解析结果区")
        self.result_title.setObjectName("sectionTitle")
        self.result_status = QLabel("🔴 待解析")
        self.result_status.setObjectName("resultStatus")
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setObjectName("resultText")
        self.result_text.setPlaceholderText("解析结果将逐条显示在这里...")

        # 4. 绑定按钮事件
        self.parse_btn.clicked.connect(self.on_parse_click)
        self.import_btn.clicked.connect(self.on_import_click)
        self.clear_btn.clicked.connect(self.on_clear_click)
        # 绑定按钮动画
        self.parse_btn.clicked.connect(lambda: self.btn_click_anim(self.parse_btn))
        self.import_btn.clicked.connect(lambda: self.btn_click_anim(self.import_btn))
        self.clear_btn.clicked.connect(lambda: self.btn_click_anim(self.clear_btn))

    def init_layout(self):
        """初始化布局（整数比例：输入4 : 按钮1 : 结果15）"""
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)

        # 输入区域布局
        input_layout = QVBoxLayout(self.input_frame)
        input_layout.setSpacing(10)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_title_layout = QHBoxLayout()
        input_title_layout.addWidget(self.input_title)
        input_title_layout.addStretch()
        input_title_layout.addWidget(self.input_hint)
        input_layout.addLayout(input_title_layout)
        input_layout.addWidget(self.input_text)

        # 按钮区域布局
        btn_layout = QHBoxLayout(self.btn_frame)
        btn_layout.setSpacing(25)
        btn_layout.setContentsMargins(20, 15, 20, 15)
        btn_layout.addStretch()
        btn_layout.addWidget(self.parse_btn)
        btn_layout.addWidget(self.import_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()

        # 结果区域布局
        result_layout = QVBoxLayout(self.result_frame)
        result_layout.setSpacing(10)
        result_layout.setContentsMargins(20, 20, 20, 20)
        result_title_layout = QHBoxLayout()
        result_title_layout.addWidget(self.result_title)
        result_title_layout.addStretch()
        result_title_layout.addWidget(self.result_status)
        result_layout.addLayout(result_title_layout)
        result_layout.addWidget(self.result_text)

        # 加入主布局
        main_layout.addWidget(self.input_frame, 4)
        main_layout.addWidget(self.btn_frame, 1)
        main_layout.addWidget(self.result_frame, 15)
        main_layout.setStretch(0, 4)
        main_layout.setStretch(1, 1)
        main_layout.setStretch(2, 15)

    def apply_style(self):
        """应用现代美观的样式表"""
        style_sheet = """
        QMainWindow { background-color: #f0f2f5; }
        QWidget#centralWidget {
            border-radius: 18px;
            background-color: #f0f2f5;
            margin: 6px;
        }
        QFrame#contentFrame {
            background-color: #ffffff;
            border-radius: 16px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            border: none;
        }
        QLabel#sectionTitle {
            font-size: 18px;
            font-weight: 600;
            color: #1e293b;
            padding-bottom: 8px;
            border-bottom: 1px solid #e2e8f0;
        }
        QLabel#sectionHint {
            font-size: 12px;
            color: #64748b;
            padding-top: 4px;
        }
        QLabel#resultStatus {
            font-size: 14px;
            font-weight: 500;
            color: #ef4444;
        }
        QTextEdit#inputText {
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 15px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            background-color: #f8fafc;
            color: #1e293b;
            selection-background-color: #3b82f6;
            selection-color: #ffffff;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
        }
        QTextEdit#inputText:focus {
            border-color: #3b82f6;
            background-color: #ffffff;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02), 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        QTextEdit#resultText {
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 15px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            background-color: #f8fafc;
            color: #1e293b;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
        }
        QTextEdit#resultText:focus {
            border-color: #3b82f6;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02), 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        .json-container {
            background-color: #f1f5f9;
            border-radius: 10px;
            padding: 15px;
            margin-top: 15px;
            overflow-x: auto;
        }
        .result-card {
            background-color: #f8fafc;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #3b82f6;
        }
        .result-divider {
            height: 1px;
            background-color: #e2e8f0;
            margin: 20px 0;
        }
        QPushButton#primaryBtn {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #3b82f6, stop: 1 #2563eb);
            color: #ffffff;
            border: none;
            border-radius: 12px;
            padding: 14px 30px;
            font-size: 15px;
            font-weight: 600;
            min-width: 140px;
            box-shadow: 0 4px 8px rgba(59, 130, 246, 0.2);
            transition: all 0.2s ease;
        }
        QPushButton#primaryBtn:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #2563eb, stop: 1 #1d4ed8);
            box-shadow: 0 6px 12px rgba(59, 130, 246, 0.3);
            transform: translateY(-1px);
        }
        QPushButton#primaryBtn:pressed {
            background: #1d4ed8;
            box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
            transform: translateY(0);
        }
        QPushButton#primaryBtn:disabled {
            background: #94a3b8;
            box-shadow: none;
            transform: none;
        }
        QPushButton#secondaryBtn {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #8b5cf6, stop: 1 #7c3aed);
            color: #ffffff;
            border: none;
            border-radius: 12px;
            padding: 14px 30px;
            font-size: 15px;
            font-weight: 600;
            min-width: 140px;
            box-shadow: 0 4px 8px rgba(139, 92, 246, 0.2);
            transition: all 0.2s ease;
        }
        QPushButton#secondaryBtn:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #7c3aed, stop: 1 #6d28d9);
            box-shadow: 0 6px 12px rgba(139, 92, 246, 0.3);
            transform: translateY(-1px);
        }
        QPushButton#secondaryBtn:pressed {
            background: #6d28d9;
            box-shadow: 0 2px 4px rgba(139, 92, 246, 0.2);
            transform: translateY(0);
        }
        QPushButton#dangerBtn {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #ef4444, stop: 1 #dc2626);
            color: #ffffff;
            border: none;
            border-radius: 12px;
            padding: 14px 30px;
            font-size: 15px;
            font-weight: 600;
            min-width: 140px;
            box-shadow: 0 4px 8px rgba(239, 68, 68, 0.2);
            transition: all 0.2s ease;
        }
        QPushButton#dangerBtn:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #dc2626, stop: 1 #b91c1c);
            box-shadow: 0 6px 12px rgba(239, 68, 68, 0.3);
            transform: translateY(-1px);
        }
        QPushButton#dangerBtn:pressed {
            background: #b91c1c;
            box-shadow: 0 2px 4px rgba(239, 68, 68, 0.2);
            transform: translateY(0);
        }
        """
        self.setStyleSheet(style_sheet)
        global_font = QFont("Inter", 11)
        self.setFont(global_font)

    # --------------------------
    # 交互事件处理
    # --------------------------
    def btn_click_anim(self, btn):
        """按钮点击缩放动画（禁用时不执行）"""
        if btn.isEnabled():
            anim = QPropertyAnimation(btn, b"geometry")
            anim.setDuration(100)
            anim.setEasingCurve(QEasingCurve.Type.OutQuad)
            orig_geo = btn.geometry()
            anim.setStartValue(orig_geo)
            anim.setEndValue(orig_geo.adjusted(2, 2, -2, -2))
            anim.finished.connect(lambda: self._reset_btn_anim(btn, orig_geo))
            anim.start()

    def _reset_btn_anim(self, btn, orig_geo):
        """按钮动画恢复"""
        reset_anim = QPropertyAnimation(btn, b"geometry")
        reset_anim.setDuration(100)
        reset_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        reset_anim.setStartValue(btn.geometry())
        reset_anim.setEndValue(orig_geo)
        reset_anim.start()

    @pyqtSlot(int, int)
    def on_progress_updated(self, current: int, total: int):
        """接收进度信号，更新状态标签"""
        self._update_result_status(f"🟡 解析中（{current}/{total}）", "#f59e0b")

    @pyqtSlot(str)
    def on_result_module_received(self, module: str):
        """接收结果模块信号，追加到显示区"""
        self.result_modules.append(module)
        # 每积累3个模块刷新一次UI，减少刷新频率
        if len(self.result_modules) % 3 == 0 or len(self.result_modules) == len(self.raw_data_list):
            full_html = "".join(self.result_modules)
            display_html = f"""
                <div style='color: #1e293b; line-height: 1.6; padding: 10px;'>
                    <h3 style='color: #3b82f6; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 20px;'>
                        📊 协议解析结果（共{len(self.raw_data_list)}条）
                    </h3>
                    {full_html}
                </div>
            """
            self.result_text.setHtml(display_html)

    @pyqtSlot(bool)
    def on_parse_finished(self, is_success: bool):
        """接收解析完成信号，更新最终状态"""
        total_count = len(self.raw_data_list)
        if is_success:
            self._update_result_status("🟢 解析完成", "#10b981")
            # 确保最后一批结果刷新
            self.on_result_module_received("")
        else:
            self._update_result_status("🔴 解析终止", "#ef4444")
            self.result_text.setHtml("""
                <div style='text-align: center; padding: 40px 0;'>
                    <span style='font-size: 28px; color: #ef4444;'>⏹️</span>
                    <h3 style='color: #ef4444; margin: 15px 0;'>解析已终止</h3>
                    <p style='color: #64748b;'>已解析部分结果保留，可继续操作</p>
                </div>
            """)
        # 启用按钮，重置线程
        self.parse_btn.setEnabled(True)
        self.import_btn.setEnabled(True)
        self.parse_worker = None

    def on_parse_click(self):
        """解析按钮点击事件（启动多线程）"""
        input_text = self.input_text.toPlainText().strip()
        if not input_text:
            self._update_result_status("🔴 解析失败", "#ef4444")
            self._show_result_html("""
                <div style='text-align: center; padding: 40px 0;'>
                    <span style='font-size: 28px; color: #ef4444;'>⚠️</span>
                    <h3 style='color: #ef4444; margin: 15px 0;'>请输入协议数据</h3>
                    <p style='color: #64748b;'>请在输入区填写十六进制协议文本（每行一条）或拖拽文件</p>
                </div>
            """)
            return

        # 拆分输入数据
        self.raw_data_list = [line.strip() for line in input_text.splitlines() if line.strip()]
        total_count = len(self.raw_data_list)
        if total_count == 0:
            self._update_result_status("🔴 解析失败", "#ef4444")
            self._show_result_html("""
                <div style='text-align: center; padding: 40px 0;'>
                    <span style='font-size: 28px; color: #ef4444;'>⚠️</span>
                    <h3 style='color: #ef4444; margin: 15px 0;'>无有效数据</h3>
                    <p style='color: #64748b;'>输入内容为空或仅包含空行，请输入有效数据</p>
                </div>
            """)
            return

        # 初始化解析状态
        self.result_modules.clear()
        self._update_result_status(f"🟡 解析中（0/{total_count}）", "#f59e0b")
        self.result_text.clear()
        self._show_result_html(f"""
            <div style='text-align: center; padding: 20px 0;'>
                <span style='font-size: 24px; color: #f59e0b;'>🔄</span>
                <h3 style='color: #f59e0b; margin: 10px 0;'>开始解析 {total_count} 条数据</h3>
                <p style='color: #64748b;'>解析过程中可正常操作窗口...</p>
            </div>
        """)

        # 禁用按钮，防止重复触发
        self.parse_btn.setEnabled(False)
        self.import_btn.setEnabled(False)

        # 创建并启动工作线程
        self.parse_worker = ParseWorker(self.raw_data_list)
        # 连接信号槽
        self.parse_worker.progress_signal.connect(self.on_progress_updated)
        self.parse_worker.result_module_signal.connect(self.on_result_module_received)
        self.parse_worker.finish_signal.connect(self.on_parse_finished)
        # 启动线程
        self.parse_worker.start()

    def on_import_click(self):
        """导入文件按钮点击事件（支持多行数据）"""
        self._update_result_status("🟡 导入中", "#f59e0b")
        QApplication.processEvents()

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择协议文件", "", "文本文件 (*.txt);;十六进制文件 (*.hex);;日志文件 (*.log)"
        )

        if not file_path:
            self._update_result_status("🔴 导入取消", "#ef4444")
            self._show_result_html("""
                <div style='text-align: center; padding: 40px 0;'>
                    <span style='font-size: 28px; color: #64748b;'>ℹ️</span>
                    <h3 style='color: #64748b; margin: 15px 0;'>文件导入已取消</h3>
                    <p style='color: #94a3b8;'>未选择任何文件</p>
                </div>
            """)
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            raw_data_list = [line.strip() for line in content.splitlines() if line.strip()]
            data_count = len(raw_data_list)
            self.input_text.setText(content)
            self.input_text.setPlaceholderText(f"已加载文件：{file_path}（共{data_count}条数据）")
            self._update_result_status("🟢 导入成功", "#10b981")
            self._show_result_html(f"""
                <div style='text-align: center; padding: 40px 0;'>
                    <span style='font-size: 28px; color: #10b981;'>📁</span>
                    <h3 style='color: #10b981; margin: 15px 0;'>文件导入成功</h3>
                    <p style='color: #64748b; margin-bottom: 10px;'>文件路径：{file_path}</p>
                    <div style='background: #f1f5f9; border-radius: 8px; padding: 10px 20px; display: inline-block; margin-bottom: 15px;'>
                        <span style='color: #1e293b; font-size: 13px;'>数据总量：{data_count} 条</span>
                    </div>
                    <p style='color: #94a3b8;'>点击「解析数据」按钮开始批量解析</p>
                </div>
            """)
        except Exception as e:
            self._update_result_status("🔴 导入失败", "#ef4444")
            self._show_result_html(f"""
                <div style='text-align: center; padding: 40px 0;'>
                    <span style='font-size: 28px; color: #ef4444;'>❌</span>
                    <h3 style='color: #ef4444; margin: 15px 0;'>文件导入失败</h3>
                    <p style='color: #64748b;'>错误原因：{str(e)}</p>
                </div>
            """)

    def on_clear_click(self):
        """清除按钮点击事件（终止线程）"""
        # 若解析中，终止线程
        if self.parse_worker and self.parse_worker.isRunning():
            self.parse_worker.stop()
            self.parse_worker.wait()  # 等待线程安全退出
            self.parse_worker = None

        # 清除内容
        self.input_text.clear()
        self.input_text.setPlaceholderText("请输入十六进制协议文本（每行一条数据）\n或直接拖拽 .txt/.hex/.log 文件到此处...")
        self.result_modules.clear()
        self._update_result_status("🔴 待解析", "#ef4444")
        self._show_result_html("""
            <div style='text-align: center; padding: 40px 0;'>
                <span style='font-size: 28px; color: #64748b;'>🗑️</span>
                <h3 style='color: #64748b; margin: 15px 0;'>内容已清除</h3>
                <p style='color: #94a3b8;'>请输入新的协议数据（每行一条）开始解析</p>
            </div>
        """)
        # 启用按钮
        self.parse_btn.setEnabled(True)
        self.import_btn.setEnabled(True)

    # --------------------------
    # 结果展示辅助函数
    # --------------------------
    def _update_result_status(self, text: str, color: str):
        """更新结果状态标签"""
        self.result_status.setText(text)
        self.result_status.setStyleSheet(f"color: {color};")

    def _show_result_html(self, html: str):
        """显示结果HTML内容"""
        self.result_text.setHtml(f"<div style='color: #1e293b; line-height: 1.6; padding: 10px;'>{html}</div>")

    def closeEvent(self, event):
        """窗口关闭事件：终止线程"""
        if self.parse_worker and self.parse_worker.isRunning():
            self.parse_worker.stop()
            self.parse_worker.wait()
        event.accept()


# --------------------------
# 程序入口
# --------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("智能协议解析工具")
    app.setApplicationVersion("2.2")
    window = ProtocolAnalyzerWindow()
    window.show()
    sys.exit(app.exec())