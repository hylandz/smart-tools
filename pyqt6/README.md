# jt808协议解析

## log

dos命令查看知道文件夹（ProtocolParserLogs）路径

`dir %USERPROFILE%\ProtocolParserLogs`

## 项目命令规则

在 Python 项目中，遵循统一的命名规范能显著提升代码可读性和协作效率。核心规范主要基于 **PEP 8**（Python 官方风格指南），以下是关键要点：

---

### **1. 包（Package）与模块（Module）**

- **包**（文件夹）：**全小写**，短名词，避免下划线（除非必需）  
  ✅ 推荐：`utils`、`data_processing`  
  ❌ 避免：`DataProcessor`、`myPackage`

- **模块**（`.py` 文件）：**全小写**，可含下划线  
  ✅ 推荐：`file_io.py`、`config.py`  
  ❌ 避免：`FileIO.py`、`myModule.py`

---

### **2. 类（Class）**

- **大驼峰式**（CapWords），首字母大写，不含下划线  
  ✅ 推荐：`class DatabaseConnection`、`class UserProfile`  
  ❌ 避免：`class database_connection`

---

### **3. 函数（Function）与方法（Method）**

- **全小写 + 下划线分隔**（snake_case）  
  ✅ 推荐：`def calculate_total()`、`def get_user_data()`  
  ❌ 避免：`def CalculateTotal()`

- **私有方法**：前缀单下划线（约定私有，非强制）  
  ✅ 示例：`def _internal_helper():`

---

### **4. 变量（Variable）与属性（Attribute）**

- **全小写 + 下划线分隔**（snake_case）  
  ✅ 推荐：`user_id`、`max_retries`  
  ❌ 避免：`userId`、`MaxRetries`

- **常量**：**全大写 + 下划线分隔**  
  ✅ 推荐：`MAX_CONNECTIONS = 100`、`DEFAULT_TIMEOUT`

- **私有属性**：前缀单下划线  
  ✅ 示例：`self._internal_cache = {}`

---

### **5. 异常（Exception）**

- **大驼峰式**，后缀通常为 `Error` 或 `Exception`  
  ✅ 推荐：`class ValidationError(Exception)`、`class ApiTimeoutError`

---

### **6. 避免的命名**

- **混淆字符**：`l`（小写L）、`O`（大写O）、`I`（大写i）等易混字母  
- **保留关键字**：避免 `str`、`list`、`dict` 等覆盖内置名称  
- **无意义名**：避免 `tmp`、`data`、`var` 等模糊名称（除非作用域极小）

---

### **7. 特殊约定**

- **双下划线开头**（`__`）：触发名称改写（Name Mangling），用于避免子类命名冲突  
  ✅ 示例：`__private_var` → 实际被改为 `_ClassName__private_var`

- **单下划线结尾**（`_`）：避免与关键字冲突  
  ✅ 示例：`class_`、`type_`

---

### **8. 项目目录结构示例**

```
my_project/                  # 项目根目录（全小写）
├── src/                     # 源码目录
│   ├── utils/               # 包（全小写）
│   │   ├── file_io.py       # 模块（snake_case）
│   │   └── __init__.py
│   └── models.py            # 包含类定义
├── tests/                   # 测试目录
│   └── test_utils.py        # 测试模块（test_前缀）
├── config.py                # 配置文件
└── README.md                # 项目文档
```

---

### **关键原则**

1. **一致性**：整个项目保持统一风格  
2. **描述性**：名称应清晰表达用途（如 `calculate_tax()` 优于 `calc()`）  
3. **简洁性**：在明确的前提下尽量简短（如 `index` 优于 `element_index`）

> 📌 **工具推荐**：使用 `flake8`、`pylint` 或 IDE 插件自动检查命名规范。

遵循这些规范能让代码更易维护，减少团队协作成本！


### 数据类型

**元组**
元组（tuple）与列表类似，不同之处在于元组的元素不能修改，元组使用小括号 ( )
tuple = ( 'abcd', 786 , 2.23, 'runoob', 70.2  )
**列表**
List（列表） 是 Python 中使用最频繁的数据类型。列表使用方括号 [ ]。
列表可以完成大多数集合类的数据结构实现。列表中元素的类型可以不相同，它支持数字，字符串甚至可以包含列表（所谓嵌套）
list = [ 'abcd', 786 , 2.23, 'runoob', 70.2 ]
**集合**
集合（set）是一个无序的不重复元素序列。
set1 = {1, 2, 3, 4}
**字典**
字典是另一种可变容器模型，且可存储任意类型对象，{k1:v1,k2:v2}
tinydict = {'name': 'runoob', 'likes': 123, 'url': 'www.runoob.com'}

## struct模块用法

### unpack方法

```python
struct.unpack(format, buffer)
```

+ format：格式字符串，定义了二进制数据的解析规则（如数据类型、字节顺序、对齐方式等）。
+ buffer：待解析的二进制数据（bytes 或 bytearray 类型）。
+ 返回值：一个元组，包含解析后的多个值（数量与格式字符串中定义的字段数一致）。

关键：格式字符串（`format`）

格式字符串由 **格式字符** 和 **修饰符** 组成，用于指定数据的解析方式。

#### 1. 字节顺序（字节序）修饰符

默认使用本地字节序（与当前系统一致），可通过以下修饰符指定：

| 修饰符 | 含义                                            | 示例场景                 |
| ------ | ----------------------------------------------- | ------------------------ |
| `@`    | 本地字节序（默认）                              | 依赖当前系统的字节序     |
| `=`    | 标准字节序（不对齐）                            | 跨平台解析（无对齐填充） |
| `<`    | 小端字节序（little-endian）(高位在后，低位在前) | 如 x86 架构 CPU          |
| `>`    | 大端字节序（big-endian）(高位在前，低位在后)    | 如网络协议（TCP/IP）     |
| `!`    | 网络字节序（同 `>`）                            | 网络数据传输（推荐）     |

#### 2. 常用格式字符（数据类型）

| 格式字符 | 对应 Python 类型 | 字节数   | 说明                                              |
| -------- | ---------------- | -------- | ------------------------------------------------- |
| `b`      | int              | 1        | 有符号字节                                        |
| `B`      | int              | 1        | 无符号字节                                        |
| `h`      | int              | 2        | 有符号短整数                                      |
| `H`      | int              | 2        | 无符号短整数                                      |
| `i`      | int              | 4        | 有符号整数（根据系统可能不同，推荐用 `l` 或 `q`） |
| `I`      | int              | 4        | 无符号整数                                        |
| `l`      | int              | 4        | 有符号长整数                                      |
| `L`      | int              | 4        | 无符号长整数                                      |
| `q`      | int              | 8        | 有符号长 long 整数                                |
| `Q`      | int              | 8        | 无符号长 long 整数                                |
| `f`      | float            | 4        | 单精度浮点数                                      |
| `d`      | float            | 8        | 双精度浮点数                                      |
| `s`      | bytes            | 指定长度 | 字节串（需指定长度，如 `5s`）                     |
| `p`      | bytes            | 可变     | 带前缀的 Pascal 字符串                            |

> 注意：格式字符的大小写通常区分有符号 / 无符号（如 `h` 是有符号，`H` 是无符号）。

#### 示例：解析二进制数据

假设我们有一段二进制数据（模拟网络协议中的一个数据包），需要解析出其中的各个字段

##### 示例1：基础用法

```python
import struct

# 二进制数据（16进制表示为：01 02 00 03 41 42 43 44）
data = b'\x01\x02\x00\x03ABCD'

# 格式字符串：
# > ：大端字节序
# H ：无符号短整数（2字节）
# I ：无符号整数（4字节）
# 4s：4字节字符串
format_str = '>H I 4s'

# 解析
result = struct.unpack(format_str, data)
print(result)  # 输出：(513, 768, b'ABCD')
```

- 解析说明：
  - `H` 解析前 2 字节 `01 02` → 大端字节序下为 `0x0102 = 258 + 256 = 513`
  - `I` 解析接下来 4 字节 `00 03 00 00` → 大端字节序下为 `0x00030000 = 196608`
  - `4s` 解析最后 4 字节 → `b'ABCD'`

##### 示例2：处理浮点数

```python
import struct

# 二进制数据（表示 3.14159 单精度浮点数）
float_data = b'\xdb\x0fI@'

# 解析单精度浮点数（格式字符 'f'）
num = struct.unpack('f', float_data)[0]
print(num)  # 输出：3.141590118408203
```

##### 示例3：解析带字节序的网络数据

网络协议（如 TCP/IP）通常使用大端字节序，解析时推荐用 `!` 修饰符：

```python
import struct

# 模拟一个网络数据包：2字节端口号 + 4字节IP地址
net_data = b'\x1f\x90\xc0\xa8\x01\x01'  # 端口号 8080，IP 192.168.1.1

# 解析：! 表示网络字节序，H 端口号，4B 4个字节（IP地址）
port, ip1, ip2, ip3, ip4 = struct.unpack('!H 4B', net_data)

print(f"端口号：{port}")  # 输出：8080
print(f"IP地址：{ip1}.{ip2}.{ip3}.{ip4}")  # 输出：192.168.1.1
```

注意事项

1. **字节长度匹配**：`buffer` 的长度必须与格式字符串计算的总字节数一致，否则会抛出 `struct.error`。
   例如，`format_str = '>HI'` 对应 2 + 4 = 6 字节，若 `buffer` 长度不是 6 则报错。

2. **字节序影响结果**：同一二进制数据用不同字节序解析会得到不同结果。
   例如，`b'\x00\x01'` 用 `'>H'` 解析为 1，用 `'<H'` 解析为 256。

3. **字符串处理**：`s` 格式字符解析的是 `bytes` 类型，如需字符串需用 `decode()` 转换：

   ```python
   import struct
   s_bytes = struct.unpack('4s', b'ABCD')[0]
   s_str = s_bytes.decode('utf-8')  # 得到 'ABCD'
   ```

4. **对齐问题**：默认修饰符 `@` 会根据系统进行字节对齐（可能添加填充字节），跨平台解析建议用 `=` 或 `!` 避免对齐差异。

### pack方法

在 Python 中，`struct.pack` 是 `struct` 模块提供的核心函数之一，用于将 Python 数据类型（如整数、浮点数、字符串等）按照指定的**格式字符串**打包成二进制字节流（`bytes` 类型）。这在处理二进制文件、网络通信、协议解析等场景中非常常用。

```python
import struct

result = struct.pack(format, v1, v2, ...)
```

- 参数说明：
  - `format`：格式字符串，指定后续数据的类型、字节顺序、对齐方式等。
  - `v1, v2, ...`：要打包的 Python 数据（数量需与格式字符串中指定的类型数量一致）。
- **返回值**：打包后的二进制字节流（`bytes` 类型）。

关键：格式字符串

格式字符串由**字节顺序指示符**、**数据类型字符**和可选的**重复计数**组成，例如 `'>i4sf'` 表示 “大端字节序，一个 int、4 个字节的字符串、一个 float”。

#### 1. 字节顺序指示符（可选）

默认使用系统原生字节序，可通过以下符号指定：

| 符号 | 含义                           |
| ---- | ------------------------------ |
| `@`  | 原生字节序（默认，与系统相关） |
| `=`  | 原生字节序，但不考虑对齐       |
| `<`  | 小端字节序（little-endian）    |
| `>`  | 大端字节序（big-endian）       |
| `!`  | 网络字节序（等同于大端，`>`）  |

#### 2. 常用数据类型字符

| 格式字符 | 对应 Python 类型 | 字节数   | 说明                                            |
| -------- | ---------------- | -------- | ----------------------------------------------- |
| `b`      | int              | 1        | 有符号字节                                      |
| `B`      | int              | 1        | 无符号字节                                      |
| `h`      | int              | 2        | 有符号短整数                                    |
| `H`      | int              | 2        | 无符号短整数                                    |
| `i`      | int              | 4        | 有符号整数（原生大小）                          |
| `I`      | int              | 4        | 无符号整数（原生大小）                          |
| `l`      | int              | 4        | 有符号长整数（同 `i`）                          |
| `L`      | int              | 4        | 无符号长整数（同 `I`）                          |
| `q`      | int              | 8        | 有符号长 long 整数                              |
| `Q`      | int              | 8        | 无符号长 long 整数                              |
| `f`      | float            | 4        | 单精度浮点数                                    |
| `d`      | float            | 8        | 双精度浮点数                                    |
| `s`      | bytes            | 指定长度 | 固定长度字符串（需加前缀，如 `4s` 表示 4 字节） |

#### 示例用法

打包基本类型

```python
import struct

# 格式：大端字节序（>），一个int（i），一个float（f）
data = struct.pack('>if', 123, 3.14)
print(data)  # b'\x00\x00\x00{' 是123的大端4字节表示，b'@\t\x1e\xb8'是3.14的4字节float表示
# 输出：b'\x00\x00\x00{\x40\t\x1e\xb8'
```

打包字符串（固定长度）

```python
# 格式：小端字节序（<），3字节字符串（3s），一个无符号短整数（H）
data = struct.pack('<3sH', b"abc", 255)
print(data)  # b'abc\xff\x00'（255的小端2字节是\xff\x00）
```

## 一个整数获取某bit位的值

传一个数字，分别获取的他的bit0到bit9位，bit10到bit12位，bit13位，bit14到bit15位

> 不一定是整数参数，可以是：字节/字符串，也都是先转成数字

位运算的核心规律：

无论提取单个位还是连续多位，本质都是先将目标位段 “移动” 到最低位，再用 “掩码” 保留目标位、过滤其他位

**步骤1：右移定位**

右移多少位？看起始索引是多少，就移多少，如bit2~bit9,右移2位；bit3，右移3位

**步骤2：掩码筛选**

用一个 “掩码” 数字（16进制数）与右移后的结果做与运算`&`，只保留目标位段，过滤其他高位，如：

- 长度 1 → 掩码 `0b1`（即 1）
- 长度 2 → 掩码 `0b11`（即 3）
- 长度 3 → 掩码 `0b111`（即 7）
- 长度 n → 掩码 `2^n - 1`（通用公式）

规律验证：提取 bit0~bit9、bit10~bit12、bit13、bit14~bit15

| 目标位段    | 起始索引 (shift) | 长度 (n) | 右移操作       | 掩码 (mask=2^n-1)  | 完整提取公式           |
| ----------- | ---------------- | -------- | -------------- | ------------------ | ---------------------- |
| bit0~bit9   | 0                | 10       | `number >> 0`  | 2^10-1=1023(0x3FF) | `number & 0x3FF`       |
| bit10~bit12 | 10               | 3        | `number >> 10` | 2^3-1=7(0x7)       | `(number >> 10) & 0x7` |
| bit13       | 13               | 1        | `number >> 13` | 2^1-1=1(0x1)       | `(number >> 13) & 0x1` |
| bit14~bit15 | 14               | 2        | `number >> 14` | 2^2-1=3(0x3)       | `(number >> 14) & 0x3` |

封装的方法：

```python
def extract_bits(number, start_index, length):
    """
    提取数字中从start_index开始、长度为length的位段
    """
    shift = start_index          # 步骤1：右移的位数
    mask = (1 << length) - 1    # 步骤2：生成掩码（2^length - 1）
    return (number >> shift) & mask
```

高效率的方法使用位运算

```python
def extract_bit_ranges(number):
    """
    从数字中提取多个位段
    
    参数:
        number: 输入的数字
        
    返回:
        dict: 包含各个位段值的字典
    """
    # 如果是字节数据，先转成数字
    num = int.from_bytes(byte_data, byteorder='big', signed=False)
    
    # 提取bit0~bit9位（共10位）
    # 与0x3FF（二进制10个1）做与运算保留这10位
    bits0_9 = number & 0x3FF
    
    # 提取bit10~bit12位（共3位）
    # 先右移10位，再与0x7（二进制111）做与运算保留这3位
    bits10_12 = (number >> 10) & 0x7
    
    # 提取bit13位（1位）
    # 先右移13位，再与0x1做与运算保留这1位
    bit13 = (number >> 13) & 0x1
    
    # 提取bit14~bit15位（共2位）
    # 先右移14位，再与0x3（二进制11）做与运算保留这2位
    bits14_15 = (number >> 14) & 0x3
    
    return {
        'bits0_9': bits0_9,
        'bits10_12': bits10_12,
        'bit13': bit13,
        'bits14_15': bits14_15
    }
# 测试示例
if __name__ == "__main__":
    # 构造一个测试数字，使各个位段有明显特征
    # 0b11 1 101 1111111111（从高位到低位：bit14-15, bit13, bit10-12, bit0-9）
    test_num = (0b11 << 14) | (0b1 << 13) | (0b101 << 10) | 0b1111111111
    
    print(f"测试数字: {test_num:#x} (十进制: {test_num})")
    print(f"二进制表示: {bin(test_num)[2:].zfill(16)} (补全16位)")
    
    # 提取各个位段
    result = extract_bit_ranges(test_num)
    
    # 打印结果
    print("\n提取结果:")
    print(f"bit0~bit9: {result['bits0_9']} (二进制: {bin(result['bits0_9'])[2:].zfill(10)})")
    print(f"bit10~bit12: {result['bits10_12']} (二进制: {bin(result['bits10_12'])[2:].zfill(3)})")
    print(f"bit13: {result['bit13']} (二进制: {result['bit13']})")
    print(f"bit14~bit15: {result['bits14_15']} (二进制: {bin(result['bits14_15'])[2:].zfill(2)})")
```

## 一个整数判断某bit位是否为1

某个bit位，它的值就只有0或1，判断是不是为1，高效率的方法：位运算再&本身（1<< n）& num

如：num = 10（二进制：1010）

```python
def is_bit_set(num: int, n: int) -> bool:
    """
    判断整数num的第n位（bit）是否为1
    :param num: 待检测的整数
    :param n: 位索引（从0开始，bit0为最低位）
    :return: 第n位为1返回True，否则返回False
    """
    # 检查n是否为非负整数（位索引不能为负数）
    if not isinstance(n, int) or n < 0:
        raise ValueError("位索引n必须是非负整数")
    
    # 构造掩码：1左移n位，使第n位为1，其他位为0
    mask = 1 << n
    
    # 与运算：若结果不为0，则第n位为1
    return (num & mask) != 0
```

### 测试结果解析

对于 `test_num = 10`（二进制 `1010`）：

- `bit0`（最右位）：`0` → 返回 `False`
- `bit1`：`1` → 返回 `True`
- `bit2`：`0` → 返回 `False`
- `bit3`：`1` → 返回 `True`

### 关键说明

1. **位索引的有效性**：对于 32 位整数，`n` 的有效范围是 `0~31`；对于 64 位整数，`n` 有效范围是 `0~63`。超出范围的 `n` 会导致结果不准确（但 Python 整数支持无限位，仅需保证 `n≥0`）。
2. **负数处理**：Python 中负数以 “补码” 形式存储，但上述方法同样适用（会检测补码中对应位是否为 1）。
3. **效率**：位运算属于底层操作，时间复杂度为 `O(1)`，效率极高，适合高频调用场景（如协议解析、权限判断等）。

通过这种方法，可以快速准确地判断任意整数的某一位是否为 1，是底层开发、嵌入式编程、协议解析等场景的常用技巧。

# PyQt5

## 简介

PyQt 是一个 GUI 小部件工具包，

Python 安装pyqt5插件：

```shell
pip install PyQt5
```

### 常用模块

- **QtCore** − 其他模块使用的核心非 GUI 类
- **QtGui** − 图形用户界面组件
- **QtMultimedia** − 低级多媒体编程类
- **QtNetwork** − 网络编程类
- **QtOpenGL** − OpenGL 支持类
- **QtScript** − 用于评估 Qt 脚本的类
- **QtSql** − 使用 SQL 进行数据库集成的类
- **QtSvg** − 显示 SVG 文件内容的类
- **QtWebKit** − 用于呈现和编辑 HTML 的类
- **QtXml** − 处理 XML 的类
- **QtWidgets** − 用于创建经典桌面风格 UI 的类
- **QtDesigner** − 用于扩展 Qt Designer 的类



# 语法记录

## Path类

pathlib工具库，

`Path(root_dir).mkdir(parents=True, exist_ok=True)`

## 创建自定义数据类型

+ 使用普通类定义
+ 使用数据类
+ 使用命名元组

### 使用类

```python
from datetime import datetime
from typing import Optional

class UpgradeData:
    """升级数据自定义类型"""
    
    def __init__(self, 
                 updatetime: Optional[datetime] = None,
                 size1: Optional[int] = None,
                 url1: Optional[str] = None,
                 size2: Optional[int] = None,
                 url2: Optional[str] = None):
        """
        初始化升级数据
        
        Args:
            updatetime: 更新时间
            size1: 文件1大小
            url1: 文件1URL
            size2: 文件2大小
            url2: 文件2URL
        """
        self.updatetime = updatetime or datetime.now()
        self.size1 = size1
        self.url1 = url1
        self.size2 = size2
        self.url2 = url2
    
    def __str__(self) -> str:
        """返回对象的字符串表示"""
        return (f"UpgradeData(updatetime={self.updatetime}, "
                f"size1={self.size1}, url1={self.url1}, "
                f"size2={self.size2}, url2={self.url2})")
    
    def __repr__(self) -> str:
        """返回对象的官方字符串表示"""
        return self.__str__()
    
    def to_dict(self) -> dict:
        """将对象转换为字典"""
        return {
            'updatetime': self.updatetime,
            'size1': self.size1,
            'url1': self.url1,
            'size2': self.size2,
            'url2': self.url2
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UpgradeData':
        """从字典创建对象"""
        return cls(
            updatetime=data.get('updatetime'),
            size1=data.get('size1'),
            url1=data.get('url1'),
            size2=data.get('size2'),
            url2=data.get('url2')
        )
    
    def is_valid(self) -> bool:
        """检查数据是否有效"""
        return all([self.size1, self.url1])
```



### 使用数据类（推荐）

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class UpgradeData:
    """升级数据自定义类型（使用数据类）"""
    
    updatetime: datetime = field(default_factory=datetime.now)
    size1: Optional[int] = None
    url1: Optional[str] = None
    size2: Optional[int] = None
    url2: Optional[str] = None
    
    def to_dict(self) -> dict:
        """将对象转换为字典"""
        return {
            'updatetime': self.updatetime,
            'size1': self.size1,
            'url1': self.url1,
            'size2': self.size2,
            'url2': self.url2
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UpgradeData':
        """从字典创建对象"""
        return cls(
            updatetime=data.get('updatetime', datetime.now()),
            size1=data.get('size1'),
            url1=data.get('url1'),
            size2=data.get('size2'),
            url2=data.get('url2')
        )
    
    def is_valid(self) -> bool:
        """检查数据是否有效"""
        return all([self.size1, self.url1])
```

### 方法三：使用命名元组

```python
from collections import namedtuple
from datetime import datetime
from typing import Optional

# 定义命名元组
UpgradeData = namedtuple('UpgradeData', ['updatetime', 'size1', 'url1', 'size2', 'url2'])

# 添加额外的方法（如果需要）
def create_upgrade_data(size1: Optional[int] = None,
                       url1: Optional[str] = None,
                       size2: Optional[int] = None,
                       url2: Optional[str] = None) -> UpgradeData:
    """创建升级数据对象"""
    return UpgradeData(
        updatetime=datetime.now(),
        size1=size1,
        url1=url1,
        size2=size2,
        url2=url2
    )

def is_valid_upgrade_data(data: UpgradeData) -> bool:
    """检查数据是否有效"""
    return all([data.size1, data.url1])
```

### 总结

1. **普通类**：最灵活，可以完全自定义
2. **数据类**（推荐）：简洁，自动生成常用方法
3. **命名元组**：轻量级，不可变

对于您的需求，我推荐使用数据类（方法二），因为它提供了最好的平衡：简洁的语法、自动生成的方法、类型提示支持，并且易于扩展。

# PyQt6的信号与槽机制

PyQt 使用**信号（Signal）**和**槽（Slot）**机制处理事件。

PyQt 的信号和槽机制是用于对象之间通信的核心机制。

- 信号(Signal):  PyQt 控件（或自定义对象），当特定事件发生时发出的通知。例如：
  - 按钮的点击（clicked）；
  - 文本框的文本变化（textChanged）。
- 槽(Slot): 响应信号的函数或方法。可以是 PyQt 内置槽，也可以是自定义函数。
- 连接(Connect): 信号与槽关联是通过`connect()`方法，使信号发出时槽自动执行



## 一、内置信号与槽

### 1. 控件内置信号与自定义槽的连接

最常见的场景：用户点击按钮，触发自定义函数（如显示消息）。

```python
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("信号与槽示例")
        self.setGeometry(100, 100, 300, 200)

        # 创建按钮（内置信号的发送者）
        self.btn = QPushButton("点击我", self)
        self.btn.setGeometry(100, 80, 100, 40)

        # 关键：将按钮的clicked信号连接到自定义槽函数
        self.btn.clicked.connect(self.show_message)  # 信号 -> 槽

    # 自定义槽函数（接收信号后执行）
    def show_message(self):
        QMessageBox.information(self, "提示", "按钮被点击了！")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())
```

**逻辑说明**：

- 按钮（`self.btn`）是信号发送者，当被点击时发出`clicked`信号；
- `show_message`是自定义槽函数（接收者）；
- 通过`self.btn.clicked.connect(self.show_message)`建立关联，点击按钮时自动执行`show_message`。

### 2. 带参数的信号与槽

如果信号需要传递参数（如文本框内容变化时传递新文本），槽函数需接收对应参数，且参数类型 / 数量需与信号匹配。

示例：文本框内容变化时，实时显示到标签中。

```python
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QLabel, QVBoxLayout

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("带参数的信号与槽")
        self.setGeometry(100, 100, 300, 150)

        # 布局
        layout = QVBoxLayout()

        # 文本框（信号发送者，textChanged信号传递当前文本）
        self.edit = QLineEdit()
        layout.addWidget(self.edit)

        # 标签（用于显示文本）
        self.label = QLabel("请输入文本...")
        layout.addWidget(self.label)

        self.setLayout(layout)

        # 连接信号与槽：textChanged信号（传递str参数） -> 自定义槽函数
        self.edit.textChanged.connect(self.update_label)

    # 槽函数接收参数（与信号的参数类型匹配）
    def update_label(self, text):  # text对应文本框的当前内容
        self.label.setText(f"当前输入：{text}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())
```

**关键**：`QLineEdit`的`textChanged`信号会传递一个`str`类型的参数（当前文本），因此槽函数`update_label`必须接收一个`str`参数。

## 二、自定义信号（重点）

除了控件内置的信号，还可以在自定义类中定义自己的信号，用于特定业务逻辑的通信（如 “数据加载完成”“任务进度更新” 等）。

### 自定义信号的步骤：

1. 在类中通过`pyqtSignal`定义信号（指定参数类型，可选）；
2. 在需要的地方通过`emit()`方法发射信号；
3. 将自定义信号与槽函数连接。

示例：自定义 “进度更新” 信号，模拟任务进度条显示，（点击开始按钮，进度条显示（0%~100%））。

```python
import sys
import time
from PyQt6.QtCore import pyqtSignal, QThread
from PyQt6.QtWidgets import QApplication, QWidget, QProgressBar, QPushButton, QVBoxLayout

# 自定义线程类（用于模拟耗时任务，发送进度信号）
class WorkerThread(QThread):
    # 1. 定义自定义信号：传递int类型的进度值（0-100）
    progress_updated = pyqtSignal(int)

    def run(self):
        # 模拟任务：10步完成，每步更新进度
        for i in range(1, 101):
            time.sleep(0.1)  # 模拟耗时
            # 2. 发射信号（传递当前进度）
            self.progress_updated.emit(i)

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("自定义信号示例")
        self.setGeometry(100, 100, 300, 150)

        layout = QVBoxLayout()

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 开始按钮
        self.btn = QPushButton("开始任务")
        layout.addWidget(self.btn)

        self.setLayout(layout)

        # 创建工作线程
        self.worker = WorkerThread()
        # 3. 连接自定义信号与槽：进度更新信号 -> 更新进度条
        self.worker.progress_updated.connect(self.update_progress)

        # 按钮点击触发任务
        self.btn.clicked.connect(self.start_task)

    def start_task(self):
        self.btn.setEnabled(False)  # 禁用按钮
        self.worker.start()  # 启动线程

    # 槽函数：更新进度条
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        if value == 100:
            self.btn.setEnabled(True)  # 任务完成，启用按钮

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())
```

**逻辑说明**：

- `WorkerThread`类中用`progress_updated = pyqtSignal(int)`定义了一个传递整数的自定义信号；
- 线程运行时，通过`self.progress_updated.emit(i)`发射信号（传递当前进度）；
- 主线程中，`self.worker.progress_updated.connect(self.update_progress)`将信号与更新进度条的槽函数关联，实现进度实时显示。

## 三、信号与槽的高级用法

### 1. 一个信号连接多个槽

一个信号可以关联多个槽函数，信号发出时所有槽会按连接顺序执行。

```python
def slot1():
    print("槽函数1执行")

def slot2():
    print("槽函数2执行")

btn.clicked.connect(slot1)
btn.clicked.connect(slot2)
# 点击按钮时，先打印“槽函数1执行”，再打印“槽函数2执行”
```

### 2. 多个信号连接同一个槽

多个信号可以关联到同一个槽函数，任一信号发出时槽都会执行。

```python
def handle_event():
    print("有事件发生")

btn1.clicked.connect(handle_event)
btn2.clicked.connect(handle_event)
# 点击btn1或btn2，都会打印“有事件发生”
```

### 3. 断开连接（disconnect）

通过`disconnect()`解除信号与槽的关联（不再响应）。

```python
# 连接信号与槽
connection = btn.clicked.connect(slot_func)

# 断开连接（方式1：通过信号断开）
btn.clicked.disconnect(slot_func)

# 方式2：通过连接对象断开（PyQt6支持）
# connection.disconnect()
```

### 4. 用 lambda 表达式适配参数

如果信号与槽的参数不匹配，可通过`lambda`表达式中转。

例如：按钮点击时传递固定参数给槽函数。

```python
def show_info(msg):
    QMessageBox.information(None, "提示", msg)

# 按钮点击信号（无参数） -> 通过lambda传递参数给show_info
btn.clicked.connect(lambda: show_info("按钮被点击了！"))
```

## 四、注意事项

1. **参数匹配**：信号与槽的参数类型和数量必须兼容（信号参数可多于槽，但多余参数会被忽略）。
2. **线程安全**：PyQt 中，信号从非主线程发射时，会自动排队到主线程执行（避免 GUI 操作线程安全问题）。
3. **自定义信号定义位置**：`pyqtSignal`必须定义为类的**类属性**（不能在`__init__`中定义）。
4. PyQt5 与 PyQt6 的区别：
   - PyQt6 中信号定义用`pyqtSignal`（需从`QtCore`导入）；
   - PyQt5 中信号定义用`Signal`（从`QtCore`导入），其他逻辑基本一致。

**总结：**

信号与槽是 PyQt 的灵魂，通过 “信号发射 - 槽响应” 的机制，实现了对象间的解耦通信。无论是控件交互（如按钮点击），还是自定义业务逻辑（如任务进度条），都依赖这一机制。掌握其基本用法和自定义信号，是开发 PyQt 应用的核心基础。