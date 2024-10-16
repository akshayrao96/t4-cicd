"""This is Controller class that integrates the CLI with the other class components
    such as DataStore, Docker, Config file validation (ConfigChecker), and
    other related class.
"""

# import os
import click
from util.common_utils import (get_logger)
from util.repo_manager import (RepoManager)
from util.db_mongo import (MongoAdapter)
from util.config_tools import (ConfigChecker)

#os.path.dirname(os.path.abspath(__file__)) #get current directory of this file

REPO_SOURCE = ""
REPO_TARGET_PATH = ""
REPO_BRANCH_NAME = "main"
# pylint: disable=fixme

class Controller:
    """Controller class that integrates the CLI with the other class components"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern: ensure only one instance exists."""
        if not cls._instance:
            cls._instance = super(Controller, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize the controller class
        """
        if hasattr(self, '_initialized'):
            return

        # init Docker
        # init RepoManager
        self.repo_manager = RepoManager(REPO_SOURCE)
        self.mongo_ds = MongoAdapter() # init DataStore (MongoDB, Postgres)
        self.config_checker = ConfigChecker() #init Configuration Checker
        # ..and many more
        self.logger = get_logger('cli.controller')
        self._initialized = True # prevent reinitialization

    ### REPOSITORY (REPO) ###
    def set_repo(self, repo_source:str) -> tuple[bool, str]:
        """_summary_

        Args:
            repo_source (str): _description_

        Returns:
            tuple[bool, str]: true if repository initialization successful and the message output
        """
        self.repo = repo_source
        self.repo_manager = RepoManager(self.repo)
        click.echo(self.repo)
        # Try extract all yaml files and validate it

    def _is_valid_repo(self, repo_source:str) -> bool:
        """private function to check if the repository path specified is a valid repository

        Args:
            repo_source (str): _description_

        Returns:
            bool: _description_
        """

    def get_repo(self) -> str:
        """_summary_

        Returns:
            bool: _description_ #check if bool is the right type to return
        """
        print(self.repo)
        return self.repo

    def get_controller_history(self) -> dict:
        """Retrieve pipeline history from Mongo DB

        Returns:
            dict: return list of pipeline_id of pipeline history commit
        """
        #TODO: need to configure mongodb local before this can be run
        #pipelines = self.mongo_ds.get_controller_history()
        #self.logger.debug("history of the pipelines: %s", str(pipelines))

        #TODO: add validation / conditional checking for returned value
        #TODO: determine if simply return <dict> or have some logic

        #return pipelines

    ### CONFIG ###
    def validate_config(self, file_name:str) -> tuple[bool, str, dict]:
        """_summary_
        command: validate configuration file `cid config validate`

        Args:
            file_name (str): _description_

        Returns:
            tuple[bool, str, dict]: status of the config validation and output message
        """

        pipeline_config = {}
        #parse the config yaml file given the file_name that the user specified, or
        #by default "pipelines.yml". Next, call the Repo Manager function that will
        #return the configuration in dictionary form (parsed with key-value pair structure)
        # assuming it is inside the .cicd-pipelines folder
        pipeline_config = self.repo_manager.parse_yaml(file_name)

        #get the pipeline_name for ConfigChecker
        pipeline_name = pipeline_config.get('global.pipeline_name')

        #call ConfigChecker to validate the configuration
        #returns: dict <valid, error_msg, pipeline_config
        response_dict = self.config_checker.validate_config(pipeline_name, pipeline_config)

        #store the response to variables
        status = response_dict.get('valid')
        error_msg = response_dict.get('error_msg')
        resp_pipeline_config = response_dict.get('pipeline_config')

        return (status, error_msg, resp_pipeline_config)

    ### PIPELINE ###
    def setup_pipeline(self):
        """ setup pipeline when is called for the first time.
        command: `cid pipeline setup`
        """

    def run_pipeline(self, **kwargs) -> tuple:
        """Executes the job by coordinating the repository, runner, artifact store, and logger.

        Returns:
            tuple: _description_
        """
        ### Pseudocode
        # # Step 0: Clone the repo
        # gitrepo = RepoManager()
        # gitrepo.cloneRepo(kwargs)
        # # Step 1: Initialize pipeline record
        # mongoadapter = MongoAdapter()
        # mongoadapter.insert_pipeline(dict)
        # # Step 2: Run the job in a Docker container
        # job_runner = DockerInterface()
        # job_id, job_status = self.job_runner.run_job(job_script)
        # self.logger.log_job_state(job_id, job_status)
        # # Step 3: Store the generated artifact
        # mysql = MySQLAdapter()
        # mysql.store(artifact)
        # # Step 4: Log job completion / failure status
        # # ...

        # create mockup data that simulate when the pipeline runs and return
        # the output to user CLI in tuple
        status = True
        message = "Pipeline runs successfully"
        pipeline_id = "pid_unique_string"

        ## This is example how to call RepoManager util class from controller
        #self.repo_manager.setup_repo()
        #self.logger.debug("is_remote_repo: %s", remote_repo)

        return tuple([status,message,pipeline_id])

    def _start_job(self):
        """_summary_
        """


    def stop_job(self):
        """_summary_
        """


    def display_or_edit_config(self):
        """_summary_
        """


    def list_configuration(self):
        """_summary_
        """
