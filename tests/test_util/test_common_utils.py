""" Test for all common utilities function
"""
import logging
from util.common_utils import get_logger


def test_get_logger():
    """ test the get_logger_function()
    """
    logger = get_logger(logger_name='tests.test_util.test_common_utils')
    assert isinstance(logger, logging.Logger)
