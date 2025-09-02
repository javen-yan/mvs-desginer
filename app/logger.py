"""
简化的日志系统 - 使用标准 Python logging
"""
import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(config=None):
    """
    设置简化的日志系统
    
    Args:
        config: 日志配置对象，如果为None则使用默认配置
    
    Returns:
        logging.Logger: 配置好的日志器
    """
    if config is None:
        # 使用默认配置
        level = os.environ.get('LOG_LEVEL', 'INFO')
        log_file = os.environ.get('LOG_FILE', 'app.log')
        log_dir = os.environ.get('LOG_DIR', 'logs')
        max_file_size = int(os.environ.get('LOG_MAX_SIZE', 10 * 1024 * 1024))
        backup_count = int(os.environ.get('LOG_BACKUP_COUNT', 5))
        enable_console = os.environ.get('LOG_CONSOLE', 'true').lower() == 'true'
        enable_file = os.environ.get('LOG_FILE_ENABLE', 'true').lower() == 'true'
        console_format = os.environ.get('LOG_CONSOLE_FORMAT', '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
        file_format = os.environ.get('LOG_FILE_FORMAT', '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    else:
        # 使用传入的配置
        level = config.level
        log_file = config.log_file
        log_dir = config.log_dir
        max_file_size = config.max_file_size
        backup_count = config.backup_count
        enable_console = config.enable_console
        enable_file = config.enable_file
        console_format = config.console_format
        file_format = config.file_format
    
    # 确保日志目录存在
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # 创建日志器
    logger = logging.getLogger('mvs_designer')
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 控制台处理器
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_formatter = logging.Formatter(console_format)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # 文件处理器
    if enable_file:
        file_path = log_path / log_file
        file_handler = RotatingFileHandler(
            file_path, 
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_formatter = logging.Formatter(file_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name=None):
    """
    获取日志器
    
    Args:
        name: 日志器名称，如果为None则返回根日志器
    
    Returns:
        logging.Logger: 日志器实例
    """
    if name:
        return logging.getLogger(f'mvs_designer.{name}')
    return logging.getLogger('mvs_designer')


# 全局日志器实例
logger = get_logger()
