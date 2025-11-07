from decimal import Decimal, ROUND_HALF_UP


def byte_to_hexstr(byte: bytes):
    return byte.hex()


def hexstr_to_byte(hex_str: str):
    return bytes.fromhex(hex_str)


def byte_to_int(byte):
    """字节类型数据转整数"""
    return int.from_bytes(byte, byteorder='big')


def byte_to_string(b_data: bytes, encoding='utf-8'):
    """
    字节类型数据转字符串
    :param b_data: 字节数据
    :param encoding: 转字符串时解码的编码方式，默认UTF-8
    :return: string
    """
    b_str = b_data.decode(encoding=encoding, errors='replace')
    return b_str


def string_to_byte(data_str: str, encoding='utf-8'):
    """
    字符串转字节类型
    :param data_str: 字符串数据
    :param encoding: 转字节的编码U方式，默认TF-8
    :return: bytes
    """
    return data_str.encode(encoding=encoding, errors='replace')


def int_to_byte(number: int):
    """数字转字节类型"""
    if number == 0:
        # 特殊情况：0的bit_length是0，至少需要1字节
        length = 1
    else:
        # 二进制位数 → 字节数：(位数 + 7) // 8（向上取整）
        bit_length = number.bit_length()
        length = (bit_length + 7) // 8
    return number.to_bytes(length, byteorder='big', signed=False)


def str_to_hex(s: str, uppercase: bool = False) -> str:
    """字符串转十六进制"""
    hex_str = s.encode("utf-8").hex()
    return hex_str.upper() if uppercase else hex_str


def hex_to_str(h: str) -> str:
    """十六进制转字符串"""
    # 移除所有非十六进制字符（如空格、0x前缀）
    clean_hex = "".join(c for c in h if c in "0123456789abcdefABCDEF")
    try:
        return bytes.fromhex(clean_hex).decode("utf-8")
    except ValueError:
        raise ValueError("无效的十六进制字符串")


def decimal_to_hex(decimal_value: int, width: int = None):
    """
    整数转16进制，带格式
    :param decimal_value: 整数
    :param width: 位数输出，不足补0
    :return: hex_str
    """
    if width is None:
        # return hex(decimal_value)
        return f"{decimal_value:X}"  # 1 >> 1
    else:
        return f"{decimal_value:0{width}X}"  # 1:04X >> 0001


def hex_to_int(h: str) -> int:
    """16进制数转整数"""
    return int(h, 16)


def hex_to_decimal(hex_str):
    """16进制字符串转整数"""
    hex_str = hex_str.upper().lstrip("0X")
    hex_digits = "0123456789ABCDEF"
    decimal = 0
    for i, char in enumerate(reversed(hex_str)):
        decimal += hex_digits.index(char) * (16 ** i)
    return decimal


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


def optimized_hex_to_binary(hex_str: str) -> str:
    """优化版十六进制转格式化二进制"""
    # 预计算长度
    # n = len(hex_str)
    # total_bits = n * 4

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


def format_hex(hex_str: str, group_size=2) -> str:
    # 去除空格
    hex_str1 = hex_str.replace(" ", "")
    # 分组
    groups = [hex_str1[i:i + group_size] for i in range(0, len(hex_str1), group_size)]
    # 空格连接分组
    return ' '.join(groups)


def jt808_lat_lon(number: int) -> str:
    """处理经纬度数值转换"""
    num = Decimal(number)
    if num == 0:
        return "0"
    result = num / Decimal('1000000')
    result = result.quantize(Decimal('0.0000000'), rounding=ROUND_HALF_UP)
    return f"{result}"


def parse_hex_flags(hex_str):
    # 将16进制字符串转换为整数
    try:
        value = int(hex_str, 16)
    except ValueError:
        raise ValueError(f"无效的16进制字符串: {hex_str}")

    # 定义每个bit位对应的功能描述
    bit_functions = {
        0: "功能1",
        1: "功能2",
        2: "功能3",
        3: "功能4",
        # 可以根据需要扩展更多bit位
    }

    # 打印解析结果
    print(f"16进制字符串: {hex_str}")
    print(f"二进制表示: {bin(value)[2:].zfill(8)} (8位)")  # 补零到8位
    print("功能状态:")

    # 检查每个bit位
    results = {}
    for bit, func in bit_functions.items():
        # 通过位运算检查指定bit位是否为1
        is_enabled = (value & (1 << bit)) != 0
        status = "开启" if is_enabled else "关闭"
        results[func] = is_enabled
        print(f"[bit{bit}]{func}:{status}")

    return results


def get_bits_0_to_31(number):
    """
    获取数字的bit0~bit31位（从0开始计数）

    参数:
        number: 输入的数字

    返回:
        list: 索引0对应bit0，索引1对应bit1...索引31对应bit31，值为0或1
    """
    bits = []
    for i in range(32):  # 遍历bit0到bit31
        # 提取第i位：右移i位后与1做与运算，保留最低位（即原biti）
        bit_value = (number >> i) & 1
        print(f"{i}, {bit_value}")
        bits.append(bit_value)
    return bits


if __name__ == '__main__':
    # print(optimized_hex_to_binary("000600C5FFFFFFFF"))
    v = 1 or 5
    n = 7
    if n != v:
        print(n)
    else:
        print("等于")
