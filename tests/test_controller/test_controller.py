"""Test controller integration
"""
import os
import json
import unittest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
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
class TestOverrideConfig(unittest.TestCase):

    @patch("controller.controller.click.echo")
    @patch(
        "controller.controller.ConfigChecker.validate_config",
        return_value={'valid': True, 'pipeline_config': {"updated_config": "value"}}
    )
    @patch(
        "controller.controller.ConfigOverrides.apply_overrides",
        return_value={"updated_config": "value"}
    )
    @patch("controller.controller.MongoAdapter")
    def test_override_config_success(
        self, mock_mongo_adapter, mock_apply_overrides, mock_validate_config, mock_echo
    ):
        """Test successful override and update of pipeline configuration"""
        mock_mongo_adapter_instance = mock_mongo_adapter.return_value
        mock_mongo_adapter_instance.get_pipeline_config.return_value = {
            'pipeline_config': {'key': 'value'}
        }
        mock_mongo_adapter_instance.update_pipeline_config.return_value = True
        controller = Controller()
        result = controller.override_config("test_pipeline", {"override_key": "override_value"})

        self.assertTrue(result)
        mock_echo.assert_any_call("Pipeline configuration updated successfully.")

    @patch("controller.controller.click.echo")
    @patch("controller.controller.MongoAdapter")
    def test_override_config_no_pipeline_config(self, mock_mongo_adapter, mock_echo):
        """Test when no pipeline configuration is found"""
        mock_mongo_adapter_instance = mock_mongo_adapter.return_value
        mock_mongo_adapter_instance.get_pipeline_config.return_value = {}
        controller = Controller()
        result = controller.override_config("test_pipeline", {"override_key": "override_value"})
        self.assertFalse(result)
        mock_echo.assert_called_once_with("No pipeline config found for 'test_pipeline'.")

    @patch("controller.controller.click.echo")
    @patch(
        "controller.controller.ConfigChecker.validate_config",
        return_value={'valid': False}
    )
    @patch(
        "controller.controller.ConfigOverrides.apply_overrides",
        return_value={"updated_config": "value"}
    )
    @patch("controller.controller.MongoAdapter")
    def test_override_config_validation_failure(
        self, mock_mongo_adapter, mock_apply_overrides, mock_validate_config, mock_echo
    ):
        """Test override config where validation fails"""
        mock_mongo_adapter_instance = mock_mongo_adapter.return_value
        mock_mongo_adapter_instance.get_pipeline_config.return_value = {
            'pipeline_config': {'key': 'value'}
        }
        controller = Controller()
        result = controller.override_config("test_pipeline", {"override_key": "override_value"})
        self.assertFalse(result)
        mock_echo.assert_called_once_with("Override pipeline configuration validation failed.")

    @patch("controller.controller.click.echo")
    @patch(
        "controller.controller.ConfigChecker.validate_config",
        return_value={'valid': True}
    )
    @patch(
        "controller.controller.ConfigOverrides.apply_overrides",
        return_value={"updated_config": "value"}
    )
    @patch("controller.controller.MongoAdapter")
    def test_override_config_update_failure(
        self, mock_mongo_adapter, mock_apply_overrides, mock_validate_config, mock_echo
    ):
        """Test override config where database update fails"""
        mock_mongo_adapter_instance = mock_mongo_adapter.return_value
        mock_mongo_adapter_instance.get_pipeline_config.return_value = {
            'pipeline_config': {'key': 'value'}
        }
        mock_mongo_adapter_instance.update_pipeline_config.return_value = False
        controller = Controller()
        result = controller.override_config("test_pipeline", {"override_key": "override_value"})
        self.assertFalse(result)
        mock_echo.assert_called_once_with("Error updating pipeline configuration.")
