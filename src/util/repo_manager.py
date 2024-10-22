"""
Manages Git repositories and parses YAML files.

For remote repositories, both the source URL and target path are required.
For local repositories, the target path defaults to the source path.
All paths must be absolute. The branch defaults to 'main' but can be changed as needed.
"""

from pathlib import Path
import os
from typing import List, Optional
from urllib.parse import urlparse
import yaml
import git
from git import Repo
from util.common_utils import get_logger

logger = get_logger(logger_name='util.repo_manager')

class RepoManager:
    """
    Usage:
    1. Call `setup_repo()` to clone a remote repo or set up a local repo.
    2. Use `parse_yaml_dict()` to retrieve a dictionary of all YAML files in the repo.
    3. Use `parse_yaml(file_name)` to parse a specific YAML file by providing its file name.
    """

    def __init__(self, repo_source: str, target_path: str = None, branch: str = "main"):
        """Initializes the RepoManager class.

        Args:
            repo_source (str): the remote URL that needs to be cloned or the local directory path.
            target_path (str): The absolute path where the repo will be stored. 
                       Example:
                           - Remote repo: 
                               repo_source="https://github.com/repo_test", 
                               target_path="/Users/test/Downloads" 
                               The repo will be cloned into '/Users/test/Downloads/repo_test').
                           - Local repo: 
                               repo_source="/Users/test/repo_test"
                               (If target_path is not provided, the repo_source path will be used).
            branch (str): The branch to work on.
        """
        self.repo_source = repo_source
        self.target_path = repo_source if not self._is_remote_repo() else target_path
        self.branch = branch
    def _is_remote_repo(self) -> bool:
        """Helper method to check if the repo is a remote repo.

        Returns:
            bool: True if the repo is a remote repo, False otherwise.
        """
        return self.repo_source.startswith("https://")
    def _extract_repo_name_from_url(self, url: str) -> str:
        """Helper method to extract the repo name from the remote URL.
        
            Args:
                url (str): The remote repo URL.

            Returns:
                str: The name of the repo.
        """
        parsed_url = urlparse(url)
        repo_name = os.path.basename(parsed_url.path)
        # Strip the `.git` extension if it exists
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        return repo_name
    def _verify_target_path(self):
        """Helper method to verify the target path. Only used for local repositories.

        Raises:
            FileNotFoundError: If the target directory does not exist.
        """
        if not os.path.exists(self.target_path):
            logger.error("Target directory %s does not exist. Try another one.", self.target_path)
            raise FileNotFoundError("Target directory not exist.")
        logger.debug("Target directory %s is valid. Proceeding...", self.target_path)

    def _get_unique_path(self, path: str) -> Path:
        """Helper method to generates a unique path by appending _1, _2, _3, etc., 
        if the path exists.

        Args:
            path (str): The original file or directory path.

        Returns:
            Path: A unique `Path` object with a numeric suffix if the path already exists.
        """
        target_path = Path(path)
        base_path = target_path.stem
        parent_dir = target_path.parent
        counter = 1
        while target_path.exists() and any(target_path.iterdir()):
            # Append the counter to the original base name
            target_path = parent_dir / f"{base_path}_{counter}"
            counter += 1
        return target_path

    def setup_repo(self):
        """Sets up the repo by cloning the remote repo or verifying the target path for local repo.

        - For remote repos:
        - If the target path is a directory, a subdirectory named after the repo will be created.
        - If the target path does not exist, it will be automatically created.

        - For local repos:
        - It checks if the target path exists.
        - If the target path does not exist, a FileNotFoundError is raised.

        Raises:
            git.GitError: If there is an error with the Git command during cloning.
            PermissionError: If there is no permission to access the target path.
            FileNotFoundError: If the target path for a local repo does not exist.
        """
        if self._is_remote_repo():
            if os.path.isdir(self.target_path):
                repo_name = self._extract_repo_name_from_url(self.repo_source)
                self.target_path = os.path.join(self.target_path, repo_name)
                self.target_path = str(self._get_unique_path(self.target_path))
            elif not os.path.exists(self.target_path):
                os.makedirs(self.target_path)
            logger.info("Cloning remote repo %s into %s", self.repo_source, self.target_path)
            try:
                Repo.clone_from(self.repo_source, self.target_path, branch=self.branch)
                logger.info("Successfully cloned repo %s into %s", self.repo_source,
                                    self.target_path)
            except (git.GitError, PermissionError) as e:
                logger.error("Failed to clone repo: %s. Error: %s", self.repo_source, e)
                raise e
        else:
            self._verify_target_path()

    def get_config_hash(self, config_file: str) -> str:
        """[To Be Completed] get configuration file hash given the configuration file path

        Args:
            config_file (str): _description_

        Returns:
            str: _description_
        """
        #check the current hash file of the sha config

        #absolute_path = self._get_yaml_path(config_file)
        #print("repo_manager | the config_file = : ", absolute_path)
        return f"sha256 - {config_file}"
