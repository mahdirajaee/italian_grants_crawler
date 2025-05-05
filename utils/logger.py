import logging
import os
from datetime import datetime
from typing import Optional


def setup_logger(
    name: str,
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up a logger with file and/or console output.
    
    Args:
        name (str): Name of the logger
        log_level (int): Logging level
        log_file (str, optional): Path to log file
        console_output (bool): Whether to output logs to console
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # Add file handler if log_file is specified
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    # Add console handler if console_output is True
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    return logger


def setup_crawl_logger(crawler_name: str) -> logging.Logger:
    """
    Set up logger for a specific crawler with standardized log file naming.
    
    Args:
        crawler_name (str): Name of the crawler
        
    Returns:
        logging.Logger: Configured logger
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/{crawler_name}_{timestamp}.log"
    
    return setup_logger(
        name=crawler_name,
        log_level=logging.INFO,
        log_file=log_file,
        console_output=True
    )