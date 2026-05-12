#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的日志系统
"""

import logging
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "shrimp_analyzer", log_file: str = None) -> logging.Logger:
    """
    设置日志系统

    Args:
        name: 日志名称
        log_file: 日志文件路径

    Returns:
        logger 对象
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出
    if log_file is None:
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f'app_{datetime.now().strftime("%Y%m%d")}.log'

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# 默认 logger
logger = setup_logger()


if __name__ == '__main__':
    # 测试
    logger.info("这是一条测试日志")
    logger.warning("这是一条警告")
    logger.error("这是一条错误")
