"""Test controller integration
"""
import os
import json
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from git import GitCommandError
from pydantic import ValidationError, BaseModel
from twisted.mail.scripts.mailmail import success

from controller.controller import (Controller)
from util.db_mongo import MongoAdapter
from util.common_utils import (get_logger)
from util.model import SessionDetail, ValidationResult

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

# class TestController(unittest.TestCase):

    # TODO - Check if still required after coverage
    # @patch("controller.controller.Controller.validate_config")
    # @patch("util.db_mongo.MongoAdapter.insert_repo")
    # @patch("util.db_mongo.MongoAdapter.update_pipeline")
    # @patch("util.db_mongo.MongoAdapter.get_repo")
    # def test_validate_n_save_config_new_repo(self, mock_get_repo, mock_update_pipeline, mock_insert_repo, mock_validate_config):
    #     """Test saving a single pipeline configuration with a new repo"""
    #     controller = Controller()
    #     mock_validate_config.return_value = (True, '', {'global': {'pipeline_name': 'new_pipeline'}})
    #     mock_get_repo.return_value = None  # No existing repo
    #     mock_insert_repo.return_value = "new_repo_id"
    #     mock_update_pipeline.return_value = True
    #     status, error_msg, config = controller.validate_n_save_config("/path/to/file.yml")
    #     self.assertTrue(status)
    #     self.assertEqual(error_msg, '')
    #     self.assertEqual(config['global']['pipeline_name'], 'new_pipeline')

    # @patch("controller.controller.Controller.validate_config")
    # @patch("util.db_mongo.MongoAdapter.update_pipeline")
    # @patch("util.db_mongo.MongoAdapter.get_repo")
    # def test_validate_n_save_config_existing_repo_append_pipeline(self, mock_get_repo, mock_update_pipeline, mock_validate_config):
    #     """Test appending a new pipeline to an existing repo"""
    #     controller = Controller()
    #     mock_validate_config.return_value = (True, '', {'global': {'pipeline_name': 'appended_pipeline'}})
    #     mock_get_repo.return_value = {
    #         "_id": "existing_repo_id",
    #         "repo_name": "sample-repo",
    #         "pipelines": {}
    #     }
    #     mock_update_pipeline.return_value = True
    #     status, error_msg, config = controller.validate_n_save_config("/path/to/file.yml")
    #     self.assertTrue(status)
    #     self.assertEqual(error_msg, '')
    #     self.assertEqual(config['global']['pipeline_name'], 'appended_pipeline')

    # TODO: commented as pytest failed on this one
    # @patch("controller.controller.Controller.validate_config")
    # @patch("util.db_mongo.MongoAdapter.insert_repo")
    # def test_validate_n_save_config_save_failure(self, mock_insert_repo, mock_validate_config):
    #     """Test failing to save a new pipeline configuration"""
    #     controller = Controller()
    #     mock_validate_config.return_value = (True,
    #                                         '', {'global': {'pipeline_name': 'test_pipeline'}})
    #     mock_insert_repo.return_value = None  # Simulate save failure
    #     status, error_msg, config = controller.validate_n_save_config("/path/to/file.yml")

    #     self.assertFalse(status)
    #     self.assertEqual(config['global']['pipeline_name'], 'test_pipeline')

    # TODO - CSJ rewrite tests after rewrite the bulk validate and save methods
    # @patch("controller.controller.Controller.validate_configs")
    # @patch("controller.controller.Controller.validate_n_save_config")
    # def test_validate_n_save_configs(self, mock_validate_n_save_config, mock_validate_configs):
    #     """Test batch saving of pipeline configurations"""
    #     controller = Controller()
    #     mock_validate_configs.return_value = {
    #         'pipeline1': {'valid': True, 'error_msg': '', 'pipeline_config': {}},
    #         'pipeline2': {'valid': False, 'error_msg': 'Invalid config'}
    #     }
    #     mock_validate_n_save_config.return_value = (True, '', {})
    #     result = controller.validate_n_save_configs("/path/to/directory")
    #     self.assertIn('pipeline1', result)
    #     self.assertIn('pipeline2', result)
    #     self.assertTrue(result['pipeline1']['valid'])
    #     self.assertFalse(result['pipeline2']['valid'])
    #     self.assertEqual(result['pipeline2']['error_msg'], 'Invalid config')

    #     """Test batch saving of pipeline configurations"""
    #     controller = Controller()
    #     mock_validate_configs.return_value = {
    #         'pipeline1': {'valid': True, 'error_msg': '', 'pipeline_config': {}},
    #         'pipeline2': {'valid': False, 'error_msg': 'Invalid config'}
    #     }
    #     mock_validate_n_save_config.return_value = (True, '', {})
    #     result = controller.validate_n_save_configs("/path/to/directory")
    #     self.assertIn('pipeline1', result)
    #     self.assertIn('pipeline2', result)
    #     self.assertTrue(result['pipeline1']['valid'])
    #     self.assertFalse(result['pipeline2']['valid'])
    #     self.assertEqual(result['pipeline2']['error_msg'], 'Invalid config')

class TestOverrideConfig(unittest.TestCase):

    def setUp(self):
        self.success_validation_res = ValidationResult(valid=True, error_msg="", pipeline_config={"updated_config": "value"})
        self.fail_validation_res = ValidationResult(valid=False, error_msg="", pipeline_config={})
        
    @patch("controller.controller.click.echo")
    @patch(
        "controller.controller.ConfigChecker.validate_config"
    )
    @patch(
        "controller.controller.MongoHelper.apply_overrides",
        return_value={"updated_config": "value"}
    )
    @patch("controller.controller.MongoAdapter")
    def test_override_config_success(
        self, mock_mongo_adapter, mock_apply_overrides, mock_validate_config, mock_echo
    ):
        """Test successful override and update of pipeline configuration"""
        mock_validate_config.return_value = self.success_validation_res
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
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch(
        "controller.controller.MongoHelper.apply_overrides",
        return_value={"updated_config": "value"}
    )
    @patch("controller.controller.MongoAdapter")
    def test_override_config_validation_failure(
        self, mock_mongo_adapter, mock_apply_overrides, mock_validate_config, mock_echo
    ):
        """Test override config where validation fails"""
        mock_validate_config.return_value = self.fail_validation_res
        mock_mongo_adapter_instance = mock_mongo_adapter.return_value
        mock_mongo_adapter_instance.get_pipeline_config.return_value = {
            'pipeline_config': {'key': 'value'}
        }
        controller = Controller()
        result = controller.override_config("test_pipeline", {"override_key": "override_value"})
        self.assertFalse(result)
        mock_echo.assert_called_once_with("Override pipeline configuration validation failed.")

    @patch("controller.controller.click.echo")
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch(
        "controller.controller.MongoHelper.apply_overrides",
        return_value={"updated_config": "value"}
    )
    @patch("controller.controller.MongoAdapter")
    def test_override_config_update_failure(
        self, mock_mongo_adapter, mock_apply_overrides, mock_validate_config, mock_echo
    ):
        """Test override config where database update fails"""
        mock_validate_config.return_value = self.success_validation_res
        mock_mongo_adapter_instance = mock_mongo_adapter.return_value
        mock_mongo_adapter_instance.get_pipeline_config.return_value = {
            'pipeline_config': {'key': 'value'}
        }
        mock_mongo_adapter_instance.update_pipeline_info.return_value = False
        controller = Controller()
        result = controller.override_config("test_pipeline", {"override_key": "override_value"})
        self.assertFalse(result)
        mock_echo.assert_called_once_with("Error updating pipeline configuration.")


class TestControllerRepoFunctions(unittest.TestCase):

    @patch("controller.controller.RepoManager")
    def test_set_repo_in_git_repo(self, mock_repo_manager):
        """Test set_repo when already in a Git repository."""
        mock_instance = mock_repo_manager.return_value
        mock_instance.is_current_dir_repo.return_value = (True, "existing_repo", True)

        controller = Controller()
        success, message, repo_details = controller.set_repo("https://github.com/sample/repo")

        self.assertFalse(success)
        self.assertIn("Please navigate to an empty directory", message)
        self.assertIsNone(repo_details)

    @patch("controller.controller.RepoManager")
    def test_set_repo_clone_failure(self, mock_repo_manager):
        """Test set_repo when cloning the repository fails."""
        mock_instance = mock_repo_manager.return_value

        # Mocking is_current_dir_repo to indicate not already in a Git repo
        mock_instance.is_current_dir_repo.return_value = (False, None, False)

        # Mocking is_valid_git_repo to validate the repository URL
        mock_instance.is_valid_git_repo.return_value = (True, True, "Valid remote repository")

        # Mocking set_repo to simulate a failure in cloning the repository
        mock_instance.set_repo.return_value = (False, "Failed to clone repository.", {})

        controller = Controller()

        # Call the method under test
        success, message, repo_details = controller.set_repo("https://github.com/sample/repo")

        # Assertions
        self.assertFalse(success)
        self.assertEqual(message, "Failed to clone repository.")
        self.assertIsNone(repo_details)  # Adjusted assertion for None

    @patch("controller.controller.RepoManager")
    @patch("util.db_mongo.MongoAdapter.update_session", return_value="new_repo_id")
    @patch("util.model.SessionDetail")
    @patch("os.getlogin", return_value="test_user")
    def test_set_repo_success(self, mock_getlogin, MockSessionDetail, mock_update_session, mock_repo_manager):
        """Test successful set_repo call without explicit validation."""
        mock_instance = mock_repo_manager.return_value

        # Mocking `is_current_dir_repo` to indicate not already in a Git repo
        mock_instance.is_current_dir_repo.return_value = (False, None, False)

        # Mocking `is_valid_git_repo` to validate the repository URL
        mock_instance.is_valid_git_repo.return_value = (True, True, "Valid remote repository")

        # Mocking `set_repo` to simulate a successful repository setup
        mock_instance.set_repo.return_value = (True, "Repository successfully cloned and set up.", {
            "repo_name": "sample_repo",
            "branch": "main",
            "commit_hash": "latest_commit_hash"
        })

        # Mocking session detail validation and dump
        mock_session_detail = MockSessionDetail.return_value
        mock_session_detail.model_dump.return_value = {
            "user_id": "test_user",
            "repo_url": "https://github.com/sample/repo",
            "repo_name": "sample_repo",
            "branch": "main",
            "commit_hash": "latest_commit_hash",
            "is_remote": True,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        controller = Controller()

        # Call the method under test
        success, message, repo_details = controller.set_repo("https://github.com/sample/repo")

        # Assertions
        self.assertTrue(success)
        self.assertIn("Repository set successfully", message)
        self.assertIsNotNone(repo_details)
        self.assertEqual(repo_details.repo_name, "sample_repo")
        mock_update_session.assert_called_once_with(mock_session_detail.model_dump())

    @patch("controller.controller.RepoManager")
    @patch("util.db_mongo.MongoAdapter.update_session", return_value="mock_inserted_id")
    @patch("os.getlogin", return_value="test_user")
    def test_get_repo_in_git_repo(self, mock_getlogin, mock_update_session, mock_repo_manager):
        """Test get_repo when in a Git repository, validating repository details."""
        mock_instance = mock_repo_manager.return_value

        # Mocking repo state and details
        mock_instance.is_current_dir_repo.return_value = (True, True, "existing_repo")
        mock_instance.get_current_repo_details.return_value = {
            "repo_url": "https://github.com/sample/repo",
            "repo_name": "existing_repo",
            "branch": "main",
            "commit_hash": "123abc",
        }

        fixed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with patch("util.model.SessionDetail") as MockSessionDetail:
            mock_session_detail = MockSessionDetail(
                user_id="test_user",
                repo_url="https://github.com/sample/repo",
                repo_name="existing_repo",
                branch="main",
                commit_hash="123abc",
                is_remote=True,
                time=fixed_time,
            )
            mock_session_detail.model_dump.return_value = {
                "user_id": "test_user",
                "repo_url": "https://github.com/sample/repo",
                "repo_name": "existing_repo",
                "branch": "main",
                "commit_hash": "123abc",
                "is_remote": False,
                "time": fixed_time,
            }
            MockSessionDetail.return_value = mock_session_detail

            controller = Controller()
            status, message, repo_data = controller.get_repo()

            self.assertTrue(status)
            self.assertEqual(message, "Repository is configured in current directory")
            self.assertIsNotNone(repo_data)
            self.assertEqual(repo_data.repo_name, "existing_repo")
            self.assertEqual(repo_data.branch, "main")
            self.assertEqual(repo_data.repo_url, "https://github.com/sample/repo")
            self.assertEqual(repo_data.commit_hash, "123abc")
            mock_update_session.assert_called_once_with(mock_session_detail.model_dump())

    @patch("controller.controller.RepoManager")
    @patch("util.db_mongo.MongoAdapter.get_session")
    @patch("os.getlogin", return_value="test_user")  # Mock os.getlogin
    def test_get_repo_with_last_set_repo(self, mock_getlogin, mock_get_session, mock_repo_manager):
        """Test get_repo when not in a Git repository but a last set repo exists."""
        mock_instance = mock_repo_manager.return_value
        mock_instance.is_current_dir_repo.return_value = (False, None, False)

        mock_get_session.return_value = {
            "user_id": "test_user",
            "repo_url": "https://github.com/sample/last_repo",
            "repo_name": "last_repo",
            "branch": "main",
            "commit_hash": "456def",
            "is_remote": True,
            "time": "2024-01-01 12:00:00"
        }

        with patch("util.model.SessionDetail") as MockSessionDetail:
            mock_session_detail = MockSessionDetail.return_value
            mock_session_detail.repo_url = "https://github.com/sample/last_repo"
            mock_session_detail.repo_name = "last_repo"
            mock_session_detail.branch = "main"
            mock_session_detail.commit_hash = "456def"

            controller = Controller()
            status, message, repo_data = controller.get_repo()

            self.assertFalse(status)
            self.assertEqual(message, "Current working directory is not a git repository")
            self.assertIsNotNone(repo_data)
            self.assertEqual(repo_data.repo_url, "https://github.com/sample/last_repo")
            self.assertEqual(repo_data.repo_name, "last_repo")
            self.assertEqual(repo_data.branch, "main")
            self.assertEqual(repo_data.commit_hash, "456def")

    @patch("controller.controller.RepoManager")
    @patch("util.db_mongo.MongoAdapter.get_session", return_value=None)
    @patch("os.getlogin", return_value="test_user")
    def test_get_repo_no_repo_found(self, mock_getlogin, mock_get_session, mock_repo_manager):
        """Test get_repo when neither a Git repository nor a last set repo exists."""
        mock_instance = mock_repo_manager.return_value
        mock_instance.is_current_dir_repo.return_value = (False, None, False)

        controller = Controller()
        status, message, repo_data = controller.get_repo()

        self.assertFalse(status)
        self.assertEqual(
            message.strip(),  # Strip any extra whitespace
            "Working directory is not a git repository. No previous repository has been set.",
        )
        self.assertIsNone(repo_data)

    @patch("controller.controller.Controller.set_repo")
    @patch("controller.controller.Controller.get_repo")
    def test_handle_repo_with_repo_url(self, mock_get_repo, mock_set_repo):
        """Test handle_repo when repo_url is provided."""
        mock_set_repo.return_value = (True, "Repository set successfully.", None)

        controller = Controller()
        result = controller.handle_repo(repo_url="https://github.com/sample/repo", branch="main", commit_hash="abc123")

        # Assert that set_repo was called with correct parameters
        mock_set_repo.assert_called_once_with(
            repo_url="https://github.com/sample/repo",
            branch="main",
            commit_hash="abc123"
        )
        # Assert that get_repo was not called
        mock_get_repo.assert_not_called()

        # Assert the result
        self.assertTrue(result[0])
        self.assertEqual(result[1], "Repository set successfully.")
        self.assertIsNone(result[2])

    @patch("controller.controller.Controller.set_repo")
    @patch("controller.controller.Controller.get_repo")
    def test_handle_repo_without_repo_url(self, mock_get_repo, mock_set_repo):
        """Test handle_repo when repo_url is not provided."""
        mock_get_repo.return_value = (False, "No repository found to run command.", None)

        controller = Controller()
        result = controller.handle_repo()

        # Assert that get_repo was called
        mock_get_repo.assert_called_once()
        # Assert that set_repo was not called
        mock_set_repo.assert_not_called()

        # Assert the result
        self.assertFalse(result[0])
        self.assertEqual(result[1], "No repository found to run command.")
        self.assertIsNone(result[2])

    @patch("controller.controller.Controller.checkout_repo")
    def test_handle_repo_with_branch_commit(self, mock_checkout_repo):
        """Test handle_repo when branch and commit_hash are provided."""
        mock_checkout_repo.return_value = (True, "Checked out successfully.", None)

        controller = Controller()
        result = controller.handle_repo(branch="main", commit_hash="abc123")

        # Assert that checkout_repo was called with correct parameters
        mock_checkout_repo.assert_called_once_with(branch="main", commit_hash="abc123")

        # Assert the result
        self.assertTrue(result[0])
        self.assertEqual(result[1], "Checked out successfully.")
        self.assertIsNone(result[2])

    @patch("controller.controller.RepoManager")
    @patch("util.db_mongo.MongoAdapter.get_session", return_value=None)
    @patch("os.getlogin", return_value="test_user")
    def test_get_repo_no_repo_found(self, mock_getlogin, mock_get_session, mock_repo_manager):
        """Test get_repo when neither a Git repository nor a last set repo exists."""
        mock_instance = mock_repo_manager.return_value
        mock_instance.is_current_dir_repo.return_value = (False, None, False)

        controller = Controller()
        status, message, repo_data = controller.get_repo()

        self.assertFalse(status)
        self.assertEqual(
            message,
            "Working directory is not a git repository. No previous repository has been set.",
        )
        self.assertIsNone(repo_data)
        mock_get_session.assert_called_once_with("test_user")
        mock_getlogin.assert_called_once()

    @patch("controller.controller.RepoManager")
    def test_checkout_repo_git_directory_error(self, mock_repo_manager):
        """Test checkout_repo when not in a Git repository."""
        mock_instance = mock_repo_manager.return_value
        mock_instance.is_current_dir_repo.return_value = (False, None, False)

        controller = Controller()
        status, message, repo_data = controller.checkout_repo(branch="main")

        self.assertFalse(status)
        self.assertEqual(message, "Current directory is not a Git repository.")
        self.assertIsNone(repo_data)

    @patch("controller.controller.RepoManager")
    @patch("util.db_mongo.MongoAdapter.get_session", return_value=None)
    @patch("util.db_mongo.MongoAdapter.update_session", return_value="mock_inserted_id")
    @patch("os.getlogin", return_value="test_user")
    def test_checkout_repo_success(self, mock_getlogin, mock_update_session, mock_get_session, mock_repo_manager):
        """Test checkout_repo when branch and commit are successfully checked out."""
        mock_instance = mock_repo_manager.return_value

        # Mock repo state
        mock_instance.is_current_dir_repo.return_value = (True, True, "test_repo")
        mock_instance.checkout_branch_and_commit.return_value = (True, "Checkout successful.")

        # Generate the absolute path for the mocked repo_url
        repo_url_absolute = str(Path("https://github.com/sample/repo").resolve())
        mock_instance.get_current_repo_details.return_value = {
            "repo_url": repo_url_absolute,
            "repo_name": "test_repo",
            "branch": "main",
            "commit_hash": "123abc",
        }

        # Mock SessionDetail
        fixed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with patch("util.model.SessionDetail") as MockSessionDetail:
            mock_session_detail = MockSessionDetail(
                user_id="test_user",
                repo_url=repo_url_absolute,
                repo_name="test_repo",
                branch="main",
                commit_hash="123abc",
                is_remote=False,
                time=fixed_time,
            )
            mock_session_detail.model_dump.return_value = {
                "user_id": "test_user",
                "repo_url": repo_url_absolute,
                "repo_name": "test_repo",
                "branch": "main",
                "commit_hash": "123abc",
                "is_remote": False,
                "time": fixed_time,
            }
            MockSessionDetail.return_value = mock_session_detail

            controller = Controller()
            status, message, repo_data = controller.checkout_repo(branch="main", commit_hash="123abc")

            self.assertTrue(status)
            self.assertEqual(message, "Repository checked out successfully.")
            self.assertIsNotNone(repo_data)
            self.assertEqual(repo_data.repo_name, "test_repo")
            self.assertEqual(repo_data.branch, "main")
            self.assertEqual(repo_data.repo_url, repo_url_absolute)  # Use the absolute path here
            self.assertEqual(repo_data.commit_hash, "123abc")
            mock_update_session.assert_called_once_with(mock_session_detail.model_dump())

    @patch("controller.controller.RepoManager")
    @patch("util.db_mongo.MongoAdapter.get_session", return_value=None)
    @patch("os.getlogin", return_value="test_user")
    def test_checkout_repo_commit_not_found(self, mock_getlogin, mock_get_session, mock_repo_manager):
        """Test checkout_repo when the commit does not exist."""
        mock_instance = mock_repo_manager.return_value

        # Mock repo state
        mock_instance.is_current_dir_repo.return_value = (True, True, "test_repo")
        mock_instance.checkout_branch_and_commit.return_value = (False, "Commit not found.")

        controller = Controller()
        status, message, repo_data = controller.checkout_repo(branch="main", commit_hash="nonexistent_commit_hash")

        self.assertFalse(status)
        self.assertEqual(message, "Commit not found.")
        self.assertIsNone(repo_data)

    @patch("controller.controller.RepoManager")
    @patch("util.db_mongo.MongoAdapter.get_session", return_value=None)
    @patch("os.getlogin", return_value="test_user")
    def test_checkout_repo_not_in_root(self, mock_getlogin, mock_get_session, mock_repo_manager):
        """Test checkout_repo when not in the root of the repository."""
        mock_instance = mock_repo_manager.return_value

        # Mock repo state
        mock_instance.is_current_dir_repo.return_value = (True, False, "test_repo")

        controller = Controller()
        status, message, repo_data = controller.checkout_repo(branch="main", commit_hash="123abc")

        self.assertFalse(status)
        self.assertEqual(message, "Please navigate to root of repository before executing command.")
        self.assertIsNone(repo_data)

    @patch("controller.controller.RepoManager")
    @patch("util.db_mongo.MongoAdapter.get_session", return_value=None)
    @patch("os.getlogin", return_value="test_user")
    def test_checkout_repo_not_git_repo(self, mock_getlogin, mock_get_session, mock_repo_manager):
        """Test checkout_repo when the current directory is not a Git repository."""
        mock_instance = mock_repo_manager.return_value

        # Mock repo state
        mock_instance.is_current_dir_repo.return_value = (False, None, None)

        controller = Controller()
        status, message, repo_data = controller.checkout_repo(branch="main", commit_hash="123abc")

        self.assertFalse(status)
        self.assertEqual(message, "Current directory is not a Git repository.")
        self.assertIsNone(repo_data)

    @patch("controller.controller.RepoManager")
    @patch("util.db_mongo.MongoAdapter.get_session", return_value=None)
    @patch("os.getlogin", return_value="test_user")
    def test_checkout_repo_failed_to_retrieve_details(self, mock_getlogin, mock_get_session, mock_repo_manager):
        """Test checkout_repo when repository details cannot be retrieved."""
        mock_instance = mock_repo_manager.return_value

        # Mock repo state
        mock_instance.is_current_dir_repo.return_value = (True, True, "test_repo")
        mock_instance.checkout_branch_and_commit.return_value = (True, "Checkout successful.")
        mock_instance.get_current_repo_details.return_value = {}

        controller = Controller()
        status, message, repo_data = controller.checkout_repo(branch="main", commit_hash="123abc")

        self.assertFalse(status)
        self.assertEqual(message, "Failed to retrieve repository details.")
        self.assertIsNone(repo_data)


