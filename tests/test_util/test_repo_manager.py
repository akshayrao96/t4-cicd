import subprocess
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from util.repo_manager import RepoManager
from util.common_utils import get_logger
from git import GitCommandError, InvalidGitRepositoryError
import util.constant as c

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
            "https://github.com/sample/repo", branch=c.DEFAULT_BRANCH
        )

        self.assertTrue(success)
        self.assertIn(
            "successfully validated, cloned, and checked out",
            message)
        self.assertEqual(
            repo_details[c.FIELD_COMMIT_HASH], "sample_commit_hash")

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
        mock_instance.remotes.return_value = "origin"
        mock_instance.remote.return_value.urls = iter(
            ["https://github.com/sample/repo.git"])  # Make `urls` an iterator
        mock_instance.active_branch.name = c.DEFAULT_BRANCH
        mock_instance.head.commit.hexsha = "123abc"

        with patch("os.getcwd", return_value="/mock/path/to/repo"):
            result = repo_manager.get_current_repo_details()

            self.assertEqual(
                result[c.FIELD_REPO_URL],
                "https://github.com/sample/repo.git")
            self.assertEqual(result[c.FIELD_REPO_NAME], "repo")
            self.assertEqual(result[c.FIELD_BRANCH], c.DEFAULT_BRANCH)
            self.assertEqual(result[c.FIELD_COMMIT_HASH], "123abc")

    @patch("util.repo_manager.Repo", side_effect=InvalidGitRepositoryError)
    def test_get_current_repo_details_not_in_git_repo(self, mock_repo):
        """Test get_current_repo_details when not in a Git repository."""
        repo_manager = RepoManager()
        result = repo_manager.get_current_repo_details()

        self.assertEqual(result, {})

    # Mock empty current directory
    @patch("util.repo_manager.Path.iterdir", return_value=[])
    @patch("util.repo_manager.Path.resolve", return_value=Path("/mock/repo"))
    @patch("util.repo_manager.Path.is_dir", return_value=True)
    @patch("util.repo_manager.Path.__truediv__",
           return_value=Path("/mock/repo/.git"))
    @patch("util.repo_manager.Path.exists",
           side_effect=lambda path: str(path) != "/mock/repo/.git")
    def test_set_repo_no_git_folder(
            self,
            mock_exists,
            mock_truediv,
            mock_is_dir,
            mock_resolve,
            mock_iterdir):
        """Test set_repo with a local path missing `.git` folder."""
        repo_manager = RepoManager()

        # Provide a local path without `.git` folder
        success, message, repo_details = repo_manager.set_repo(
            "/mock/repo", is_remote=False
        )

        self.assertFalse(success)
        self.assertIn(
            "failed to clone or validate repository. invalid branch or commit.",
            message.lower())
        self.assertEqual(repo_details, {})

    # Mock empty current directory
    @patch("util.repo_manager.Path.iterdir", return_value=[])
    def test_set_repo_empty_path(self, mock_iterdir):
        """Test set_repo with an empty path."""
        repo_manager = RepoManager()

        # Provide an empty path
        success, message, repo_details = repo_manager.set_repo(
            "", is_remote=False)

        self.assertFalse(success)
        self.assertIn("provided repository path is empty.", message.lower())
        self.assertEqual(repo_details, {})

    # Mock empty current directory
    @patch("util.repo_manager.Path.iterdir", return_value=[])
    def test_set_repo_invalid_path_characters(self, mock_iterdir):
        """Test set_repo with a path containing invalid characters."""
        repo_manager = RepoManager()

        # Provide a path with invalid characters
        success, message, repo_details = repo_manager.set_repo(
            "/mock/repo/<>|:*?", is_remote=False)

        self.assertFalse(success)
        self.assertIn(
            "failed to clone or validate repository. invalid branch or commit",
            message.lower())
        self.assertEqual(repo_details, {})

    @patch("util.repo_manager.Repo", autospec=True)
    def test_checkout_branch_and_commit_remote_branch_exists(self, mock_repo):
        """Test checkout_branch_and_commit when the branch exists remotely."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Mock clean repository and remote branch
        mock_instance.is_dirty.return_value = False
        mock_instance.branches = []
        mock_instance.git.ls_remote.return_value = "refs/heads/feature-branch"
        mock_instance.iter_commits.return_value = [MagicMock(hexsha="123abc")]

        # Mock the latest commit as "123abc"
        mock_instance.head.commit.hexsha = "123abc"

        # Call the method without specifying commit_hash
        success, message = repo_manager.checkout_branch_and_commit(
            branch="feature-branch")

        # Assertions
        self.assertTrue(success)
        self.assertIn("feature-branch", message)

        # Verify that fetch and checkout were called with the correct parameters
        mock_instance.git.fetch.assert_called_once_with(
            "origin", "refs/heads/feature-branch:refs/remotes/origin/feature-branch"
        )
        mock_instance.git.checkout.assert_called_once_with(
            "-b", "feature-branch", "origin/feature-branch"
        )

    @patch("util.repo_manager.Repo", autospec=True)
    def test_checkout_branch_and_commit_invalid_remote_branch(self, mock_repo):
        """Test checkout_branch_and_commit when the remote branch does not exist."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Mock clean repository and no remote branch
        mock_instance.is_dirty.return_value = False
        mock_instance.git.ls_remote.return_value = ""

        # Call the method
        success, message = repo_manager.checkout_branch_and_commit(
            branch="nonexistent-branch")

        self.assertFalse(success)
        self.assertIn("does not exist remotely", message)
        mock_instance.git.ls_remote.assert_called_once_with(
            "--heads", "origin", "nonexistent-branch")

    @patch("util.repo_manager.Repo", autospec=True)
    def test_checkout_branch_and_commit_valid_commit_hash(self, mock_repo):
        """Test checkout_branch_and_commit with a valid commit hash."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Mock clean repository, local branch, and valid commit
        mock_instance.is_dirty.return_value = False
        mock_instance.branches = [c.DEFAULT_BRANCH]
        mock_instance.iter_commits.return_value = [MagicMock(hexsha="123abc")]

        # Call the method
        success, message = repo_manager.checkout_branch_and_commit(
            branch=c.DEFAULT_BRANCH, commit_hash="123abc")

        self.assertTrue(success)
        self.assertIn("123abc", message)
        # mock_instance.git.checkout.assert_called_with(c.DEFAULT_BRANCH)
        # mock_instance.git.execute.assert_called_once_with(
        #    ["git", "reset", "--hard", "123abc"])

    @patch("util.repo_manager.Repo", autospec=True)
    def test_checkout_branch_and_commit_invalid_commit_hash(self, mock_repo):
        """Test checkout_branch_and_commit with an invalid commit hash."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Mock clean repository with a local branch and no matching commit
        mock_instance.is_dirty.return_value = False
        mock_instance.branches = [c.DEFAULT_BRANCH]
        mock_instance.head.commit.hexsha = "Head"
        mock_instance.commit.side_effect = ValueError()
        mock_instance.iter_commits.return_value = [MagicMock(hexsha="456def")]

        # Call the method with an invalid commit hash
        success, message = repo_manager.checkout_branch_and_commit(
            branch=c.DEFAULT_BRANCH, commit_hash="invalid"
        )

        # Assert failure
        self.assertFalse(success)
        self.assertIn(
            "Commit 'invalid' does not exist on local branch 'main'.", message)
        # mock_instance.git.checkout.assert_called_once_with(c.DEFAULT_BRANCH)

    @patch("util.repo_manager.Repo", autospec=True)
    def test_checkout_branch_and_commit_with_unstaged_changes(self, mock_repo):
        """Test checkout_branch_and_commit when there are unstaged changes."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Mock unclean repository
        mock_instance.is_dirty.return_value = True

        # Call the method
        success, message = repo_manager.checkout_branch_and_commit(
            branch=c.DEFAULT_BRANCH)

        self.assertFalse(success)
        self.assertIn("Unstaged changes detected", message)
        mock_instance.git.checkout.assert_not_called()

    @patch("util.repo_manager.Repo")
    def test_checkout_commit_after_clone_branch_exists_locally(self, mock_repo):
        """Test _checkout_commit_after_clone when the branch exists locally."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Simulate branch and commit existence
        mock_instance.branches = [c.DEFAULT_BRANCH]
        mock_instance.iter_commits.return_value = [
            MagicMock(hexsha="123abc"), MagicMock(hexsha="456def")
        ]

        # Call the method
        success, message = repo_manager._checkout_commit_after_clone(
            mock_instance, c.DEFAULT_BRANCH, "123abc"
        )

        # Assertions
        self.assertTrue(success)
        self.assertIn(
            "Checked out to commit '123abc' on branch 'main'", message)
        mock_instance.git.checkout.assert_called_once_with(c.DEFAULT_BRANCH)
        mock_instance.git.execute.assert_called_once_with(
            ["git", "reset", "--hard", "123abc"])

    @patch("util.repo_manager.Repo")
    def test_checkout_commit_after_clone_branch_does_not_exist_locally(self, mock_repo):
        """Test _checkout_commit_after_clone when the branch exists remotely but not locally."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Simulate branch absence locally and presence remotely
        mock_instance.branches = []
        mock_instance.git.ls_remote.return_value = "refs/heads/main"
        mock_instance.iter_commits.return_value = [
            MagicMock(hexsha="123abc"), MagicMock(hexsha="456def")
        ]

        # Call the method
        success, message = repo_manager._checkout_commit_after_clone(
            mock_instance, c.DEFAULT_BRANCH, "123abc"
        )

        # Assertions
        self.assertTrue(success)
        self.assertIn(
            "Checked out to commit '123abc' on branch 'main'", message)
        mock_instance.git.fetch.assert_called_once_with(
            "origin refs/heads/main:refs/remotes/origin/main"
        )
        mock_instance.git.checkout.assert_called_once_with(
            "-b", c.DEFAULT_BRANCH, "origin/main")
        mock_instance.git.execute.assert_called_once_with(
            ["git", "reset", "--hard", "123abc"])

    @patch("util.repo_manager.Repo")
    def test_checkout_commit_after_clone_invalid_commit(self, mock_repo):
        """Test _checkout_commit_after_clone when the commit hash is invalid."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Simulate branch and commit existence
        mock_instance.branches = [c.DEFAULT_BRANCH]
        mock_instance.iter_commits.return_value = [
            MagicMock(hexsha="123abc"), MagicMock(hexsha="456def")
        ]

        # Call the method
        success, message = repo_manager._checkout_commit_after_clone(
            mock_instance, c.DEFAULT_BRANCH, "invalid_commit"
        )

        # Assertions
        self.assertFalse(success)
        self.assertIn(
            "Commit 'invalid_commit' does not exist on branch 'main'", message)
        mock_instance.git.checkout.assert_called_once_with(c.DEFAULT_BRANCH)
        mock_instance.git.execute.assert_not_called()

    @patch("util.repo_manager.Repo")
    def test_checkout_commit_after_clone_branch_does_not_exist_remotely(self, mock_repo):
        """Test _checkout_commit_after_clone when the branch does not exist remotely."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Simulate branch absence locally and remotely
        mock_instance.branches = []
        mock_instance.git.ls_remote.return_value = ""

        # Call the method
        success, message = repo_manager._checkout_commit_after_clone(
            mock_instance, "nonexistent-branch", "123abc"
        )

        # Assertions
        self.assertFalse(success)
        self.assertIn(
            "Branch 'nonexistent-branch' does not exist remotely.", message)
        mock_instance.git.ls_remote.assert_called_once_with("--heads",
                                                            "origin", "nonexistent-branch")
        mock_instance.git.fetch.assert_not_called()
        mock_instance.git.checkout.assert_not_called()

    @patch("util.repo_manager.Repo")
    def test_checkout_commit_after_clone_git_command_error(self, mock_repo):
        """Test _checkout_commit_after_clone when a GitCommandError is raised."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Simulate a GitCommandError
        mock_instance.git.checkout.side_effect = GitCommandError(
            "checkout", "Error during checkout"
        )

        # Call the method
        success, message = repo_manager._checkout_commit_after_clone(
            mock_instance, c.DEFAULT_BRANCH, "123abc"
        )

        # Assertions
        self.assertFalse(success)
        self.assertIn("Error during checkout", message)

    @patch("util.repo_manager.Repo")
    def test_checkout_commit_after_clone_branch_exists_but_commit_not_found(self, mock_repo):
        """Test _checkout_commit_after_clone when branch exists but the commit is not found."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Simulate branch existence but no matching commits
        mock_instance.branches = [c.DEFAULT_BRANCH]
        mock_instance.iter_commits.return_value = []

        # Call the method
        success, message = repo_manager._checkout_commit_after_clone(
            mock_instance, c.DEFAULT_BRANCH, "nonexistent_commit"
        )

        # Assertions
        self.assertFalse(success)
        self.assertIn(
            "Commit 'nonexistent_commit' does not exist on branch 'main'", message)
        mock_instance.git.checkout.assert_called_once_with(c.DEFAULT_BRANCH)
        mock_instance.git.execute.assert_not_called()

    @patch("util.repo_manager.Repo", autospec=True)
    def test_checkout_branch_and_commit_success(self, mock_repo):
        """Test checkout_branch_and_commit with valid branch and commit hash."""
        repo_manager = RepoManager()
        mock_instance = mock_repo.return_value

        # Mock clean repository with local branch and valid commit
        mock_instance.is_dirty.return_value = False
        mock_instance.branches = [c.DEFAULT_BRANCH]
        mock_instance.iter_commits.return_value = [
            MagicMock(hexsha="123abc"),
            MagicMock(hexsha="456def"),
        ]

        # Call the method
        success, message = repo_manager.checkout_branch_and_commit(
            branch=c.DEFAULT_BRANCH, commit_hash="123abc"
        )

        # Assert success
        self.assertTrue(success)
        self.assertIn("Repository successfully checked out to branch 'main' and commit '123abc'.",
                      message)

        # Assert branch and commit actions
        # mock_instance.git.checkout.assert_called_once_with(c.DEFAULT_BRANCH)
        # mock_instance.git.execute.assert_called_once_with(["git", "reset", "--hard", "123abc"])
