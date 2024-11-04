""" test the controller integration with container
"""
from docker.errors import DockerException
import util.constant as c
from util.container import (DockerManager)
from util.common_utils import (get_logger)
logger = get_logger("tests.test_util.test_controller_container")

# def test_stop():
#     docker_manager = DockerManager()
#     try:
#         log = docker_manager.stop_job('sample_job')
#         print(log)
#     except DockerException as de:
#         logger.warning(f"During stop job, exception thrown, {de}")
# test_stop()