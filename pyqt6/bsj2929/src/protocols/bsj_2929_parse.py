import logging
import re
import struct
from typing import Tuple, Optional, Dict, List

# 配置日志：级别为DEBUG（显示所有级别），格式包含时间、级别、消息
logging.basicConfig(
    level=logging.INFO,  # 日志级别：DEBUG < INFO < WARNING < ERROR < CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s',  # 格式
    datefmt='%Y-%m-%d %H:%M:%S'  # 时间格式
)

GROUPS = {
    141: 141,
    161: 145,
    171: 139,
    191: 143
}
GROUPS2 = {
    125: 141,
    161: 145,
    171: 139,
    191: 143
}

# ------------------------------
# 2929协议常量
# ------------------------------
D04_START = 0x2929  # 包头
D04_END = 0x0D  # 包尾

# ------------------------------
# 主信令常量
# ------------------------------
MAIN_SIGNAL_PLATFORM_RESPONSE = 0x21  # 平台通用应答
MAIN_SIGNAL_DEVICE_RESPONSE = 0x85  # 设备通用应答
MAIN_SIGNAL_LOCATION_REPORT = 0x80  # 设备位置上报
MAIN_SIGNAL_REQUEST_PARSE_WIFI = 0xD9  # 设备请求解析wifi
MAIN_SIGNAL_REQUEST_PARSE_WIFI_RESPONSE = 0x22  # 平台应答0xD9
MAIN_SIGNAL_REQUEST_PARAMS_CONFIG = 0xD8  # 设备请求参数配置
MAIN_SIGNAL_PLATFORM_PARAMS_CONFIG = 0X3A  # 平台下发参数
MAIN_SIGNAL_BLIND_SPOT_REPORT = 0x8E  # 盲区上报
MAIN_SIGNAL_OTA_UPDATE_DISTRIBUTE = 0x3B  # 平台下发OTA升级
MAIN_SIGNAL_OTA_UPDATE_DISTRIBUTION_RESPONSE = 0x86  # 平台应答0x3B
MAIN_SIGNAL_OTA_UPDATE_RESULT_REPORT = 0xDB  # OTA升级结果上报

# ------------------------------
# 扩展数据指令常量
# ------------------------------
EXTEND_DATA_4G_STATION = 0x00D8
EXTEND_DATA_BATTERY_VOLTAGE = 0x0004
EXTEND_DATA_BATTERY_LEVEL_COUNT = 0x0008
EXTEND_DATA_SOFTWARE_VERSION = 0x00A3
EXTEND_DATA_TERMINAL_MODEL = 0x00A5
EXTEND_DATA_WIFI_POINTS = 0x00B9
EXTEND_DATA_ALARM1 = 0x0089
EXTEND_DATA_ALARM2 = 0x00C5
EXTEND_DATA_ICCID = 0x00B2
EXTEND_DATA_GPS_COUNT = 0x00B7
EXTEND_DATA_IMEI = 0x00D5
EXTEND_DATA_WORK_MODE = 0x00AE


def format_hex(hex_str: str, group_size=2) -> str:
    # 去除空格
    hex_str1 = hex_str.replace(" ", "")
    # 分组
    groups = [hex_str1[i:i + group_size] for i in range(0, len(hex_str1), group_size)]
    # 空格连接分组
    return ' '.join(groups).upper()


def hex_to_formatted_binary(hex_str: str):
    """16进制字符串转二进制"""
    # 16进制转整数
    num = int(hex_str, 16)
    # 计算16进制转二进制的长度（1个16进制=4位二进制）
    total_bits = len(hex_str) * 4
    # 整数转二进制字符串，并填充指定长度（2开始，去掉"0b"前缀）
    bin_str = bin(num)[2:].zfill(total_bits)
    # 每4位分组，组间添加空格
    return ' '.join([bin_str[i:i + 4] for i in range(0, len(bin_str), 4)])


def parse_main_signal_21(content_data: bytes) -> dict:
    """解析中心确认包（主信令=0x21）"""
    logging.info(content_data.hex())
    if len(content_data) != 3:
        raise ValueError(f"0x21包内容长度错误，预期3个字节，实际{len(content_data)}个字节")
    rec_checksum, rec_main_signal, rec_sub_signal = struct.unpack(">B 1s 1s", content_data)
    return {
        "msg_type": "中心确认包",
        f'[{rec_checksum:02X}]收到的数据包校验值': rec_checksum,
        f'[{rec_main_signal.hex()}]收到的包-主信令': rec_main_signal.hex(),
        f'[{rec_sub_signal.hex()}]收到的包-子信令': rec_sub_signal.hex()
    }


def parse_main_signal_85(content_data: bytes) -> dict:
    """解析车载终端确认包（主信令=0x85）"""
    if len(content_data) != 34:
        raise ValueError(f"0x85包内容长度必须是34个字节，实际为{len(content_data)}个字节")
    result = parse_location_data(content_data)
    return {
        "msg_type": "车载终端确认包",
        "内容": result
    }


def parse_main_signal_80(content_data: bytes) -> dict:
    """解析一般位置数据包（主信令=0x80）"""
    data_len = len(content_data)
    if data_len < 34:
        raise ValueError(f"0x80包内容长度至少34个字节，实际为{data_len}个字节")
    location_parsed = parse_location_data(content_data[0:34])

    extend_data = content_data[34:]

    eb_parsed = parse_extend_data(extend_data)

    return {
        "msg_type": "一般位置数据包",
        "位置数据": location_parsed,
        "扩展数据": eb_parsed
    }


def add_colons(s):
    """将12位十六进制字符串按每2位添加冒号"""
    # 按每2个字符分割，再用冒号连接
    return ':'.join([s[i:i + 2] for i in range(0, len(s), 2)])


def parse_main_signal_d9(content_data: bytes) -> dict:
    """解析设备请求wifi解析包（主信令=0xD9）"""
    if len(content_data) < 7:
        raise ValueError(f"0xD9包内容长度至少为7个字节，当前{len(content_data)}个字节")
    wifi_num = struct.unpack(">B", content_data[0:1])[0]
    wifi_group_num = len(content_data) // 6
    if wifi_num != wifi_group_num:
        raise ValueError(f"wifi数量个数{wifi_num}和wifi热点组数{wifi_group_num}不一致")
    wifi_groups_b = content_data[1:]
    wifi_list = [wifi_groups_b[i:i + 6] for i in range(0, len(wifi_groups_b), 6)]
    wifi_groups = [add_colons(item.hex()) for item in wifi_list]
    logging.info(wifi_groups)

    return {
        "msg_type": "设备请求wifi解析包",
        "value": content_data.hex(),
        "WiFi热点数据": {
            f"[{wifi_num:02X}]WiFi数量": wifi_num,
            "热点列表": wifi_groups,
        }
    }


def parse_main_signal_22(content_data: bytes) -> dict:
    """解析设备请求wifi解析的应答（主信令=0x22）"""
    if len(content_data) != 8:
        raise ValueError(f"0x22包内容长度应8个字节，实际{len(content_data)}个字节")
    lat_b = content_data[0:4].hex()
    # lat_str = bcd_to_string(lat_b)
    lat = handle_latitude(lat_b)

    long_b = content_data[4:8]
    # long_str = bcd_to_string(long_b)
    long = handle_longtitude(long_b)

    return {
        "msg_type": "设备请求wifi解析应答包",
        "value": content_data.hex(),
        "纬度": lat,
        "经度": long
    }


def parse_main_signal_d8(content_data: bytes) -> dict:
    """解析设备请求参数配置（主信令=0xD8）"""
    return {
        "msg_type": "设备请求参数配置包",
        "内容": None if len(content_data) == 0 else content_data.hex(),
    }


def parse_main_signal_3a(content_data: bytes) -> dict:
    """解析平台下发参数配置（主信令=0x3A）"""
    if len(content_data) > 240:
        raise ValueError(f"0x3A包内容长度不能超过240个字节，当前{len(content_data)}个字节")
    content = content_data.decode("ascii", errors="ignore")

    return {
        "msg_type": "下发调度文本信息包",
        "文本信息": content
    }


def parse_main_signal_8e(content_data: bytes) -> dict:
    """解析盲区数据包（主信令=0x8E）"""
    data_len = len(content_data)
    if data_len < 34:
        raise ValueError(f"0x80包内容长度至少34个字节，实际为{data_len}个字节")
    location_parsed = parse_location_data(content_data[0:34])

    extend_data = content_data[34:]

    eb_parsed = parse_extend_data(extend_data)

    return {
        "msg_type": "盲区数据包",
        "位置数据": location_parsed,
        "扩展数据": eb_parsed
    }


def parse_main_signal_3b(content_data: bytes) -> dict:
    """解析平台OTA指令下发（主信令=0x3A）"""
    command_str = content_data.decode("utf-8")
    split_list = command_str.split(";")
    command_list = [item for item in split_list if item]  # 去除前后的空列表元素
    result_dict = {}
    for item in command_list:
        # 用 split(':') 分割，指定 maxsplit=1 避免值中含冒号时出错
        key, value = item.split(':', 1)  # 只分割第一个冒号
        result_dict[key] = value
    return {
        "msg_type": "平台OTA指令下发包",
        "value": content_data.hex(),
        "OTA指令": command_str,
        "OTA指令详情": result_dict
    }


def parse_main_signal_86(content_data: bytes) -> dict:
    """解析设备应答平台OTA指令下发（主信令=0x86）"""
    data_len = len(content_data)
    if data_len != 34:
        raise ValueError(f"0x80包内容长度应为34个字节，实际为{data_len}个字节")
    location_parsed = parse_location_data(content_data)

    return {
        "msg_type": "平台OTA指令下发应答包",
        "位置数据": location_parsed
    }


def parse_main_signal_db(content_data: bytes) -> dict:
    """解析设备上报OTA升级结果包（主信令=0xdb）"""
    if len(content_data) != 2:
        raise ValueError(f"0xDB包内容长度应为2个字节，当前{len(content_data)}个字节")
    module_type, ota_result = struct.unpack(">B B", content_data[:2])

    return {
        "msg_type": "设备上报OTA升级结果包",
        f"[{content_data.hex()}]升级结果": {
            f"[{module_type:02x}]类型": "通讯模块" if module_type == 1 else "单片机",
            f"[{ota_result:02x}]结果": "成功" if ota_result == 0 else "失败"
        }
    }


def parse_default(content_data: bytes):
    """解析未知的主信令"""
    return True, "消息合法，但未实现主信令解析", content_data.hex()


MAIN_SIGNAL = {
    MAIN_SIGNAL_PLATFORM_RESPONSE: parse_main_signal_21,
    MAIN_SIGNAL_DEVICE_RESPONSE: parse_main_signal_85,
    MAIN_SIGNAL_LOCATION_REPORT: parse_main_signal_80,
    MAIN_SIGNAL_REQUEST_PARSE_WIFI: parse_main_signal_d9,
    MAIN_SIGNAL_REQUEST_PARSE_WIFI_RESPONSE: parse_main_signal_22,
    MAIN_SIGNAL_REQUEST_PARAMS_CONFIG: parse_main_signal_d8,
    MAIN_SIGNAL_PLATFORM_PARAMS_CONFIG: parse_main_signal_3a,
    MAIN_SIGNAL_BLIND_SPOT_REPORT: parse_main_signal_8e,
    MAIN_SIGNAL_OTA_UPDATE_DISTRIBUTE: parse_main_signal_3b,
    MAIN_SIGNAL_OTA_UPDATE_DISTRIBUTION_RESPONSE: parse_main_signal_86,
    MAIN_SIGNAL_OTA_UPDATE_RESULT_REPORT: parse_main_signal_db

}


def parse_extend_d8(values: bytes) -> Dict:
    """解析4G单基站（命令=0x000B 0x00D8）"""
    if len(values) != 9:
        raise ValueError(f"扩展-4G单基站内容长度应9个字节，实际{len(values)}个字节")
    mcc, mnc, ceil, station = struct.unpack(">H B 2s 4s", values)

    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EXTEND_DATA_4G_STATION:04X}]扩展指令": EXTEND_DATA_4G_STATION,
        f"[{values.hex()}]4G基站": {
            f"[{mcc:04X}]MCC": mcc,
            f"[{mnc:02X}]MNC": mnc,
            f"[{ceil.hex()}]ceil": ceil.hex(),
            f"[{station.hex()}]station": station.hex()
        }
    }


def parse_extend_04(values: bytes) -> Dict:
    """解析电池电压（命令=0x0005 0x0004）"""
    if len(values) != 3:
        raise ValueError(f"扩展-电池电压内容长度应3个字节，实际{len(values)}个字节")
    bat_val = f"{int(values.hex()) / 100000.0:.5f}"
    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EXTEND_DATA_BATTERY_VOLTAGE:04X}]扩展指令": EXTEND_DATA_BATTERY_VOLTAGE,
        f"[{values.hex()}]电池电压": f"{bat_val}V"
    }


def parse_extend_08(values: bytes) -> Dict:
    """解析电量条数（命令=0x0004 0x0008）"""
    if len(values) != 2:
        raise ValueError(f"扩展-电量条数内容长度应2个字节，实际{len(values)}个字节")
    rest_quantity = struct.unpack(">H", values)[0]
    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EXTEND_DATA_BATTERY_LEVEL_COUNT:04X}]扩展指令": EXTEND_DATA_BATTERY_LEVEL_COUNT,
        f"[{rest_quantity:04X}]电量剩余条数": {
            "满条数": 1500,
            "剩余条数": rest_quantity,
            "已用条数": 1500 - rest_quantity
        }
    }


def parse_extend_a3(values: bytes) -> Dict:
    """解析软件版本（命令=0x0016 0x00A3）"""
    if len(values) != 20:
        raise ValueError(f"扩展-软件版本内容长度应20个字节，实际{len(values)}个字节")
    version = values.decode("UTF-8", errors="ignore")
    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EXTEND_DATA_SOFTWARE_VERSION:04X}]扩展指令": EXTEND_DATA_SOFTWARE_VERSION,
        "软件版本": version
    }


def parse_extend_a5(values: bytes) -> Dict:
    """解析终端型号（命令=0x0006 0x00A5）"""
    if len(values) != 4:
        raise ValueError(f"扩展-终端型号内容长度应4个字节，实际{len(values)}个字节")
    terminal_code = struct.unpack(">I", values)[0]
    terminal_model = {
        220: "AG-18",
        27: "A5D-1W"
    }

    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EXTEND_DATA_TERMINAL_MODEL:04X}]扩展指令": EXTEND_DATA_TERMINAL_MODEL,
        f"[{terminal_code:08X}]终端型号": {
            "代码": terminal_code,
            "型号": terminal_model.get(terminal_code, "未知")
        },
    }


def parse_extend_b9(values: bytes) -> Dict:
    """解析WiFi热点信息（命令=0x00XX 0x00B9）"""
    # 总字节长度N，命令长度2，内容长度=热点数长度1+热点数内容长度X（N = 2 + 1 + X）
    if len(values) < 1:
        raise ValueError(f"扩展-WiFi信息点内容长度最少1个字节，实际{len(values)}个字节")
    wifi_num = struct.unpack(">B", values[0:1])[0]
    # num = int.from_bytes(values[0:1], "big")

    if wifi_num != 0:
        mac_len = 22 * wifi_num - 1
        if len(values) - 1 != mac_len:
            raise ValueError(f"mac地址长度错误，mac长度应为{mac_len}个字节,实际{len(values) - 1}个字节")
        wifi_str = values[1:].decode("UTF-8", errors="ignore")
        wifi_list = wifi_str.split(",")
        mac_list = [','.join(wifi_list[i:i + 2]) for i in range(0, len(wifi_list), 2)]
        # mac_list1 = [item for item in mac_list of item]
    else:
        mac_list = []

    if wifi_num != len(mac_list):
        raise ValueError(f"热点数量和mac个数不等，热点数：{wifi_num},mac数：{len(mac_list)}")
    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EXTEND_DATA_WIFI_POINTS:04X}]扩展指令": EXTEND_DATA_WIFI_POINTS,
        "WiFi热点信息": {
            "value": values.hex(),
            "热点数": wifi_num,
            "热点列表": mac_list if mac_list else None
        }
    }


def parse_extend_89(values: bytes) -> Dict:
    """解析扩展报警状态位 1（命令=0x0006 0x0089）"""
    if len(values) != 4:
        raise ValueError(f"扩展-扩展报警状态位1内容长度应4个字节，实际{len(values)}个字节")
    alarm1 = struct.unpack(">I", values)[0]
    bit12 = (alarm1 >> 12) & 0x1  # bit12: 1-正常, 0-拆除报警

    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EXTEND_DATA_ALARM1:04X}]扩展指令": EXTEND_DATA_ALARM1,
        f"[{alarm1:08X}]扩展报警状态位1": {
            "binary": hex_to_formatted_binary(values.hex()),
            f"[bit12]拆除报警": '正常' if bit12 else '触发拆除报警'
        }
    }


def parse_extend_c5(values: bytes) -> Dict:
    """解析扩展报警状态位 2（命令=0x0006 0x00C5）"""
    if len(values) != 4:
        raise ValueError(f"扩展-扩展报警状态位2内容长度应4个字节，实际{len(values)}个字节")
    alarm2 = struct.unpack(">I", values)[0]
    bit3_4 = (alarm2 >> 3) & 0x03
    bit12 = (alarm2 >> 12) & 0x1
    bit14 = (alarm2 >> 14) & 0x1
    bit19_20 = (alarm2 >> 19) & 0x3

    position_state = "不定位" if bit3_4 == 0 else "GPS定位" if bit3_4 == 1 else "WiFi定位"

    gps_power_state = "未强开" if bit12 else "强开"

    real_time_light_state2 = "不见光" if bit14 else "见光报警"

    position_mode = "双模" if bit19_20 == 0 else "单GPS" if bit19_20 == 1 else "单北斗"

    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EXTEND_DATA_ALARM2:04X}]扩展指令": EXTEND_DATA_ALARM2,
        f"[{alarm2:08X}]扩展报警状态位2": {
            "binary": hex_to_formatted_binary(values.hex()),
            f"[bit3~bit4]定位状态": position_state,
            f"[bit12]GPS电源": gps_power_state,
            f"[bit14]实时见光状态2": real_time_light_state2,
            f"[bit19~bit20]定位模式": position_mode
        }
    }


def parse_extend_b2(values: bytes) -> Dict:
    """解析上传ICCID（命令=0x000C 0x00B2）"""
    if len(values) != 10:
        raise ValueError(f"扩展-ICCID内容长度应10个字节，实际{len(values)}个字节")

    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EXTEND_DATA_ICCID:04X}]扩展指令": EXTEND_DATA_ICCID,
        "ICCID": values.hex()
    }


def parse_extend_b7(values: bytes) -> Dict:
    """解析GPS星数（命令=0x0004 0x00B7）"""
    if len(values) != 2:
        raise ValueError(f"扩展-GPS星数内容长度应2个字节，实际{len(values)}个字节")
    signal_level, gps_used_num = struct.unpack(">2B", values)

    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EXTEND_DATA_GPS_COUNT:04X}]扩展指令": EXTEND_DATA_GPS_COUNT,
        f"[{values.hex().upper()}]GPS星数": {
            f"[{signal_level:02X}]信号强度": "强" if signal_level > 20 else "中" if signal_level > 10 else "弱",
            f"[{gps_used_num:02X}]GPS使用星数": gps_used_num,
        }
    }


def parse_extend_d5(values: bytes) -> Dict:
    """解析IMEI（命令=0x0011 0x00D5）"""
    if len(values) != 15:
        raise ValueError(f"扩展-IMEI内容长度应15个字节，实际{len(values)}个字节")
    imei = values.decode("ASCII", errors="ignore")

    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EXTEND_DATA_IMEI:04X}]扩展指令": EXTEND_DATA_IMEI,
        f"IMEI": imei
    }


def parse_extend_ae(values: bytes) -> Dict:
    """解析设备当前模式和唤醒时间上传（命令=0x00XX 0x00AE）"""
    mp_len = len(values)
    m = struct.unpack(f">B", values[0:1])[0]
    p = values[1:]
    p_len = len(p)

    match m:
        case 0x01:  # 闹钟模式 01 1200,1213,1111,2359
            if mp_len > 8:
                raise ValueError(f"闹钟模式最多为4组，最多8个字节，当前{mp_len}个字节")
            elif p_len % 2 != 0:
                raise ValueError(f"闹钟模式内容长度必须是偶数，当前{p_len}个字节")
            else:
                clock_mode = ["".join(p[i:i + 4].hex()) for i in range(0, p_len, 4)]
                work_mode = {
                    f"[{m:02X}]模式": "闹钟模式",
                    f"[{p.hex()}]时间点": clock_mode
                }

        case 0x03:  # 定位定位模式 03 001F
            if mp_len != 3:
                raise ValueError(f"定时定位模式内容应为3个字节，当前{p_len}个字节")
            time_mode = struct.unpack(">H", p)[0]
            work_mode = {
                f"[{m:02X}]模式": "定时模式",
                f"[{time_mode:04X}]时间（min）": time_mode
            }
        case 0x04:  # 星期模式 04 01 5 0102030405 0900
            week_switch, week_num = struct.unpack(">2B", p[:2])
            weeks, time = struct.unpack(f">{week_num}s 2s", p[2:])
            weeks = ["".join(weeks[i:i + 1].hex()) for i in range(0, len(weeks), 1)]
            # print(week_switch, week_num, weeks, time)
            work_mode = {
                f"[{m:02X}]模式": "星期模式",
                f"[{p.hex()}]唤醒时间": {
                    "开关": '开' if week_switch else '关',
                    "星期个数": week_num,
                    "星期": weeks,
                    "时间点": time.hex()
                }
            }
        case _:
            work_mode = {
                f"[{m:02X}]模式": "未知",
                f"[{p.hex()}]时间": "未知"
            }

    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EXTEND_DATA_WORK_MODE:04X}]扩展指令": EXTEND_DATA_WORK_MODE,
        f"[{values.hex()}]工作模式": work_mode
    }


EXTEND_PARSERS = {
    EXTEND_DATA_4G_STATION: parse_extend_d8,
    EXTEND_DATA_BATTERY_VOLTAGE: parse_extend_04,
    EXTEND_DATA_BATTERY_LEVEL_COUNT: parse_extend_08,
    EXTEND_DATA_SOFTWARE_VERSION: parse_extend_a3,
    EXTEND_DATA_TERMINAL_MODEL: parse_extend_a5,
    EXTEND_DATA_WIFI_POINTS: parse_extend_b9,
    EXTEND_DATA_ALARM1: parse_extend_89,
    EXTEND_DATA_ALARM2: parse_extend_c5,
    EXTEND_DATA_ICCID: parse_extend_b2,
    EXTEND_DATA_GPS_COUNT: parse_extend_b7,
    EXTEND_DATA_IMEI: parse_extend_d5,
    EXTEND_DATA_WORK_MODE: parse_extend_ae
}


def handle_latitude(hex_value: str):
    # 处理输入为32位整数（跳过字符串处理，直接传整数效率更高）
    if isinstance(hex_value, str):
        hex_value = int(hex_value.replace("0x", ""), 16)

    # 1. 提取符号位（最高位）
    sign_bit = (hex_value >> 31) & 1
    direction = "N" if sign_bit == 0 else "S"

    # 2. 提取4字节BCD数据（清除符号位）
    bcd = hex_value & 0x7FFFFFFF  # 保留低31位（实际有效为32位中的低32位，符号位已分离）

    # 3. 直接按字节拆分并计算（4个字节：b0 b1 b2 b3，大端模式）
    b0 = (bcd >> 24) & 0xFF  # 第1个字节（高8位）
    b1 = (bcd >> 16) & 0xFF  # 第2个字节
    b2 = (bcd >> 8) & 0xFF  # 第3个字节
    b3 = bcd & 0xFF  # 第4个字节（低8位）

    # 4. 压缩BCD转十进制（每个字节拆分为两个数字，高4位*10 + 低4位）
    # 示例0x02232556的字节为：b0=0x02, b1=0x23, b2=0x25, b3=0x56
    degrees = ((b0 & 0x0F) * 10) + ((b1 >> 4) & 0x0F)  # 0x02的低4位=2，0x23的高4位=2 → 2*10+2=22
    minutes_int = ((b1 & 0x0F) * 10) + ((b2 >> 4) & 0x0F)  # 0x23低4位=3，0x25高4位=2 → 3*10+2=32
    minutes_dec = ((b2 & 0x0F) * 100) + ((b3 >> 4) * 10) + (b3 & 0x0F)  # 0x25低4=5，0x56高4=5，低4=6 → 5*100+5*10+6=556

    # 5. 组合结果
    minutes = minutes_int + minutes_dec / 1000.0
    latitude = degrees + minutes / 60.0
    if sign_bit:
        latitude = -latitude

    return f"{degrees}°{minutes:.3f}'{direction}（{latitude}）"


def handle_longtitude(hex_value: bytes):
    # 处理输入（优先接受整数，字符串自动转换）
    # if isinstance(hex_value, str):
    #    hex_value = int(hex_value.replace("0x", ""), 16)

    hex_value = int.from_bytes(hex_value, byteorder="big")
    # 1. 提取符号位（32位最高位）
    sign_bit = (hex_value >> 31) & 1
    direction = "E" if sign_bit == 0 else "W"

    # 2. 提取BCD数据（清除符号位）
    bcd = hex_value & 0x7FFFFFFF

    # 3. 拆分4个字节（大端模式：b0-b3依次为高到低字节）
    b0 = (bcd >> 24) & 0xFF  # 第1个字节（最高位字节）
    b1 = (bcd >> 16) & 0xFF  # 第2个字节
    b2 = (bcd >> 8) & 0xFF  # 第3个字节
    b3 = bcd & 0xFF  # 第4个字节（最低位字节）

    # 4. 压缩BCD转十进制（每个字节高4位*10 + 低4位）
    # 示例0x11405281的字节：b0=0x11, b1=0x40, b2=0x52, b3=0x81
    degrees = (
            ((b0 >> 4) & 0x0F) * 100 +  # 0x11高4位=1 → 1*100
            ((b0 & 0x0F) * 10) +  # 0x11低4位=1 → 1*10
            ((b1 >> 4) & 0x0F)  # 0x40高4位=4 → 4 → 总和114
    )
    minutes_int = (
            ((b1 & 0x0F) * 10) +  # 0x40低4位=0 → 0*10
            ((b2 >> 4) & 0x0F)  # 0x52高4位=5 → 5 → 总和05
    )
    minutes_dec = (
            ((b2 & 0x0F) * 100) +  # 0x52低4位=2 → 2*100
            ((b3 >> 4) & 0x0F) * 10 +  # 0x81高4位=8 → 8*10
            (b3 & 0x0F)  # 0x81低4位=1 → 1 → 总和281
    )

    # 5. 组合结果（1度=60分）
    minutes = minutes_int + minutes_dec / 1000.0
    longitude = degrees + minutes / 60.0
    if sign_bit:
        longitude = -longitude  # 西经为负值

    return f"{degrees}°{minutes:.3f}'{direction}（{longitude}）"


def parse_location_data(data: bytes) -> dict:
    """解析位置数据，34 byte"""

    # 解析时间
    time_bcd = data[0:6]  # 6字节BCD时间（YYMMDDHHMMSS）
    time_str = bcd_to_str(time_bcd)
    try:
        time_formatted = f"20{time_str[:2]}-{time_str[2:4]}-{time_str[4:6]} " \
                         f"{time_str[6:8]}:{time_str[8:10]}:{time_str[10:12]}"
    except ValueError as e:
        time_formatted = f"{str(e)},无效时间格式({time_str})"

    # 经、纬度 4字节BCD编码
    latitude = data[6:10].hex()
    lat = handle_latitude(latitude)

    longitude = data[10:14]
    lon = handle_longtitude(longitude)

    speed, direction, T, LLL = struct.unpack(">2s 2s B 3s", data[14:22])
    speed_v = int(bcd_to_string(speed.hex()))
    direction_v = int(bcd_to_string(direction.hex()))

    # T：定位，天线，电源状态 F8（1111 1000）
    position_flag = (T >> 7) & 0x1  # bit7
    gps_antenna_state = (T >> 5) & 0x3  # bit5~bit6
    power_state = (T >> 3) & 0x3  # bit3~bit4
    login_sign = T & 0x7  # bit0~bit2~bit3

    # LLL：里程数3个字节，未用到，预留0
    mileage = int.from_bytes(LLL, byteorder="big")

    # ABCD：车辆状态，共4个字节
    A, B, C, D = struct.unpack(">1s 2B 1s", data[22:26])

    # B
    reserve_d4_7 = (B >> 4) & 0x0F
    real_time_light_state1 = (B >> 3) & 0x1
    reserve_d2 = (B >> 2) & 0x1
    gprs_state = (B >> 1) & 0x1
    terminal_dial = (B >> 0) & 0x1

    # C
    gprs_register = (C >> 7) & 0x1
    distribute_21 = (C >> 6) & 0x1
    communication_methods = (C >> 5) & 0x1
    csq_state = C & 0x1F

    # WWERTYU：（终端未用到,各1个字节），I:应答中心下发的主命令1个字节
    WWERTYU, i = struct.unpack(">7s B", data[26:])

    return {
        "Values": data.hex(),
        f"[{time_str}]定位时间": time_formatted,
        f"[{latitude}]纬度": lat,
        f"[{longitude.hex()}]经度": lon,
        f"[{speed.hex()}]速度（未使用）": speed_v,
        f"[{direction.hex()}]方向": direction_v,
        f"[{T:02X}]定位，天线，电源状态": {
            f"binary": hex_to_formatted_binary(f"{T:02X}"),
            f"D7[{position_flag}]定位标志": "GPS已定位" if position_flag else "GPS未定位",
            f"D5D6[{bin(gps_antenna_state)[2:].zfill(2)}]GPS天线（未使用）": "正常（默认1）" if gps_antenna_state else "不正常",
            f"D3D4[{bin(power_state)[2:].zfill(2)}]电源状态": "正常" if power_state else "电池电量低于2V",
            f"D0~D2[{bin(login_sign)[2:].zfill(3)}]登签ID（未使用）": f"{login_sign}（默认0）"
        },
        f"[{LLL.hex()}]里程（未用到）": f"{mileage}（预留0）",
        "车辆状态": {
            "ABCD": format_hex(data[22:26].hex()),
            f"[{A.hex()}]A（未用到）": A.hex(),
            f"[{B:02X}]B": {
                "Binary": hex_to_formatted_binary(f"{B:02X}"),
                f"D4~D7[{reserve_d4_7:04x}]（未使用）": reserve_d4_7,
                f"D3[{real_time_light_state1}]实时见光状态1": '见光' if real_time_light_state1 else '正常-不见光',
                f"D2[{reserve_d2}]保留": reserve_d2,
                f"D1[{gprs_state}]GPRS上线状态": '未上线' if gprs_state else '已上线',
                f"D0[{terminal_dial}]终端拨号状态": '未成功' if terminal_dial else '成功'
            },
            f"[{C:02X}]C": {
                "Binary": hex_to_formatted_binary(f"{C:02X}"),
                f"D7[{gprs_register}]GPRS注册": '未注册' if gprs_register else '已注册',
                f"D6[{distribute_21}]中心下发21应答指令": '应下发指令' if distribute_21 else '不需下发',
                f"D5[{communication_methods}]通讯方式": '未知' if communication_methods else 'UDP',
                f"D0~D4[{csq_state:04X}]CSQ值": csq_state
            },
            f"[{D.hex().upper()}]D（未用到）": D.hex(),
            "WWERTYU（未用到）": WWERTYU.hex(),
            f"[{i:02x}]I应答中心下发的主命令": '非主动发送' if i else '主动发送'
        }
    }


def parse_extend_data(extend_data: bytes) -> List[Dict]:
    """解析扩展数据"""
    ex_list = []
    index = 0
    total_len = len(extend_data)

    while index < total_len:
        # 扩展字段总长，2个字节
        if index + 2 > total_len:
            # 剩余字符不足4个，无法读取长度,退出循环
            break
        ex_length = struct.unpack(">H", extend_data[index:index + 2])[0]
        index += 2

        # 命令字，2个字节
        if index + 2 > total_len:
            raise ValueError(f"扩展命令字长度错误，index={index}，数据总长{total_len}字节")
        ex_command = struct.unpack(">2s", extend_data[index:index + 2])[0]
        ex_command_hex = ex_command.hex()
        index += 2

        # 扩展内容，（总长-2）字节
        ex_content_len = ex_length - 2
        if index + ex_content_len > total_len:
            raise ValueError(
                f"扩展内容截取错误，eb_length={ex_length},command={ex_command_hex},index={index + ex_content_len}，数据总长{total_len}字节")
        ex_content = struct.unpack(f">{ex_content_len}s", extend_data[index:index + ex_content_len])[0]
        index += ex_content_len

        command_value = int.from_bytes(ex_command, "big")

        if command_value in EXTEND_PARSERS:
            try:
                ex_part = EXTEND_PARSERS[command_value](ex_content)
                ex_list.append(ex_part)
            except Exception as e:
                ex_list.append({
                    "type": f"扩展解析错误(0x{ex_command_hex})",
                    "eb_command": f"0x{ex_command_hex}",
                    "error": str(e),
                    "value": ex_content.hex()
                })
        else:
            ex_list.append({
                "type": "未知扩展数据类型",
                "tlv_type": f"0x{ex_command_hex}",
                "eb_command": ex_command_hex,
                "value": ex_content.hex()
            })

    return ex_list


def bcd_to_str(bcd_bytes: bytes) -> str:
    """BCD码转字符串（如终端手机号）"""
    # return "".join(f"{b:02x}" for b in bcd_bytes).upper()
    # bcd_bytes = bytes.fromhex(hex_str)  # b'\x12\x34'
    result = []
    for b in bcd_bytes:
        high = (b >> 4) & 0x0F  # 高4位：0x1 → 1；0x3 → 3
        low = b & 0x0F  # 低4位：0x2 → 2；0x4 → 4
        result.append(f"{high}{low}")
    result = ''.join(result)  # 结果："1234"（看似相同，逻辑完全不同）
    return result


def bcd_to_string(hex_str: str) -> str:
    """将压缩BCD编码的16进制字符串转换为十进制数字字符串"""
    # 预处理：移除0x前缀，确保小写，检查长度为偶数
    hex_clean = hex_str.lower().replace("0x", "").strip()
    if len(hex_clean) % 2 != 0:
        raise ValueError("压缩BCD的16进制字符串长度必须为偶数")

    result = []
    # 每2个字符（1个字节）处理一次
    for i in range(0, len(hex_clean), 2):
        # 取1个字节的16进制字符串（如"11"）
        byte_hex = hex_clean[i:i + 2]
        # 转换为整数（0x11 → 17）
        byte_val = int(byte_hex, 16)
        # 高4位 → 第一个数字（17 >> 4 = 1 → "1"）
        high_digit = (byte_val >> 4) & 0x0F
        # 低4位 → 第二个数字（17 & 0x0F = 1 → "1"）
        low_digit = byte_val & 0x0F

        # 验证是否为有效BCD数字（0-9）
        if not (0 <= high_digit <= 9 and 0 <= low_digit <= 9):
            raise ValueError(f"无效的BCD编码：{byte_hex}（包含非十进制数字）")

        # 追加到结果
        result.append(str(high_digit))
        result.append(str(low_digit))

    return ''.join(result)


def hex_to_bytes(content: str) -> bytes:
    """十六进制字符串转字节流（处理空格）"""
    # 正则模式：可选前缀0x/0X，后面跟1个以上的16进制字符
    hex_pattern = re.compile(r'^0x[0-9a-fA-F]+$|^[0-9a-fA-F]+$')
    # 完全匹配则返回True，否则False
    hex_flag = bool(hex_pattern.fullmatch(content))
    if not hex_flag:
        raise ValueError("输入的内容不是16进制数据")
    hex_str = content.replace(" ", "").strip()
    if len(hex_str) % 2 != 0:
        raise ValueError("十六进制字符串长度必须为偶数")
    return bytes.fromhex(hex_str)


def calculate_checksum(data: bytes) -> int:
    """
    计算校验位
    :param data: 从包头开始到内容结束，异或
    :return: 整数
    """
    checksum = 0
    for byte in data:
        checksum ^= byte
    return checksum & 0xFF


def imei2ip(imei_str: str) -> bytes:
    """
    设备号转伪IP
    :param imei_str: 设备imei
    :return: 伪ip（bytes类型）
    """
    if len(imei_str) != 11:
        raise ValueError("设备号长度必须是11位")
    # 截取前3位数
    num0_3 = int(imei_str[:3])

    # 整数值特殊处理，作为原数
    # 161、145 -> 都是145
    nGroup = GROUPS.get(num0_3, num0_3) - 100 - 30

    # 剩余数，每2位分割成一个列表 191 99 69 69 69
    ips = [int(imei_str[3:5]), int(imei_str[5:7]), int(imei_str[7:9]), int(imei_str[9:11])]

    # 判断原数值的bit0~bit3是否为真，是就对应列表索引的值就加128
    for i in range(4):
        if (1 << 3 - i) & nGroup:
            ips[i] += 0x80

    # 打包成一个字节类型数据
    ip_bytes = struct.pack('4B', ips[0], ips[1], ips[2], ips[3])
    return ip_bytes


def ip2imei(ip: bytes):
    ips = struct.unpack('>4B', ip)

    group = {
        141: 125,
        145: 161,
        139: 171,
        143: 191
    }
    nGroup = 0

    sn = ''

    for i in range(4):
        if ips[i] & 0x80:
            nGroup |= 1 << (3 - i)
        sn += '%02d' % (ips[i] & 0x7f)
    ng = nGroup + 100 + 30
    sn = str(group.get(ng, ng)) + sn
    return sn


def ip_to_possible_imeis(ip_bytes: bytes, group=None) -> list:
    # 步骤1：从伪IP解析出ips数组（4个整数）
    if group is None:
        group = GROUPS
    try:
        ips = struct.unpack('4B', ip_bytes)
        if len(ips) != 4:
            raise ValueError("伪IP必须是4字节的bytes")
    except struct.error:
        raise ValueError("伪IP格式错误，必须是4字节的bytes")

    # 步骤2：还原IMEI的后8位（4个两位数，不足两位补零）
    last_8_digits = []
    for num in ips:
        # 反推原始两位数（ips[i] = 原始值 ± 128）
        original = num - 128 if num >= 128 else num
        # 确保是两位数（补零，如5 → "05"）
        last_8_digits.append(f"{original:02d}")
    last_8 = ''.join(last_8_digits)  # 拼接成8位字符串

    # 步骤3：计算nGroup（控制前3位的参数）
    n_group = 0
    for i in range(4):
        # 若ips[i] >= 128，说明该位为1
        if ips[i] >= 128:
            n_group |= 1 << (3 - i)  # 置位：bit3对应i=0，bit0对应i=3

    # 步骤4：反推可能的前3位（n）
    m = n_group + 130  # 由 nGroup = group.get(n, n) - 130 变形而来
    possible_n = []

    # 情况1：查找group中值为m的所有key（多对一映射）
    for key, value in group.items():
        if value == m:
            possible_n.append(key)
            possible_n.append(value)

    # 情况2：若m不在group的值中，则n = m（group.get(n, n) = n）
    if m not in group.values():
        possible_n.append(m)

    # 步骤5：生成所有可能的11位IMEI（前3位+后8位，前3位不足3位补零）
    possible_imeis = []
    for n in possible_n:
        # 确保前3位是3位数（补零，如99 → "099"）
        first_3 = f"{n:03d}"
        # 拼接成11位IMEI
        imei = first_3 + last_8
        if len(imei) == 11:  # 校验长度
            possible_imeis.append(imei)

    return possible_imeis


def parse_2929(data: str, debug: bool = False) -> Tuple[bool, str, Optional[Dict]]:
    """
    验证JT808协议数据并解析内容
    :param data: 十六进制字符串
    :param debug: 是否打印调试信息
    :return: (是否合法, 提示信息, 解析结果)
    """
    try:
        # 1. 输入的内容转换为字节类型
        frame_bytes = hex_to_bytes(data)
        if debug:
            logging.info(f"原始字节流: {frame_bytes.hex().upper()}")
        if len(frame_bytes) < 4:
            return False, "帧长度过短（至少4字节）", None

        # 2. 验证报文包头和包尾
        if frame_bytes[:2] != D04_START and frame_bytes[-1] != D04_END:
            return False, f"起始/结束符错误（应为0x2929/0x0D，实际首尾:0x{frame_bytes[:2].hex()}/0x{frame_bytes[-1:].hex()}）", None

        # 3. 转义

        # 4. 校验验证码
        checksum = int.from_bytes(frame_bytes[-2:-1], "big")  # 报文校验码
        effective_data = frame_bytes[:-2]  # 包头到内容部分
        calculated_checksum = calculate_checksum(effective_data)

        if debug:
            logging.info(f"校验码验证: 实际0x{checksum:02X}, 计算0x{calculated_checksum:02X}")

        if calculated_checksum != checksum:
            return False, f"校验码错误（实际:0x{checksum:02X}, 计算:0x{calculated_checksum:02X}）", None

        # 5. 验证包长
        package_data = frame_bytes[5:]  # 包长=伪ip开始到包尾结束
        package_len = frame_bytes[3] << 8 | frame_bytes[4]  # 报文包长
        if len(package_data) != package_len:
            return False, f"消息体长度不匹配（实际:{len(package_data)}, 预期:{package_len}）", None

        # 6.主信令
        # 去除首尾
        content = frame_bytes[2:-1]
        # logging.info(f"去除首尾：{content.hex()}")
        # logging.info(f"主信令：{content[0:1].hex()}")
        main_signal = int.from_bytes(content[0:1], "big")

        # 7. 解析伪IP
        main_signal_byte = 4
        if main_signal in [MAIN_SIGNAL_PLATFORM_RESPONSE, MAIN_SIGNAL_REQUEST_PARSE_WIFI_RESPONSE]:
            fake_ip, imeis, main_signal_byte = None, [], 0
        else:
            fake_ip = content[3:7]
            imeis = ip_to_possible_imeis(fake_ip)
            if debug:
                logging.info(f"伪ip转设备号：伪ip={fake_ip.hex()},可能的设备号：{imeis}")

        # 8. 解析内容（根据主信令）
        msg_body = content[1 + 2 + main_signal_byte:-1]

        main_signal_fun = MAIN_SIGNAL.get(main_signal, parse_default)
        parse_data = main_signal_fun(msg_body)

        show_data = {
            "[2929]包头": D04_START,
            f"[{main_signal:02X}]主信令": main_signal,
            f"[{package_len:04X}]包长": package_len,
            f"[{fake_ip.hex() if fake_ip else None}]伪IP": imeis if imeis else ['无'],
            "数据内容": parse_data,
            f"[{checksum:02X}]校验位": checksum,
            "[0D]包尾": D04_END
        }
        return True, "数据合法且解析成功", show_data

    except Exception as e:
        return False, f"解析失败：{str(e)}", None
