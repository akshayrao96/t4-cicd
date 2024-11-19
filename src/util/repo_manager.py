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
        Clones the repository and checks out a specific branch and/or commit if valid

        Args:
            repo_source (str): The repository URL or local path.
            branch (str): The branch to clone or validate (default is "main").
            commit_hash (str): Optional specific commit hash to validate.
            is_local (bool): Indicates if the source is a local repository.

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
            # For local repositories, use the local path as the "URL" for
            # cloning
            clone_source = repo_source if not is_local else str(
                Path(repo_source).resolve())

            # Clone the repository contents directly into the current working
            # directory
            repo = Repo.clone_from(
                clone_source,
                current_directory,
                branch=branch,
                single_branch=True
            )
            latest_commit_hash = repo.head.commit.hexsha
            logger.debug(
                "Successfully cloned branch '%s' with latest commit %s.",
                branch,
                latest_commit_hash)

            # If a specific commit hash is provided, check out that commit
            if commit_hash:
                success, message = self._checkout_commit(
                    repo, branch, commit_hash)
                if not success:
                    self._safe_cleanup(current_directory)
                    return False, message, {}

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

    def _checkout_commit(
            self,
            repo: Repo,
            branch: str,
            commit_hash: str) -> tuple[bool, str]:
        """
        Checks out a specific commit on a branch.

        Args:
            repo (Repo): The cloned repository object.
            branch (str): The branch to check out.
            commit_hash (str): The commit hash to check out.

        Returns:
            tuple: (bool, str) indicating success status and a message.
        """
        try:
            if any(
                    commit_hash == commit.hexsha for commit in repo.iter_commits(branch)):
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
        except Exception as e:
            logger.error("Error during commit checkout: %s", e)
            return False, f"Error during commit checkout: {e}"

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
            repo_name = self._extract_repo_name_from_url(
                origin_url) if origin_url else repo_path.name

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
            branch (str): The branch to check out. If None, stay on the current branch.
            commit_hash (str): The commit hash to check out. If None, defaults to latest commit.

        Returns:
            tuple: (bool, str)
                - bool: True if successful, False otherwise.
                - str: Message indicating the outcome.
        """
        # Ensure at least a branch or commit is provided
        if not branch and not commit_hash:
            return False, "Branch or commit must be provided to check out."

        try:
            # Validate that the current directory is a valid Git repository
            repo = Repo(os.getcwd())
        except InvalidGitRepositoryError:
            return False, "Current directory is not a valid Git repository."
        except Exception as e:
            return False, f"Unexpected error: {e}"

        # Fetch all remote branches to ensure up-to-date information
        try:
            repo.remotes.origin.fetch()
        except GitCommandError as e:
            return False, "Failed to fetch remote branches. Ensure the remote is accessible."

        # Handle branch validation and checkout
        if branch:
            try:
                if branch not in repo.branches:
                    # Check if the branch exists on the remote
                    ls_remote_output = repo.git.ls_remote("--heads", "origin", branch)
                    if not ls_remote_output.strip():
                        return False, f"Branch '{branch}' does not exist locally or remotely."

                    # Preserve the original commit_hash if provided
                    if not commit_hash:
                        commit_hash = ls_remote_output.split()[0]

                    # Explicitly fetch the branch
                    try:
                        repo.git.fetch("origin", branch)
                    except GitCommandError as fetch_error:
                        return False, f"Failed to fetch branch '{branch}': {fetch_error}"

                    # Create the local branch to match the remote
                    remote_branch = f"origin/{branch}"
                    if remote_branch not in repo.refs:
                        repo.git.checkout("-b", branch, commit_hash)
                    else:
                        repo.git.checkout("-b", branch, remote_branch)
                else:
                    # If branch exists locally, check it out
                    repo.git.checkout(branch)
            except GitCommandError as e:
                return False, f"Error while checking out branch '{branch}': {e}"

        # Handle commit validation and checkout
        if commit_hash:
            try:
                # Ensure the commit exists if no branch is provided
                if not branch and not any(commit_hash == commit.hexsha for commit in repo.iter_commits()):
                    return False, f"Commit '{commit_hash}' does not exist in the current repository."

                # Use the helper function to validate and checkout the commit
                success, message = self._checkout_commit(
                    repo, branch or repo.active_branch.name, commit_hash)
                if not success:
                    return False, message
            except GitCommandError as e:
                return False, f"Error while checking out commit '{commit_hash}': {e}"
        elif not commit_hash:
            # Ensure branch is up-to-date if no specific commit is provided
            try:
                repo.git.pull("origin", branch)
            except GitCommandError as e:
                return False, f"Error pulling latest changes for branch '{branch}': {e}"

        return True, f"Git repository successfully checked out to branch '{branch}' and commit '{commit_hash or repo.head.commit.hexsha}'."
