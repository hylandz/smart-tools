import csv
import re
from pathlib import Path

import pandas as pd


class ICCIDUtil:
    def __init__(self):
        self.all_data = []
        self.prefix_str = "000c00b2"
        self.pos = -1

    def get_data_csv(self, in_file, out_file):
        """
        数据源：csv文件
        截取字符串"000c00b2"开头，后20个字符串
        去重并导出.txt文件
        """
        prefix = self.prefix_str
        prefix_len = len(prefix)  # 前缀长度（12）
        required_length = 20  # 需要截取的字符数
        # 存储提取的数据
        extracted_data = []
        # 读取CSV文件并处理数据
        with open(in_file, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)

            for row in reader:
                if not row:  # 跳过空行
                    continue
                line = row[0].strip()  # 假设每行只有一个字段

                # 查找所有出现的前缀位置
                # pos = -1
                while True:
                    pos = line.find(prefix, self.pos + 1)  # 从下一个位置继续查找
                    if pos == -1:
                        break
                    # 计算截取范围
                    start = pos + prefix_len
                    end = start + required_length
                    # 检查长度是否足够
                    if end <= len(line):
                        extracted = line[start:end]
                        extracted_data.append(extracted)

        # 去重并保持顺序（Python 3.7+）
        unique_data = list(dict.fromkeys(extracted_data))
        # 写入输出文件
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(f"原始匹配数量={len(extracted_data)},去重后数量={len(unique_data)},结果已保存至: {out_file}\n")
            for item in unique_data:
                f.write(f"{item}\n")
        # 打印统计信息
        print(f"原始匹配数量: {len(extracted_data)}")
        print(f"去重后数量: {len(unique_data)}")
        print(f"结果已保存至: {out_file}")

    @staticmethod
    def get_data_csv_reg(in_file, out_file):
        """
        使用正则表达式去匹配，ebxx000c00b2要比000c00b2更精确
        """

        # prefix_len = len(self.prefix_str)
        reg_str = r'(?i)(eb..000c00b2)'
        pattern = re.compile(reg_str)  # 正则表达式（忽略大小写）
        required_length = 20
        extracted_data = []

        with open(in_file, 'r', encoding='utf-8', newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                if not row:  # 空行跳过
                    continue
                line = row[0].strip()  # 假设每行只有一条数据

                # 查找所有匹配项
                matches = pattern.finditer(line)
                for match in matches:
                    start_pos = match.end()  # 匹配结束位置（即后续20字符的起点）
                    end_pos = start_pos + required_length
                    # 检查长度是否足够
                    if end_pos <= len(line):
                        extracted = line[start_pos:end_pos]
                        extracted_data.append(extracted)

        unequal_data = list(dict.fromkeys(extracted_data))

        p = Path(out_file)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)

        # 输出文件命名：用数据源文件名称
        out_path = p / f"{in_file.stem}.txt"
        #
        total_sum = len(extracted_data)
        unequal_sum = len(unequal_data)

        if total_sum != 0:
            # 写入输出文件
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"原始匹配数量={total_sum},去重后数量={unequal_sum},结果已保存至: {out_path}\n")
                for item in unequal_data:
                    f.write(f"{item.upper()}\n")

        # 打印统计信息
        print("***********数据分析结果*****************")
        print(f"原始匹配数量: {total_sum}")
        print(f"去重后数量: {unequal_sum}")
        print(f"结果已保存至: {out_path}" if total_sum != 0 else f"结果已保存至: 不保存(total_sum={total_sum})")

    def get_data_from_excel(self, in_file, out_file):
        """
        数据源：excl文件
        截取字符串"000c00b2"开头，后20个字符串
        去重并导出.txt文件
        """
        # 配置参数
        prefix = self.prefix_str  # 目标前缀
        prefix_len = len(prefix)  # 前缀长度（12）
        required_length = 20  # 需要截取的字符数

        # 存储提取的数据
        extracted_data = []

        # 读取Excel文件（默认读取第一个工作表）
        df = pd.read_excel(in_file, header=None)  # header=None表示无表头

        # 遍历每一行数据
        for index, row in df.iterrows():
            line = str(row[0]).strip()  # 假设数据在第一列，转换为字符串并去空格

            # 查找所有出现的前缀位置
            pos = -1
            while True:
                pos = line.find(prefix, pos + 1)  # 从下一个位置继续查找
                if pos == -1:
                    break
                # 计算截取范围
                start = pos + prefix_len
                end = start + required_length
                # 检查长度是否足够
                if end <= len(line):
                    extracted = line[start:end]
                    extracted_data.append(extracted)

        # 去重并保持顺序（Python 3.7+）
        unique_data = list(dict.fromkeys(extracted_data))

        # 写入输出文件
        with open(out_file, "w", encoding="utf-8") as f1:
            f1.write(f"原始匹配数量={len(extracted_data)},去重后数量={len(unique_data)},结果已保存至: {out_file}\n")
            for data in unique_data:
                f1.write(f"{data}\n")

        # 打印统计信息
        print(f"原始匹配数量: {len(extracted_data)}")
        print(f"去重后数量: {len(unique_data)}")
        print(f"结果已保存至: {out_file}")

    @staticmethod
    def process_csv_files(file_path, out_path):
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"路径不存在：{file_path}")

        csv_files = []
        if path.is_file() and path.suffix.lower() == ".csv":
            csv_files.append(path)
        elif path.is_dir():
            # 不递归子文件夹
            csv_files = list(path.glob('*.csv'))
            csv_files.extend(list(path.glob('*.CSV')))
            csv_files = list(set(csv_files))
        else:
            raise ValueError(f"路径不是文件也不是目录：{file_path}")

        for csv_file in csv_files:
            print(f"处理文件：{csv_file}")
            ICCIDUtil.get_data_csv_reg(in_file=csv_file, out_file=out_path)

    @staticmethod
    def sms_command_N(path):
        if not path:
            return None

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"路径不存在：{path}")

        if path.is_file() and path.suffix.lower() == ".txt":
            with open(path, "r", encoding="utf-8") as txtfile:
                # 跳过第一行（如果文件只有1行，会报错，可加try-except处理）
                next(txtfile, None)  # 第二个参数None：若文件为空，不报错
                # 读取剩余行
                for line in txtfile:
                    content = line.strip()
                    command = f"<SPBSJ*P:BSJGPS*N:{content}>"
                    print(command)


if __name__ == '__main__':
    iu = ICCIDUtil()

    # input_file = r'G:\\Work\\批量升级\\A08设备擦除\\数据源\\110.csv'  # 输入文件名
    input_file = 'G:\\Work\\批量升级\\A08设备擦除\\阿里云数据源\\1031'
    output_unique = './result'  # 去重数据输出文件路径
    iu.process_csv_files(file_path=input_file, out_path=output_unique)
