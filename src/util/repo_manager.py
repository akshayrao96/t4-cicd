"""
Manages Git repositories and parses YAML files.

For remote repositories, both the source URL and target path are required.
For local repositories, the target path defaults to the source path.
All paths must be absolute. The branch defaults to 'main' but can be changed as needed.
"""

from pathlib import Path
import os
from urllib.parse import urlparse
import subprocess
import shutil
from git import Repo, GitCommandError, InvalidGitRepositoryError
from util.common_utils import get_logger

logger = get_logger(logger_name='util.repo_manager')


class RepoManager:
    """
    Utility class for managing Git repositories, including cloning, validation,
    branch and commit handling, and metadata extraction.
    """

    def set_repo(
            self,
            repo_source: str,
            branch: str = "main",
            commit_hash: str = None) -> tuple:
        """
        Validate the repository, clone it if necessary, and avoid redundant cloning if possible.

        Args:
            repo_source (str): The repository URL.
            branch (str): The branch to validate (default is "main").
            commit_hash (str): Optional commit hash to validate.

        Returns:
            tuple: (bool, str, dict) indicating success status, message, and repository details.
        """
        logger.debug(
            "Checking if given repo %s is a valid git repo",
            repo_source)
        if not self._is_valid_git_repo(repo_source):
            return False, "Repository is not a valid Git repository.", {}

        current_directory = Path(os.getcwd())

        if any(current_directory.iterdir()):
            logger.warning(
                "Current working directory is not empty. Please use an empty directory.")
            return False, "Current working directory is not empty. Please use an empty directory.", {}

        logger.debug(
            "Starting repository validation for %s with branch '%s' and commit '%s'.",
            repo_source,
            branch,
            commit_hash)

        # Step 3: Attempt to clone and validate the repo
        success, message, repo_details = self.validate_and_clone_repo(
            repo_source, branch, commit_hash)

        if not success:
            return False, message, {}

        repo_details = self.get_current_repo_details()

        if not repo_details:
            return False, "Failed to retrieve repository details after cloning.", {}

        return True, "Repository successfully cloned and set up in the current directory.", repo_details

    def validate_and_clone_repo(
            self,
            repo_source: str,
            branch: str = "main",
            commit_hash: str = None) -> tuple:
        """
        Validate the branch and commit, clone the repository if valid, and return repository details.

        Args:
            repo_source (str): The repository URL.
            branch (str): The branch to validate (default is "main").
            commit_hash (str): Optional commit hash to validate.

        Returns:
            tuple: (bool, str, dict) where the first element is success status,
            the second element is a message,
            the third element is a dictionary containing repo details (if successful).
        """
        logger.debug(
            "Starting validation and cloning for %s with branch '%s' and commit '%s'.",
            repo_source,
            branch,
            commit_hash)

        current_directory = Path(os.getcwd())
        repo_name = self._extract_repo_name_from_url(repo_source)

        # Check if the current directory is empty
        if any(current_directory.iterdir()):
            logger.warning("Current working directory is not empty.")
            return False, "Current working directory is not empty. Please use an empty directory.", {}

        try:
            # Clone the repository contents directly into the current working
            # directory
            repo = Repo.clone_from(
                repo_source,
                current_directory,
                branch=branch,
                single_branch=True)
            latest_commit_hash = repo.head.commit.hexsha
            logger.debug(
                "Successfully cloned branch '%s' with latest commit %s.",
                branch,
                latest_commit_hash)

            # If a specific commit hash is provided, check out that commit
            # without detaching HEAD
            if commit_hash:
                success, message = self._checkout_commit(
                    repo, branch, commit_hash)
                if not success:
                    self._safe_cleanup(current_directory)
                    return False, message

            return True, "Repository successfully validated, cloned, and checked out.", {
                "repo_name": repo_name,
                "repo_source": repo_source,
                "branch": branch,
                "commit_hash": commit_hash or latest_commit_hash
            }

        except GitCommandError as e:
            logger.warning("An error occurred during cloning: %s", e)
            return False, "Failed to clone repository. Branch given not found in repository.",{}

    def _checkout_commit(
            self,
            repo: Repo,
            branch: str,
            commit_hash: str) -> tuple:
        """
        Check out a specific commit on a branch without detaching HEAD.

        Args:
            repo (Repo): The cloned repository object.
            branch (str): The branch to check out.
            commit_hash (str): The specific commit hash to check out.

        Returns:
            tuple: (bool, str) indicating success status and message.
        """
        if any(commit_hash == commit.hexsha for commit in repo.iter_commits(branch)):
            repo.git.checkout(commit_hash)
            repo.git.execute(
                ["git", "update-ref", f"refs/heads/{branch}", commit_hash])
            repo.git.checkout(branch)
            logger.debug(
                "Checked out and reset branch '%s' to commit %s.",
                branch,
                commit_hash)
            return True, f"Checked out branch '{branch}' at commit {commit_hash}."
        else:
            logger.warning(
                "Commit hash %s does not exist on branch '%s'.",
                commit_hash,
                branch)
            return False, f"Commit hash {commit_hash} does not exist on branch '{branch}'."

    def _is_valid_git_repo(self, repo_source: str) -> bool:
        """
        Check if the given repo source is a valid Git repository.

        Args:
            repo_source (str): The repository source URL.

        Returns:
            bool: True if the repository is valid, False otherwise.
        """
        logger.debug(
            "Validating if %s is a valid Git repository.",
            repo_source)
        try:
            subprocess.run(["git", "ls-remote", repo_source],
                           capture_output=True, check=True, text=True)
            logger.info("Repository %s is valid.", repo_source)
            return True
        except subprocess.CalledProcessError:
            logger.warning("Repository %s is invalid.", repo_source)
            return False

    def _extract_repo_name_from_url(self, url: str) -> str:
        """
        Extract the repository name from the URL.

        Args:
            url (str): The repository URL.

        Returns:
            str: The extracted repository name, or an empty string if invalid.
        """
        try:
            parsed_url = urlparse(url)
            repo_name = os.path.basename(
                parsed_url.path.strip("/"))  # Strip any trailing slashes
            repo_name = repo_name.rstrip(".git")
            logger.debug(
                "Extracted repo name '%s' from URL %s.",
                repo_name,
                url)
            return repo_name
        except Exception as e:
            logger.error(
                "Failed to extract repo name from URL %s: %s",
                url,
                str(e))
            return ""

    def is_current_repo(self) -> tuple[bool, str | None]:
        """
        Check if the current working directory is a Git repository.

        Returns:
            tuple[bool, Optional[str]]: True and repo name if in Git repo, otherwise False and None.
        """
        try:
            repo = Repo(os.getcwd(), search_parent_directories=True)
            repo_name = os.path.basename(repo.working_tree_dir)
            return True, repo_name
        except InvalidGitRepositoryError:
            return False, None

    def _safe_cleanup(self, path: Path):
        """Safely remove all contents of the specified directory without deleting the directory itself."""
        for item in path.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            except Exception as e:
                logger.error("Failed to remove %s: %s", item, e)
        logger.info("Cleaned up all contents inside the directory %s", path)

    def get_current_repo_details(self) -> dict:
        """
        Retrieve details of the current Git repository.

        Returns:
            dict: A dictionary containing repository details such as repo_url, repo_name, branch, and commit_hash.
                  Returns an empty dictionary if not in a Git repository.
        """
        try:
            repo = Repo(os.getcwd(), search_parent_directories=True)
            origin_url = next(repo.remote().urls)
            branch = repo.active_branch.name
            commit_hash = repo.head.commit.hexsha
            repo_name = self._extract_repo_name_from_url(origin_url)

            return {
                "repo_url": origin_url,
                "repo_name": repo_name,
                "branch": branch,
                "commit_hash": commit_hash
            }

        except InvalidGitRepositoryError:
            return {}

        except GitCommandError as e:
            logger.error("Error while retrieving repository details: %s", e)
            return {}
