""" All related Controller
"""

from util.common_utils import (get_logger)
from util.repo_manager import (RepoManager)

SET_LOCAL_PATH = '/Users/jason.gautama/Documents/code/GitHub/CS6510-SEA-F24/t4-cicd'

class Controller:
    """This is class controller
    """
    def __init__(self):
        self.logger = get_logger('cli.controller')
        self.repo_manager = RepoManager('', SET_LOCAL_PATH)


    def run_pipeline(self, **kwargs) -> tuple:
        """
        Executes the job by coordinating the repository, runner, artifact store, and logger.
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

    def set_repo(self, repo_url:str) -> bool:
        """
        User provides repository url to initialize

        Args:
            repo_url (str): remote repository url (starts with https://)

        Returns:
            bool: true if repoisotry initialization successful
        """


    def setup_pipeline(self):
        """
        setup pipeline when `cid pipeline setup` is called for the first time.
        """

    def start_job(self):
        pass

    def stop_job(self):
        pass

    def display_or_edit_config(self):
        pass

    def list_configuration(self):
        pass
