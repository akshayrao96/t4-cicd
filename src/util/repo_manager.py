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
            is_remote: bool,
            branch: str = "main",
            commit_hash: str = None) -> tuple[bool, str, dict]:
        """
        Validates the repository, clones it, and returns repository details.

        Args:
            repo_source (str): The repository URL or local path.
            is_remote (bool): Indicates if the source is remote or local.
            branch (str): The branch to use for remote repositories.
            commit_hash (str): Optional specific commit hash to check out.

        Returns:
            tuple: (bool, str, dict) indicating success status, message, and repository details.
        """
        if not repo_source:  # Check for empty path or URL
            return False, "Provided repository path is empty.", {}

        current_directory = Path(os.getcwd())

        if not is_remote:
            repo_source = str(Path(repo_source).resolve())

        # Step 1: Ensure the current directory is empty
        if any(current_directory.iterdir()):
            logger.warning(
                "Current working directory is not empty. Please use an empty directory.")
            return False, ("Current working directory is not empty. "
                           "Please use an empty directory."), {}

        logger.debug(
            "Repository setup. Repo: %s, Branch: %s, Commit: %s",
            repo_source, branch, commit_hash)

        # Step 2: Handle repository cloning based on whether it's remote or
        # local
        success, message, repo_details = self.validate_and_clone_repo(
            repo_source, branch, commit_hash, is_local=not is_remote
        )

        # Step 3: Handle errors during setup
        if not success:
            logger.error("Failed to set up repository: %s", message)
            return False, message, {}

        # Step 4: Return success and repository details
        logger.info("Repository setup completed successfully.")
        return True, "Repository successfully cloned.", repo_details

    def validate_and_clone_repo(
            self,
            repo_source: str,
            branch: str = "main",
            commit_hash: str = None,
            is_local: bool = False) -> tuple[bool, str, dict]:
        """
        Clones the repository and optionally checks out a specific branch and/or commit.

        Args:
            repo_source (str): The repository URL or local path.
            branch (str): The branch to clone (default: "main").
            commit_hash (str): Optional commit hash to check out.
            is_local (bool): Indicates if the source is local.

        Returns:
            tuple: (bool, str, dict) indicating success status, message, and repository details.
        """
        logger.debug(
            "Starting validation and cloning for %s with branch '%s' and commit '%s'.",
            repo_source,
            branch,
            commit_hash)

        current_directory = Path(os.getcwd())
        repo_name = self._extract_repo_name_from_url(
            repo_source) if not is_local else Path(repo_source).name

        try:
            # Clone the repository
            clone_source = repo_source if not is_local else str(
                Path(repo_source).resolve())
            repo = Repo.clone_from(
                clone_source,
                current_directory,
                branch=branch,
                single_branch=True
            )
            logger.debug("Successfully cloned branch '%s'.", branch)

            # Checkout the commit (delegated)
            if commit_hash:
                success, message = self._checkout_commit_after_clone(
                    repo, branch, commit_hash)
                if not success:
                    self._safe_cleanup(current_directory)
                    return False, message, {}

            latest_commit_hash = repo.head.commit.hexsha

            return True, "Repository successfully validated, cloned, and checked out.", {
                "repo_name": repo_name,
                "repo_source": repo_source,
                "branch": branch,
                "commit_hash": commit_hash or latest_commit_hash
            }

        except GitCommandError as e:
            logger.warning("An error occurred during cloning: %s", e)
            return False, "Failed to clone or validate repository. Invalid branch or commit.", {}

        except Exception as e:
            logger.error("Unexpected error during cloning: %s", e)
            return False, f"Unexpected error: {e}", {}

    def _checkout_commit_after_clone(
            self, repo: Repo, branch: str, commit_hash: str) -> tuple[bool, str]:
        """
        Handles checkout of a specific commit after cloning.

        Args:
            repo (Repo): The cloned repository object.
            branch (str): The branch to operate on.
            commit_hash (str): The commit hash to check out.

        Returns:
            tuple[bool, str]: Success status and a message.
        """
        try:
            # Ensure the branch exists and is checked out
            if branch not in repo.branches:
                ls_remote_output = repo.git.ls_remote(
                    "--heads", "origin", branch)
                if not ls_remote_output.strip():
                    return False, f"Branch '{branch}' does not exist locally or remotely."
                repo.git.fetch("origin", branch)
                repo.git.checkout("-b", branch, f"origin/{branch}")
            else:
                repo.git.checkout(branch)

            # Validate the commit
            if commit_hash not in [
                    commit.hexsha for commit in repo.iter_commits(branch)]:
                return False, f"Commit '{commit_hash}' does not exist on branch '{branch}'."

            # Checkout the commit
            repo.git.execute(["git", "reset", "--hard", commit_hash])
            return True, f"Checked out to commit '{commit_hash}' on branch '{branch}'."

        except GitCommandError as e:
            return False, f"Error during checkout: {e}"

    def is_valid_git_repo(self, repo_source: str) -> tuple[bool, bool, str]:
        """
        Checks if the given source is a valid Git repository (remote or local).

        Args:
            repo_source (str): The repository URL or local path.

        Returns:
            tuple[bool, bool, str]:
                - First bool: True if the repository is valid, False otherwise.
                - Second bool: True if the repository is remote, False if it is local.
                - str: Message describing the result.
        """
        # Check if the source is a local path

        try:
            local_path = Path(repo_source).resolve()
            if local_path.is_dir() and (local_path / ".git").is_dir():
                return True, False, "Local repository is valid."
        except Exception as e:
            logger.debug(e)

        # Check if the source is a valid remote repository
        try:
            subprocess.run(["git", "ls-remote", repo_source],
                           capture_output=True, check=True, text=True)
            return True, True, "Remote repository is valid."
        except subprocess.CalledProcessError:
            return False, False, f"Repository {repo_source} is invalid."
        except FileNotFoundError:
            # `git` is not installed or not in PATH
            return False, False, "Git is not installed or not available in the given repo file."
        except Exception as e:
            # Catch unexpected errors
            return False, False, f"Unexpected error occurred: {str(e)}"

    def _extract_repo_name_from_url(self, url: str) -> str:
        """
        Extracts the repository name from a URL.

        Args:
            url (str): The repository URL.

        Returns:
            str: The extracted repository name, or an empty string if invalid.
        """
        try:
            # Parse the URL
            parsed_url = urlparse(url)

            # Extract the path and handle any trailing or leading slashes
            repo_path = parsed_url.path.strip("/")
            logger.debug("Extracted path from URL: '%s'", repo_path)

            # Extract the base name of the repository
            repo_name = os.path.basename(repo_path)

            # Remove ".git" extension if present
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]

            # Log the extracted repo name
            logger.debug(
                "Final extracted repo name: '%s' from URL: '%s'",
                repo_name,
                url)

            return repo_name
        except Exception as e:
            logger.error("Failed to extract repo name from URL %s: %s", url, e)
            return ""

    def is_current_dir_repo(self) -> tuple[bool, bool, str | None]:
        """
        Checks if the current working directory is a Git repository and if it is at the root.

        Returns:
            tuple: (bool, str | None, bool) where:
                - bool: True if in a Git repository.
                - str | None: The repository name if in a Git repo, otherwise None.
                - bool: True if in the root directory of the Git repo, otherwise False.
        """
        try:
            repo = Repo(os.getcwd(), search_parent_directories=True)
            repo_name = os.path.basename(repo.working_tree_dir)

            # Check if the current directory is the root of the repository
            is_in_root = os.getcwd() == repo.working_tree_dir
            return True, is_in_root, repo_name
        except InvalidGitRepositoryError:
            return False, False, None

    def _safe_cleanup(self, path: Path) -> None:
        """
        Safely removes all contents of a directory without deleting the directory itself.

        Args:
            path (Path): The directory path to clean up.
        """
        for item in path.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            except Exception as e:
                logger.error("Failed to remove %s: %s", item, e)

    def get_current_repo_details(self, repo_path: Path = None) -> dict:
        """
        Retrieves details of the current or specified Git repository.

        Args:
            repo_path (Path, optional): Path to the repository.
            Defaults to the current working directory.

        Returns:
            dict: Repository details, or an empty dictionary if not a Git repository.
        """
        try:
            repo = Repo(
                repo_path or os.getcwd(),
                search_parent_directories=True)
            origin_url = next(
                iter(
                    repo.remote().urls),
                None) if repo.remotes else None
            branch = repo.active_branch.name
            commit_hash = repo.head.commit.hexsha
            repo_name = self._extract_repo_name_from_url(origin_url) if (
                origin_url) else Path(os.getcwd()).name

            return {
                "repo_url": origin_url or str(repo_path),
                "repo_name": repo_name,
                "branch": branch,
                "commit_hash": commit_hash,
            }
        except InvalidGitRepositoryError:
            logger.error(
                "Invalid Git repository at %s",
                repo_path or os.getcwd())
            return {}
        except Exception as e:
            logger.error("Error while retrieving repository details: %s", e)
            return {}

    def checkout_branch_and_commit(
            self, branch: str = None, commit_hash: str = None) -> tuple[bool, str]:
        """
        Checks out the current repository to the specified branch and commit.

        Args:
            branch (str): The branch to check out. If None, stays on the current branch.
            commit_hash (str): The commit hash to check out. If None, defaults to the latest commit.

        Returns:
            tuple: (bool, str)
                - bool: True if successful, False otherwise.
                - str: Message indicating the outcome.
        """
        repo = Repo(os.getcwd())

        # Check for dirty working directory
        if repo.is_dirty(untracked_files=True):
            return False, "Unstaged changes detected. Please commit or stash changes before proceeding."

        # Validate the commit first, before performing any branch-related
        # actions
        if commit_hash and branch:
            valid_commit = any(
                commit_hash == commit.hexsha for commit in repo.iter_commits(branch))
            if not valid_commit:
                return False, f"Invalid commit hash '{commit_hash}' for branch '{branch}'."

        # Handle branch checkout or validation
        if branch:
            success, message = self._handle_branch_checkout(repo, branch)
            if not success:
                return False, message

        # Handle commit checkout
        success, message = self._handle_commit_checkout(
            repo, branch, commit_hash)
        if not success:
            return False, message

        return True, (f"Repository successfully checked out to "
                      f"branch '{branch or repo.active_branch.name}' and "
                      f"commit '{commit_hash or repo.head.commit.hexsha}'.")

    def _handle_branch_checkout(
            self, repo: Repo, branch: str) -> tuple[bool, str]:
        """
        Validates and checks out the specified branch in the given repository.

        Args:
            repo (Repo): The Git repository object.
            branch (str): The branch to check out. Defaults to 'main'.

        Returns:
            tuple[bool, str]:
                - bool: True if the branch was successfully checked out, False otherwise.
                - str: A descriptive message about the result.
        """
        branch = branch or "main"  # Default to 'main'
        try:
            if branch not in repo.branches:
                # Check if the branch exists on the remote
                ls_remote_output = repo.git.ls_remote(
                    "--heads", "origin", branch)
                if not ls_remote_output.strip():
                    return False, f"Branch '{branch}' does not exist locally or remotely."

                # Fetch and create the branch locally
                repo.git.fetch("origin", branch)
                repo.git.checkout("-b", branch, f"origin/{branch}")
            else:
                # Checkout the branch locally if it exists
                repo.git.checkout(branch)
            return True, f"Checked out branch '{branch}'."
        except GitCommandError as e:
            return False, f"Error while checking out branch '{branch}': {e}"

    def _handle_commit_checkout(
            self, repo: Repo, branch: str, commit_hash: str) -> tuple[bool, str]:
        """
        Validates and checks out the specified commit in the given repository.

        Args:
            repo (Repo): The Git repository object.
            branch (str): The branch to operate on. Defaults to 'main'.
            commit_hash (str): The commit hash to check out. Defaults to the latest commit on the branch.

        Returns:
            tuple[bool, str]:
                - bool: True if the commit was successfully checked out, False otherwise.
                - str: A descriptive message about the result.

        Behavior:
            - Checks out the specified branch.
            - If no commit is provided, defaults to the latest commit on the branch.
            - Resets the branch to the specified commit hash.
        """
        branch = branch or "main"  # Default to 'main'
        try:
            # Ensure the branch is checked out first
            if branch not in repo.branches:
                # Create the branch from the commit hash if it doesn't exist
                if not commit_hash:
                    # Fetch the latest commit on the remote branch
                    remote_refs = repo.git.ls_remote(
                        "--heads", "origin", branch)
                    if not remote_refs.strip():
                        return False, f"Branch '{branch}' does not exist remotely."
                    # First column is the commit hash
                    commit_hash = remote_refs.split("\t")[0]
                repo.git.checkout("-b", branch, commit_hash)
            else:
                # Checkout the existing branch
                repo.git.checkout(branch)

                # If no commit_hash is provided, default to the latest commit
                if not commit_hash:
                    repo.git.pull("origin", branch)
                    commit_hash = repo.head.commit.hexsha

                # Reset the branch to the specified commit hash
                repo.git.execute(["git", "reset", "--hard", commit_hash])

            # Ensure the HEAD is now attached to the branch
            repo.git.checkout(branch)
            return True, f"Checked out to commit '{commit_hash}' on branch '{branch}'."
        except GitCommandError as e:
            return False, f"Error while checking out commit: {e}"
