import logging
from colorlog import ColoredFormatter


# 禁用Ultralytics内部日志
for name in ['ultralytics']:
    logger = logging.getLogger(name)
    logger.setLevel(logging.CRITICAL)
    logger.propagate = False


# 配置彩色日志格式
color_formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)

# 配置根日志
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# 控制台处理器（带颜色）
console_handler = logging.StreamHandler()
console_handler.setFormatter(color_formatter)


# 添加处理器
logger.addHandler(console_handler)
