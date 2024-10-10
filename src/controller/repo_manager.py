"""
This module provides functionality to manage Git repositories.
"""
import os
import logging
import yaml
import git
from git import Repo
from util.common_utils import get_logger

logger = get_logger(logger_name='RepoManager', log_level=logging.INFO,
                    log_file='repo_manager.log')

class RepoManager:
    """
    Manages cloning, authentication, and retrieving YAML configurations.
    """

    def __init__(self, repo_url: str, local_dir: str = None, branch: str = "main"):
        """
        Initializes the RepoManager class.

        Args:
            repo_url (str): URL of the remote repository.
            local_dir (str): the local directory where the repository will be cloned, 
            defaults to the repository name and is created in the current working directory.
            branch (str): The branch to work on.
        """
        self.repo_url = repo_url
        self.local_dir = local_dir if local_dir else repo_url.split("/")[-1]
        self.branch = branch
        self.yaml_path = None
    def is_remote_repo(self):
        """
        Checks if the repository is a remote repository.
        """
        return self.repo_url.startswith("https://")

    def verify_local_dir(self):
        """
        Verifies if the local directory exists and is writable.
        """
        if not os.path.exists(self.local_dir):
            logger.info("Local directory %s does not exist. Attempting to create it.",
                             self.local_dir)
            try:
                os.makedirs(self.local_dir)
                logger.info("Successfully created local directory: %s", self.local_dir)
            except PermissionError:
                logger.error("Permission denied to create directory: %s", self.local_dir)
            except OSError as e:
                logger.error("Failed to create directory: %s. Error: %s", self.local_dir, e)
        elif not os.access(self.local_dir, os.W_OK):
            logger.error("Local directory %s is not writable", self.local_dir)
    def setup_repo(self):
        """
        Clones the repository from the remote URL or verifies the local repository.
        """
        if self.is_remote_repo():
            self.verify_local_dir()
            if not os.path.exists(self.local_dir):
                logger.info("Cloning remote repository %s into %s", self.repo_url,
                                 self.local_dir)
                try:
                    Repo.clone_from(self.repo_url, self.local_dir, branch=self.branch)
                    logger.info("Successfully cloned repository %s into %s", self.repo_url,
                                     self.local_dir)
                except (git.exc.GitCommandError, git.exc.NoSuchPathError,
                        git.exc.InvalidGitRepositoryError, PermissionError) as e:
                    logger.error("Failed to clone repository: %s. Error: %s", self.repo_url, e)
                    raise
            else:
                logger.info("Repository already exists.")
        else:
            if not os.path.exists(self.local_dir):
                logger.error("Local directory %s does not exist", self.local_dir)
                raise FileNotFoundError(f"Local directory {self.local_dir} not found.")

    def get_yaml_path(self, yaml_file_path: str = None) -> None:
        """
        Locates the YAML file in the local repository or uses the provided file path.

        Args:
            yaml_file_path (str): Optional path to the specific YAML file.
        """
        if yaml_file_path:
            self.yaml_path = yaml_file_path
        else:
            # Auto-discover the first YAML file in the repo if no path is provided
            self.yaml_path = None
            for root, _, files in os.walk(self.local_dir):
                for file in files:
                    if file.endswith(".yaml") or file.endswith(".yml"):
                        self.yaml_path = os.path.join(root, file)
                        break
                if self.yaml_path:
                    break

        if self.yaml_path is None:
            logger.error("No YAML file found in the repository.")

    def parse_yaml(self) -> dict:
        """
        Parses the YAML file located at self.yaml_path into a dictionary.

        Returns:
            dict: Parsed contents of the YAML file.
        """
        if not self.yaml_path:
            logger.error("YAML file path is not set")
            return {}
        try:
            with open(self.yaml_path, 'r', encoding='utf-8') as file:
                logger.info("Parsing YAML file at %s", self.yaml_path)
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error("YAML file not found: %s", self.yaml_path)
            return {}
        except yaml.YAMLError as error:
            logger.error("Error parsing YAML file: %s", error)
            return {}
