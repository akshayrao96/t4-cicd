"""
    A class for managing code repositories, focusing on validating repository states,
    cloning repositories, handling branch and commit checkouts.
"""

from pathlib import Path
import os
from urllib.parse import urlparse
import subprocess
import shutil
from git import Repo, GitCommandError, InvalidGitRepositoryError
from util.common_utils import get_logger
import util.constant as c

logger = get_logger(logger_name='util.repo_manager')


class RepoManager:
    """
        Utility class for managing Git repositories.

        This class handles interactions with Git repositories, supporting operations
        such as cloning, fetching, checking out branches, and resetting to specific commits.
        It uses GitPython library for handling such features.

        Use cases include:
        - Validating the current directory as a Git repository.
        - Retrieving repository details such as branch and commit hash.
        - Checking out branches or specific commits.
        - Handling remote branches and commits during repository setup or updates.
    """

    def set_repo(
            self,
            repo_source: str,
            is_remote: bool,
            branch: str = c.DEFAULT_BRANCH,
            commit_hash: str = None) -> tuple[bool, str, dict]:
        """
        Validates the repository URL given, clones it, and returns repository details.

        Args:
            repo_source (str): The repository URL or local path.
            is_remote (bool): Indicates if the source is remote or local.
            branch (str): The branch to be cloned for the repository. Defaults to main.
            commit_hash (str): The commit to be cloned for the repository. Defaults to latest commit

        Returns:
            tuple: (bool, str, dict) indicating success status, message, and repository details.
        """

        # Checks for empty path or URL
        if not repo_source:
            return False, "Provided repository path is empty.", {}

        current_directory = Path(os.getcwd())

        if not is_remote:
            repo_source = str(Path(repo_source).resolve())

        # Ensure the current directory is empty for cloning
        # Else, return error message
        if any(current_directory.iterdir()):
            logger.warning(
                "Current working directory is not empty. Please use an empty directory.")
            return False, ("Current working directory is not empty. "
                           "Please use an empty directory."), {}

        logger.debug(
            "Repository setup. Repo: %s, Branch: %s, Commit: %s",
            repo_source, branch, commit_hash)

        # Handle repository cloning using helper method
        success, message, repo_details = self.validate_and_clone_repo(
            repo_source, branch, commit_hash, is_local=not is_remote
        )

        # Case for when clone is not successful
        if not success:
            logger.error("Failed to set up repository: %s", message)
            return False, message, {}

        # Case for successful clone. Return success and repository details
        logger.info("Repository setup completed successfully.")
        return True, "Repository successfully cloned.", repo_details

    def validate_and_clone_repo(
            self,
            repo_source: str,
            branch: str = c.DEFAULT_BRANCH,
            commit_hash: str = None,
            is_local: bool = False) -> tuple[bool, str, dict]:
        """
        Clones the repository and checks out a specific branch and/or commit from given
        args.

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

        # Get repo name using helper method, based on local or remote
        repo_name = self._extract_repo_name_from_url(
            repo_source) if not is_local else Path(repo_source).name

        # Logic for cloning repository
        try:
            clone_source = repo_source if not is_local else str(
                Path(repo_source).resolve())
            repo = Repo.clone_from(
                clone_source,
                current_directory,
                branch=branch,
                single_branch=True
            )
            logger.debug("Successfully cloned branch '%s'.", branch)

            # Checkout the commit if valid, latest commit if commit not given
            if commit_hash:
                success, message = self._checkout_commit_after_clone(
                    repo, branch, commit_hash)
                if not success:
                    self._safe_cleanup(current_directory)
                    return False, message, {}

            latest_commit_hash = repo.head.commit.hexsha

            # Case where clone is successful. Return metadata of the cloned
            # repository
            return True, "Repository successfully validated, cloned, and checked out.", {
                "repo_name": repo_name,
                "repo_source": repo_source,
                "branch": branch,
                "commit_hash": commit_hash or latest_commit_hash
            }

        # Exceptions when cloning, not due to invalid branch or commit
        # Likely due to GitPython library error, or network error
        except GitCommandError as e:
            logger.warning("An error occurred during cloning: %s", e)
            return False, "Failed to clone or validate repository. Invalid branch or commit.", {}

        except Exception as e:
            logger.error("Unexpected error during cloning: %s", e)
            return False, f"Unexpected error: {e}", {}

    def _checkout_commit_after_clone(
            self, repo: Repo, branch: str, commit_hash: str) -> tuple[bool, str]:
        """
        Helper method to handles checkout of a specific commit after cloning.

        Args:
            repo (Repo): The cloned repository object.
            branch (str): The branch to operate on.
            commit_hash (str): The commit hash to check out.

        Returns:
            tuple[bool, str]: Success status and a message.
        """

        # Ensure the branch exists first, then check for valid commit
        try:
            if branch not in repo.branches:
                ls_remote_output = repo.git.ls_remote(
                    "--heads", "origin", branch)
                if not ls_remote_output.strip():
                    return False, f"Branch '{branch}' does not exist remotely."

                repo.git.fetch(
                    f"origin refs/heads/{branch}:refs/remotes/origin/{branch}")
                repo.git.checkout("-b", branch, f"origin/{branch}")
            else:
                repo.git.checkout(branch)

            # Validate the commit hash exists on the branch
            commit_hashes = [
                commit.hexsha for commit in repo.iter_commits(branch)]
            if commit_hash not in commit_hashes:
                return False, f"Commit '{commit_hash}' does not exist on branch '{branch}'."

            # Reset the branch to the specified commit, if branch is not
            # up to date with the remote tracking version of the branch
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

        # Check if the source is a local path, then check if given
        # repo source is a valid git repository
        try:
            local_path = Path(repo_source).resolve()
            if local_path.is_dir() and (local_path / ".git").is_dir():
                return True, False, "Local repository is valid."
        except Exception as e:
            logger.debug(e)

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
        Extracts the repository name from the given repo url

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
        Checks if the current working directory is a Git repository and if it is at
        the root of the repisitory.

        Returns:
            tuple: (bool, str | None, bool) where:
                - bool: True if in a Git repository.
                - str | None: The repository name if in a Git repo, otherwise None.
                - bool: True if in the root directory of the Git repo, otherwise False.
        """
        try:
            repo = Repo(os.getcwd(), search_parent_directories=True)
            repo_name = os.path.basename(repo.working_tree_dir)
            is_in_root = os.getcwd() == repo.working_tree_dir
            return True, is_in_root, repo_name
        except InvalidGitRepositoryError:
            return False, False, None

    def _safe_cleanup(self, path: Path) -> None:
        """
        Safely removes all contents of a directory without deleting the directory itself.
        This is used for cases where a valid branch has been cloned, but the commit
        given is not valid.

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

        branch = branch or repo.active_branch.name

        # Check for unstaged changes from the user. Prompt return message, that
        # checkout can only be executed once changes have been staged
        if repo.is_dirty(untracked_files=True):
            return False, ("Unstaged changes detected. "
                           "Please commit or stash changes before proceeding.")

        # Handle branch checkout. For checkout cases, handling of remote tracking (local view)
        # remote view, and full remote branches. Hence, method needs to be seperated from checkouts
        # after cloning
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
        try:
            # Check if the branch exists locally
            if branch in repo.branches:
                repo.git.checkout(branch)  # Checkout local branch
                return True, f"Checked out branch '{branch}' locally."

            # Check if the branch exists remotely
            remote_refs = repo.git.ls_remote("--heads", "origin", branch)
            if not remote_refs.strip():
                return False, f"Branch '{branch}' does not exist remotely."

            # Extract the ref path and fetch the branch explicitly
            ref_path = f"refs/heads/{branch}"
            repo.git.fetch(
                "origin",
                f"{ref_path}:refs/remotes/origin/{branch}")

            # Create a local branch from the fetched remote branch
            repo.git.checkout("-b", branch, f"origin/{branch}")
            return True, f"Fetched and checked out branch '{branch}' from remote."

        except GitCommandError as e:
            return False, f"Error while checking out branch '{branch}': {e}"

    def _handle_commit_checkout(
            self, repo: Repo, branch: str, commit_hash: str) -> tuple[bool, str]:
        """
        Validates and checks out the specified commit on the given branch.
        Defaults to the latest commit if `commit_hash` is None.

        Args:
            repo (Repo): The Git repository object.
            branch (str): The branch to operate on.
            commit_hash (str): The commit hash to check out.

        Returns:
            tuple[bool, str]: Success status and a descriptive message.
        """
        try:
            # Default to the latest commit if commit_hash is None
            # previous operation should guarantee branch will exist.
            if not commit_hash:
                commit_hash = repo.head.commit.hexsha
                logger.debug(commit_hash)
            elif not repo.head.commit.hexsha.startswith(commit_hash):
                # Only checkout specific commit if it is not equal to head.
                # Ensure the commit exists on the branch
                # repo.commit()
                try:
                    repo.commit(commit_hash)
                except GitCommandError as e:
                    return False, f"Commit '{commit_hash}' does not exist on local branch '{branch}'."
                # commit_hashes = [
                #     commit.hexsha for commit in repo.iter_commits(branch)]
                # if commit_hash not in commit_hashes:
                #     return False, f"Commit '{commit_hash}' does not exist on local branch '{branch}'."
                # Checkout the specified commit in detached stage
                repo.git.checkout(commit_hash)
            return True, f"Checked out to commit '{commit_hash}' on branch '{branch}'."
        except GitCommandError as e:
            return False, f"Error during checkout: {e}"
