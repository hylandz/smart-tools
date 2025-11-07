from enum import Enum
from pathlib import Path


class DeviceNameEnum(Enum):
    ZL_A08 = 'ZL-A08'
    ZL_A08_BD = r'ZL-A08_ML307R'
    ZL_A08_EL_GX = r'ZL-A08_307H_DU'
    TC10 = 'TC10'
    TC06_EL = 'TC06-EL-EG800K'
    A12 = r'ZL-A12_307H_DC'
    TC02_4 = 'TC02-4'
    # A01-BD-GJ版本V1.10及之后
    A01_BD_GJ_V10 = r'ZT-A01-BD-GJ-EC800K'
    # A01-EL-GJ版本V1.46及之后
    A01_EL_GJ_V46 = r'ZT-A01-EL-GJ-EC800K'
    # A01-BD版本V1.08及之前
    A01_BD_V08 = r'ZT-A01-BD-CC1177W'
    A01_BD = 'ZT-A01'
    A01_EL = 'ZT-A01'


class OtaModel:
    def __init__(self):
        self.command_head = "AT^zr_cfg:ota@"
        self.id = 0
        self.dev_name = ""
        self.software_ver = 0
        self.update_time = 0
        self.size1 = 0
        self.url1 = None
        self.size2 = 0
        self.url2 = None


class OtaCommandGenerator:
    """
    Generates OTA commands
    AT^zr_cfg:ota@
    id:0;
    devname:ZL-A08_307H_DC;
    softwarever:4;
    updatetime:0;
    size1:173862;
    url1:http://lbsupgrade.lunz.cn:8080/LBSManagement/ZL_A12_Bluetooth_MD5_1753344737.bin;
    size2:0;
    url2:
    """

    def __init__(self, single_file=True, ota_type=1):
        """"
        :param single_file: ota升级文件
        :param ota_type:ota类型，1：字符串指令，2：报文指令
        """
        self.delimiter = ";"
        self.single_file = single_file
        self.ota_type = ota_type
        self.model = OtaModel()

    def generate(self, update_id, name, ota_version) -> OtaModel:
        """
        设置升级必要参数
        :param update_id:模块1，单片机0
        :param name: 设备名称
        :param ota_version: ota版本
        :return: OtaModel
        """
        self.model.id = update_id
        self.model.dev_name = name
        self.model.software_ver = ota_version
        return self.model

    def generate_command(self, file_info: list) -> str:
        url = r"http://lbsupgrade.lunz.cn:8080/LBSManagement/"
        file_num = len(file_info)
        str_command = ""

        match self.ota_type:
            case 1:  # 字符串指令
                if self.single_file and file_num == 1:
                    # print(f"单文件:{file_num}，字符串指令：{self.ota_type}")
                    self.model.url1 = f"{url}{file_info[0][0]}"
                    self.model.size1 = file_info[0][1]
                elif self.single_file is False and file_num == 2:
                    # print(f"双文件:{file_num}，字符串指令：{self.ota_type}")
                    self.model.url1 = f"{url}{file_info[0][0]}"
                    self.model.size1 = file_info[0][1]
                    self.model.url2 = f"{url}{file_info[1][0]}"
                    self.model.size2 = file_info[1][1]
                else:
                    raise ValueError("url和size解析失败")
                str_command = f"{self.model.command_head}id:{self.model.id};devname:{self.model.dev_name};softwarever:{self.model.software_ver};updatetime:{self.model.update_time};size1:{self.model.size1};url1:{self.model.url1};size2:{self.model.size2};url2:{self.model.url2};"
            case 2:  # 报文类型指令
                # id
                self.model.id = f"{self.model.id:02X}"
                # 设备名称
                hex_device_name = self.model.dev_name.encode("utf-8").hex()
                # 长度
                byte_device_name = bytes.fromhex(hex_device_name)
                len_device_name = f"{len(byte_device_name):02X}"
                self.model.dev_name = f"{len_device_name}{hex_device_name}"
                # 软件版本
                hex_version = f"{self.model.software_ver:04X}"
                self.model.software_ver = f"01{hex_version}"
                # 更新时间
                self.model.update_time = f"{self.model.update_time:08X}"

                if self.single_file and file_num == 1:
                    # print(f"单文件:{file_num}，报文类型指令:{self.ota_type}")
                    # 文件名
                    str_single_file_name = f"{url}{file_info[0][0]}"
                    self.model.url1 = str_single_file_name.encode("utf-8").hex()
                    # 文件大小
                    self.model.size1 = f"{file_info[0][1]:08X}"
                    len_url1 = f"{len(bytes.fromhex(self.model.url1)):02X}"
                    self.model.url2 = ""
                    self.model.size2 = ""
                    len_url2 = ""
                elif self.single_file is False and file_num == 2:
                    # print(f"双文件:{file_num}，报文类型指令：{self.ota_type}")

                    self.model.url1 = f"{url}{file_info[0][0]}".encode("utf-8").hex()
                    self.model.size1 = f"{file_info[0][1]:08X}"
                    len_url1 = f"{len(bytes.fromhex(self.model.url1)):02X}"
                    self.model.url2 = f"{url}{file_info[1][0]}".encode("utf-8").hex()
                    self.model.size2 = f"{file_info[1][1]:08X}"
                    len_url2 = f"{len(bytes.fromhex(self.model.url2)):02X}"
                else:
                    raise FileExistsError("url和size解析失败")

                str_command = f"{self.model.command_head}{self.model.id}{self.model.dev_name}{self.model.software_ver}{self.model.update_time}{self.model.size1}{len_url1}{self.model.url1}{self.model.size2}{len_url2}{self.model.url2}"
            case _:
                raise FileNotFoundError("指令类型不匹配")
        return str_command

    @staticmethod
    def get_files_info(ota_path: str) -> list[tuple]:
        """
        获取指定路径下所有文件的名称和大小（递归包含子目录）
        返回格式：[(文件名, 大小), ...]
        """
        files_info = []
        try:
            # 转换为Path对象并验证路径存在
            dir_path = Path(ota_path)
            if not dir_path.exists():
                raise FileNotFoundError(f"路径不存在: {ota_path}")

            # 只遍历当前目录
            for file_path in dir_path.iterdir():  # .rglob('*')当前目录及子目录
                if file_path.is_file():  # 仅处理文件
                    try:
                        # 获取文件大小（字节）
                        size = file_path.stat().st_size
                        # 存储相对路径和大小
                        rel_path = file_path.relative_to(dir_path)
                        files_info.append((str(rel_path), size))
                    except (OSError, PermissionError) as e:
                        print(f"无法访问 {file_path}: {str(e)}")

            return files_info

        except Exception as e:
            print(f"错误发生: {str(e)}")
            return []

    def show_data(self, file_info: str):
        """
        id:0;devname:ZL-A12_307H_DC;softwarever:5;updatetime:0;size1:171388;url1:http://lbsupgrade.lunz.cn:8080/LBSManagement/ZL-A12-BT-V05_1755675494.bin;size2:0;url2:None;
        :param file_info:
        """
        try:
            search_files = self.get_files_info(file_info)
            # self.generate(update_id=1, name=A12_name, ota_version=4)
            print("***********升级参数信息*************")
            print(f"升级类型:单文件" if self.single_file else '升级类型:双文件')
            print(f"指令类型:字符串指令" if self.ota_type == 1 else '指令类型:报文类型指令')
            print(f"升级id:{self.model.id}")
            print(f"设备名称：{self.model.dev_name}")
            print(f"升级版本：{self.model.software_ver}")
            print(f"升级文件名，字节大小：{search_files}")
            print("***********升级指令*************")
            command_str = self.generate_command(search_files)
            print(command_str)
        except Exception as e:
            print(str(e))

    @staticmethod
    def human_readable_size(ota_size) -> str:
        units = ['B', 'KB', 'MB', 'GB']
        index = 0
        while ota_size >= 1024 and index < len(units) - 1:
            ota_size /= 1024
            index += 1
        return f"{ota_size:.2f} {units[index]}"


if __name__ == "__main__":
    # 升级包文件所在的目录路径
    file = "ota_file/byte_double/13"
    # 设备名称
    # dev_name = DeviceNameEnum.A01_BD_GJ_V10.value
    # # 升级文件类型：单/双文件；串口指令类型：报文/字符串
    # ocg = OtaCommandGenerator(single_file=False, ota_type=2)
    # # 升级信息：id、设备名称、ota版本
    # ocg.generate(update_id=1, name=dev_name, ota_version=275)
    # ocg.show_data(file_info=file)
    a = None
    if a:
        print('True')
    else:
        print('False')

