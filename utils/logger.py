"""
日志模块

提供统一的日志记录功能，支持文件和控制台输出。
"""

import logging
import os
from datetime import datetime
from typing import Optional
from pathlib import Path


class Logger:
    """
    日志管理器
    
    提供统一的日志接口，支持：
    - 文件日志输出
    - 控制台日志输出
    - 日志级别控制
    - 日志文件自动按时间命名
    """
    
    # 日志级别常量
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    def __init__(self, 
                 name: str = 'data_factory',
                 log_dir: str = 'logs',
                 level: int = logging.INFO,
                 console_output: bool = True,
                 file_output: bool = True):
        """
        初始化日志管理器
        
        Args:
            name: 日志名称
            log_dir: 日志文件目录
            level: 日志级别
            console_output: 是否输出到控制台
            file_output: 是否输出到文件
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.level = level
        
        # 创建日志目录
        if file_output:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()  # 清除已有处理器
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # 文件处理器
        if file_output:
            log_file = self.log_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """记录DEBUG级别日志"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """记录INFO级别日志"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """记录WARNING级别日志"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录ERROR级别日志"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """记录CRITICAL级别日志"""
        self.logger.critical(message)


# 全局日志实例
_default_logger: Optional[Logger] = None


def get_logger(name: str = 'data_factory', **kwargs) -> Logger:
    """
    获取日志实例（单例模式）
    
    Args:
        name: 日志名称
        **kwargs: 其他参数（仅在首次创建时生效）
    
    Returns:
        日志实例
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = Logger(name, **kwargs)
    return _default_logger

