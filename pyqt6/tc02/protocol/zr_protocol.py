# 配置日志：级别为DEBUG（显示所有级别），格式包含时间、级别、消息
import json
import logging
import re
import struct
import traceback
from datetime import datetime
from typing import Tuple, Optional, Dict, List, Any
from zoneinfo import ZoneInfo

from tc02.utils.byte_utils import hex_to_formatted_binary, decode_iccid_bcd

logging.basicConfig(
    level=logging.INFO,  # 日志级别：DEBUG < INFO < WARNING < ERROR < CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s',  # 格式
    datefmt='%Y-%m-%d %H:%M:%S'  # 时间格式
)

# -------------------
# TC02常量
# -------------------
ZR_FRAME_START = 0xDDDD
ZR_FRAME_END = 0xFFFF

ZR_FRAME_START_ = b'\xdd\xdd'
ZR_FRAME_END_ = b'\xff\xff'
# -------------------
# TC02消息包类型变量
# -------------------
FRAME_TYPE_POSITION = 0x0102  # 事件/位置包
FRAME_TYPE_SERVER_RESPONSR = 0x0400  # 平台通用应答包
FRAME_TYPE_HEARTBEAT = 0x0100  # 心跳包
FRAME_TYPE_BASICK_INFORMATION = 0x0101  # 基础属性包
FRAME_TYPE_lBS_TRANSFER_REQUEST = 0x0103  # 设备请求LBS解析包
FRAME_TYPE_lBS_TRANSFER_RESPONSE = 0x0403  # 设备请求LBS解析-平台应答包
FRAME_TYPE_TIME_SYNCHRONIZATION_REQUEST = 0x0104  # 设备请求同步服务器时间包
FRAME_TYPE_TIME_SYNCHRONIZATION_RESPONSE = 0x0404  # 设备请求同步服务器时间-平台应答包
FRAME_TYPE_PARAMS_CONFIGURATION = 0x0700  # 平台下发参数配置包
FRAME_TYPE_DEVICE_RESPONSE = 0x0A00  # 设备通用应答包
FRAME_TYPE_PARAMS_QUERY = 0x0701  # 平台下发参数查询包
FRAME_TYPE_PARAMS_QUERY_RESPONSE = 0x0A01  # 平台下发参数查询-设备应答包

# -------------------
# TLV类型变量
# -------------------
TLV_230F = 0x230F
TLV_2310 = 0x2310
TLV_2400 = 0x2400
TLV_2406 = 0x2406
TLV_2415 = 0x2415
TLV_2480 = 0x2480
TLV_24C0 = 0x24C0
TLV_240C = 0x240C
TLV_2003 = 0x2003
TLV_2004 = 0x2004
TLV_2005 = 0x2005
TLV_2028 = 0x2028
TLV_2030 = 0x2030  # Duration of ignition on
TLV_2031 = 0x2031  # Duration of ignition off
TLV_2032 = 0x2032  # acc state
TLV_2042 = 0x2042  # Ignition setting
TLV_2046 = 0x2046  # Duration of voltage on
TLV_2047 = 0x2047  # Duration of voltage off
TLV_204F = 0x204F  # Voltage virtual ignition setting
TLV_2095 = 0x2095  # Unary GNSS
TLV_20C6 = 0x20C6  # Fixed frequency upload
TLV_2110 = 0x2110  # cornering reason
TLV_2114 = 0x2114  # cornering upload setting
TLV_2130 = 0x2130  # Unary LBS
TLV_22A0 = 0x22A0  # OTA Module ID and update state
TLV_22B4 = 0x22B4  # Download URL
TLV_23A3 = 0x23A3  # UTC Timestamp
TLV_2333 = 0x2333  # Ignition detection mode and state
TLV_2350 = 0x2350
TLV_2391 = 0x2391
TLV_2980 = 0x2980  # IO1（断油电）
TLV_2A80 = 0x2A80  # External power supply monitoring


# TLV_ = 0x
# TLV_ = 0x
# TLV_ = 0x
# TLV_ = 0x
# TLV_ = 0x
# TLV_ = 0x
# TLV_ = 0x
# TLV_ = 0x
# TLV_ = 0x
# TLV_ = 0x
# TLV_ = 0x


def parse_frame_0102(msg_body: bytes) -> Dict:
    """解析报文（消息ID=0x0102）"""
    tlv_datas = parse_tlv_stream(msg_body)
    return {
        'type': '0x0102位置/事件包',
        'tlv_datas': tlv_datas
    }


def parse_frame_0400(msg_body: bytes) -> Dict:
    tlv_datas = parse_tlv_stream(msg_body)
    return {
        'type': '0x0400平台通用应答包',
        'tlv_datas': tlv_datas
    }


def parse_frame_0100(msg_body: bytes) -> Dict:
    tlv_datas = parse_tlv_stream(msg_body)
    return {
        'type': '0x0100心跳包',
        'tlv_datas': tlv_datas
    }


def parse_frame_0101(msg_body: bytes) -> Dict:
    """解析基础属性报文（消息ID=0x0101）"""
    tlv_datas = parse_tlv_stream(msg_body)
    return {
        'type': '0x0101基础属性包',
        'tlv_datas': tlv_datas
    }


def parse_frame_0103(msg_body: bytes) -> Dict:
    tlv_datas = parse_tlv_stream(msg_body)
    return {
        'type': '0x0103设备请求LBS解析包',
        'tlv_datas': tlv_datas
    }


def parse_frame_0403(msg_body: bytes) -> Dict:
    tlv_datas = parse_tlv_stream(msg_body)
    return {
        'type': '0x0403设备请求LBS解析-平台应答包',
        'tlv_datas': tlv_datas
    }


def parse_frame_0104(msg_body: bytes) -> Dict:
    tlv_datas = parse_tlv_stream(msg_body)
    return {
        'type': '0x0104设备请求同步服务器时间包',
        'tlv_datas': tlv_datas
    }


def parse_frame_0404(msg_body: bytes) -> Dict:
    tlv_datas = parse_tlv_stream(msg_body)
    return {
        'type': '0x0404设备请求同步服务器时间-平台应答包',
        'tlv_datas': tlv_datas
    }


def parse_frame_0700(msg_body: bytes) -> Dict:
    tlv_datas = parse_tlv_stream(msg_body)
    return {
        'type': '0x0700平台下发参数配置包',
        'tlv_datas': tlv_datas
    }


def parse_frame_0a00(msg_body: bytes) -> Dict:
    tlv_datas = parse_tlv_stream(msg_body)
    return {
        'type': '0x0A01设备通用应答包',
        'tlv_datas': tlv_datas
    }


def parse_frame_0701(msg_body: bytes) -> Dict:
    tlv_datas = parse_tlv_stream(msg_body)
    return {
        'type': '0x0701平台下发参数查询包',
        'tlv_datas': tlv_datas
    }


def parse_frame_0a01(msg_body: bytes) -> Dict:
    tlv_datas = parse_tlv_stream(msg_body)
    return {
        'type': '0x0A01平台下发参数查询-设备应答包',
        'tlv_datas': tlv_datas
    }


def default_parse(msg_body: bytes, msg_type, frame) -> Tuple:
    frame['消息体'] = msg_body.hex()
    return True, f"消息合法，但未实现消息ID=0x{msg_type:04x}的解析", frame


MSG_TYPE_FUNCTION = {
    FRAME_TYPE_POSITION: parse_frame_0102,
    FRAME_TYPE_SERVER_RESPONSR: parse_frame_0400,
    FRAME_TYPE_HEARTBEAT: parse_frame_0100,
    FRAME_TYPE_BASICK_INFORMATION: parse_frame_0101,
    FRAME_TYPE_lBS_TRANSFER_REQUEST: parse_frame_0103,
    FRAME_TYPE_lBS_TRANSFER_RESPONSE: parse_frame_0403,
    FRAME_TYPE_TIME_SYNCHRONIZATION_REQUEST: parse_frame_0104,
    FRAME_TYPE_TIME_SYNCHRONIZATION_RESPONSE: parse_frame_0404,
    FRAME_TYPE_PARAMS_CONFIGURATION: parse_frame_0700,
    FRAME_TYPE_DEVICE_RESPONSE: parse_frame_0a00,
    FRAME_TYPE_PARAMS_QUERY: parse_frame_0701,
    FRAME_TYPE_PARAMS_QUERY_RESPONSE: parse_frame_0a01
}


def hex_to_bytes(hex_str: str) -> bytes:
    """十六进制字符串转字节流（处理空格）"""
    # 正则模式：可选前缀0x/0X，后面跟1个以上的16进制字符
    hex_pattern = re.compile(r'^0x[0-9a-fA-F]+$|^[0-9a-fA-F]+$')
    # 完全匹配则返回True，否则False
    hex_flag = bool(hex_pattern.fullmatch(hex_str))
    if not hex_flag:
        raise ValueError("输入的内容不是16进制数据")
    hex_str = hex_str.replace(" ", "").strip()
    if len(hex_str) % 2 != 0:
        raise ValueError("十六进制字符串长度必须为偶数")
    return bytes.fromhex(hex_str)


def calculate_checksum(data: bytes) -> int:
    """计算校验码（异或和）"""
    checksum = 0
    for byte in data:
        checksum ^= byte
    return checksum & 0xFF


def parse_tlv_230f(values: bytes) -> Dict:
    major = struct.unpack(">B", values)[0]
    match major:
        case 0x01:
            major_desc = 'Driving behaviour data'
        case 0x02:
            major_desc = 'GNSS data'
        case 0x03:
            major_desc = 'Real-time device information data'
        case 0x04:
            major_desc = 'Peripheral status'
        case 0x05:
            major_desc = 'Emergency event'
        case _:
            major_desc = 'Unknow major type'

    return {
        '事件主类型': major_desc,
    }


def detect_event_type(data_bytes):
    """
    更高效的事件类型检测方法
    """
    data_int = int.from_bytes(data_bytes, byteorder='big', signed=False)
    event_masks = {
        0x0000000000000001: "开机事件",
        0x0000000000000004: "外电连接事件",
        0x0000000000000008: "外电断开事件",
        0x0000000000000010: "外电低压事件",
        0x0000000000000020: "电池低电事件",
        0x0000000000000040: "开始充电事件",
        0x0000000000000080: "结束充电事件",
        0x0000000000000100: "gensor静止事件",
        0x0000000000000200: "gensor运动事件",
        0x0000000000001000: "ACC点火事件",
        0x0000000000002000: "ACC熄火事件",
        0x0000000004000000: "定时上报事件",
        0x0000004000000000: "OTA升级结果",
        0x0020000000000000: "轮动报警",
        0x0040000000000000: "Acc非法点火报警",
        0x0000100000000000: "震动报警",
        0x0000080000000000: "碰撞报警",
        0x0001000000000000: "数字IO变化（油电）",
        0x0000000200000000: "拐点",
        0x0000000000800000: "超速报警"
    }
    # 使用位运算技巧快速检测
    # 1. 检查是否为0
    if data_int == 0:
        return "未知事件"

    # 2. 检查是否只有一个位被设置（即2的幂）
    if (data_int & (data_int - 1)) == 0:
        # 只有一个位被设置，使用字典查找
        return event_masks.get(data_int, "未知事件")

    # 3. 多个位被设置
    active_bits = bin(data_int).count("1")
    # 检测所有发生的事件
    # active_events = []
    # for mask, event_name in event_masks.items():
    #     if data_int & mask:
    #         active_events.append(event_name)
    #
    # if not active_events:
    #     return ["未知事件"]

    return f"多个事件同时发生（{active_bits}个事件）"


def parse_tlv_2310(values: bytes) -> Dict:
    return {
        "事件次类型": detect_event_type(values)
    }


def parse_tlv_2032(values: bytes) -> Dict:
    acc = struct.unpack(">B", values)[0]
    return {
        "ACC 状态": '已连接' if acc == 2 else '已断开' if acc == 1 else '未连接'
    }


def parse_tlv_2400(values: bytes) -> Dict:
    return {
        "设备名称": values.decode("utf-8"),
    }


def parse_tlv_2480(values: bytes) -> Dict:
    index = 0
    # 2g APN：cmnet 123 123
    apn_len_2g = struct.unpack(">B", values[:1])[0]  # [0:1] 1
    index += 1

    apn_2g = struct.unpack(f">{apn_len_2g}s", values[index:index + apn_len_2g])[0] if apn_len_2g else b""  # [1:1+5] 6
    index += apn_len_2g

    # 2g APN-username
    username_len_2g = struct.unpack(">B", values[index:index + 1])[0]  # [6:6+1] 7
    index += 1

    username_2g = struct.unpack(f">{username_len_2g}s", values[index:index + username_len_2g])[0] \
        if username_len_2g else b""  # [7:7+3] 10
    index += username_len_2g

    pwd_len_2g = struct.unpack(">B", values[index:index + 1])[0]  # [10:10+1] 11
    index += 1

    pwd_2g = struct.unpack(f">{pwd_len_2g}s", values[index:index + pwd_len_2g])[
        0] if pwd_len_2g else b""  # [11:11+3] 14
    index += pwd_len_2g

    # -----------------------------------4g APN
    apn_len_4g = struct.unpack(">B", values[index:index + 1])[0]  # [14:14+1] 15
    index += 1

    apn_4g = struct.unpack(f">{apn_len_2g}s", values[1:apn_len_4g + 1])[0] if apn_len_4g else b""  # [15:15+5] 20
    index += apn_len_4g

    # APN-username
    username_len_4g = struct.unpack(">B", values[index:index + 1])[0]  # [20:20+1] 21
    index += 1

    username_4g = struct.unpack(f">{username_len_4g}s", values[index:index + username_len_4g])[0] \
        if username_len_4g else b""  # [21:21+3] 24
    index += username_len_4g

    pwd_len_4g = struct.unpack(">B", values[index:index + 1])[0]  # [24:24+1] 25
    index += 1

    pwd_4g = struct.unpack(f">{pwd_len_4g}s", values[index:index + pwd_len_4g])[
        0] if pwd_len_4g else b""  # [25:25+3] 28
    index += pwd_len_4g

    #
    apn_auth, gprs_mode, lte_mode = struct.unpack(">3B", values[index:])
    index += 3

    return {
        "APN参数": {
            "2G-APN": {
                "APN长度": apn_len_2g,
                "APN": apn_2g.decode("utf-8"),
                "用户名长度": username_len_2g,
                "用户名": username_2g.decode("utf-8"),
                "密码长度": pwd_len_2g,
                "密码": pwd_2g.decode("utf-8"),
            },
            "4G-APN": {
                "APN长度": apn_len_4g,
                "APN": apn_4g.decode("utf-8"),
                "用户名长度": username_len_4g,
                "用户名": username_4g.decode("utf-8"),
                "密码长度": pwd_len_4g,
                "密码": pwd_4g.decode("utf-8"),
            },
            "其他": {
                "APN加密方式": apn_auth,
                "4G模式": gprs_mode,
                "2G模式": lte_mode
            }
        }
    }


def parse_tlv_2406(values: bytes) -> Dict:
    start_index = 0
    # 设备名称长度1+设备名称6
    dev_name_len = struct.unpack(">B", values[:start_index + 1])[0]  #[0:1] 1
    start_index += 1

    dev_name = values[start_index:start_index + dev_name_len].decode("utf-8")  # [1:1+6] 7
    start_index += dev_name_len

    # 设备类型长度1+设备类型2
    dev_type_len = struct.unpack(">B", values[start_index:start_index + 1])[0]  # [7:7+1] 8
    start_index += 1

    dev_type = struct.unpack(f">{dev_type_len}s", values[start_index:start_index + dev_type_len])[0]  # [8:8+2] 10
    start_index += dev_type_len

    # 软件版本3
    software_version = struct.unpack(">3s", values[start_index:start_index + 3])[0]  # [10:10+3] 13
    start_index += 3

    # 硬件版本长度1+硬件版本8
    hardware_ver_len = struct.unpack(">B", values[start_index:start_index + 1])[0]  # [13:13+1] 14
    start_index += 1

    hardware_ver = struct.unpack(f">{hardware_ver_len}s", values[start_index:start_index + hardware_ver_len])[
        0]  # [14:14+8] 22
    start_index += hardware_ver_len

    # 模块版本长度1+模块版本31
    module_ver_len = struct.unpack(">B", values[start_index:start_index + 1])[0]  # [22:22+1] 23
    start_index += 1

    module_ver = struct.unpack(f">{module_ver_len}s", values[start_index:start_index + module_ver_len])[
        0]  # [23:23+31] 54
    start_index += module_ver_len

    # 模块类型长度1+模块类型6
    module_type_len = struct.unpack(">B", values[start_index:start_index + 1])[0]  # [54:54+1] 55
    start_index += 1

    module_type = struct.unpack(f"{module_type_len}s", values[start_index:start_index + module_type_len])[
        0]  # [55:55+6] 61
    start_index += module_type_len

    return {
        "版本信息": {
            "设备名称长度": dev_name_len,
            "设备名称": dev_name,
            "设备类型长度": dev_type_len,
            "设备类型": dev_type.decode("utf-8"),
            "软件版本": software_version.hex(),
            "硬件版本长度": hardware_ver_len,
            "硬件版本": hardware_ver.decode("utf-8"),
            "模块版本长度": module_ver_len,
            "模块版本": module_ver.decode("utf-8"),
            "模块类型长度": module_type_len,
            "模块类型": module_type.decode("utf-8")
        }
    }


def parse_tlv_24c0(values: bytes) -> Dict:
    connect_mode, priority, chose, port, server_len = struct.unpack(">B B B H B", values[:6])
    server, sms_gateway_len = struct.unpack(f">{server_len}s B", values[6:-5])
    if sms_gateway_len == 0:
        sms_gateway = None
        heart_beat_time = struct.unpack(">I", values[-4:])[0]
    else:
        sms_gateway, heart_beat_time = struct.unpack(f">{sms_gateway_len}s I", values[-5:])

    communications = {
        1: "关闭",
        2: "TCP short-connection",
        3: "TCP long-connection",
        4: "UDP short-connection",
        5: "Only SMS",
        6: "TCP short-connection & SMS",
        7: "TCP long-connection & SMS",
        8: "TCP short-connection & BackupServer",
        9: "TCP long-connection & BackupServer",
    }

    connect = communications.get(connect_mode, f"未知：{connect_mode}")
    buff_priority = "low priority" if priority == 2 else "high priority" if priority == 3 else "关闭"
    chose_set = "添加/修改" if chose == 1 else "删除" if chose == 2 else None

    return {
        "IP参数": {
            "通讯模式": connect,
            "优先级": buff_priority,
            "IP设置": chose_set,
            "IP/域名长度": server_len,
            "IP/域名": server.decode("utf-8") if server_len else None,
            "端口": port,
            "SMS-Gateway长度": sms_gateway_len,
            "SMS-Gateway": sms_gateway.decode("utf-8") if sms_gateway else None,
            "心跳间隔": heart_beat_time
        }
    }


def parse_tlv_2415(values: bytes) -> Dict:
    """Device information（消息ID=0x2415）"""
    formate_s = ">B 1s 10s B B B I I I 4s 5s B 2s B 2s"
    (ignition_mode, state, iccid, csq_rssi, csq_ber, ex_power_connect_status, mileages, last_positiom_utc,
     external_voltage, reserve1, reserve2, led_mode, reserve3, network, reserve4) = struct.unpack(formate_s, values)

    ignition = detection_mode.get(ignition_mode, f"未知：{ignition_mode}")
    state_bit = hex_to_formatted_binary(state.hex())
    lpt = datetime.fromtimestamp(last_positiom_utc, tz=ZoneInfo("UTC")).strftime("%Y-%m-%d %H:%M:%S")

    return {
        "设备信息": {
            f"[{ignition_mode:02x}]点火检测模式": ignition,
            "状态": state_bit,
            "ICCID": decode_iccid_bcd(iccid),
            "CSQ_RSSI": csq_rssi,
            "CSQ_BER": csq_ber,
            "外电连接状态": "已连接" if ex_power_connect_status == 2 else "未连接",
            "里程": f"{mileages}（{mileages / 1000.0}km）",
            "最近定位时间UTC": lpt,
            "外电电压": f"{external_voltage}（{external_voltage / 1000.0}v）",
            "保留1": reserve1.hex(),
            "保留2": reserve2.hex(),
            "灯模式": led_mode,
            "保留3": reserve3.hex(),
            "网络类型": network,
            "保留4": reserve4.hex()
        }
    }


def parse_tlv_23a3(values: bytes) -> Dict:
    t = struct.unpack(">I", values)[0]
    bj_time = datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
    utc_time = datetime.fromtimestamp(t, tz=ZoneInfo("UTC")).strftime('%Y-%m-%d %H:%M:%S')
    return {
        f"[{t:08X}]打包时间": {
            "UTC时间": utc_time,
            "北京时间": bj_time
        }
    }


def parse_tlv_2333(values: bytes) -> Dict:
    ignition_detect, state = struct.unpack(">B 1s", values)
    return {
        "点火检测模式和状态": {
            "检测模式": detection_mode.get(ignition_detect, f"未知:{ignition_detect}"),
            f"[{state.hex()}]状态": hex_to_formatted_binary(state.hex()),
        }
    }


def parse_tlv_2391(values: bytes) -> Dict:
    return {
        "密码": values.hex()
    }


def parse_tlv_2003(values: bytes) -> Dict:
    xyz = struct.unpack(">H", values)[0]
    unit = 0.01  # 0.01m/s²
    return {
        f"[{xyz:04X}]XYZ-轴值（m/s²）": xyz * unit
    }


def parse_tlv_2004(values: bytes) -> Dict:
    stationary_to_move, move_to_move = struct.unpack(">2I", values)
    return {
        "运动期间": {
            "静止到运动（s）": stationary_to_move,
            "上次运动到本次运动（s）": move_to_move
        }
    }


def parse_tlv_2005(values: bytes) -> Dict:
    move_to_stationary, stationary_to_stationary = struct.unpack(">2I", values)
    return {
        "静止期间": {
            "运动到静止（s）": move_to_stationary,
            "上次静止到本次静止（s）": stationary_to_stationary
        }
    }


def parse_tlv_2028(values: bytes) -> Dict:
    format_str = ">1s B B B H 1s B B 1s B 6s"
    (reserve1, vib_threshold, vib_count, vib_keep_time, static_keep_time, reserve2,
     command_state, report_mode, reserve3, xyz, reserve4) = struct.unpack(format_str, values)

    state_command = {
        1: "接收但不执行",
        2: "强制进入运动状态",
        3: "强制进入运动状态"
    }
    report_event_mode = {
        0: "都不上报",
        1: "只上报G-sensor进入运动状态",
        2: "只上报G-sensor进入静止状态",
        3: "都上报"
    }
    return {
        "G-sensor参数": {
            "保留1": reserve1.hex(),
            "震动阈值": vib_threshold,
            "震动次数": vib_count,
            "震动持续时间": vib_keep_time,
            "静止持续时间": static_keep_time,
            "保留2": reserve2.hex(),
            f"[{command_state}]命令状态": state_command.get(command_state, f"未知:{command_state}"),
            f"[{report_mode}]G-sensor事件上报": report_event_mode.get(report_mode, f"未知:{report_mode}"),
            "保留3": reserve3.hex(),
            "xyz-3轴": xyz,
            "保留4": reserve4.hex()
        }
    }


detection_mode = {
    1: "ACC检测",
    2: "保留",
    3: "ACC+Gensor检测（ACC优先）",
    4: "ACC+虚拟电压检测（ACC优先）",
    5: "G-sensor检测"
}


def parse_tlv_2030(values: bytes) -> Dict:
    return {
        "熄火期间": {}
    }


def parse_tlv_2031(values: bytes) -> Dict:
    return {
        "点火期间": {}
    }


def parse_tlv_2350(values: bytes) -> Dict:
    ignition_detection_mode = struct.unpack(">B", values)[0]

    return {
        f"[{ignition_detection_mode}]点火检测模式": detection_mode.get(ignition_detection_mode,
                                                                       f"未知:{ignition_detection_mode}")
    }


def parse_tlv_2095(values: bytes) -> Dict:
    format_s = ">H H H I I I I"
    accuracy, speed, azimuth, altitude, longitude, latitude, utc = struct.unpack(format_s, values)
    return {
        "GPS数据": {
            "精度": accuracy,
            "速度": speed / 10.0,
            "角度": azimuth,
            "高度": altitude,
            f"[{longitude:08X}]经度": longitude / 1000000.0,
            f"[{latitude:08X}]纬度": latitude / 1000000.0,
            f"[{utc:08X}]定位时间（UTC）": datetime.fromtimestamp(utc, tz=ZoneInfo("UTC")).strftime('%Y-%m-%d %H:%M:%S')
        }
    }


def parse_tlv_2130(values: bytes) -> Dict:
    mcc, mnc, lac, cell_id, utc_time = struct.unpack(">2s 2s 2s 4s I", values)
    return {
        "LBS数据": {
            "MCC": mcc.hex(),
            "MNC": mnc.hex(),
            "LAC": lac.hex(),
            "CellID": cell_id.hex(),
            "UTC": datetime.fromtimestamp(utc_time, tz=ZoneInfo("UTC")).strftime('%Y-%m-%d %H:%M:%S')
        }

    }


def parse_tlv_20c6(values: bytes) -> Dict:
    """工作模式设置"""
    format_s = ">B B B 4s H 2s 2s 4s I 4s I 4s 4s H H B B"
    (report_mode, delay_receive, agps, reserve1, gps_timeout, s_timer, e_time, reserve2, run_interval, reserve3,
     static_interval, reserve4, reserve5, distance, mileage, nofix, nofix_interval) = struct.unpack(format_s, values)

    work_mode = {
        1: "关闭",
        2: "定时上报",
        3: "直线距离上报",
        4: "里程上报",
        5: "里程或定时上报",
        6: "里程和定时上报"
    }
    return {
        "工作模式参数": {
            "工作模式": work_mode.get(report_mode, f"未知：{report_mode}"),
            "延迟接收（s）": delay_receive,
            "AGPS": "开启" if agps == 2 else "关闭",
            "保留1": reserve1.hex(),
            "定位超时（s）": gps_timeout,
            "开始时间": s_timer.hex(),
            "结束时间": e_time.hex(),
            "保留2": reserve2.hex(),
            f"[{run_interval:08X}]运动上传间隔（s）": run_interval,
            "保留3": reserve3.hex(),
            f"[{static_interval:08X}]静止上传间隔（s）": "不传" if static_interval == 0 else static_interval,
            "保留4": reserve4.hex(),
            "保留5": reserve5.hex(),
            "距离（m）": distance,
            "里程（m）": mileage,
            "不定位上传位置": "开启" if nofix_interval == 2 else "关闭",
            "不定位上传间隔（min）": nofix_interval,

        }
    }


def parse_tlv_240c(values: bytes) -> Dict:
    odo_mileage = struct.unpack(">I", values)[0]

    return {
        f"[{odo_mileage:08X}]里程": f"{odo_mileage}（{odo_mileage / 1000}km）",
    }


def parse_tlv_22a0(values: bytes) -> Dict:
    module_id, ota_result = struct.unpack(">2B", values)
    ota_code = {
        0: "升级成功",
        1: "禁止升级",
        2: "保留",
        3: "设备名称不匹配",
        4: "保留",
        5: "升级包为空文件",
        6: "URL为空",
        7: "下载文件超时",
        8: "连接升级服务器次数超过限制",
        9: "当前状态不允许升级",
        10: "保留",
        11: "读/写文件失败",
        12: "MD5值校验失败"
    }
    return {
        "OTA升级结果": {
            f"[{module_id:02X}]升级类型": "模块" if module_id == 1 else "MCU",
            f"[{ota_result:02X}]状态码": ota_code.get(ota_result, f"未知：{ota_result}")
        }
    }


def parse_tlv_22b4(values: bytes) -> Dict:
    total_len = len(values)
    index = 0

    update_id, dev_name_len = struct.unpack(">2B", values[:2])  # [0:2] 2
    index += 2

    dev_name = struct.unpack(f">{dev_name_len}s", values[index:index + dev_name_len])[0]  # [2:2+4] 6
    index += dev_name_len

    software_version = struct.unpack(">3s", values[index: index + 3])[0]  # [6: 6+3] 9
    index += 3

    delay_time = struct.unpack(">I", values[index: index + 4])[0]  # [9:9+4] 13
    index += 4

    file_size1 = struct.unpack(">I", values[index: index + 4])[0]  # [13:13+4] 17
    index += 4

    url1_len = struct.unpack(">B", values[index: index + 1])[0]  # [17::17+4] 21
    index += 1

    url1 = struct.unpack(f">{url1_len}s", values[index:index + url1_len])[0]  # [21: 21+url1_len]
    index += url1_len

    file_size2, url2_len, url2 = 0, 0, b''
    if total_len > index:
        # 双文件
        file_size2 = struct.unpack(">I", values[index: index + 4])[0]
        index += 4

        url2_len = struct.unpack(f">B", values[index:index + 1])[0]
        index += 1

        url2 = struct.unpack(f">{url2_len}s", values[index:index + url2_len])[0]
        index += url2_len

    if total_len != index:
        raise ValueError(f"0x22b4 内容值解析失败{total_len}!={index}")

    print(total_len == index)

    return {
        "OTA参数": {
            f"[{update_id:02X}]升级类型": "模块" if update_id == 1 else "MCU",
            "设备名称长度": dev_name_len,
            "设备名称": dev_name.decode("utf-8"),
            "软件版本": software_version.hex(),
            "延时时间（s）": delay_time if delay_time else "立即下发",
            "升级文件1大小（byte）": file_size1,
            "url1长度": url1_len,
            "url1": url1.decode("utf-8"),
            "升级文件2大小（byte）": file_size2,
            "url2长度": url2_len,
            "url2": url2.decode("utf-8")
        }
    }


def parse_tlv_2980(values: bytes) -> Dict:
    force_io1 = struct.unpack(">B", values)[0]
    return {
        f"[{force_io1:02x}]断油电": "断油电" if force_io1 == 2 else "恢复油电" if force_io1 == 1 else "未知",
    }


def parse_tlv_2a80(values: bytes) -> Dict:
    (report_num, break_threshold, low_threshold, check_times, break_time, low_time,
     break_offset, low_offset, reserver) = struct.unpack(">B I I B B B B B 4s", values)
    # 0000 0关闭、  0001 1断开、 0010 2低压、 0100 4连接、 0011 3断开+低压、0101 5连接+断开、0110 6低压+连接、0111 7断开+连接+低压
    report_mode = {
        0: "全部关闭",
        1: "只上报外电断开",
        2: "只上报外电连接",
        3: "外电断开+外电低压",
        4: "只上报外电连接",
        5: "外电连接+外电断开",
        6: "外电低压+外电连接",
        7: "全部开启"
    }

    return {
        "外电参数": {
            f"[{report_num}]事件上报": report_mode.get(report_num, f"未知：{report_num}"),
            "断电阈值（mv）": f"{break_threshold}（{break_threshold / 1000:.3f}v）",
            "低压阈值（mv）": f"{low_threshold}（{low_threshold / 1000:.3f}v）",
            "检测频率（s）": check_times,
            "断电持续时间（s）": break_time,
            "低压持续时间（s）": low_time,
            "断电误差电压（mv）": f"{break_offset}（{break_offset / 1000:.3f}v）",
            "低压误差电压（mv）": f"{low_offset}（{low_offset / 1000:.3f}v）",
            "保留": reserver.hex()
        }
    }


TLV_PARSERS_FUN = {
    TLV_230F: parse_tlv_230f,
    TLV_2310: parse_tlv_2310,
    TLV_2400: parse_tlv_2400,
    TLV_2406: parse_tlv_2406,
    TLV_2415: parse_tlv_2415,
    TLV_240C: parse_tlv_240c,
    TLV_24C0: parse_tlv_24c0,
    TLV_2480: parse_tlv_2480,
    TLV_23A3: parse_tlv_23a3,
    TLV_2333: parse_tlv_2333,
    TLV_2391: parse_tlv_2391,
    TLV_2003: parse_tlv_2003,
    TLV_2004: parse_tlv_2004,
    TLV_2005: parse_tlv_2005,
    TLV_2028: parse_tlv_2028,
    TLV_2030: parse_tlv_2030,
    TLV_2031: parse_tlv_2031,
    TLV_2032: parse_tlv_2032,
    TLV_2350: parse_tlv_2350,
    TLV_2095: parse_tlv_2095,
    TLV_20C6: parse_tlv_20c6,
    TLV_2130: parse_tlv_2130,
    TLV_22A0: parse_tlv_22a0,
    TLV_22B4: parse_tlv_22b4,
}


def parse_tlv_unknow(data: bytes) -> Dict:
    return {
        "未知TLV类型": "暂未做解析"
    }


def parse_tlv_stream(data: bytes) -> List:
    tlv_list = []  # 存储解析结果和异常信息
    index = 0  # 当前解析位置索引
    tlv_index = 0  # 当前TLV单元计数

    while index < len(data):
        tlv_index += 1
        current_start = index  # 记录当前TLV单元起始位置
        raw_data_for_this_tlv = None  # 初始化，用于保存出错TLV的原始数据
        length = 0
        try:
            # 1. 检查是否剩余足够的数据读取Tag和Length（共4字节）
            if index + 4 > len(data):
                raise ValueError(f"数据不足以读取Tag和Length（需要4字节，剩余{len(data) - index}字节）")

            # 2. 读取Tag (2字节, 大端序)
            tag = struct.unpack_from('>H', data, index)[0]
            index += 2

            # 3. 读取Length (2字节, 大端序)
            length = struct.unpack_from('>H', data, index)[0]
            index += 2

            # 4. 检查Length值是否合理
            if length < 0:
                raise ValueError(f"Length字段值({length})无效，应为非负整数")
            if length > 1024:  # 设置合理的最大长度限制
                raise ValueError(f"Length字段值({length})超出允许的最大限制(1024字节)")

            # 5. 检查是否剩余足够的数据读取Value
            if index + length > len(data):
                raise ValueError(f"数据不足以读取Value（需要{length}字节，剩余{len(data) - index}字节）")

            # 6. 读取Value
            value = data[index:index + length]
            index += length
            tlv_fun = TLV_PARSERS_FUN.get(tag, parse_tlv_unknow)
            parse_tlv = tlv_fun(value)

            # 7. 计算整个TLV数据块
            raw_tlv_data = data[current_start:index]

            # 8. 将成功解析的结果存入列表
            # tlv_list.append({
            #     'status': 'success',
            #     'tlv_index': tlv_index,
            #     'tag': f"{tag:04X}",
            #     'length': length,
            #     'value': value,
            #     'raw_data': raw_tlv_data.hex()
            # })
            tlv_result = {
                # 'status': 'success',
                # 'tlv_index': tlv_index,
                'tag': f"{tag:04X}",
                'raw_data': raw_tlv_data.hex()
            }
            tlv_result.update(parse_tlv)
            tlv_list.append(tlv_result)

        except Exception as e:
            # 9. 异常处理块
            # 如果在尝试获取原始数据之前就出错了（比如在读取Length时），则尝试抓取尽可能多的原始字节
            if raw_data_for_this_tlv is None:
                # 计算从当前起始位置到数据末尾的剩余字节
                bytes_available = min(4, len(data) - current_start)  # 尝试获取Tag和Length（最多4字节）
                raw_data_for_this_tlv = data[current_start: current_start + bytes_available]

            # 7. 创建异常记录
            error_record = {
                'status': 'error',
                'tlv_index': tlv_index,
                'raw_data': raw_data_for_this_tlv.hex().upper() if raw_data_for_this_tlv else None,
                'offset': current_start,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
            tlv_list.append(error_record)

            # 8. 关键：恢复索引，继续解析下一个TLV
            # 如果已经成功解析了Length，就跳到这个TLV理论上的结束位置
            if 'length' in locals():
                presumed_next_index = current_start + 4 + length
                if presumed_next_index <= len(data):
                    index = presumed_next_index
                else:
                    # 如果理论结束位置超出了数据范围，则跳到末尾
                    index = len(data)
            else:
                # 如果连Length都没读出来，说明数据损坏严重，保守地前进1个字节尝试重新同步
                index = current_start + 1
                if index >= len(data):
                    index = len(data)

            # 打印警告信息（可选，用于实时监控）
            # print(f"警告: 在偏移量 {current_start} 处解析TLV #{tlv_index} 时出错: {e}")
    return tlv_list


def parse_protocol_data(hex_str: str, debug: bool = False) -> Tuple[bool, str, Optional[Dict]]:
    try:
        # 1、转换为字节流
        frame_bytes = hex_to_bytes(hex_str)
        if debug:
            logging.info(f"原始字节流: {frame_bytes.hex().upper()}")
        if len(frame_bytes) < 26:
            return False, "⚠️ 帧长度过短（至少26字节）", None

        # 2、校验起始/结束符
        if frame_bytes[:2] != ZR_FRAME_START_ or frame_bytes[-2:] != ZR_FRAME_END_:
            return False, f"⚠️ 起始/结束符错误（应为0xFFFF/0xDDDD，实际首尾:0x{frame_bytes[:2].hex().upper()}/0x{frame_bytes[-2:].hex().upper()}）", None

        # 去除首尾
        content = frame_bytes[2:-2]
        if debug:
            logging.info(f"去除首尾：{content.hex().upper()}")

        # 包长2+协议版本2+加密1+IMEI10+消息类型2+子包1+消息流水2
        (package_len, protocol_ver, encrypt, imei, msg_type,
         sub_package, msg_serial, msg_body_len) = struct.unpack(">H H B 10s H B H B", content[:21])  # 21byte

        # 3、校验校验码
        checksum = content[-1]
        effective_data = content[:-1]  # 消息长度到消息体内容
        calculated_checksum = calculate_checksum(effective_data)
        if debug:
            logging.info(f"校验码验证: （当前：0x{checksum:02X}, 计算0x{calculated_checksum:02X}）")
        if calculated_checksum != checksum:
            return False, f"⚠️ 校验码错误（当前:0x{checksum:02X}, 计算:0x{calculated_checksum:02X}）", None

        # 4、校验包长（协议版本到校验码）
        package_data_len = len(content[2:])
        if package_len != package_data_len:
            return False, f"⚠️ 包长度错误（当前：0x{package_len:02X}, 计算:0x{package_data_len:02X}）", None

        # 5、校验消息体长
        body_data = content[21:-1]
        if msg_body_len != len(body_data):
            return False, f"⚠️ 消息体长度错误（当前：0x{msg_body_len:02X}, 计算:0x{len(body_data):02X}）", None

        blind_data = msg_serial
        if 0xB1E0 <= msg_serial <= 0xD8EF:
            blind_data = f"{msg_serial}（盲区数据）"

        frame = {
            "包头": "DDDD",
            "包长度": package_len,
            "协议版本": protocol_ver,
            "加密": encrypt,
            "IMEI": imei.hex(),
            "消息类型": msg_type,
            "分包": sub_package,
            f"[{msg_serial:04X}]流水号": blind_data,
            "消息体长度": msg_body_len,
            "消息体": "",
            "校验码": calculated_checksum,
            "包尾": "FFFF"
        }
        # 6、解析消息体
        type_fun = MSG_TYPE_FUNCTION.get(msg_type, default_parse(effective_data, msg_type, frame))
        # 调用对应解析函数
        parse_result = type_fun(body_data)
        frame['消息体'] = parse_result
        return True, "数据合法且解析成功", frame
    except Exception as e:
        return False, f"⚠️ 解析失败：{str(e)}", None


# if __name__ == '__main__':
#     hex_0102 = "dddd008410400000000863998043643668010211d93270230f000103231000080000000000000100203200010124000006544330322d3423a3000468eee425200500080000012b000001fd2028001100020000012c00010300020000000000002350000103209500160059000000db0000066e05ce5fb90119785968eee3ad240c00040024d998ddff"
#     hex_0102_error = "dddd008610400000000863998043643668010211d93272230f000103231000080000000000000100203200010124000006544330322d3423a3000468eee425200500080000012b000001fd2028001100020000012c00010300020000000000002350000103209500160059000000db0000066e05ce5fb90119785968eee3ad240c00040024d9982222DDffff"
#     tc02_0101 = "dddd008b1040000000086399804364366801011102c9772406003d06544330322d34025443800006082d687756312e30301f4547393135552c4547393135554c4141425230354130314d30385f4f4350550645473931355523a3000468eee3e12415002a0308894301035241985463331b00020024d99868eee3ad0000326900000000000000000000000004000061ffff"
#     tc10 = "dddd00bd10400000000860878140506195010211d8f4a9230f0001032310000800000000000001002032000100200600060009ffedfbf93021000231dd2a0100040301010121c000040101011b21e1000e0400011548011349011249011548310000050100010046240000045443313023a30004687af6ef200500080000012b000003612028001100020000012c00010300020000000000002350000103209500160051000000000000003906ca3c5e01587c47687af6ef240c000400000000e1ffff"
#     tc02_gps = "dddd00991040000000086399804364366801021102d585230f000102231000080000000004000000203200010224000006544330322d3423a3000468eef19e20030002009d23330002030920c6002b06050200000000005a00000000000000000000001e000000000000000000000000000000000050003201002095001600dc000000000000068005ce5f77011978c468eef19d240c00040024d99892ffff"
#     tc02_0700 = "dddd0039104000000008639980426996040700113a41252391000312345624c0001a0302012f4c0e3131382e3137382e3137352e3237000000000000a6ffff"
#     tc02_error = "dddd00841040000000086399"
#     tc02_vib = "DDDD00A010400000000860878140506195010211000A8C230F0001052310000800001000000000002032000101200600060054FF99FB73302100022E6F2A0100040301010121C000040101011421E1000E0400011147010F47010F47011048310000050100010000240000045443313023A30004687B53A628800005020032003C209500160077000E00000000003C06CA3C6F01587C8B687B50FD240C000400000000AAFFFF"
#     tc02_ota = "dddd007c1040000000086399804269949707001104d2682391000312345622b4005d010454433032010020000000000001c59e4b687474703a2f2f6c6273757067726164652e6c756e7a2e636e3a383038302f4c42534d616e6167656d656e742f544330322d45552d5632302d6f6c645f313736313631393131322e7061639affff"
#     tc02_0a00 = "dddd002b104000000008639980435518530a011101321724800013054a544d324d0000054a544d324d0000000100dcffff"
#     tc10_22a0 = "dddd00df104000000008608781405060390102110002cb230f00010323100008000000400000000020320001003021000200002a0100040301010121c0000401010112240000045443313023a3000466aa223d22a00002000022b400630004544331300100060000000000006e7851687474703a2f2f6c6273757067726164652e6c756e7a2e636e3a383038302f4c42534d616e6167656d656e742f544331305f4150505f4d44355f7630365f746573745f313732323432353735392e62696e209500160082000100000000003206ca3c3501587c8866aa223d240c00040000000052ffff"
#     tc10_blind = "dddd009910400000000860878140506096010211b7b185230f000102231000080000000004000000203200010024000006544330322d3423a3000467e6489220030002001823330002030820c6002b02000200000000005a00000000000000000000000100000000000000000000000000000000003c003201012095001600450000009b0000003d06ca3c8b01587c4b67e64891240c000400000000bbffff"
#
#     is_valid, msg, r = parse_protocol_data(hex_str=tc10_blind, debug=True)
#     logging.info(f"结果: {msg}")
#     if is_valid:
#         import json
#
#         logging.info("解析结果:")
#
#         logging.info(json.dumps(r, ensure_ascii=False, indent=2))

