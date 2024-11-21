import subprocess
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from util.repo_manager import RepoManager
from util.common_utils import get_logger
from git import GitCommandError, InvalidGitRepositoryError

logger = get_logger("tests.test_util.test_repo_manager")


class TestRepoManager(unittest.TestCase):
    from unittest.mock import patch

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
        self.assertIn(
            "Failed to clone or validate repository. Invalid branch or commit.",
            message)

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

        success, message = repo_manager._handle_checkout_commit(
            mock_repo, "main", "nonexistent_commit_hash")

        self.assertFalse(success)
        self.assertIn(
            "Commit hash nonexistent_commit_hash does not exist on branch 'main'",
            message)

    @patch("subprocess.run")
    def test_is_valid_git_repo_valid(self, mock_run):
        """Test is_valid_git_repo with a valid repository URL."""
        repo_manager = RepoManager()
        mock_run.return_value.returncode = 0
        result = repo_manager.is_valid_git_repo(
            "https://github.com/sample/repo")

        self.assertTrue(result)

    @patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git"))
    def test_is_valid_git_repo_invalid(self, mock_run):
        """Test is_valid_git_repo with an invalid repository URL."""
        repo_manager = RepoManager()
        result = repo_manager.is_valid_git_repo("https://invalid-url/repo")

        # Assert the tuple values
        self.assertEqual(
            result, (False, False, "Repository https://invalid-url/repo is invalid."))

    @patch("util.repo_manager.Repo", autospec=True)
    def test_is_current_dir_repo_in_git_repo(self, mock_repo):
        """Test is_current_dir_repo when the current directory is a Git repository."""
        repo_manager = RepoManager()
        mock_repo.return_value.working_tree_dir = "/mock/path/to/repo"
        mock_repo.return_value.head.commit.hexsha = "latest_commit_hash"

        with patch("os.getcwd", return_value="/mock/path/to/repo"):
            result, is_in_root, repo_name = repo_manager.is_current_dir_repo()

            self.assertTrue(result)
            self.assertEqual(repo_name, "repo")
            self.assertTrue(is_in_root)

    @patch("util.repo_manager.Repo", side_effect=InvalidGitRepositoryError)
    def test_is_current_dir_repo_not_in_git_repo(self, mock_repo):
        """Test is_current_dir_repo when the current directory is not a Git repository."""
        repo_manager = RepoManager()
        result, is_in_root, repo_name = repo_manager.is_current_dir_repo()

        self.assertFalse(result)
        self.assertIsNone(repo_name)
        self.assertFalse(is_in_root)

    @patch("util.repo_manager.shutil.rmtree")
    @patch("util.repo_manager.Path.unlink")
    def test_safe_cleanup(self, mock_unlink, mock_rmtree):
        """Test _safe_cleanup with a temporary directory to ensure it removes contents."""
        with patch("util.repo_manager.Path.iterdir") as mock_iterdir:
            # Set up mock items: one file and one directory
            mock_file = MagicMock(spec=Path)
            mock_file.is_dir.return_value = False
            mock_file.unlink = mock_unlink  # Ensure `unlink` is assigned to this mock file

            mock_dir = MagicMock(spec=Path)
            mock_dir.is_dir.return_value = True

            # Mock `iterdir` to return a list containing the file and directory
            mock_iterdir.return_value = [mock_file, mock_dir]

            # Run the cleanup
            repo_manager = RepoManager()
            repo_manager._safe_cleanup(Path("/mock/path"))

            # Assert `unlink` was called on the file and `rmtree` on the
            # directory
            mock_unlink.assert_called_once_with()
            mock_rmtree.assert_called_once_with(mock_dir)

    @patch("util.repo_manager.Repo", autospec=True)
    def test_get_current_repo_details_success(self, mock_repo):
        """Test get_current_repo_details when in a Git repository."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value
        mock_instance.remote.return_value.urls = iter(
            ["https://github.com/sample/repo.git"])  # Make `urls` an iterator
        mock_instance.active_branch.name = "main"
        mock_instance.head.commit.hexsha = "123abc"

        with patch("os.getcwd", return_value="/mock/path/to/repo"):
            result = repo_manager.get_current_repo_details()

            self.assertEqual(
                result["repo_url"],
                "https://github.com/sample/repo.git")
            self.assertEqual(result["repo_name"], "repo")
            self.assertEqual(result["branch"], "main")
            self.assertEqual(result["commit_hash"], "123abc")

    @patch("util.repo_manager.Repo", side_effect=InvalidGitRepositoryError)
    def test_get_current_repo_details_not_in_git_repo(self, mock_repo):
        """Test get_current_repo_details when not in a Git repository."""
        repo_manager = RepoManager()
        result = repo_manager.get_current_repo_details()

        self.assertEqual(result, {})

    @patch("util.repo_manager.Path.iterdir", return_value=[])  # Mock empty current directory
    @patch("util.repo_manager.Path.resolve", return_value=Path("/mock/repo"))
    @patch("util.repo_manager.Path.is_dir", return_value=True)
    @patch("util.repo_manager.Path.__truediv__", return_value=Path("/mock/repo/.git"))
    @patch("util.repo_manager.Path.exists", side_effect=lambda path: str(path) != "/mock/repo/.git")
    def test_set_repo_no_git_folder(self, mock_exists, mock_truediv, mock_is_dir, mock_resolve, mock_iterdir):
        """Test set_repo with a local path missing `.git` folder."""
        repo_manager = RepoManager()

        # Provide a local path without `.git` folder
        success, message, repo_details = repo_manager.set_repo(
            "/mock/repo", is_remote=False
        )

        self.assertFalse(success)
        self.assertIn("failed to clone or validate repository. invalid branch or commit.", message.lower())
        self.assertEqual(repo_details, {})

    @patch("util.repo_manager.Path.iterdir", return_value=[])  # Mock empty current directory
    def test_set_repo_empty_path(self, mock_iterdir):
        """Test set_repo with an empty path."""
        repo_manager = RepoManager()

        # Provide an empty path
        success, message, repo_details = repo_manager.set_repo("", is_remote=False)

        self.assertFalse(success)
        self.assertIn("provided repository path is empty.", message.lower())
        self.assertEqual(repo_details, {})

    @patch("util.repo_manager.Path.iterdir", return_value=[])  # Mock empty current directory
    def test_set_repo_invalid_path_characters(self, mock_iterdir):
        """Test set_repo with a path containing invalid characters."""
        repo_manager = RepoManager()

        # Provide a path with invalid characters
        success, message, repo_details = repo_manager.set_repo("/mock/repo/<>|:*?", is_remote=False)

        self.assertFalse(success)
        self.assertIn("failed to clone or validate repository. invalid branch or commit", message.lower())
        self.assertEqual(repo_details, {})

    @patch("util.repo_manager.Repo", autospec=True)
    def test_checkout_branch_and_commit_branch_exists_locally(self, mock_repo):
        """Test checkout_branch_and_commit when the branch exists locally."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Mock the repository to simulate a clean state
        mock_instance.is_dirty.return_value = False

        # Mock branches to behave like GitPython branches
        mock_branch = MagicMock()
        mock_branch.name = "feature-branch"
        mock_instance.branches = [mock_branch]

        # Simulate successful branch checkout
        mock_instance.git.checkout.return_value = None

        # Simulate remote branch (optional: only needed if method handles remote branches)
        mock_instance.git.ls_remote.return_value = "refs/heads/feature-branch"

        # Call the method
        success, message = repo_manager.checkout_branch_and_commit(branch="feature-branch")

        self.assertTrue(success)
        self.assertIn("Repository successfully checked out to branch 'feature-branch'", message)

        # Check that `checkout` was called appropriately
        try:
            # If branch exists locally, it should not use `-b`
            mock_instance.git.checkout.assert_called_once_with("feature-branch")
        except AssertionError:
            # If the branch was created (remote branch scenario), check for `-b`
            mock_instance.git.checkout.assert_called_once_with("-b", "feature-branch", "origin/feature-branch")

    @patch("util.repo_manager.Repo", autospec=True)
    def test_checkout_branch_and_commit_with_commit_hash(self, mock_repo):
        """Test checkout_branch_and_commit with a specific commit hash."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Mock the repository to simulate a clean state
        mock_instance.is_dirty.return_value = False

        # Mock branches to behave like GitPython branches
        mock_branch = MagicMock()
        mock_branch.name = "main"
        mock_instance.branches = [mock_branch]

        # Simulate the existence of the commit in the branch
        mock_instance.iter_commits.return_value = [
            type("Commit", (object,), {"hexsha": "123abc"})
        ]

        # Simulate successful commit checkout
        mock_instance.git.checkout.return_value = None

        # Call the method
        success, message = repo_manager.checkout_branch_and_commit(branch="main", commit_hash="123abc")

        self.assertTrue(success)
        self.assertIn("Repository successfully checked out to branch 'main' and commit '123abc'", message)
        mock_instance.git.checkout.assert_called_with("123abc")

    @patch("util.repo_manager.Repo", autospec=True)
    def test_checkout_branch_and_commit_invalid_commit(self, mock_repo):
        """Test checkout_branch_and_commit when the commit hash is invalid."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Mock the repository to simulate a clean state
        mock_instance.is_dirty.return_value = False

        # Mock branches to behave like GitPython branches
        mock_branch = MagicMock()
        mock_branch.name = "main"
        mock_instance.branches = [mock_branch]

        # Simulate no matching commits for the provided hash
        mock_instance.iter_commits.return_value = []

        # Call the method
        success, message = repo_manager.checkout_branch_and_commit(branch="main", commit_hash="nonexistent")

        self.assertFalse(success)
        self.assertIn("Commit 'nonexistent' does not exist on branch 'main'", message)

    @patch("util.repo_manager.Repo", autospec=True)
    def test_checkout_branch_and_commit_remote_branch_not_found(self, mock_repo):
        """Test checkout_branch_and_commit when the remote branch does not exist."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Mock the repository to simulate a clean state
        mock_instance.is_dirty.return_value = False

        # Simulate no remote branch found
        mock_instance.git.ls_remote.return_value = ""

        # Call the method
        success, message = repo_manager.checkout_branch_and_commit(branch="nonexistent-branch")

        self.assertFalse(success)
        self.assertIn("Branch 'nonexistent-branch' does not exist locally or remotely.", message)
        mock_instance.git.ls_remote.assert_called_once_with("--heads", "origin", "nonexistent-branch")

    @patch("util.repo_manager.Repo", autospec=True)
    def test_checkout_branch_and_commit_pull_latest(self, mock_repo):
        """Test checkout_branch_and_commit pulling the latest changes when no commit hash is provided."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Mock the repository to simulate a clean state
        mock_instance.is_dirty.return_value = False

        # Mock branch
        mock_branch = MagicMock()
        mock_branch.name = "main"
        mock_instance.branches = [mock_branch]

        # Simulate successful pull
        mock_instance.git.pull.return_value = None

        # Call the method
        success, message = repo_manager.checkout_branch_and_commit(branch="main")

        self.assertTrue(success)
        self.assertIn("Repository successfully checked out to branch 'main'", message)
        mock_instance.git.pull.assert_called_once_with("origin", "main")

    @patch("util.repo_manager.Repo", autospec=True)
    def test_checkout_branch_and_commit_with_unstaged_changes(self, mock_repo):
        """Test checkout_branch_and_commit when there are unstaged changes in the repository."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Mock the repository to simulate an unclean state
        mock_instance.is_dirty.return_value = True

        # Call the method
        success, message = repo_manager.checkout_branch_and_commit(branch="main")

        self.assertFalse(success)
        self.assertIn("Unstaged changes detected. Please commit or stash changes before proceeding.", message)