"""
This module provides functionality to manage Git repositories. 
"""
import os
import yaml
import git
from git import Repo
from util.common_utils import get_logger

logger = get_logger(logger_name='util.repo_manager')

class RepoManager:
    """
    Manages cloning, authentication, and retrieving YAML configurations.
    """

    def __init__(self, repo_source: str, target_path: str = None, branch: str = "main"):
        """
        Initializes the RepoManager class.

        Args:
            repo_source (str): the remote / local repo URL that needs to be cloned.
            target_path (str): the directory where the repo will be stored.
            branch (str): The branch to work on.
        """
        self.repo_source = repo_source
        self.target_path = target_path
        self.branch = branch
        self.yaml_path = None
    def is_remote_repo(self):
        """
        Checks if the repository is a remote repository.
        """
        return self.repo_source.startswith("https://")

    def verify_target_path(self):
        """
        Verifies the target path. If the directory does not exist, it raises an error and exits.
        """
        if not os.path.exists(self.target_path):
            logger.error("Target directory %s does not exist. Try another one.", self.target_path)
            raise FileNotFoundError("Target directory not exist.")
        logger.debug("Target directory %s is valid. Proceeding...", self.target_path)

    def setup_repo(self):
        """
        Clones the repository from the remote URL or verifies the local repository.
        """
        self.verify_target_path()
        if self.is_remote_repo():
            logger.info("Cloning remote repository %s into %s", self.repo_source,
                                self.target_path)
            try:
                Repo.clone_from(self.repo_source, self.target_path, branch=self.branch)
                logger.info("Successfully cloned repository %s into %s", self.repo_source,
                                    self.target_path)
            except (git.exc.GitCommandError, git.exc.NoSuchPathError,
                    git.exc.InvalidGitRepositoryError, PermissionError) as e:
                logger.error("Failed to clone repository: %s. Error: %s", self.repo_source, e)
                raise

        else:
            if not os.path.exists(self.target_path):
                logger.error("Local directory %s does not exist", self.target_path)
                raise FileNotFoundError(f"Local directory {self.target_path} not found.")

    def get_yaml_path(self, file_name: str = "pipelines.yml") -> None:
        """
        Searches for the given file name in the '.cicd-pipelines' directory 
        and sets the absolute path of the YAML file.
        """
        cicd_dir = os.path.join(self.target_path, ".cicd-pipelines")
        # Check if the directory exists
        if not os.path.isdir(cicd_dir):
            logger.error("Directory '.cicd-pipelines' not found in the repository, please create the directory and place your config file inside it.")
            return
        # Search for the YAML file
        self.yaml_path = None
        for root, _, files in os.walk(cicd_dir):
            for file in files:
                if file == file_name:
                    self.yaml_path = os.path.join(root, file)
                    break
            if self.yaml_path:
                break
        if self.yaml_path is None:
            logger.error(
                "File '%s' not found in the '.cicd-pipelines' directory. "
                "Please create a pipelines.yml inside the directory.")

    def parse_yaml(self) -> dict:
        """
        Parses the YAML file into a dictionary.
        """
        try:
            with open(self.yaml_path, 'r', encoding='utf-8') as file:
                logger.info("Parsing YAML file at %s", self.yaml_path)
                return yaml.safe_load(file)
        except Exception as e:
            logger.error("Failed to parse YAML file at %s. Error: %s", self.yaml_path, e)
            raise
