import logging
import time
from pathlib import Path
from typing import List, Any

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'  # 自定义时间格式
)


def find_excel_files(root_dir: str) -> List[Any]:
    """
    Search all files in given path.
    :param root_dir: path to search
    :return: list of files
    """
    root_path = Path(root_dir)

    if not root_path.exists():
        raise ValueError(f'Root path - {root_path} does not exist')

    if not root_path.is_dir():
        raise ValueError(f'Root path - {root_path} is not a directory')

    # 仅匹配当前目录下的.xls和.xlsx文件（不递归子目录）
    # 模式说明：*.xls 表示当前目录下所有.xls文件，不含子目录
    xls_files = root_path.glob("*.xls")  # 当前目录下的.xls文件
    xlsx_files = root_path.glob("*.xlsx")  # 当前目录下的.xlsx文件

    # 合并结果并过滤为文件（排除目录）
    excel_files = []
    for file in xls_files:
        if file.is_file():
            excel_files.append(file)
    for file in xlsx_files:
        if file.is_file():
            excel_files.append(file)

    return excel_files


def analyze_excel_files(select_path: str, dev_name_prefix: str, customers_exclude: list) -> None:
    logging.info("===== 分析文件 =====")
    try:
        # 根据指定目录遍历该目录下excel文件
        file_paths = find_excel_files(select_path)
        file_num = len(file_paths)
        if file_num == 0:
            logging.info(f"该目录下的文件数量={file_num}")
            raise FileExistsError("未找到符合要求的数据表(*.xls/*.xlsx)，程序执行退出！")
    except Exception as e:
        logging.error(e)
        return

    logging.info(f"需要处理的文件数量={file_num}")
    logging.info('*' * 20)

    all_sum, all_offline_sum, result, excel_num = 0, 0, 0, 0
    start_time = time.time()

    for path in file_paths:
        excel_num += 1
        logging.info(f"正处理文件{excel_num}-={path}")
        try:
            # 读取Excel文件（假设文件名为input.xlsx）
            df = pd.read_excel(path)

            # 确保“设备”列为字符串类型（避免数字类型报错）
            df["设备"] = df["设备"].astype(str)

            # 第一步：筛选“设备”列以5开头的行
            filtered_df = df[df["设备"].str.startswith(dev_name_prefix)]

            # 第二步：删除“客户名称”为“安吉”或“三亚民生”的行
            filtered_df = filtered_df[~filtered_df["客户名称"].isin(customers_exclude)]
            # 第三步：统计“设备状态”为“离线”的总数
            sum_count = len(filtered_df)
            offline_count = (filtered_df["设备状态"] == "离线").sum()

            all_sum += sum_count
            all_offline_sum += offline_count

            # 输出结果
            logging.info(f"符合过滤条件的设备总数为：{sum_count}")
            logging.info(f"符合过滤条件的离线设备总数为：{offline_count}")
            logging.info('*' * 20)
        except Exception as ex:
            logging.error(f"处理excel表{excel_num}异常：{str(ex)}")
            logging.info('*' * 20)
            continue

    end_time = time.time()
    elapsed_time = end_time - start_time
    # 计算小时、分钟和秒
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    # 格式化输出
    formatted_time = f"{int(hours)} 时 {int(minutes):02d} 分 {seconds:.2f} 秒"

    logging.info(f"*A08设备过滤总数：{all_sum}")
    logging.info(f"*A08设备过滤离线总数：{all_offline_sum}")

    try:
        result = all_offline_sum / all_sum
    except ZeroDivisionError as zde:
        logging.error(zde)
        return

    logging.info(f"*A08设备过滤离线率：{result * 100:.2f}%")
    logging.info(f"*执行所需的时间：{formatted_time}")


if __name__ == '__main__':
    p = r"G:\Work\补亩及报表统计\离线率统计\ZL-A08离线率统计\40多W台A08设备\1011"
    clients_exclude = ["安吉租赁有限公司,亚民生旅业有限责任公司（民生）,上海东正汽车金融股份有限公司（东正）,浙江大搜车融资租赁有限公司,塔比星信息技术（深圳）有限公司,"
                       "广西通盛融资租赁有限公司,北京中交兴路车联网科技有限公司,WJJZ皖江金融租赁股份有限公司,华润集团"]

    analyze_excel_files(p, "5", clients_exclude)
