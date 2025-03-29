import os, requests, zipfile, uuid, secrets, string, hashlib, time,socket,subprocess
from log import logging
from tqdm import tqdm
from urllib.parse import unquote
from random import shuffle
import psutil
import platform
from datetime import datetime
from datetime import time as dtime
import time
import cpuinfo
import sys 
import config

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('223.5.5.5', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def kill_pid(pid):
    shell = ""
    if sys.platform.startswith('win'):
        shell = "taskkill /PID %d /F" % (pid)
    if sys.platform.startswith('linux'):
        shell = "kill -9 %d" % (pid)
    if shell != "":
        os.system(shell)


def unzip_file(filename):
     # 自动解压处理
    if filename.lower().endswith('.zip'):
        logging.info("正在解压到: {%s}..." % (os.path.abspath("./")))
        try:
            with zipfile.ZipFile(filename, 'r') as zip_ref:
                zip_ref.extractall("./")
            logging.info(f"解压完成！共解压 {len(zip_ref.namelist())} 个文件")
        except zipfile.BadZipFile:
            logging.error("错误：文件不是有效的ZIP压缩包")
        except Exception as e:
            logging.error(f"解压过程中发生错误: {str(e)}")

def download_file(
    url, 
    filename=None,
    chunk_size=2048,
    max_retries=3,
    retry_delay=3,
    timeout=30
):
    """
    支持断点续传的可靠文件下载函数
    
    参数:
    url: 下载地址 (必需)
    filename: 保存文件名（默认从URL或headers获取）
    chunk_size: 分块大小（字节）
    max_retries: 最大重试次数
    retry_delay: 重试等待时间（秒）
    timeout: 请求超时时间（秒）
    """
    # 初始化配置
    session = requests.Session()
    retries = 0
    last_exception = None

    # 自动获取文件名逻辑
    if not filename:
        filename = _get_filename_from_url(url)
    
    # 重试循环
    while retries <= max_retries:
        try:
            # 检查现有文件
            file_exists = os.path.exists(filename)
            current_size = os.path.getsize(filename) if file_exists else 0
            
            # 设置请求头
            headers = {}
            if current_size > 0:
                headers['Range'] = f'bytes={current_size}-'

            # 发起带超时的请求
            with session.get(
                url, 
                headers=headers, 
                stream=True, 
                timeout=timeout
            ) as resp:
                resp.raise_for_status()

                # 处理文件名更新（仅在首次下载）
                if current_size == 0:
                    filename = _handle_content_disposition(resp, filename)

                # 处理不同状态码
                if resp.status_code == 206:
                    total_size = _get_total_size(resp, current_size)
                elif resp.status_code == 200:
                    if current_size > 0:
                        logging.warning("服务器不支持断点续传，重新下载")
                        current_size = 0
                        filename = f"{filename}.temp"
                    total_size = int(resp.headers.get('content-length', 0))
                else:
                    raise requests.exceptions.HTTPError(f"异常状态码: {resp.status_code}")

                # 准备下载进度条
                progress = tqdm(
                    desc=filename,
                    total=total_size,
                    initial=current_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
                )

                # 写入文件
                with open(filename, 'ab' if current_size else 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            progress.update(len(chunk))
                
                progress.close()
                _validate_download(filename, total_size)
                
                logging.info(f"\n下载完成: {os.path.abspath(filename)}")
                return True

        except (requests.exceptions.RequestException, IOError) as e:
            last_exception = e
            logging.warning(f"下载中断 ({e}), {max_retries - retries}次重试剩余...")
            logging.warning("%d秒后尝试继续下载..." % (retry_delay))
            time.sleep(retry_delay)
            retries += 1

    # 所有重试失败后
    raise Exception(f"下载失败，超过最大重试次数 {max_retries}") from last_exception

def _get_filename_from_url(url):
    """从URL提取文件名"""
    filename = unquote(url.split('/')[-1])
    return filename.split('?')[0] if '?' in filename else filename

def _handle_content_disposition(response, default_name):
    """处理Content-Disposition头"""
    if "content-disposition" in response.headers:
        try:
            parts = response.headers["content-disposition"].split("filename=")
            if len(parts) > 1:
                new_name = unquote(parts[1].strip('"\''))
                if not os.path.exists(new_name):
                    return new_name
        except Exception as e:
            logging.warning(f"解析Content-Disposition失败: {e}")
    return default_name

def _get_total_size(response, existing_size):
    """获取完整文件大小"""
    if response.headers.get("Content-Range"):
        return int(response.headers["Content-Range"].split('/')[-1])
    return existing_size + int(response.headers.get('content-length', 0))

def _validate_download(file_path, expected_size):
    """验证下载完整性"""
    actual_size = os.path.getsize(file_path)
    if actual_size < expected_size:
        raise IOError(f"文件不完整: {actual_size}/{expected_size} 字节")
    if actual_size > expected_size:
        raise IOError(f"文件异常: {actual_size}字节（预期{expected_size}字节）")

def generate_password(length=12, use_uppercase=True, use_lowercase=True, 
                     use_digits=True, use_symbols=True):
    """
    生成一个安全的随机密码
    参数:
        length: 密码长度 (默认12)
        use_uppercase: 包含大写字母 (默认True)
        use_lowercase: 包含小写字母 (默认True)
        use_digits: 包含数字 (默认True)
        use_symbols: 包含特殊符号 (默认True)
    """
    # 定义字符集
    char_sets = []
    required_chars = []
    
    if use_uppercase:
        upper = string.ascii_uppercase
        char_sets.append(upper)
        required_chars.append(secrets.choice(upper))
    if use_lowercase:
        lower = string.ascii_lowercase
        char_sets.append(lower)
        required_chars.append(secrets.choice(lower))
    if use_digits:
        digits = string.digits
        char_sets.append(digits)
        required_chars.append(secrets.choice(digits))
    if use_symbols:
        symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        char_sets.append(symbols)
        required_chars.append(secrets.choice(symbols))
    
    if not char_sets:
        raise ValueError("至少需要选择一个字符集")
    
    # 确保密码长度足够包含所有必选字符
    min_length = len(required_chars)
    if length < min_length:
        raise ValueError(f"密码长度不能小于{min_length}（必选字符数量）")
    
    # 生成剩余字符
    all_chars = ''.join(char_sets)
    remaining_length = length - min_length
    password_chars = required_chars + [secrets.choice(all_chars) for _ in range(remaining_length)]
    
    # 打乱顺序
    shuffle(password_chars)
    
    return ''.join(password_chars)

def get_uuid_v4():
    return str(uuid.uuid4())

def hash_text(text,type='md5'):
    hash = eval("hashlib." + type + "(text.encode())")
    result = hash.hexdigest().lower()
    return result


def write_file_text(filepath,content,mode='w'):
    fp = open(filepath,mode,encoding='utf-8')
    fp.write(content)
    fp.close()

def read_file_text(filepath):
    try:
        fp = open(filepath,'r',encoding='utf-8')
    except:
        fp = open(filepath,'r',encoding='gbk')
    content = fp.read()
    fp.close()
    return content

def get_timestamp(type='ms'):
    if type == 'ms':
        return int(time.time()*1000)
    if type == 's':
        return int(time.time())
    if type == 'today':
        today = datetime.today()
        today_midnight = datetime.combine(today, dtime.min)
        today_midnight_timestamp = int(today_midnight.timestamp())
        return today_midnight_timestamp

def get_cpu_info():
     # 获取 CPU 核心数（物理核心）
    cores = psutil.cpu_count(logical=False)
    
    # 使用 cpuinfo 获取详细型号
    info = cpuinfo.get_cpu_info()
    
    # 从不同平台获取更友好的型号名称
    model = info.get('brand_raw', info.get('vendor_id', platform.processor()))
    
    # 组合型号 + 核心数（例如："Intel(R) Core(TM) i5-8400 CPU @ 2.80GHz * 6"）
    formatted_model = f"{model.strip()} * {cores}"
    
    cpu_info = {
        "model": formatted_model,
        "cores": cores,
        "usage": psutil.cpu_percent(interval=1)
    }
    return cpu_info

def get_memory_info():
    mem = psutil.virtual_memory()
    memory_info = {
        "total": mem.total,
        "used": mem.used,
        "usage": mem.percent
    }
    return memory_info

def get_disk_info():
    partitions = psutil.disk_partitions()
    disk_info = {
        "total_size": 0,
        "used_space": 0,
        "usage": 0
    }
    for partition in partitions:
        usage = psutil.disk_usage(partition.mountpoint)
        disk_info["total_size"] += usage.total
        disk_info["used_space"] += usage.used
    if disk_info["total_size"] > 0:
        disk_info["usage"] = round((disk_info["used_space"] / disk_info["total_size"]) * 100,1)
    return disk_info

def get_system_version():
    system_info = {
        "system": platform.system(),
        "version": platform.version(),
        "release": platform.release()
    }
    return system_info

def get_default_mac():
    try:
        if sys.platform == 'linux':
            # Linux 系统：通过 /proc/net/route 找到默认接口
            with open("/proc/net/route", "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2 and parts[1] == '00000000':
                        interface = parts[0]
                        break
                else:
                    return "未找到默认接口"
            # 读取 MAC 地址
            mac_path = f"/sys/class/net/{interface}/address"
            if os.path.exists(mac_path):
                with open(mac_path, "r") as f:
                    return f.read().strip()
            return "MAC 地址未找到"

        elif sys.platform == 'win32':
            # Windows 系统：通过 ipconfig 解析
            result = subprocess.check_output(["ipconfig", "/all"], text=True, encoding='utf-8')
            interface = None
            for line in result.split('\n'):
                if '默认网关' in line and interface is None:
                    # 默认网关所在接口即为默认网卡
                    interface = line.split()[-1]
                if interface and f' {interface} ' in line and '物理地址' in line:
                    return line.split(':')[-1].strip()
            return "MAC 地址未找到"

        else:
            return "暂不支持此操作系统"

    except Exception as e:
        return f"获取失败: {e}"
    

def find_process_by_psutil(process_name):
    for proc in psutil.process_iter(['name']):
        if proc.info["name"] == process_name:
            return True
    return False

def calculate_file_hash(file_path, algorithm="sha256", chunk_size=4096):
    # 统一转换为小写处理
    algorithm = algorithm.lower()
    
    # 验证算法有效性
    available_algorithms = hashlib.algorithms_available
    if algorithm not in available_algorithms:
        err_msg = f"不支持的哈希算法: {algorithm}\n可用算法列表:\n"
        err_msg += "\n".join(sorted(available_algorithms))
        raise ValueError(err_msg)
    
    hash_obj = hashlib.new(algorithm)
    file_size = os.path.getsize(file_path)
    
    with open(file_path, "rb") as f:
        with tqdm(
            total=file_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc="计算文件 %s (%s)" % (algorithm.upper(),os.path.basename(file_path))
        ) as pbar:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hash_obj.update(chunk)
                pbar.update(len(chunk))
    
    return hash_obj.hexdigest()

    


def format_size(size_bytes, decimal_units=False):
    """
    将字节大小格式化为易读的单位（自动选择 KB/MB/GB）
    :param size_bytes: 字节大小
    :param decimal_units: 是否使用十进制单位（默认False，使用二进制单位）
    :return: 格式化后的字符串
    """
    base = 1000 if decimal_units else 1024
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    
    if size_bytes == 0:
        return "0 B"

    unit_index = 0
    while size_bytes >= base and unit_index < len(units) - 1:
        size_bytes /= base
        unit_index += 1

    # 根据单位决定小数精度
    precision = 0 if unit_index == 0 else 2
    return f"{size_bytes:.{precision}f} {units[unit_index]}"

def get_file_size(file_path, decimal_units=False):
    """
    获取文件大小并格式化
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    size_bytes = os.path.getsize(file_path)
    return format_size(size_bytes, decimal_units)

def get_client_id():
    if os.path.exists("./client_id"):
        return read_file_text("./client_id")
    else:
        client_id = get_uuid_v4()
        write_file_text("./client_id",client_id)
        logging.warning("生成当前设备的client_id:" + client_id)
        

 # 检查当前系统中有没有启动 clamav 
def start_up_clamav():

    if not find_process_by_psutil("clamd.exe"):
        logging.warning("Clam AV 没有启动,启动 Clam AV 主程序")
        clamav_proc = subprocess.Popen(
            os.path.abspath(config.env_clamav_path) + "\\" +"clamd.exe", 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        logging.info("启动 Clam AV 主进程...")
        init_clamd = False
        while not init_clamd:
            line = clamav_proc.stdout.readline()
            if not line:  
                break
            line = line.strip()
            if "Self checking every 600 seconds." in line:
                init_clamd = True
            sys.stdout.flush()
        logging.info("Clam AV 主进程激活成功")  
    cd = pyclamd.ClamdAgnostic()
    cd.ping()
    cd_version = cd.version()
    logging.info("Clam AV 版本:" + cd_version)
    return cd 

# pyclamav 获取病毒库版本信息
def get_virus_db_version(cd):
    try:
        cd.ping()
        version_info = cd.version()
        parts = version_info.split('/')
        if len(parts) >= 3:
            return {
                "clamav_version": parts[0].strip(),
                "virus_db_version": parts[1].strip(),
                "last_updated": parts[2].strip()
            }
        else:
            return {"error": "无法解析版本信息"}
    except ConnectionError:
        return {"error": "ClamAV守护进程连接失败"}
    except Exception as e:
        return {"error": f"发生错误: {str(e)}"}


def format_dict_key_lower(dict_data):
    data = {}
    for key in dict_data.keys():
        data[key.lower()] = dict_data[key]
    return data
