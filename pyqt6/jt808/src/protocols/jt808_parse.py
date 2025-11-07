import re
import struct
from datetime import datetime
from typing import Tuple, Dict, Optional, List, Any
from zoneinfo import ZoneInfo

# ------------------------------
# 协议常量定义
# ------------------------------
JT808_START_END = 0x7E  # 起始/结束符
JT808_ESCAPE = 0x7d  # 转义符
JT808_ESCAPE_7E = 0x02  # 0x7e转义后第二字节
JT808_ESCAPE_7D = 0x01  # 0x7d转义后第二字节

PROTCCOL_ZIYOU = 1
PROTCCOL_BSJ2929 = 2
PROTCCOL_GT06 = 3
PROTCCOL_JT808 = 4
PROTCCOL_JT809 = 5
PROTCCOL_TYPE = {
    1: '自有协议',
    2: 'BSJ2929协议',
    3: 'GT06协议',
    808: 'jt808协议'
}

# 消息ID定义
MSG_ID_PLATFORM_RESPONSE = 0x8001  # 平台通用应答
MSG_ID_DEVICE_RESPONSE = 0x0001  # 设备通用应答
MSG_ID_DEVICE_REGISTER = 0x0100  # 设备注册
MSG_ID_DEVICE_REGISTER_ACK = 0x8100  # 平台注册应答
MSG_ID_DEVICE_LOGIN = 0x0102  # 设备鉴权
MSG_ID_TERMINER_LOGINOUT = 0x0003  # 终端注销
MSG_ID_LOCATION_REPORT = 0x0200  # 位置信息汇报
MSG_ID_HEARTBEAT = 0x0002  # 终端心跳
MSG_ID_TEXT_DISTRIBUTE = 0x8300  # 文本信息下发
MSG_ID_TEXT_MESSAGE_REPORT = 0x6006  # 文本信息上报
MSG_ID_BLIND_SPOT_REPORT = 0x0704  # 位置数据批量上传
MSG_ID_TERMINER_CONTROL = 0x8105  # 终端控制指令
MSG_ID_PLATFORM_PARAMS_SET = 0x8103  # 平台下发设置参数
MSG_ID_PLATFORM_PARAMS_QUERY = 0x8104  # 平台下发参数查询
MSG_ID_TERMINER_PARAMS_QUERY_RESPONSE = 0x8104  # 平台下发参数查询的应答
MSG_ID_OTA_RESULT = 0x6007  # OTA升级结果上报
MSG_ID_VERSION_REPORT = 0x0105  # 版本信息上报
MSG_ID_VERSION_REPORT_ACK = 0x8005

# TLV类型定义（JT808协议规定）附加信息ID
TLV_TYPE_MILEAGE = 0x01  # 里程
TLV_TYPE_OILL = 0x02  # 油量
TLV_TYPE_SPEED = 0x03  # 行驶记录速度
TLV_TYPE_ALARM_CONFIRMED = 0x04  # 需要人工确认报警事件的ID
TLV_TYPE_SPEED_ATTACH = 0x11  # 超速报警
TLV_TYPE_ADC = 0x2B  # ADC模拟量
TLV_TYPE_SIGNAL_STRENGTH = 0x30  # 网络信号强度
TLV_TYPE_SATELLITE_COUNT = 0x31  # GNSS定位卫星数
TLV_TYPE_EB_EXTEND = 0xEB  # EB扩展

# EB扩展指令
EB_EXTEND_ICCID = 0x00B2  # ICCID
EB_EXTEND_ALARM1 = 0x0089  # 碰撞和三急报警
EB_EXTEND_ALARM2 = 0x00C5  # 震动报警和定位状态及模式
EB_EXTEND_ADC = 0x002D  # ADC电压检测
EB_EXTEND_IMEI = 0x00D5  # 模块IMEI
EB_EXTEND_ALARM3 = 0x00E5  # 翻转和摔车、倾倒报警
EB_EXTEND_4G_CELL = 0x00D8  # 4G基站
EB_EXTEND_GENSOR_VALUE = 0x00E0  # G-Sensor 震动阈值

# 报警标志位定义
ALARM_FLAGS = {
    0: "紧急报警",
    1: "超速报警",
    2: "疲劳驾驶",
    3: "危险驾驶行为",
    4: "GNSS模块故障",
    5: "GNSS天线未接或被剪断",
    6: "GNSS天线短路",
    7: "终端主电源欠压",
    8: "终端主电源断电",
    9: "终端LCD或显示器故障",
    10: "TTS模块故障",
    11: "摄像头故障",
    12: "道路运输证IC卡模块故障",
    13: "超速预警",
    14: "疲劳驾驶预警",
    15: "保留",
    16: "保留",
    17: "保留",
    18: "当天累计驾驶超时",
    19: "超时停车",
    20: "进出区域",
    21: "进出路线",
    22: "路段行驶时间不足/过长",
    23: "路线偏离报警",
    24: "车辆VSS故障",
    25: "车辆油量异常",
    26: "车辆被盗",
    27: "车辆非法点火",
    28: "车辆非法位移",
    29: "碰撞预警",
    30: "侧翻预警",
    31: "非法开门报警"

}

# 状态位定义
STATUS_FLAGS = {
    0: "ACC",
    1: "定位",
    2: "北纬",
    3: "南纬",
    4: "东经",
    5: "西经",
}


# ------------------------------
# 工具函数：字节处理与转换
# ------------------------------
def is_hexadecimal(content) -> bool:
    """
    判断输入的数据是否为16进制数据
    :param content: 输入的数据
    """
    # 正则模式：可选前缀0x/0X，后面跟1个以上的16进制字符
    hex_pattern = re.compile(r'^0x[0-9a-fA-F]+$|^[0-9a-fA-F]+$')
    # 完全匹配则返回True，否则False
    return bool(hex_pattern.fullmatch(content))


def hex_to_bytes(hex_str: str) -> bytes:
    """十六进制字符串转字节流（处理空格）"""
    hex_str = hex_str.replace(" ", "").strip()

    if len(hex_str) % 2 != 0:
        raise ValueError("十六进制字符串长度必须为偶数")
    return bytes.fromhex(hex_str)


def bcd_to_str(bcd_bytes: bytes) -> str:
    """BCD码转字符串（如终端手机号）"""
    return "".join(f"{b:02x}" for b in bcd_bytes).upper()


def unescape(data: bytes) -> bytes:
    """反转义处理（恢复0x7e和0x7d）"""
    unescaped = []
    i = 0
    while i < len(data):
        if data[i] == JT808_ESCAPE and i + 1 < len(data):
            if data[i + 1] == JT808_ESCAPE_7E:
                unescaped.append(JT808_START_END)
                i += 2
            elif data[i + 1] == JT808_ESCAPE_7D:
                unescaped.append(JT808_ESCAPE)
                i += 2
            else:
                unescaped.append(data[i])
                i += 1
        else:
            unescaped.append(data[i])
            i += 1
    return bytes(unescaped)


def calculate_checksum(data: bytes) -> int:
    """计算校验码（异或和）"""
    checksum = 0
    for byte in data:
        checksum ^= byte
    return checksum & 0xFF


def parse_bit_flags(flag_value: int, flag_definitions: Dict[int, str]) -> Tuple[List[str], List[Dict[str, Any]]]:
    """解析报警标志位（将整数按位解析为具体含义）"""
    flags = []
    alarm_list = []
    result = {}
    for bit, meaning in flag_definitions.items():
        k = f"[bit{bit}]{meaning}"
        # result[k] = 1 if flag_value & (1 << bit) else 0
        if flag_value & (1 << bit):
            result[k] = 1
            alarm_list.append(meaning)
        else:
            result[k] = 0
    flags.append(result)  # {"bit[1]XXX报警": 1, "bit[2]XXX报警": 0}
    return alarm_list, flags


def parse_bit_status(status_value: int) -> Dict:
    """解析设备状态标志位，4个字节"""
    status = {}
    # 1. ACC状态（bit0：1=开，0=关）
    # status['ACC状态'] = '开' if (status_value & (1 << 0)) else '关'
    bit0 = (status_value >> 0) & 1
    status[f'[{bit0}]bit0'] = 'ACC开' if (status_value & (1 << 0)) else 'ACC关'

    # 2. 定位状态（bit1：1=定位，0=未定位）
    bit1 = (status_value >> 1) & 1
    status[f'[{bit1}]bit1'] = '定位' if (status_value & (1 << 1)) else '未定位'  # status_value & (1 << 1)判断bit1是否为1

    # 3. 纬度半球（bit2：1=南纬，0=北纬）
    bit2 = (status_value >> 2) & 1
    status[f'[{bit2}]bit2'] = '南纬' if bit2 else '北纬'

    # 4. 经度半球（bit3：1=西经，0=东经）
    bit4 = (status_value >> 5) & 1
    status[f'[{bit4}]bit3'] = '西经' if bit4 else '东经'

    # 5. 终端工作状态（bit4：1=停运状态，0=运营状态）
    bit4 = (status_value >> 4) & 1
    status[f'[{bit4}]bit4'] = '停运状态' if bool(bit4) else '运营状态'

    # 6. （bit5：1=经纬度保已经密插件加密，0=经纬度保未经密插件加密）
    bit5 = (status_value >> 5) & 1
    status[f'[{bit5}]bit5'] = '经纬度已经保密插件加密' if bit5 else '经纬度未经保密插件加密'

    # 7. bit6~7保留
    bit6_7 = (status_value >> 6) & 0b11
    status['[bit6~bit7]保留'] = bin(bit6_7)[2:].zfill(2)

    # 8. bit8~9 用于客车的空、重车及货车的空载、满载状态表示，（bit8~9：00：空车；01：半载；10：保留；11：满载）
    bit8_9 = (status_value >> 8) & 0b11
    status[f'[{bin(bit8_9)[2:].zfill(2)}]bit8~bit9'] = get_vehicle_status(status_value)

    # 9.车辆油路（bit10：0：正常；1：断开）
    bit10 = (status_value >> 10) & 1
    status[f'[{bit10}]bit10'] = '车辆油路断开' if bit10 else '车辆油路正常'

    # 10.车辆电路（bit11：0：正常；1：断开）
    bit11 = (status_value >> 11) & 1
    status[f'[{bit11}]bit11'] = '车辆电路断开' if bit11 else '车辆电路正常'

    # 车门锁状态（bit12：0：车门解锁；1：车门加锁）
    bit12 = (status_value >> 12) & 1
    status[f'[{bit12}]bit12'] = '车门加锁' if bit12 else '车门解锁'

    # 门1状态（bit13：0：门1关；1：门1开（前门））
    bit13 = (status_value >> 13) & 1
    status[f'[{bit13}]bit13'] = '门1开' if bit13 else '门1关'

    # 门2状态（bit14：0：门2关；1：门2开（中门））
    bit14 = (status_value >> 14) & 1
    status[f'[{bit14}]bit14'] = '门2开' if bit14 else '门2关'

    # 门3状态（bit15：0：门3关；1：门3开（后门））
    bit15 = (status_value >> 15) & 1
    status[f'[{bit15}]bit15'] = '门3开' if bit15 else '门3关'

    # 门4状态（bit16：0：门4关；1：门4开（驾驶席门））
    bit16 = (status_value >> 16) & 1
    status[f'[{bit16}]bit16'] = '门4开' if bit16 else '门4关'

    # 门5状态（bit17：0：门5关；1：门5开（自定义门））
    bit17 = (status_value >> 17) & 1
    status[f'[{bit17}]bit17'] = '门5开' if bit17 else '门5关'

    # 使用GPS卫星定位（bit18：0：使用；1：未使用）
    bit18 = (status_value >> 18) & 1
    status[f'[{bit18}]bit18'] = '使用GPS卫星进行定位' if bit18 else '未使用GPS卫星进行定位'

    # 使用北斗卫星定位（bit19：0：使用；1：未使用）
    bit19 = (status_value >> 19) & 1
    status[f'[{bit19}]bit19'] = '使用北斗卫星定位' if bit19 else '未使用北斗卫星定位'

    # 使用北斗卫星定位（bit20：0：使用；1：未使用）
    bit20 = (status_value >> 20) & 1
    status[f'[{bit20}]bit20'] = '使用GLONASS卫星定位' if bit20 else '未使用GLONASS卫星定位'

    # 使用北斗卫星定位（bit21：0：使用；1：未使用）
    bit21 = (status_value >> 21) & 1
    status[f'[{bit21}]bit21'] = '使用Galileo卫星定位' if bit21 else '未使用Galileo卫星定位'

    # bit22~bit31 保留
    bit21_31 = (status_value >> 22) & 0x3FF
    status['[bit22~bit31]保留'] = bin(bit21_31)[2:].zfill(10)

    # 原始值（调试用）
    # status['原始值（十六进制）'] = f"0x{status_value:08X}"

    return status


def get_vehicle_status(number) -> str:
    # 提取bit8~bit9位的值（先右移8位，再与0b11进行与运算）
    # 0b11是二进制的3，用于只保留最后两位
    status_bits = (number >> 8) & 0b11
    ststus_vehicle = {0b00: "空车", 0b01: "半载", 0b10: "保留", 0b11: "满载"}
    # 根据提取的位值判断状态
    # if status_bits == 0b00:  # 00
    #     return "空车"
    # elif status_bits == 0b01:  # 01
    #     return "半载"
    # elif status_bits == 0b10:  # 10
    #     return "保留"
    # elif status_bits == 0b11:  # 11
    #     return "满载"
    # else:
    #     return "未知状态"  # 理论上不会走到这里
    return ststus_vehicle.get(status_bits, "未知状态")


# ------------------------------
# TLV信息解析函数
# ------------------------------
def parse_tlv_mileage(value: bytes) -> Dict:
    """解析行驶里程TLV(0x01)：4字节无符号整数，单位：0.1km"""
    tlv_id = f"{TLV_TYPE_MILEAGE:02X}"
    tlv_length = 4
    if len(value) != tlv_length:
        raise ValueError(f"行驶里程TLV长度错误，预期4字节，实际{len(value)}字节")
    mileage = struct.unpack(">I", value)[0]
    return {
        f"[01]附加信息ID": tlv_id,
        f"[04]附加信息长度": tlv_length,
        f"[{mileage:08X}]里程": mileage / 10,
        "单位": "km"
    }


def parse_tlv_oil_level(value: bytes) -> Dict:
    """解析油量TLV(0x02)：2字节无符号整数，单位：L"""
    tlv_id = f"{TLV_TYPE_OILL:02X}"
    tlv_length = 2
    if len(value) != tlv_length:
        raise ValueError(f"油量长度错误，预期2字节，实际{len(value)}字节")
    oil = struct.unpack(">H", value)[0]
    return {
        "[02]附加信息ID": tlv_id,
        "[02]附加信息长度": tlv_length,
        f"[{oil:04X}]油量": oil / 10,
        "单位": "L"
    }


def parse_tlv_alarm_id_confirmed(value: bytes) -> Dict:
    """需要人工确认报警事件的 ID，2个字节，无符号整数"""
    tlv_id = f"{TLV_TYPE_ALARM_CONFIRMED:02X}"
    tlv_length = 2
    if len(value) != tlv_length:
        raise ValueError(f"报警事件IDTLV长度错误，预期2字节，实际{len(value)}字节")
    count = struct.unpack(">H", value)[0]
    return {
        "[04]附加信息ID": tlv_id,
        "[02]附加信息长度": tlv_length,
        f"[{count:04X}]需要人工确认报警事件的ID": count
    }


def parse_tlv_driving_speed(value: bytes) -> Dict:
    """解析行驶记录速度TLV(0x0005)：2字节无符号整数，单位：0.1km/h"""
    tlv_id = f"{TLV_TYPE_SPEED:02X}"
    tlv_length = 2
    if len(value) != tlv_length:
        raise ValueError(f"行驶速度TLV长度错误，预期2字节，实际{len(value)}字节")
    speed = struct.unpack(">H", value)[0]
    return {
        "[03]附加信息ID": tlv_id,
        "[02]附加信息长度": tlv_length,
        f"[{speed:04X}]行驶记录功能获取的速度": speed / 10,
        "unit": "km/h"
    }


def parse_tlv_over_speed_attach(value: bytes) -> Dict:
    """解析超速报警附加信息TLV(0x11)：变长字节"""
    tlv_id = f"{TLV_TYPE_SPEED_ATTACH:02X}"
    tlv_length = 1 or 5
    if len(value) != tlv_length:
        raise ValueError(f"超速报警附加信息TLV长度错误，预期1或5个字节，实际{len(value)}字节")
    # 11 01 00、11 05 04 00000122
    loc_type = struct.unpack(">B", value[:1])[0]
    if loc_type != 0:
        loc_id = struct.unpack(">4s", value[1:])[0].decode("utf-8")
    else:
        loc_id = None

    return {
        "[11]附加信息ID": tlv_id,
        f"[{len(value):02X}]附加信息长度": len(value),
        "超速报警附加信息": {
            f"[{loc_type:02X}]位置类型": loc_type,
            "区域或路段ID": loc_id
        }
    }


def parse_tlv_adc(value: bytes) -> Dict:
    """解析ADC模拟量TLV(0x2D)：4字节无符号整数"""
    tlv_id = f"0x{TLV_TYPE_ADC:02X}"
    tlv_length = 4

    if len(value) != tlv_length:
        raise ValueError(f"ADC模拟量TLV长度错误，预期4字节，实际{len(value)}字节")
    uint32_value = struct.unpack(">I", value)[0]
    # 提取 bit0-15（低16位）：用 0xFFFF 掩码做与运算
    bit0_15 = uint32_value & 0xFFFF  # 0xFFFF = 二进制 16个1，屏蔽高16位
    # 提取 bit16-31（高16位）：先右移16位，再用掩码（或直接右移）
    bit16_31 = (uint32_value >> 16) & 0xFFFF  # 右移后高16位补0，掩码可省略（但写更严谨）
    return {
        "[2B]附加信息ID": tlv_id,
        "[04]附加信息长度": tlv_length,
        f"[{uint32_value:04X}]ADC模拟量": {
            "[bit0~bit15]AD0": bit0_15,
            "[bit16~bit31]AD1": bit16_31
        }
    }


def parse_tlv_signal_strength(value: bytes) -> Dict:
    """解析信号强度TLV(0x30)：1字节无符号整数，0-31"""
    if len(value) != 1:
        raise ValueError(f"信号强度TLV长度错误，预期1字节，实际{len(value)}字节")
    strength = struct.unpack(">B", value)[0]
    return {
        "[30]附加信息ID": "信号强度",
        "[01]附加信息长度": 1,
        f"[{strength:02X}]信号强度": "强" if strength > 20 else "中" if strength > 10 else "弱",
    }


def parse_tlv_satellite_count(value: bytes) -> Dict:
    """解析GNSS定位卫星数TLV(0x31)：1字节无符号整数"""
    if len(value) != 1:
        raise ValueError(f"GNSS状态TLV长度错误，预期1字节，实际{len(value)}字节")
    gnss_num = struct.unpack(">B", value)[0]
    return {
        "[31]附加信息ID": '',
        "[01]附加信息长度": 1,
        f"[{gnss_num:02X}]GNSS定位卫星数": gnss_num
    }


def parse_eb_data(data: bytes) -> Dict:
    """解析EB扩展数据"""
    eb_list = []
    index = 0
    total_len = len(data)

    while index < total_len:
        # 扩展字段总长，2个字节
        if index + 2 > total_len:
            # 剩余字符不足4个，无法读取长度,退出循环
            break
        eb_length = struct.unpack(">H", data[index:index + 2])[0]
        index += 2

        # 命令字，2个字节
        if index + 2 > total_len:
            raise ValueError(f"EB扩展命令字长度错误，index={index}>数据总长{total_len}字节")
        eb_command = struct.unpack(">2s", data[index:index + 2])[0]
        eb_command_hex = eb_command.hex()
        index += 2

        # 扩展内容，（总长-2）字节
        eb_content_len = eb_length - 2
        if index + eb_content_len > total_len:
            raise ValueError(
                f"EB扩展内容command={eb_command_hex}截取错误,index={index + eb_content_len}>数据总长{total_len}字节")
        eb_content = struct.unpack(f">{eb_content_len}s", data[index:index + eb_content_len])[0]
        index += eb_content_len

        command_num = int.from_bytes(eb_command, "big")

        if command_num in EB_PARSERS:
            try:
                eb_part = EB_PARSERS[command_num](eb_content)
                # eb_part["EB扩展指令"] = f"0x{eb_length:04X} 0x{eb_command_hex.upper()}"
                # eb_part["eb_command"] = f"0x{eb_command_hex}"
                eb_list.append(eb_part)
            except Exception as e:
                eb_list.append({
                    "type": f"EB解析错误(0x{eb_command_hex})",
                    "eb_command": f"0x{eb_command_hex}",
                    "error": str(e),
                    "value": eb_content.hex()
                })
        else:
            eb_list.append({
                "type": "未知EB类型",
                "tlv_type": f"0x{eb_command_hex}",
                "eb_command": eb_command_hex,
                "value": eb_content.hex()
            })

    return {
        "[EB]附加信息ID": f"{TLV_TYPE_EB_EXTEND:02X}",
        f"[{total_len:02X}]附加信息长度": total_len,
        "EB扩展列表项": eb_list

    }


# TLV解析函数映射
TLV_PARSERS = {
    TLV_TYPE_MILEAGE: parse_tlv_mileage,
    TLV_TYPE_OILL: parse_tlv_oil_level,
    TLV_TYPE_SPEED: parse_tlv_driving_speed,
    TLV_TYPE_ALARM_CONFIRMED: parse_tlv_alarm_id_confirmed,
    TLV_TYPE_SPEED_ATTACH: parse_tlv_over_speed_attach,
    TLV_TYPE_ADC: parse_tlv_adc,
    TLV_TYPE_SIGNAL_STRENGTH: parse_tlv_signal_strength,
    TLV_TYPE_SATELLITE_COUNT: parse_tlv_satellite_count,
    TLV_TYPE_EB_EXTEND: parse_eb_data
}


def parse_eb_iccid(values: bytes) -> Dict:
    """解析扩展SIM的ICCID（扩展指令=0x000C 0x00B2）"""
    if len(values) != 10:
        raise ValueError(f"ICCID长度错误，预期10个字节，实际{len(values)}个字节")
    value = struct.unpack(">10s", values)[0]

    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EB_EXTEND_ICCID:04X}]扩展指令": EB_EXTEND_ICCID,
        f"ICCID": value.hex()
    }


def parse_eb_alarm1(values: bytes) -> Dict:
    """解析扩展报警状态位1（扩展指令=0x0006 0x0089）"""
    if len(values) != 4:
        raise ValueError(f"扩展报警状态位1长度错错误，预期4个字节，实际{len(values)}个字节")
    value = struct.unpack(">4s", values)[0]
    alarm1 = int.from_bytes(value, "big", signed=False)
    battery_switch = '电池关' if (alarm1 & 1) else '电池开'
    collision_alarm = '正常' if ((alarm1 >> 4) & 1) else '碰撞报警'
    accelerate_sharply_alarm = '正常' if ((alarm1 >> 8) & 1) else '急加速报警'
    slow_sharply_alarm = '正常' if ((alarm1 >> 9) & 1) else '急减速报警'
    sharp_alarm = '正常' if ((alarm1 >> 25) & 1) else '急转弯报警'

    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EB_EXTEND_ALARM1:04X}]扩展指令": EB_EXTEND_ALARM1,
        f"[{values.hex().upper()}]碰撞和三急报警": {
            "binary": optimized_hex_to_binary(values.hex()),
            "[bit0]电池开-关": battery_switch,
            "[bit4]碰撞报警": collision_alarm,
            "[bit8]急加速报警": accelerate_sharply_alarm,
            "[bit9]急减速报警": slow_sharply_alarm,
            "[bit25]急转弯报警": sharp_alarm
        }
    }


def parse_eb_alarm2(values: bytes) -> Dict:
    """解析扩展报警状态位2（扩展指令=0x0006 0x00C5）"""
    if len(values) != 4:
        raise ValueError(f"扩展报警状态位2长度错错误，预期4个字节，实际{len(values)}个字节")

    value = struct.unpack(">4s", values)[0]

    alarm2 = int.from_bytes(value, "big", signed=False)

    position_flag = 'GPS定位' if ((alarm2 >> 3) & 0x3) else 'GPS不定位'  # bit3_4：00：GPS不定位；10：GPS定位

    vib_alarm = '正常' if ((alarm2 >> 6) & 1) else '震动报警'  # bit6：0：正常；1：震动报警

    status = '静止' if ((alarm2 >> 9) & 1) else '运动'  # bit9：0：运动；1：静止

    gps_mode_flag = (alarm2 >> 19) & 0x3  # bit19~bit20:定位模式

    gps_mode = {0: '双模', 1: '单GPS', 2: '单北斗'}

    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EB_EXTEND_ALARM2:04X}]扩展指令": EB_EXTEND_ALARM2,
        f"[{values.hex().upper()}]震动报警和定位状态及模式": {
            "binary": optimized_hex_to_binary(values.hex()),
            '[bit3~bit4]定位状态': position_flag,
            '[bit6]震动报警': vib_alarm,
            '[bit9]状态': status,
            '[bit19~bit20]定位模式': gps_mode.get(gps_mode_flag, f'未知模式{gps_mode_flag}')
        }
    }


def parse_eb_alarm3(values: bytes) -> Dict:
    """解析扩展报警状态位3（扩展指令=0x0006 0x00E5）"""
    if len(values) != 4:
        raise ValueError(f"扩展报警状态位3长度错错误，预期4个字节，实际{len(values)}个字节")
    value = struct.unpack(">4s", values)[0]

    alarm3 = int.from_bytes(value, "big", signed=False)

    overturn_alarm = '正常' if ((alarm3 >> 22) & 1) else '翻转报警'  # bit22: 1:正常 0：翻转报警

    tumble_down = '正常' if ((alarm3 >> 23) & 1) else '摔车报警'  # bit23: 1:正常 0：摔车报警（摩托车设备）

    topple_over = '正常' if ((alarm3 >> 24) & 1) else '倾倒报警'  # bit23: 1:正常 0：倾倒报警（摩托车设备）

    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EB_EXTEND_ALARM3:04X}]扩展指令": EB_EXTEND_ALARM3,
        f"[{values.hex().upper()}]翻转和摔车、倾倒报警": {
            "binary": optimized_hex_to_binary(values.hex()),
            "[bit22]翻转报警": overturn_alarm,
            "[bit23]摔车报警（摩托车设备专用）": tumble_down,
            "[bit24]倾倒报警（摩托车设备专用）": topple_over
        }
    }


def parse_eb_imei(values: bytes) -> Dict:
    """解析扩展模块IMEI号（扩展指令=0x0004 0x002D）"""
    if len(values) != 15:
        raise ValueError(f"设备（模块）IMEI号长度错错误，预期15个字节，实际{len(values)}个字节")
    value = struct.unpack(">15s", values)[0]
    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EB_EXTEND_IMEI:04X}]扩展指令": EB_EXTEND_IMEI,
        "设备（模块）IMEI号": value.decode("utf-8")
    }


def parse_eb_adc(values: bytes) -> Dict:
    """解析扩展ADC电压值（扩展指令=0x0011 0x00D5）"""
    if len(values) != 2:
        raise ValueError(f"ADC电压长度错错误，预期2个字节，实际{len(values)}个字节")
    value = struct.unpack(">H", values)[0]
    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EB_EXTEND_ADC:04X}]扩展指令": EB_EXTEND_ADC,
        f"[{values.hex().upper()}]ADC外电电压": {
            "Value": value,
            "电压值": f"{value / 1000:.3f}v",
        }
    }


def parse_eb_4g_cell(values: bytes) -> Dict:
    """解析扩展4G基站（扩展指令=0x000B 0x00D8）"""
    if len(values) != 9:
        raise ValueError(f"4G基站长度错错误，预期9个字节，实际{len(values)}个字节")
    mcc, mnc, ceil, station = struct.unpack(">H B 2s 4s", values)
    # 01cc 00 2866 0a80b50c
    country_code = '中国' if (mcc == 460) else '其他'
    mnc_hex = f"{mnc:02x}"

    match mnc_hex:
        case '00' | '02' | '04' | '07':
            net_code = '移动'
        case '01' | '06' | '09':
            net_code = '联通'
        case '03' | '05' | '11':
            net_code = '电信'
        case '20':
            net_code = '铁通'
        case _:
            net_code = '其他'

    return {
        f"[{len(values) + 2:04X}]总长度": len(values) + 2,
        f"[{EB_EXTEND_4G_CELL:04X}]扩展指令": EB_EXTEND_4G_CELL,
        f"[{values.hex()}]4G基站": {
            f"[{mcc:04X}]MCC": country_code,
            f"[{mnc_hex}]MNC": net_code,
            f"[{ceil.hex().upper()}]Ceil": ceil.hex(),
            f"[{station.hex().upper()}]Station": station.hex()
        }
    }


def parse_eb_gensor(values: bytes) -> Dict:
    """解析上传G-Sensor的震动值（扩展指令=0x002A 0x00E0）"""
    value_byte = len(values)
    if value_byte > 40:
        raise ValueError(f"G-Sensor震动值长度错错误，最多40个字节，实际{value_byte}字节")
    elif value_byte % 2 != 0:
        raise ValueError(f"G-Sensor震动值长度错错误，应为2的倍数值，实际{value_byte}字节")
    # 0012 0012 000e 000e 0012 0011 000c 000d 0010 000d 000b 0012 000f 000c 0010 0010 000f 0014 000e 000a
    value = struct.unpack(f">{value_byte}s", values)[0]

    # value_list = [f'0x{value[i:i + 2].hex()}' for i in range(0, value_byte, 2)]
    g_value_list = [f'{int.from_bytes(value[i:i + 2])}' for i in range(0, value_byte, 2)]

    return {
        f"[{value_byte + 2:04X}]总长度": len(values) + 2,
        f"[{EB_EXTEND_GENSOR_VALUE:04X}]扩展指令": EB_EXTEND_GENSOR_VALUE,
        "G-Sensor震动值": {
            "Value": value.hex(),
            "点数量": value_byte // 2,
            "点数列表": g_value_list
        }
    }


# EB扩展解析
EB_PARSERS = {
    EB_EXTEND_ICCID: parse_eb_iccid,
    EB_EXTEND_ALARM1: parse_eb_alarm1,
    EB_EXTEND_ALARM2: parse_eb_alarm2,
    EB_EXTEND_ALARM3: parse_eb_alarm3,
    EB_EXTEND_IMEI: parse_eb_imei,
    EB_EXTEND_ADC: parse_eb_adc,
    EB_EXTEND_4G_CELL: parse_eb_4g_cell,
    EB_EXTEND_GENSOR_VALUE: parse_eb_gensor
}


def parse_tlv_data(data: bytes) -> List[Dict]:
    """解析位置包的TLV数据集合（附加位置消息项）"""
    tlv_list = []
    index = 0
    while index < len(data):
        # TLV头部：1字节类型 + 1字节长度
        if index + 2 > len(data):
            raise ValueError(f"TLV数据不完整，剩余{len(data) - index}字节不足4字节头部")

        tlv_id = struct.unpack(">B", data[index:index + 1])[0]  # index=0 [0:1]
        tlv_length = struct.unpack(">B", data[index + 1:index + 2])[0]  # index=0 [1:2]
        index += 2

        # TLV值
        if index + tlv_length > len(data):
            raise ValueError(f"TLV[{tlv_id}]值长度不足，预期{tlv_length}字节，实际{len(data) - index}字节")

        tlv_value = data[index:index + tlv_length]  # index=4 [4:length]
        index += tlv_length

        # 解析TLV值
        if tlv_id in TLV_PARSERS:

            try:
                tlv_info = TLV_PARSERS[tlv_id](tlv_value)
                tlv_list.append(tlv_info)
            except Exception as e:
                tlv_list.append({
                    "type": f"TLV解析错误(0x{tlv_id:02x})",
                    "tlv_id": f"0x{tlv_id:02x}",
                    "error": str(e),
                    "value": tlv_value.hex()
                })
        else:
            tlv_list.append({
                "type": "未知TLV类型",
                "tlv_id": f"0x{tlv_id:02x}",
                "tlv_length": tlv_length,
                "value": tlv_value.hex()
            })

    return tlv_list


# ------------------------------
# 消息体解析函数（按消息ID实现）
# ------------------------------
def number_to_hex_format(num: int) -> str:
    """
    将数字转换为4字节大端字节序的十六进制格式，如1027 -> "00 00 04 03"
    参数:
        num: 要转换的整数
    返回:
        格式化后的十六进制字符串
    """
    # 确保数字在4个字节无符号整数范围内
    if num < 0 or num > 0xFFFFFFFF:
        raise ValueError("数字必须在0到4294967295之间")

    # 将数字转换为4字节大端字节序的bytes
    # '>I'表示大端字节序，无符号32位整数
    import struct
    bytes_data = struct.pack('>I', num)

    # 将每个字节转换为两位十六进制，并大写，用空格分隔
    return ' '.join(f'{b:02X}' for b in bytes_data)


def optimized_hex_to_binary(hex_str: str) -> str:
    """优化版十六进制转格式化二进制"""
    # 预计算长度

    # 直接映射转换
    hex_to_bin_map = {
        '0': '0000', '1': '0001', '2': '0010', '3': '0011',
        '4': '0100', '5': '0101', '6': '0110', '7': '0111',
        '8': '1000', '9': '1001', 'a': '1010', 'b': '1011',
        'c': '1100', 'd': '1101', 'e': '1110', 'f': '1111',
        'A': '1010', 'B': '1011', 'C': '1100', 'D': '1101',
        'E': '1110', 'F': '1111'
    }

    # 处理前缀
    if hex_str.startswith(('0x', '0X')):
        hex_str = hex_str[2:]

    # 直接映射转换
    bin_groups = [hex_to_bin_map[char] for char in hex_str]

    return ' '.join(bin_groups)


def parse_0100(msg_body: bytes) -> Dict:
    """解析终端注册包（消息ID=0x0100）"""
    msg_len = len(msg_body)

    if msg_len < 25:
        raise ValueError(f"注册消息体长度字少是25个字节，实际{msg_len}个字节")

    #  省域ID:2、市县域ID:2、制造商ID:5、终端型号:8/20、终端ID:7、车牌颜色:1、车牌:n（已知字节2+2+5+7+1=17）
    terminal_model_len = 8  # 终端型号长度
    if msg_len - 17 - 20 > 0:
        terminal_model_len = 20

    # 车牌长度
    license_plate_len = msg_len - 17 - terminal_model_len

    (province_id, city_id, manufacturer_id, terminal_model, terminal_id, license_plate_color,
     license_plate) = struct.unpack(f">H H 5s {terminal_model_len}s 7s B {license_plate_len}s", msg_body)

    return {
        "终端注册": msg_body.hex(),
        f"[{province_id:04X}]省域ID": province_id,
        f"[{city_id:04X}]市县域ID": city_id,
        f"[{manufacturer_id.hex()}]制造商ID(5)": manufacturer_id.decode("utf-8", errors="replace"),
        f"[{terminal_model.hex()}]终端型号({len(terminal_model)})": terminal_model.rstrip(b'\x00').decode("utf-8"),
        f"[{terminal_id.hex()}]终端ID(7)": terminal_id.decode("utf-8", errors="replace").zfill(7 * 2),
        f"[{license_plate_color:02x}]车牌颜色": license_plate_color,
        f"[{license_plate.hex()}]车牌号码": license_plate.decode("GBK", errors="replace"),
    }


def parse_8100(msg_body: bytes) -> Dict:
    """解析终端注册应答包（消息ID=0x8100）"""
    msg_len = len(msg_body)
    login_code = None

    if msg_len < 3:
        raise ValueError(f"终端注册应答消息体长度至少是3个字节，实际{msg_len}个字节")

    respon_serial, result = struct.unpack(">H B", msg_body[:3])
    login_key = f"[{login_code}]鉴权码"

    if msg_len > 3:
        login_code = struct.unpack(f">{msg_len - 3}s", msg_body[3:])[0]
        login_key = f"[{login_code.hex()}]鉴权码"

    login_result = {
        0: '成功',
        1: '车辆已被注册',
        2: '数据库中无该车辆',
        3: '终端已被注册',
        4: '数据库中无该车辆'
    }
    return {
        "终端注册应答": msg_body.hex(),
        f"[{respon_serial:04X}]应答流水号": respon_serial,
        f"[{result:02x}]结果": login_result.get(result, "未知结果"),
        login_key: login_code.decode("utf-8", errors="ignore") if login_code else None
    }


def parse_0102(msg_body: bytes) -> Dict:
    """解析终端鉴权包（消息ID=0x0102）"""
    if len(msg_body) == 0:
        raise ValueError("鉴权消息体内容不能为空")
    login_code = struct.unpack(f">{len(msg_body)}s", msg_body)[0]
    login_code_str = login_code.decode("utf-8", errors="ignore")
    return {
        "终端鉴权": msg_body.hex(),
        f"[{login_code.hex()}]鉴权码": login_code_str,
    }


# def parse_0003(msg_body: bytes) -> Dict:


def parse_0200(msg_body: bytes) -> Dict:
    """解析位置信息汇报消息（消息ID=0x0200）- 修复版"""
    # 基础信息28字节 + TLV至少2字节（1组TLV）= 最小28字节
    if len(msg_body) < 28:
        raise ValueError(f"位置信息消息体长度不足，预期28字节，实际{len(msg_body)}字节")

    # 报警4byte,状态4byte,纬度4byte,经度4byte,
    alarm_flag, status, latitude, longitude = struct.unpack(">I I I I", msg_body[:16])
    # 高度2byte,速度2byte,方向2byte
    high, speed, direction = struct.unpack(">H H H", msg_body[16:22])
    # 定位时间6byte(BCD[6])
    time_bcd = msg_body[22:28]  # 6字节BCD时间（YYMMDDHHMMSS）

    # 解析时间
    time_str = bcd_to_str(time_bcd)
    try:
        time_formatted = f"20{time_str[:2]}-{time_str[2:4]}-{time_str[4:6]} " \
                         f"{time_str[6:8]}:{time_str[8:10]}:{time_str[10:12]}"
    except ValueError as e:
        time_formatted = f"{str(e)},无效时间格式({time_str})"

    # 经纬度转换（协议：度分格式，除以10^6转为十进制）
    lat = latitude / 1000000.0
    lon = longitude / 1000000.0

    # 解析报警标志和状态
    alarms, alarm_info = parse_bit_flags(alarm_flag, ALARM_FLAGS)
    status_info = parse_bit_status(status)

    # 解析TLV附加信息（26个字节之后的内容）
    tlv_data = msg_body[28:]
    tlv_info_list = parse_tlv_data(tlv_data)

    return {
        "位置信息汇报": msg_body.hex(),
        "报警标志对象": {
            "value": number_to_hex_format(alarm_flag),
            "报警标志预览": alarms if len(alarms) > 0 else ["无报警"],
            "报警标志位列表": alarm_info or ["无报警"]
        },
        "状态标志对象": {
            "value": number_to_hex_format(status),
            "状态标志位列表": status_info
        },
        f"[{latitude:08X}]纬度": lat,  # 纬度（十进制）
        f"[{longitude:08X}]经度": lon,  # 经度（十进制）
        f"[{high:04X}]高程": high,  # 高程（海拔高度，单位：米）
        f"[{speed:04X}]速度": speed / 10.0,  # 速度（km/h，协议单位为0.1km/h）
        f"[{direction:04X}]方向": direction,  # 方向（度）
        f"[{time_bcd.hex()}]定位时间": time_formatted,  # 定位时间
        "位置附加信息项列表": tlv_info_list  # TLV附加信息
    }


def parse_0704(msg_body: bytes) -> Dict:
    """解析盲区数据（消息ID=0x0704）"""
    blind_data_count, blind_data_type = struct.unpack(">HB", msg_body[:3])
    blind_list = []

    if blind_data_count == 0:
        raise ValueError(f"数据项个数必须为1，实际个数{blind_data_count}")
    elif blind_data_count == 1:
        blind_data_length = struct.unpack(">H", msg_body[3:5])[0]
        parse_loc = parse_0200(msg_body[5:])
        blind_list.append({
            f'[{blind_data_length:04X}]位置汇报数据长度': blind_data_length,
            '位置信息': parse_loc
        })
    else:
        many_data = msg_body[3:]
        many_data_len = len(many_data)
        index = 0
        while index < many_data_len:
            if index + 2 > many_data_len:
                raise ValueError(f"盲区数据不完整，剩余{many_data_len - index}个字节,不足2字节")

            # 盲区数据长度
            data_len = struct.unpack(">H", many_data[index:index + 2])[0]
            index += 2
            if index + data_len > many_data_len:
                raise ValueError(f"盲区数据读取错误，预计长度{data_len}个字节,索引超过总长")
            # 盲区数据
            blind_data = many_data[index:index + data_len]
            index += data_len

            parse_loc = parse_0200(blind_data)
            blind_list.append({
                f'[{data_len:04X}]位置汇报数据长度': data_len,
                '位置信息': parse_loc
            })

    return {
        "盲区上传": msg_body.hex() if len(msg_body) < 120 else f"{msg_body.hex()[:50]}...{msg_body.hex()[-30:]}",
        f"[{blind_data_count:04X}]数据项个数": blind_data_count,
        f"[{blind_data_type:02X}]数据类型": '盲区补报' if blind_data_type else '正常位置批量汇报',
        '盲区数据列表': blind_list
    }


def parse_0002(msg_body: bytes) -> Dict:
    """解析终端心跳消息（消息ID=0x0002，无消息体）"""
    if len(msg_body) != 0:
        raise ValueError("终端心跳消息体应为空")
    return {
        "终端心跳": None
    }


def parse_8001(msg_body: bytes) -> Dict:
    """解析平台通用应答消息（消息ID=0x8001）"""
    if len(msg_body) != 5:
        raise ValueError("平台通用应答消息体长度应为5字节")
    msg_id, msg_seq, result = struct.unpack(">H H B", msg_body)
    result_map = {0: "成功/确认", 1: "失败", 2: "消息错误", 3: "不支持"}
    return {
        "平台通用应答": msg_body.hex(),
        f"[{msg_id:04X}]应答流水": msg_id,  # 被应答的消息ID
        f"[{msg_seq:04X}]应答ID": msg_seq,  # 被应答的消息流水号
        f"[{result:02X}]result": result_map.get(result, f"未知状态({result})")
    }


def parse_0001(msg_body: bytes) -> Dict:
    """设备通用应答（消息ID=0x0001）"""
    if len(msg_body) != 5:
        raise ValueError(f"消息体内容长度应是5个字节，实际{len(msg_body)}个字节")
    ack_seq, ack_id, ack_result = struct.unpack(">2HB", msg_body)
    result_map = {
        0: "成功/确认",
        1: "失败",
        2: "消息有误",
        3: "不支持",
        4: "报警处理确认"
    }
    return {
        "设备通用应答": msg_body.hex(),
        f"[{ack_seq:04X}]应答流水": ack_seq,
        f"[{ack_id:04X}]应答ID": f"0x{ack_id:04X}",
        f"[{ack_result:02X}]结果": result_map.get(ack_result, f"未知{ack_result}")
    }


def parse_6006(msg_body: bytes) -> Dict:
    """文本信息上报（消息ID=0x6006）"""
    len_byte = len(msg_body)

    if len_byte < 2:
        raise ValueError("文本信息上报消息体长度至少2个字节")
    text_encode, content_byte = struct.unpack(f">B {len_byte - 1}s ", msg_body)

    encode = "UNICODE" if text_encode else "GB2312"

    return {
        "6006文本信息上报": msg_body.hex(),
        "编码方式": encode,
        "content": content_byte.decode(encode, errors="replace")
    }


def parse_8300(msg_body: bytes) -> Dict:
    """文本信息下发（消息ID=0x8300）"""
    len_byte = len(msg_body)
    text_flag, text_content = struct.unpack(f">B {len_byte - 1}s ", msg_body)

    return {
        "8300文本信息下发": msg_body.hex(),
        f"文本信息标志对象[{text_flag:02x}]": {
            "[bit6~bit7]保留": f"{(text_flag >> 6) & 3:02x}",
            f"[bit5]{((text_flag >> 5) & 1)}": "CAN故障码信息" if ((text_flag >> 5) & 1) else "中心导航信息",
            f"[bit4]{((text_flag >> 4) & 1)}": "广告屏显示",
            f"[bit5]{((text_flag >> 3) & 1)}": "终端 TTS 播读",
            f"[bit5]{((text_flag >> 2) & 1)}": "终端显示器显示",
            f"[bit5]{((text_flag >> 1) & 1)}": "保留",
            f"[bit5]{((text_flag >> 0) & 1)}": "紧急",
        },
        "文本内容": text_content.decode("GBK", errors="replace")
    }


def parse_8105(msg_body: bytes) -> Dict:
    """终端控制指令（消息ID=0x8105）"""
    """"""
    len_byte = len(msg_body)
    text_flag, text_content = struct.unpack(f">B {len_byte - 1}s ", msg_body)

    return {
        "8300文本信息下发": msg_body.hex(),
        "文本标志": text_flag,
        "文本内容": text_content.decode("GBK", errors="replace")
    }


def parse_0105(msg_body: bytes) -> Dict:
    """解析版本信息上报（消息ID=0x8105）"""
    if len(msg_body) != 3:
        raise ValueError(f"消息体内容长度必须为3个字节，当前为{len(msg_body)}个字节")
    protocol_ver, mcu_ver, module_ver = struct.unpack(">3B", msg_body)
    protocol_ver_hex = f"{protocol_ver:02x}"
    mcu_ver_hex = f"{mcu_ver:02x}"
    module_ver_hex = f"{module_ver:02x}"
    return {
        "设备版本信息上报": msg_body.hex(),
        f"[{protocol_ver_hex}]协议版本": protocol_ver_hex,
        f"[{mcu_ver_hex}]MCU版本": mcu_ver_hex,
        f"[{module_ver_hex}]模块版本": module_ver_hex

    }


def parse_8005(msg_body: bytes) -> Dict:
    """平台应答版本信息上报（消息ID=0x8005）"""
    # 7e8005000405076400802600016906cc36d57e
    if len(msg_body) != 4:
        raise ValueError(f"消息体内容长度必须为4个字节，当前为{len(msg_body)}个字节")
    timestap = struct.unpack(">I", msg_body)[0]

    utc_time = datetime.fromtimestamp(timestap, tz=ZoneInfo("UTC")).strftime('%Y-%m-%d %H:%M:%S')
    localtime = datetime.fromtimestamp(timestap).strftime('%Y-%m-%d %H:%M:%S')

    return {
        "msg_type": "平台应答设备版本信息上报",
        f"[{msg_body.hex().upper()}]UTC时间": utc_time,
        f"[{msg_body.hex().upper()}]北京时间": localtime
    }


def parse_6007(msg_body: bytes) -> Dict:
    module_id, ota_result = struct.unpack(">2B", msg_body)
    ota_type = '模块' if module_id == 1 else 'MCU'
    ota_code = {
        0: '升级成功',
        1: '禁止升级',
        2: '外电低压升级失败',
        3: '设备名称不匹配',
        4: 'OTA版本值不匹配',
        5: '空文件错误',
        6: 'URL为空',
        7: '下载超时',
        8: '下载次数达到上限',
        9: '设备状态限制',
        10: '电池低电',
        11: '文件操作错误',
        12: 'MD5校验错误',
        13: '模块ID错误',
        14: '看文狗关闭失败'
    }
    return {
        "OTA升级结果": {
            f"[{module_id:02X}]升级类型": ota_type,
            f"[{ota_result:02X}]升级结果": ota_code.get(ota_result, f"未知：{ota_result}")
        }
    }


# 注册消息解析函数（消息ID -> 解析函数）
MSG_PARSERS = {
    MSG_ID_PLATFORM_RESPONSE: parse_8001,
    MSG_ID_DEVICE_RESPONSE: parse_0001,
    MSG_ID_DEVICE_REGISTER: parse_0100,
    MSG_ID_DEVICE_REGISTER_ACK: parse_8100,
    MSG_ID_DEVICE_LOGIN: parse_0102,
    # MSG_ID_TERMINER_LOGINOUT: parse_0003,
    MSG_ID_LOCATION_REPORT: parse_0200,
    MSG_ID_BLIND_SPOT_REPORT: parse_0704,
    MSG_ID_HEARTBEAT: parse_0002,
    MSG_ID_TEXT_MESSAGE_REPORT: parse_6006,
    MSG_ID_TEXT_DISTRIBUTE: parse_8300,
    MSG_ID_TERMINER_CONTROL: parse_8105,
    MSG_ID_VERSION_REPORT: parse_0105,
    MSG_ID_VERSION_REPORT_ACK: parse_8005,
    MSG_ID_OTA_RESULT: parse_6007,

}

# ------------------------------
# 主流程：验证与解析
# ------------------------------
def parse_jt808(hex_str: str, debug: bool = False) -> Tuple[bool, str, Optional[Dict]]:
    """
    验证JT808协议数据并解析内容
    :param hex_str: 十六进制字符串
    :param debug: 是否打印调试信息
    :return: (是否合法, 提示信息, 解析结果)
    """
    try:
        # 校验数据
        if not is_hexadecimal(hex_str):
            return False, "⚠️ 输入的数据不符合16进制格式！", None
        # 1. 转换为字节流
        frame_bytes = hex_to_bytes(hex_str)
        if debug:
            print(f"原始字节流: {frame_bytes.hex().upper()}")
        if len(frame_bytes) < 4:
            return False, "⚠️ 帧长度过短（至少4字节）", None

        # 2. 验证起始/结束符
        if frame_bytes[0] != JT808_START_END or frame_bytes[-1] != JT808_START_END:
            return False, f"⚠️ 起始/结束符错误（应为0x7e，实际首尾:0x{frame_bytes[0]:02x},0x{frame_bytes[-1]:02x}）", None

        # 3. 反转义内容（去除首尾符后）
        content = frame_bytes[1:-1]
        unescaped_content = unescape(content)  # 转义还原
        if debug:
            print(f"转义还原后的内容: {unescaped_content.hex().upper()}")
        if len(unescaped_content) < 1:
            return False, "⚠️ 帧内容为空", None

        # 4. 校验码验证
        checksum = unescaped_content[-1]
        effective_data = unescaped_content[:-1]  # 消息头 + 消息体
        calculated_checksum = calculate_checksum(effective_data)
        if debug:
            print(f"校验码验证: 实际0x{checksum:02x}, 计算0x{calculated_checksum:02x}")
        if calculated_checksum != checksum:
            return False, f"⚠️ 校验码错误（实际:0x{checksum:02x}, 计算:0x{calculated_checksum:02x}）", None

        # 5. 解析消息头（12个字节）
        if len(effective_data) < 12:
            return False, "⚠️ 消息头不完整（需12字节）", None

        bit10 = (effective_data[2] >> 10) & 1
        bit10_12 = (effective_data[2] >> 10) & 0x07
        if bit10:
            data_encrypt = "RSA算法加密"
        elif bit10_12 != 0:
            data_encrypt = "保留"
        else:
            data_encrypt = "不加密"

        header = {
            "msg_id": (effective_data[0] << 8) | effective_data[1],
            "msg_body_attr": {
                "value": f"0x{(effective_data[2] << 8) | effective_data[3]:04X}",
                "body_length": (effective_data[2] << 8 | effective_data[3]) & 0x3FF,  # 低10位为长度
                "is_encrypted": data_encrypt,  # 加密标志（bit10~bit12）
                "has_subpackage": '分包' if ((effective_data[2] >> 13) & 0x1) else '不分包',  # 分包标志（bit13）
                "reserve": bin((effective_data[2] >> 14) & 0x3)[2:].zfill(2)  # bit14~bit15保留
            },
            "terminal_phone": bcd_to_str(effective_data[4:10]),  # 6字节BCD
            "msg_seq": (effective_data[10] << 8) | effective_data[11]
        }

        # 6. 验证消息体长度
        msg_body = effective_data[12:]

        if len(msg_body) != header["msg_body_attr"]["body_length"]:
            return False, f"⚠️ 消息体长度不匹配（实际:{len(msg_body)}, 预期:{header["msg_body_attr"]["body_length"]}）", header

        show_data = {
            f"[{JT808_START_END:02X}]开始": JT808_START_END,
            "消息头": {
                f"[{header["msg_id"]:04X}]消息ID": header["msg_id"],
                "消息体属性": {
                    "Value": header["msg_body_attr"]['value'],
                    "[bit0~bit9]消息体长度": header["msg_body_attr"]['body_length'],
                    "[bit10~bit12]数据加密": header["msg_body_attr"]['is_encrypted'],
                    "[bit13]分包": header["msg_body_attr"]['has_subpackage'],
                    "[bit14~bit15]": header["msg_body_attr"]['reserve'],
                }
            },
            f"[{header['terminal_phone']}]终端号码": header["terminal_phone"],
            f"[{header['msg_seq']:04X}]消息流水号": header['msg_seq'],
            "消息体": '',
            f"[{checksum:02X}]校验码": checksum,
            f"[{JT808_START_END:02X}]结束": JT808_START_END
        }

        # 7. 解析消息体（根据消息ID）
        msg_id = header["msg_id"]
        if msg_id not in MSG_PARSERS:
            show_data['消息体'] = msg_body.hex()
            return True, f"消息合法，但未实现消息ID=0x{msg_id:04x}的解析", show_data

        # 调用对应解析函数
        body_parsed = MSG_PARSERS[msg_id](msg_body)
        show_data['消息体'] = body_parsed
        return True, "数据合法且解析成功", show_data
    except Exception as e:
        return False, f"解析失败：{str(e)}", None


# if __name__ == '__main__':
#
#     test_0200_gps = "7e0200009c045038354346013d000000000000040001587c6406ca3c74003800000000250911143132010400000000eb78000c00b28986081703248026187100060089fffffffe000600c5ffe7ffe70004002d3057001100d5313233343536373839303132333437000600e5ffffffff000b00d801cc0028660998f741002a00e00025002700230027003700130027000c0015002b000e000e001a003a0014002100280027002300247c7e"
#     test_ = "7e00020000050764008195000d7d017e"
#     t_8005 = "7e8005000405076400802600016906cc36d57e"
#     t_blind2 = "7e0704025b0220000224520013000501007600000000000000020155a654068326ae0055000000002511040510410104001d8aebeb52000c00b28986049910217079605200060089fffffffe000600c5ffe7fdef000600e5ffffffff002a00e000000000000000000000000000000000000000000000000000000000000000000000000000000000007600000000000000020155a654068326ae0055000000002511040511110104001d8aebeb52000c00b28986049910217079605200060089fffffffe000600c5ffe7fdef000600e5ffffffff002a00e000000000000000000000000000000000000000000000000000000000000000000000000000000000007600000000000000020155a670068326cf0040000000be2511040511410104001d8aeceb52000c00b28986049910217079605200060089fffffffe000600c5ffe7fdef000600e5ffffffff002a00e000000000000000000000000000000000000000000000000000000000000000000000000000000000007600000000000000020155a6170683269e003b004600b72511040512120104001d8aeceb52000c00b28986049910217079605200060089fffffffe000600c5ffe7fdef000600e5ffffffff002a00e000000000000000000000000000000000000000000000000000000000000000000000000000000000007600000000000000020155a5e6068326ef003e000000b72511040512420104001d8aeceb52000c00b28986049910217079605200060089fffffffe000600c5ffe7fdef000600e5ffffffff002a00e000000000000000000000000000000000000000000000000000000000000000000000000000000000547e"
#     t_blind = "7e070400a10450383543470097000101009c000000000000000001587c4d06ca3c66003900000000251104094619010400000000eb78000c00b2898600f71425fa02498800060089fffffffe000600c5ffe7fde70004002d2dea001100d5383635353330303737383230383834000600e5ffffffff000b00d801cc00286602b9e403002a00e00010000e0021001d0010001000160029001000100014002b00100012000e000e0013000c00100014c57e"
#     is_valid, msg, r = parse_jt808(t_blind, debug=False)
#     print(f"结果: {msg}")
#     if is_valid:
#         import json
#
#         print("解析结果:")
#         print(json.dumps(r, ensure_ascii=False, indent=2))
