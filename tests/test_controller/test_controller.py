"""Test controller integration
"""
from controller.controller import (Controller)
from util.common_utils import (get_logger)
logger = get_logger("tests.test_controller.test_controller")

# def test_validate_config():
#     """test configuration file validation
#     """
#     controller = Controller()

#     expected_passed = True
#     expected_error_msg = ""

#     #Note: in order for this to work, currently need to create .cicd-pipelines/
#     #in this t4-cicd project.
#     result = controller.validate_config("pipelines.yml")
#     passed, error_msg, config_dict = result[0], result[1], result[2]

#     assert passed is expected_passed
#     assert error_msg == expected_error_msg

#     logger.info(passed)
#     logger.info(error_msg)
#     logger.info(config_dict)
