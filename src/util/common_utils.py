""" 
Provide the common utility functions used by all other modules
"""
import logging


def get_logger(logger_name='', log_level=logging.DEBUG, log_file='debug.log') -> logging.Logger:
    """_summary_

    Args:
        logger_name (str, optional): _description_. Defaults to ''.
        log_level (_type_, optional): _description_. Defaults to logging.DEBUG.
        log_file (str, optional): _description_. Defaults to 'debug.log'.

    Returns:
        logging.Logger: _description_
    """
    # Retrieve logger and set log level
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    # add file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)

    return logger
