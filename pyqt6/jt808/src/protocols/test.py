import time

from jt808.src.protocols.jt808_parse import parse_jt808


def measure_single_parse_time(test_data: str, loop_count: int = 100):
    """
    测量单条数据的解析耗时（多次测量取平均）
    :param test_data: 典型单条数据
    :param loop_count: 测量次数（默认100次）
    :return: 平均耗时（秒）
    """
    if loop_count < 1:
        loop_count = 1

    # 预热（避免首次执行的额外开销，如缓存加载）
    parse_jt808(test_data)

    # 开始测量
    start_time = time.perf_counter()
    for _ in range(loop_count):
        parse_jt808(test_data)  # 多次执行解析函数
    end_time = time.perf_counter()

    # 计算平均耗时（秒）
    total_time = end_time - start_time
    avg_time = total_time / loop_count
    print(f"测量{loop_count}次，总耗时：{total_time:.6f}秒")
    print(f"单条数据平均解析耗时：{avg_time:.6f}秒（约{avg_time * 1000:.2f}毫秒）")
    return avg_time


# --------------------------
# 测试执行
# --------------------------
if __name__ == "__main__":
    # 1. 准备典型单条数据（替换为你的实际数据）
    typical_data = "7e0200008f050763996108127d01000001000000000201742bcf06340a5803e000000000250903234335010400000b73eb6b000c00b28986085916257000830800060089fffffffe000600c5ffe7fdef0004002d05f2001100d5383637363836303733363632363139000600e5ffffffff002a00e0000c0010000c000c000d000d000a000c000a0011000b000c000b000d000e000b000c0007000b000b8e7e"  # 示例数据
    test_83 = "7e830000cb01599969699104d20269643a313b6465766e616d653a5a4c2d4130383b736f6674776172657665723a323b75706461746574696d653a303b73697a65313a35313230383b75726c313a687474703a2f2f6c6273757067726164652e6c756e7a2e636e3a383038302f4c42534d616e6167656d656e742f7a715f776c5f32342e62696e5f313b73697a65323a3636333634343b75726c323a687474703a2f2f6c6273757067726164652e6c756e7a2e636e3a383038302f4c42534d616e6167656d656e742f7a715f776c5f32342e62696e5f323ba27e"
    # 2. 测量（100次取平均）
    avg_ms = measure_single_parse_time(typical_data, loop_count=100) * 1000

    # 3. 根据结果判断策略, 50ms
    if avg_ms < 50:
        print("结论：单条解析耗时短，可在UI线程直接调用")
    else:
        print("结论：单条解析耗时长，建议用线程处理")
