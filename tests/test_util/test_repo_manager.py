import subprocess
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from util.repo_manager import RepoManager
from util.common_utils import (get_logger)
from git import GitCommandError, InvalidGitRepositoryError

logger = get_logger("tests.test_util.test_repo_manager")


class TestRepoManager(unittest.TestCase):

    # Test for invalid repo URL. Return error, must be given repo
    @patch("util.repo_manager.RepoManager._is_valid_git_repo", return_value=False)
    def test_set_repo_invalid_url(self, mock_is_valid):
        """Test set_repo when provided with an invalid repository URL."""
        repo_manager = RepoManager()
        success, message, _ = repo_manager.set_repo("https://invalid-url/repo")
        self.assertFalse(success)
        self.assertIn("not a valid Git repository", message)

    @patch("util.repo_manager.Path.iterdir", return_value=[])
    @patch("util.repo_manager.Repo.clone_from")
    def test_validate_and_clone_repo_empty_dir(
            self, mock_clone_from, mock_iterdir):
        """Test validate_and_clone_repo with an empty directory and valid cloning."""
        repo_manager = RepoManager()
        mock_repo = MagicMock()
        mock_clone_from.return_value = mock_repo
        mock_repo.head.commit.hexsha = "sample_commit_hash"

        success, message, repo_details = repo_manager.validate_and_clone_repo(
            "https://github.com/sample/repo", branch="main"
        )

        self.assertTrue(success)
        self.assertIn(
            "successfully validated, cloned, and checked out",
            message)
        self.assertEqual(repo_details["commit_hash"], "sample_commit_hash")

    @patch("util.repo_manager.Path.iterdir", return_value=[])
    @patch("util.repo_manager.Repo.clone_from",
           side_effect=GitCommandError("clone", "error"))
    def test_validate_and_clone_repo_clone_failure(
            self, mock_clone_from, mock_iterdir):
        """Test validate_and_clone_repo when cloning fails with GitCommandError."""
        repo_manager = RepoManager()

        success, message, _ = repo_manager.validate_and_clone_repo(
            "https://github.com/sample/repo", branch="nonexistent_branch"
        )

        self.assertFalse(success)
        self.assertIn("Failed to clone repository", message)

    def test_extract_repo_name_with_and_without_git(self):
        """Test _extract_repo_name_from_url extracts repo names with or without .git extension."""
        repo_manager = RepoManager()
        name_with_git = repo_manager._extract_repo_name_from_url(
            "https://github.com/sample/repo.git")
        name_without_git = repo_manager._extract_repo_name_from_url(
            "https://github.com/sample/repo")

        self.assertEqual(name_with_git, "repo")
        self.assertEqual(name_without_git, "repo")

    def test_extract_repo_name_malformed_url(self):
        """Test _extract_repo_name_from_url handles malformed URLs gracefully."""
        repo_manager = RepoManager()
        name = repo_manager._extract_repo_name_from_url(
            "https://github.com/sample")

        self.assertEqual(name, "sample")

    @patch("util.repo_manager.Repo.iter_commits", return_value=[])
    def test_checkout_commit_not_found(self, mock_iter_commits):
        """Test _checkout_commit when the specified commit hash is not found in the branch."""
        repo_manager = RepoManager()
        mock_repo = MagicMock()

        success, message = repo_manager._checkout_commit(
            mock_repo, "main", "nonexistent_commit_hash")

        self.assertFalse(success)
        self.assertIn(
            "Commit hash nonexistent_commit_hash does not exist on branch 'main'",
            message)

    @patch("subprocess.run")
    def test_is_valid_git_repo_valid(self, mock_run):
        """Test _is_valid_git_repo with a valid repository URL."""
        repo_manager = RepoManager()
        mock_run.return_value.returncode = 0
        result = repo_manager._is_valid_git_repo(
            "https://github.com/sample/repo")

        self.assertTrue(result)

    @patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git"))
    def test_is_valid_git_repo_invalid(self, mock_run):
        """Test _is_valid_git_repo with an invalid repository URL."""
        repo_manager = RepoManager()
        result = repo_manager._is_valid_git_repo("https://invalid-url/repo")

        self.assertFalse(result)

    @patch("util.repo_manager.Repo", autospec=True)
    def test_is_current_repo_in_git_repo(self, mock_repo):
        """Test is_current_repo when the current directory is a git repository."""
        repo_manager = RepoManager()
        mock_repo.return_value.working_tree_dir = "/mock/path/to/repo"
        result, repo_name = repo_manager.is_current_repo()

        self.assertTrue(result)
        self.assertEqual(repo_name, "repo")

    @patch("util.repo_manager.Repo", side_effect=InvalidGitRepositoryError)
    def test_is_current_repo_not_in_git_repo(self, mock_repo):
        """Test is_current_repo when the current directory is not a git repository."""
        repo_manager = RepoManager()
        result, repo_name = repo_manager.is_current_repo()

        self.assertFalse(result)
        self.assertIsNone(repo_name)

    @patch("util.repo_manager.shutil.rmtree")
    @patch("util.repo_manager.Path.unlink")
    def test_safe_cleanup(self, mock_unlink, mock_rmtree):
        """Test _safe_cleanup with temporary directory to ensure it is safe."""
        # Create a temporary directory with some files and directories
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            file1 = temp_path / "file1"
            dir1 = temp_path / "dir1"
            file1.touch()  # Create an empty file
            dir1.mkdir()  # Create an empty directory

            # Initialize RepoManager and run _safe_cleanup
            repo_manager = RepoManager()
            repo_manager._safe_cleanup(temp_path)

            # Verify `unlink` was called for files and `rmtree` for directories
            mock_unlink.assert_called_once_with()
            mock_rmtree.assert_called_once_with(dir1)
