"""This is Controller class that integrates the CLI with the other class components
    such as DataStore, Docker, Config file validation (ConfigChecker), and
    other related class.
"""


from datetime import datetime
import os
import click
import git.exc
import util.constant as const
from util.common_utils import (get_logger)
from util.repo_manager import (RepoManager)
from util.db_mongo import (MongoAdapter)
from util.yaml_parser import YamlParser
from util.config_tools import (ConfigChecker)

REPO_SOURCE = ""
REPO_TARGET_PATH = ""
REPO_BRANCH_NAME = "main"
# pylint: disable=fixme


class Controller:
    """Controller class that integrates the CLI with the other class components"""

    def __init__(self):
        """Initialize the controller class
        """
        # init Docker
        # init RepoManager
        self.repo_manager = RepoManager(REPO_SOURCE)
        self.mongo_ds = MongoAdapter()  # init DataStore (MongoDB, Postgres)
        self.config_checker = ConfigChecker()  # init Configuration Checker
        # ..and many more
        self.logger = get_logger('cli.controller')
        self._initialized = True  # prevent reinitialization

    ### REPOSITORY (REPO) ###
    def set_repo(self, repo_url: str) -> tuple[bool, str]:
        """Set the repository URL, validate it, and store in MongoDB.

        Args:
            repo_url (str): The repository URL provided by the user.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """

        mongo = MongoAdapter()

        if not self._is_valid_repo(repo_url):
            return False, "The provided URL is not a valid URL or a valid Git repository."

        repo_name = self.repo_manager._extract_repo_name_from_url(repo_url)

        # can use main branch for now, can later extract branch from
        # repoManager
        branch = "main"

        now = datetime.now()
        time_log = now.strftime("%Y-%m-%d %H:%M:%S")

        repo_data = {
            "repo-url": repo_url,
            "repo-name": repo_name,
            "branch": branch,
            "time": time_log
        }

        inserted_id = mongo.insert_repo(repo_data)
        if inserted_id:
            return True, f"Repository set successfully with ID: {inserted_id}"
        else:
            return False, "Failed to set repository."

    def _is_valid_repo(self, repo_source: str) -> bool:
        """private function to check if the repository path specified is a valid repository

        Args:
            repo_source (str): _description_

        Returns:
            bool: _description_
        """
        return self.repo_manager._is_remote_repo_valid(repo_source)

    def get_repo(self) -> str:
        """Check if the current directory is a Git repository.

        Returns:
            str: Repository's name if current working directory is a Git repo, None otherwise.
        """
        mongo = MongoAdapter()
        try:
            repo = git.Repo(os.getcwd(), search_parent_directories=True)
            repo_name = os.path.basename(repo.working_tree_dir)
            return repo_name
        except git.exc.InvalidGitRepositoryError:
            self.logger.info(
                "Not in a git repository, fetching last set repo from MongoDB.")
            last_repo = mongo.get_last_set_repo()
            if last_repo:
                return last_repo.get('repo-url', '')
            else:
                return ""

    def get_controller_history(self) -> dict:
        """Retrieve pipeline history from Mongo DB

        Returns:
            dict: return list of pipeline_id of pipeline history commit
        """
        # TODO: need to configure mongodb local before this can be run
        # pipelines = self.mongo_ds.get_controller_history()
        # self.logger.debug("history of the pipelines: %s", str(pipelines))

        # TODO: add validation / conditional checking for returned value
        # TODO: determine if simply return <dict> or have some logic

        # return pipelines

    ### CONFIG ###
    def validate_n_save_configs(self, directory: str) -> dict:
        """ Set Up repo, validate config, and save the config into datastore

        Args:
            directory (str): valid directory containing pipeline configuration

        Returns:
            dict: dictionary of {
                <pipeline_name>:<single validation results>
            }
        """
        # stub response for repo set up
        click.echo("Setting Up Repo")
        results = self.validate_configs(directory)
        # stub response for save
        click.echo("Saving into datastore")
        return results

    def validate_n_save_config(self, file_name: str) -> tuple[bool, str, dict]:
        """ Set Up repo, validate config, and save the config into datastore

        Args:
            file_name (str): full absolute path of the file to be validated

        Returns:
            tuple[bool, str, dict]: status of the config validation and output message
        """
        status = True
        error_msg = ""
        resp_pipeline_config = {}
        # stub response for repo set up
        click.echo("Setting Up Repo")
        status, error_msg, resp_pipeline_config = self.validate_config(
            file_name)
        # stub response for save
        click.echo("Saving into datastore")
        return (status, error_msg, resp_pipeline_config)

    def validate_configs(self, directory: str) -> dict:
        """ Validate configuration file in a directory

        Args:
            directory (str): valid directory containing pipeline configuration

        Returns:
            dict: dictionary of {
                <pipeline_name>:<single validation results>
            }
        """
        # stub response
        parser = YamlParser()
        results = {}
        pipeline_configs = parser.parse_yaml_directory(directory)
        for pipeline_name, values in pipeline_configs.items():
            pipeline_file_name = values[const.KEY_PIPE_FILE]
            pipeline_config = values[const.KEY_PIPE_CONFIG]
            response_dict = self.config_checker.validate_config(
                pipeline_name, pipeline_config, pipeline_file_name, True)
            # response_dict[const.KEY_PIPE_FILE] = pipeline_file_name
            results[pipeline_name] = response_dict
        return results

    def validate_config(self, file_name: str) -> tuple[bool, str, dict]:
        """ Validate a single configuration file

        Args:
            file_name (str): full absolute path of the file to be validated

        Returns:
            tuple[bool, str, dict]: status of the config validation and output message
        """
        parser = YamlParser()
        pipeline_config = parser.parse_yaml_file(file_name)

        # get the pipeline_name for ConfigChecker
        pipeline_name = pipeline_config.get('global.pipeline_name')
        # Extract the filename without extension or path
        pipeline_file_name = os.path.basename(file_name)
        click.echo(f"Validating file in {pipeline_file_name}")

        # call ConfigChecker to validate the configuration
        # returns: dict <valid, error_msg, pipeline_config
        response_dict = self.config_checker.validate_config(pipeline_name,
                                                            pipeline_config,
                                                            pipeline_file_name,
                                                            error_lc=True)

        # store the response to variables
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
        # Pseudocode
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

        # This is example how to call RepoManager util class from controller
        # self.repo_manager.setup_repo()
        # self.logger.debug("is_remote_repo: %s", remote_repo)

        return tuple([status, message, pipeline_id])

    # def _start_job(self):
    #     """_summary_
    #     """

    # def stop_job(self):
    #     """_summary_
    #     """

    def display_or_edit_config(self):
        """_summary_
        """

    def list_configuration(self):
        """_summary_
        """

    def dry_run(self, config_name: str) -> str:
        """dry run methods responsible for the `--dry-run` method for pipelines.
        The function will retrieve any pipeline history from database, then validate
        the configuration file (check hash_commit), and then perform the dry_run

        Args:
            pipeline_name (str): _description_

        Returns:
            str: _description_
        """
        # 1. Usecase 1a/b - call function to check if it's a valid git repo

        # 2. call RepoManager to check_commit whether hash file is modified or git commit is changed
        # TODO: in a way, pipeline_name means we need to implement repo_manager
        # to parse the dict

        # 3. call MongoAdapter get_pipeline_record(repo_name:str, pipeline_name:str, branch:str)
        # what can I do with this?

        # 4. if step #2 sets to True (commit hash different) run usecase 2a (call
        # validate_config(filename: str))
        # TODO: check hash commit of current file. can use import hashlib.
        # then, call method to compare previous_file (mongodb) and current_file

        # current_config_hash = repo_manager.get_config_hash(config_name)
        # initialize MongoAdapter()
        status, message, config_dict = self.validate_config(config_name)
        # print what validate_config() returns
        # print(f"{status}, {message}")

        # not successful
        if not status:
            return f"[ERROR] {message}"

        # test_get_db()
        mongo = MongoAdapter()

        # Print Dry-Run
        # 5. Simulate Dry run
        dry_run_msg = ""
        # TODO: need to know the order of execution
        # output_dict #to combine the global and jobs
        # call methods
        global_dict = config_dict.get("global")
        jobs_dict = config_dict.get("jobs")
        stages_dict = config_dict.get("stages")
        # print("global\n", global_dict)
        global_output = self._run_global(global_dict, dry_run=True)
        # print(global_output)
        dry_run_msg += global_output

        # self._run_stages(stages_dict, dry_run=True)
        # print(stages_dict)

        # print("jobs\n", jobs_dict)
        jobs_output = self._run_jobs(jobs_dict, dry_run=True)
        dry_run_msg += jobs_output

        # GET TIME
        now = datetime.now()
        time_log = now.strftime("%Y-%m-%d %H:%M:%S")
        pipeline_history = {
            "dry_run_message": dry_run_msg,
            "executed_time": time_log}

        # TODO: instead of inserting the the dry_run_msg, make it more useful
        pipeline_id = mongo.insert_pipeline(pipeline_history)

        # get the pipeline_id inserted to mongodb
        print(f"Insert successfully!\npipeline_id: {pipeline_id}")

        # 6. return message of the dry_run info
        return dry_run_msg

    # what shall I return?
    def _run_global(self, global_dict: dict, dry_run: bool = False) -> str:

        # Step 1. Parse the dict.
        # Step 2. check if dry_run=True
        if dry_run:
            # parse what you get from the dict...
            pipeline_name = global_dict.get("pipeline_name")
            docker_registry = global_dict.get("docker_registry")

            global_output = f"pipeline name: {pipeline_name}\ndocker registry: {docker_registry}\n"

            return global_output

        # TODO; call DockerRunner and perform the execution
        return

    def _run_jobs(self, jobs: dict, dry_run: bool = False) -> str:
        if dry_run:
            jobs_output = ""

            for job in jobs:
                jobs_output += self._format_job_info_msg(
                    job, jobs[job]['stage'], jobs[job]['scripts'], jobs[job]['allow_failure'])

            return jobs_output

        # TODO: implement job run
        return "not implemented yet - run jobs"

    def _format_job_info_msg(self, job_name, stage, command, allow_failure):
        formatted_msg = f'[INFO] Running job: "{job_name}"\n'
        formatted_msg += f'  -> Stage: {stage}\n'
        formatted_msg += f'  -> Command: {command}\n'
        formatted_msg += f'  -> Allow Failure: {allow_failure}\n'

        return formatted_msg

    def _test_mongo_db(self) -> str:
        mongo = MongoAdapter()

        # INSERT
        pipeline_history = {"hello": "world"}
        inserted_id = mongo.insert_pipeline(pipeline_history)

        return inserted_id
