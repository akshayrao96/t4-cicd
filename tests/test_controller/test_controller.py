"""Test controller integration
"""
import os
import json
from controller.controller import (Controller)
from util.db_mongo import MongoAdapter
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

def test_edit_config():
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, 'pipeline_data.json')
    with open(file_path, 'r', encoding='utf-8') as file:
        pipeline_data = json.load(file)
    db = MongoAdapter()
    # db.insert_pipeline(pipeline_data, "CICDControllerDB", "repo_configs")
    controller = Controller()
    updates = {'global': {'docker': {'image': 'gradle:jdk8'}}}
    # controller.edit_config(pipeline_data['pipeline_name'], updates)
test_edit_config()

def test_run_pipeline_invalid_config():
    """test controller run_pipeline() method using invalid_config.yml file.
    This should return status == False and pipeline_id == ""
    """
    controller = Controller()
    config_file = '.cicd-pipelines/invalid_config.yml'
    dry_run = True
    git_details = {}
    local = False
    yaml_output = False

    expected_status = False
    expected_pipeline_id = ""
    status, _message, pipeline_id = controller.run_pipeline(config_file, dry_run, git_details,
                                                           local, yaml_output)

    assert status == expected_status
    assert pipeline_id == expected_pipeline_id
