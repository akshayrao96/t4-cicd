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
    db = MongoAdapter()
    controller = Controller()
    # id = db.insert_job("672817cdabdfc031a3ff26f4", pipeline_config)
    pg = db.create_job_log("checkout", "started")
    _ = db.update_job_logs("67281a551b30182de9ac740d", "build", "started", pg)
test_edit_config()


class TestController(unittest.TestCase):

    @patch("controller.controller.Controller.validate_config")
    @patch("util.db_mongo.MongoAdapter.insert_repo")
    @patch("util.db_mongo.MongoAdapter.update_pipeline")
    @patch("util.db_mongo.MongoAdapter.get_repo")
    def test_validate_n_save_config_new_repo(self, mock_get_repo, mock_update_pipeline, mock_insert_repo, mock_validate_config):
        """Test saving a single pipeline configuration with a new repo"""
        controller = Controller()
        mock_validate_config.return_value = (True, '', {'global': {'pipeline_name': 'new_pipeline'}})
        mock_get_repo.return_value = None  # No existing repo
        mock_insert_repo.return_value = "new_repo_id"
        mock_update_pipeline.return_value = True
        status, error_msg, config = controller.validate_n_save_config("/path/to/file.yml")
        self.assertTrue(status)
        self.assertEqual(error_msg, '')
        self.assertEqual(config['global']['pipeline_name'], 'new_pipeline')

    @patch("controller.controller.Controller.validate_config")
    @patch("util.db_mongo.MongoAdapter.update_pipeline")
    @patch("util.db_mongo.MongoAdapter.get_repo")
    def test_validate_n_save_config_existing_repo_append_pipeline(self, mock_get_repo, mock_update_pipeline, mock_validate_config):
        """Test appending a new pipeline to an existing repo"""
        controller = Controller()
        mock_validate_config.return_value = (True, '', {'global': {'pipeline_name': 'appended_pipeline'}})
        mock_get_repo.return_value = {
            "_id": "existing_repo_id",
            "repo_name": "sample-repo",
            "pipelines": []
        }
        mock_update_pipeline.return_value = True
        status, error_msg, config = controller.validate_n_save_config("/path/to/file.yml")
        self.assertTrue(status)
        self.assertEqual(error_msg, '')
        self.assertEqual(config['global']['pipeline_name'], 'appended_pipeline')

    @patch("controller.controller.Controller.validate_config")
    @patch("util.db_mongo.MongoAdapter.insert_repo")
    def test_validate_n_save_config_save_failure(self, mock_insert_repo, mock_validate_config):
        """Test failing to save a new pipeline configuration"""
        controller = Controller()
        mock_validate_config.return_value = (True,
                                            '', {'global': {'pipeline_name': 'test_pipeline'}})
        mock_insert_repo.return_value = None  # Simulate save failure
        status, error_msg, config = controller.validate_n_save_config("/path/to/file.yml")

        self.assertFalse(status)
        self.assertEqual(config['global']['pipeline_name'], 'test_pipeline')

    @patch("controller.controller.Controller.validate_configs")
    @patch("controller.controller.Controller.validate_n_save_config")
    def test_validate_n_save_configs(self, mock_validate_n_save_config, mock_validate_configs):
        """Test batch saving of pipeline configurations"""
        controller = Controller()
        mock_validate_configs.return_value = {
            'pipeline1': {'valid': True, 'error_msg': '', 'pipeline_config': {}},
            'pipeline2': {'valid': False, 'error_msg': 'Invalid config'}
        }
        mock_validate_n_save_config.return_value = (True, '', {})
        result = controller.validate_n_save_configs("/path/to/directory")
        self.assertIn('pipeline1', result)
        self.assertIn('pipeline2', result)
        self.assertTrue(result['pipeline1']['valid'])
        self.assertFalse(result['pipeline2']['valid'])
        self.assertEqual(result['pipeline2']['error_msg'], 'Invalid config')

        """Test batch saving of pipeline configurations"""
        controller = Controller()
        mock_validate_configs.return_value = {
            'pipeline1': {'valid': True, 'error_msg': '', 'pipeline_config': {}},
            'pipeline2': {'valid': False, 'error_msg': 'Invalid config'}
        }
        mock_validate_n_save_config.return_value = (True, '', {})
        result = controller.validate_n_save_configs("/path/to/directory")
        self.assertIn('pipeline1', result)
        self.assertIn('pipeline2', result)
        self.assertTrue(result['pipeline1']['valid'])
        self.assertFalse(result['pipeline2']['valid'])
        self.assertEqual(result['pipeline2']['error_msg'], 'Invalid config')


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


class TestControllerRepoFunctions(unittest.TestCase):

    @patch("controller.controller.RepoManager")
    def test_set_repo_in_git_repo(self, mock_repo_manager):
        """Test set_repo when already in a Git repository."""
        mock_instance = mock_repo_manager.return_value
        mock_instance.is_current_repo.return_value = (True, "existing_repo")

        controller = Controller()
        success, message = controller.set_repo("https://github.com/sample/repo")

        self.assertFalse(success)
        self.assertIn("Please navigate to an empty directory", message)

    @patch("controller.controller.RepoManager")
    def test_set_repo_clone_failure(self, mock_repo_manager):
        """Test set_repo when cloning the repository fails."""
        mock_instance = mock_repo_manager.return_value
        mock_instance.is_current_repo.return_value = (False, None)
        mock_instance.set_repo.return_value = (False, "Failed to clone repository.", {})

        controller = Controller()
        success, message = controller.set_repo("https://github.com/sample/repo")

        self.assertFalse(success)
        self.assertEqual(message, "Failed to clone repository.")

    @patch("controller.controller.RepoManager")
    def test_set_repo_success(self, mock_repo_manager):
        """Test successful set_repo call."""
        mock_instance = mock_repo_manager.return_value
        mock_instance.is_current_repo.return_value = (False, None)
        mock_instance.set_repo.return_value = (True, "Repository successfully cloned and set up.", {
            "repo_name": "sample_repo",
            "branch": "main",
            "commit_hash": "latest_commit_hash"
        })

        with patch("os.getlogin", return_value="test_user"), \
                patch("util.db_mongo.MongoAdapter.insert_repo", return_value="new_repo_id"):
            controller = Controller()
            success, message = controller.set_repo("https://github.com/sample/repo")

            self.assertTrue(success)
            self.assertIn("Repository set successfully", message)

    @patch("controller.controller.RepoManager")
    @patch("util.db_mongo.MongoAdapter.get_last_set_repo")
    def test_get_repo_in_git_repo(self, mock_get_last_set_repo, mock_repo_manager):
        """Test get_repo when in a Git repository."""
        mock_instance = mock_repo_manager.return_value
        mock_instance.is_current_repo.return_value = (True, "existing_repo")

        controller = Controller()
        status, repo_name = controller.get_repo()

        self.assertTrue(status)
        self.assertEqual(repo_name, "existing_repo")
        mock_get_last_set_repo.assert_not_called()

    @patch("controller.controller.RepoManager")
    @patch("util.db_mongo.MongoAdapter.get_last_set_repo")
    def test_get_repo_with_last_set_repo(self, mock_get_last_set_repo, mock_repo_manager):
        """Test get_repo when not in a Git repository but a last set repo exists."""
        mock_instance = mock_repo_manager.return_value
        mock_instance.is_current_repo.return_value = (False, None)
        mock_get_last_set_repo.return_value = {"repo_url": "https://github.com/sample/last_repo"}

        controller = Controller()
        status, repo_url = controller.get_repo()

        self.assertFalse(status)
        self.assertEqual(repo_url, "https://github.com/sample/last_repo")

    @patch("controller.controller.RepoManager")
    @patch("util.db_mongo.MongoAdapter.get_last_set_repo")
    def test_get_repo_no_repo_found(self, mock_get_last_set_repo, mock_repo_manager):
        """Test get_repo when neither a Git repository nor a last set repo exists."""
        mock_instance = mock_repo_manager.return_value
        mock_instance.is_current_repo.return_value = (False, None)
        mock_get_last_set_repo.return_value = None

        controller = Controller()
        status, repo_url = controller.get_repo()

        self.assertFalse(status)
        self.assertIsNone(repo_url)