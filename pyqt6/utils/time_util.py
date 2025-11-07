import time
from datetime import datetime
from zoneinfo import ZoneInfo


class TimeUtil:
    @staticmethod
    def convert_local_time(time_str: str) -> str:
        """
        16进制字符串时间转北京时间
        格式：北京时间 如2025-08-18 09:08:00
        :param time_str:16进制字符串，如68a27cf0
        :return 字符串
        """
        time_str = time_str.upper().lstrip("0X")
        second_time = int(time_str, 16)
        obj = datetime.fromtimestamp(second_time)
        str_time = obj.strftime('%Y-%m-%d %H:%M:%S')
        return str_time

    @staticmethod
    def convert_utc_time(time_str: str) -> str:
        """
        16进制字符串时间转UTC时间
        格式：UTC时间 如2025-01-18 09:08:00
        :param time_str: 16进制字符串，如68a27cf0
        :return: 字符串
        """
        time_str = time_str.upper().lstrip("0X")
        time_stap = int(time_str, 16)
        obj = datetime.fromtimestamp(time_stap, tz=ZoneInfo("UTC"))
        utc_time = obj.strftime('%Y-%m-%d %H:%M:%S')
        return utc_time

    @staticmethod
    def jt808_time(time_str: str) -> str:
        # 250813154816
        if len(time_str) == 12:
            year = time_str[:2]
            month = time_str[2:4]
            day = time_str[4:6]
            hour = time_str[6:8]
            mini = time_str[8:10]
            sec = time_str[10:12]
            jt808_t = f"{year}-{month}-{day} {hour}:{mini}:{sec}"

        else:
            jt808_t = f"数据长度错误：{len(time_str)}"

        return jt808_t


if __name__ == '__main__':
    t = "68eee425"
    jt808_time = "250813154816"
    lat = "01587c62"
    print(TimeUtil.convert_local_time(t))
    print(TimeUtil.convert_utc_time(t))

