""" 
Provide the common utility functions used by all other modules
"""
import logging
from dotenv import dotenv_values


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
    # create console handler and set level to info
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

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


def get_env() -> dict:
    """ Retrieve the env variables from the environment. Perform further processing if necessary

    Returns:
        dict: dictionary of env values in key=value pairs
    """
    config = dotenv_values(".env")
    return config
