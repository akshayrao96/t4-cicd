"""Test controller integration
"""
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from controller.controller import (Controller)
from util.common_utils import (get_logger)
import util.constant as c


logger = get_logger("tests.test_controller.test_controller")

class TestControllerRepoFunctions(unittest.TestCase):
    """Test cases for the Controller class repository functions."""
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
            c.FIELD_REPO_NAME: "sample_repo",
            c.FIELD_BRANCH: c.DEFAULT_BRANCH,
            c.FIELD_COMMIT_HASH: "latest_commit_hash"
        })

        # Mocking session detail validation and dump
        mock_session_detail = MockSessionDetail.return_value
        mock_session_detail.model_dump.return_value = {
            c.FIELD_USER_ID: "test_user",
            c.FIELD_REPO_URL: "https://github.com/sample/repo",
            c.FIELD_REPO_NAME: "sample_repo",
            c.FIELD_BRANCH: c.DEFAULT_BRANCH,
            c.FIELD_COMMIT_HASH: "latest_commit_hash",
            c.FIELD_IS_REMOTE: True,
            c.FIELD_TIME: datetime.now().strftime(c.DATETIME_FORMAT)
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
            c.FIELD_REPO_URL: "https://github.com/sample/repo",
            c.FIELD_REPO_NAME: "existing_repo",
            c.FIELD_BRANCH: c.DEFAULT_BRANCH,
            c.FIELD_COMMIT_HASH: "123abc",
        }

        fixed_time = datetime.now().strftime(c.DATETIME_FORMAT)

        with patch("util.model.SessionDetail") as MockSessionDetail:
            mock_session_detail = MockSessionDetail(
                user_id="test_user",
                repo_url="https://github.com/sample/repo",
                repo_name="existing_repo",
                branch=c.DEFAULT_BRANCH,
                commit_hash="123abc",
                is_remote=True,
                time=fixed_time,
            )
            mock_session_detail.model_dump.return_value = {
                c.FIELD_USER_ID: "test_user",
                c.FIELD_REPO_URL: "https://github.com/sample/repo",
                c.FIELD_REPO_NAME: "existing_repo",
                c.FIELD_BRANCH: c.DEFAULT_BRANCH,
                c.FIELD_COMMIT_HASH: "123abc",
                c.FIELD_IS_REMOTE: False,
                c.FIELD_TIME: fixed_time,
            }
            MockSessionDetail.return_value = mock_session_detail

            controller = Controller()
            status, message, repo_data = controller.get_repo()

            self.assertTrue(status)
            self.assertEqual(message, "Repository is configured in current directory")
            self.assertIsNotNone(repo_data)
            self.assertEqual(repo_data.repo_name, "existing_repo")
            self.assertEqual(repo_data.branch, c.DEFAULT_BRANCH)
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
            c.FIELD_USER_ID: "test_user",
            c.FIELD_REPO_URL: "https://github.com/sample/last_repo",
            c.FIELD_REPO_NAME: "last_repo",
            c.FIELD_BRANCH: c.DEFAULT_BRANCH,
            c.FIELD_COMMIT_HASH: "456def",
            c.FIELD_IS_REMOTE: True,
            c.FIELD_TIME: "2024-01-01 12:00:00"
        }

        with patch("util.model.SessionDetail") as MockSessionDetail:
            mock_session_detail = MockSessionDetail.return_value
            mock_session_detail.repo_url = "https://github.com/sample/last_repo"
            mock_session_detail.repo_name = "last_repo"
            mock_session_detail.branch = c.DEFAULT_BRANCH
            mock_session_detail.commit_hash = "456def"

            controller = Controller()
            status, message, repo_data = controller.get_repo()

            self.assertFalse(status)
            self.assertEqual(message, "Current working directory is not a git repository")
            self.assertIsNotNone(repo_data)
            self.assertEqual(repo_data.repo_url, "https://github.com/sample/last_repo")
            self.assertEqual(repo_data.repo_name, "last_repo")
            self.assertEqual(repo_data.branch, c.DEFAULT_BRANCH)
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
        result = controller.handle_repo(repo_url="https://github.com/sample/repo",
                                        branch=c.DEFAULT_BRANCH, commit_hash="abc123")

        # Assert that set_repo was called with correct parameters
        mock_set_repo.assert_called_once_with(
            repo_url="https://github.com/sample/repo",
            branch=c.DEFAULT_BRANCH,
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
        result = controller.handle_repo(branch=c.DEFAULT_BRANCH, commit_hash="abc123")

        # Assert that checkout_repo was called with correct parameters
        mock_checkout_repo.assert_called_once_with(branch=c.DEFAULT_BRANCH, commit_hash="abc123")

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
        status, message, repo_data = controller.checkout_repo(branch=c.DEFAULT_BRANCH)

        self.assertFalse(status)
        self.assertEqual(message, "Current directory is not a Git repository.")
        self.assertIsNone(repo_data)

    @patch("controller.controller.RepoManager")
    @patch("util.db_mongo.MongoAdapter.get_session", return_value=None)
    @patch("util.db_mongo.MongoAdapter.update_session", return_value="mock_inserted_id")
    @patch("os.getlogin", return_value="test_user")
    def test_checkout_repo_success(self, mock_getlogin, mock_update_session,
                                   mock_get_session, mock_repo_manager):
        """Test checkout_repo when branch and commit are successfully checked out."""
        mock_instance = mock_repo_manager.return_value

        # Mock repo state
        mock_instance.is_current_dir_repo.return_value = (True, True, "test_repo")
        mock_instance.checkout_branch_and_commit.return_value = (True, "Checkout successful.")

        # Generate the absolute path for the mocked repo_url
        repo_url_absolute = str(Path("https://github.com/sample/repo").resolve())
        mock_instance.get_current_repo_details.return_value = {
            c.FIELD_REPO_URL: repo_url_absolute,
            c.FIELD_REPO_NAME: "test_repo",
            c.FIELD_BRANCH: c.DEFAULT_BRANCH,
            c.FIELD_COMMIT_HASH: "123abc",
        }

        # Mock SessionDetail
        fixed_time = datetime.now().strftime(c.DATETIME_FORMAT)
        with patch("util.model.SessionDetail") as MockSessionDetail:
            mock_session_detail = MockSessionDetail(
                user_id="test_user",
                repo_url=repo_url_absolute,
                repo_name="test_repo",
                branch=c.DEFAULT_BRANCH,
                commit_hash="123abc",
                is_remote=False,
                time=fixed_time,
            )
            mock_session_detail.model_dump.return_value = {
                c.FIELD_USER_ID: "test_user",
                c.FIELD_REPO_URL: repo_url_absolute,
                c.FIELD_REPO_NAME: "test_repo",
                c.FIELD_BRANCH: c.DEFAULT_BRANCH,
                c.FIELD_COMMIT_HASH: "123abc",
                c.FIELD_IS_REMOTE: False,
                c.FIELD_TIME: fixed_time,
            }
            MockSessionDetail.return_value = mock_session_detail

            controller = Controller()
            status, message, repo_data = controller.checkout_repo(branch=c.DEFAULT_BRANCH, commit_hash="123abc")

            self.assertTrue(status)
            self.assertEqual(message, "Repository checked out successfully.")
            self.assertIsNotNone(repo_data)
            self.assertEqual(repo_data.repo_name, "test_repo")
            self.assertEqual(repo_data.branch, c.DEFAULT_BRANCH)
            self.assertEqual(repo_data.repo_url, repo_url_absolute)  # Use the absolute path here
            self.assertEqual(repo_data.commit_hash, "123abc")
            mock_update_session.assert_called_once_with(mock_session_detail.model_dump())

    @patch("controller.controller.RepoManager")
    @patch("util.db_mongo.MongoAdapter.get_session", return_value=None)
    @patch("os.getlogin", return_value="test_user")
    def test_checkout_repo_commit_not_found(self, mock_getlogin, mock_get_session,
                                            mock_repo_manager):
        """Test checkout_repo when the commit does not exist."""
        mock_instance = mock_repo_manager.return_value

        # Mock repo state
        mock_instance.is_current_dir_repo.return_value = (True, True, "test_repo")
        mock_instance.checkout_branch_and_commit.return_value = (False, "Commit not found.")

        controller = Controller()
        status, message, repo_data = controller.checkout_repo(branch=c.DEFAULT_BRANCH, commit_hash="nonexistent_commit_hash")

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
        status, message, repo_data = controller.checkout_repo(branch=c.DEFAULT_BRANCH,
                                                              commit_hash="123abc")

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
        status, message, repo_data = controller.checkout_repo(branch=c.DEFAULT_BRANCH,
                                                              commit_hash="123abc")

        self.assertFalse(status)
        self.assertEqual(message, "Current directory is not a Git repository.")
        self.assertIsNone(repo_data)

    @patch("controller.controller.RepoManager")
    @patch("util.db_mongo.MongoAdapter.get_session", return_value=None)
    @patch("os.getlogin", return_value="test_user")
    def test_checkout_repo_failed_to_retrieve_details(self, mock_getlogin,
                                                      mock_get_session, mock_repo_manager):
        """Test checkout_repo when repository details cannot be retrieved."""
        mock_instance = mock_repo_manager.return_value

        # Mock repo state
        mock_instance.is_current_dir_repo.return_value = (True, True, "test_repo")
        mock_instance.checkout_branch_and_commit.return_value = (True, "Checkout successful.")
        mock_instance.get_current_repo_details.return_value = {}

        controller = Controller()
        status, message, repo_data = controller.checkout_repo(branch=c.DEFAULT_BRANCH,
                                                              commit_hash="123abc")

        self.assertFalse(status)
        self.assertEqual(message, "Failed to retrieve repository details.")
        self.assertIsNone(repo_data)
