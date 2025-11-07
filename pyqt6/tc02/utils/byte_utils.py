from datetime import datetime
from zoneinfo import ZoneInfo


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


def decode_iccid_bcd(iccid_bytes: bytes):
    """
    解码ICCID的BCD编码（常见于SIM卡）

    ICCID格式: 89 86 00 12 34 56 78 90 12 34 5F
    解码后: 898600123456789012345
    """
    result = ""

    for i, byte in enumerate(iccid_bytes):
        high_digit = (byte >> 4) & 0x0F
        low_digit = byte & 0x0F

        # 最后一个字节的特殊处理（可能有校验位）
        if i == len(iccid_bytes) - 1:
            if low_digit == 0x0F:  # F填充位
                result += str(high_digit)
            else:
                result += str(high_digit) + str(low_digit)
        else:
            result += str(high_digit) + str(low_digit)

    return result


def timestap_to_utc_time(time: int):
    utc_time = datetime.fromtimestamp(time, tz=ZoneInfo("UTC")).strftime('%Y-%m-%d %H:%M:%S')
    return utc_time
