"""This is Controller class that integrates the CLI with the other class components
    such as DataStore, Docker, Config file validation (ConfigChecker), and
    other related class.
"""


from datetime import datetime
import copy
import os
import time
#import pprint
import click
#import git.exc
from pydantic import ValidationError
from ruamel.yaml import YAMLError
import util.constant as const
from util.container import (DockerManager)
from util.model import (SessionDetail, PipelineConfig, ValidatedStage, PipelineInfo, PipelineHist)
from util.common_utils import (get_logger, MongoHelper, DryRun, PrintMessage)
from util.repo_manager import (RepoManager)
from util.db_mongo import (MongoAdapter)
from util.yaml_parser import YamlParser
from util.config_tools import (ConfigChecker)

REPO_SOURCE = ""
REPO_TARGET_PATH = ""
REPO_BRANCH_NAME = "main"
MONGO_PIPELINES_TABLE = "repo_configs"
DEFAULT_CONFIG_DIR = ".cicd-pipelines/"

# pylint: disable=logging-fstring-interpolation
# pylint: disable=logging-not-lazy
# pylint: disable=fixme


class Controller:
    """Controller class that integrates the CLI with the other class components"""

    def __init__(self):
        """Initialize the controller class
        """
        # init Docker
        # init RepoManager
        self.repo_manager = RepoManager()
        self.mongo_ds = MongoAdapter()  # init DataStore (MongoDB, Postgres)
        self.config_checker = ConfigChecker()  # init Configuration Checker
        # ..and many more
        self.logger = get_logger('cli.controller')

    def handle_repo(
            self,
            repo_url: str = None, branch: str = "main",
            commit_hash: str = None) -> tuple[bool, str, SessionDetail | None]:
        """
        If repo_url is given, call set_repo for the cloning process.
        If no repo_url is given, call get_repo to validate $PWD as a git repository.

        Args:
            repo_url (str, optional): URL of the Git repository to configure. Defaults to None.
            branch (str, optional): The branch to use, defaults to 'main'.
            commit_hash (str, optional): Specific commit hash to check out, defaults to None.

        Returns:
            tuple: (bool, str, SessionDetail | None)
                - bool: True if successful, False otherwise.
                - str: Message about the result.
                - SessionDetail or None: Repository details if available, otherwise None.
        """
        if repo_url:
            return self.set_repo(repo_url=repo_url, branch=branch, commit_hash=commit_hash)
        else:
            return self.get_repo()

    def set_repo(self, repo_url: str = None, branch: str = "main",
                 commit_hash: str = None) -> tuple[bool, str, SessionDetail | None]:
        """
        Configure and save a Git repository for CI/CD checks.

        Clones the specified Git repository to the current working directory, with an optional branch and commit.
        If the current directory is already a Git repository, it returns an error.

        Args:
            repo_url (str): URL of the Git repository to configure.
            branch (str, optional): The branch to use, defaults to 'main'.
            commit_hash (str, optional): Specific commit hash to check out, defaults to the latest commit.

        Returns:
            tuple: (bool, str, SessionDetail | None)
                - bool: True if the repository was successfully configured, False otherwise.
                - str: Message indicating the result.
                - SessionDetail or None: Session details if successful, or None if it failed.
        """

        # Check : User's $PWD is a git repo. Return failure, error message, and none
        in_git_repo, message, repo_name = self.repo_manager.is_current_dir_repo()
        if in_git_repo:
            return False, f"Currently in a Git repository: '{repo_name}'. Please navigate to an empty directory.", None


        # Check : User has cloned a repo successfully, branch and commit are valid
        is_valid, message, repo_details = self.repo_manager.set_repo(
            repo_url, branch, commit_hash)

        # If not, return failure, error message, and none
        if not is_valid:
            return False, message, None

        time_log = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_id = os.getlogin()

        # Put the information into a SessionDetail Object.
        # Returns true, message, and the SessionDetail if successful
        # Else: If not, return false, message, and none
        try:
            repo_data = SessionDetail.model_validate({
                "user_id": user_id,
                "repo_url": repo_url,
                "repo_name": repo_details["repo_name"],
                "branch": repo_details["branch"],
                "commit_hash": repo_details["commit_hash"],
                "is_remote": True,
                "time": time_log
            })

            inserted_id = self.mongo_ds.update_session(repo_data.model_dump())
            if not inserted_id:
                return False, "Failed to store repository details in MongoDB.", None

            return True, "Repository set successfully.", repo_data

        except ValidationError as e:
            return False, f"Data validation error: {e}", None

    def get_repo(self) -> tuple[bool, str, SessionDetail | None]:
        """
        Retrieve the current or last saved repository details.

        Checks if the current directory is a Git repository:
        - If yes, returns its details.
        - If no, returns details of the last configured repository for the user if available.

        Returns:
            tuple: (bool, str, SessionDetail | None)
                - bool: True if in a Git repository, False otherwise.
                - str: Message about the repository status or any issues.
                - SessionDetail or None: Repository details if available, otherwise None.
        """

        # Case: check if user is in a $PWD that is a git repo
        in_git_repo, repo_name, is_in_root = self.repo_manager.is_current_dir_repo()
        user_id = os.getlogin()

        if in_git_repo:
            repo_details = self.repo_manager.get_current_repo_details()

            time_log = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            try:
                repo_data = SessionDetail.model_validate({
                    "user_id": user_id,
                    "repo_url": repo_details["repo_url"],
                    "repo_name": repo_details["repo_name"],
                    "branch": repo_details["branch"],
                    "commit_hash": repo_details["commit_hash"],
                    "is_remote": True,
                    "time": time_log
                })

                self.mongo_ds.update_session(repo_data.model_dump())

                if not is_in_root:
                    return False, "Not in the root of the repository. Please navigate to the root of the repo and try again.", repo_data

                return True, "Repository is configured in current directory", repo_data

            except ValidationError as e:
                return False, f"Data validation error: {e}", None

        last_repo = self.mongo_ds.get_session(user_id)

        if last_repo:
            try:
                last_repo_data = SessionDetail.model_validate(last_repo)
                return False, "Current working directory is not a git repository", last_repo_data

            except ValidationError as e:
                self.logger.warning(f"Failed to convert last_repo to SessionDetail: {e}")
                return False, "Failed to convert last repository to SessionDetail.", None

        # No repository information available
        return False, "No repository found to run command.", None

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
    def validate_n_save_configs(self, directory: str, saving:bool = True) -> dict:
        """ Set Up repo, validate config, and save the config into datastore

        Args:
            directory (str): valid directory containing pipeline configuration
            saving (optional, bool): whether to save the result to db. 
            Default to True

        Returns:
            dict: dictionary of {<pipeline_name>:<single validation results>}
        """
        # stub response for repo set up
        # stub response for repo set up
        session_data = SessionDetail(
            user_id='random',
            repo_name='cicd-python',
            repo_url="https://github.com/sjchin88/cicd-python",
            branch='main',
            is_remote=True,
            commit_hash="abcdef"
        )
        click.echo("Setting Up Repo")
        parser = YamlParser()
        results = {}
        pipeline_configs = parser.parse_yaml_directory(directory)
        
        # Loop through each items
        for pipeline_name, values in pipeline_configs.items():
            response = self.config_checker.validate_config(
                pipeline_name, values.pipeline_config, values.pipeline_file_name, True)
            results[pipeline_name] = response
            status = response.valid
            
            # Perform saving
            if status and saving:
                updates = {
                    'pipeline_name': pipeline_name,
                    'pipeline_file_name':values.pipeline_file_name,
                    'pipeline_config': response.pipeline_config.model_dump(by_alias=True),
                }
                status = self.mongo_ds.update_pipeline_info(
                        repo_name=session_data.repo_name,
                        repo_url=session_data.repo_url,
                        branch=session_data.branch,
                        pipeline_name=pipeline_name,
                        updates=updates
                    )
                if not status:
                    response.valid = status
                    response.error_msg = "Fail to save to datastore"
        # stub response for save
        return results

    def validate_n_save_config(
        self, file_name: str = None,
        pipeline_name: str = None,
        override_configs:dict = None,
    ) -> tuple[bool, str, PipelineInfo]:
        """ apply overrides if any, validate config, and save the config into datastore. 
        The pipeline configuration can come from three sources: (1) file_name, 
        (2) pipeline_name

        Args:
            file_name (str, optional): target file_name. Defaults to None.
            pipeline_name (str, optional): target pipeline_name. Defaults to None.
            override_configs (dict, optional): override if any. Defaults to None.

        Returns:
            tuple[bool, str, PipelineInfo]: First item is indicator for success or fail. 
            second item is the error message if any. 
            third item is the PipelineInfo object. 
        """
        status = True
        error_msg = ""

        # stub response for repo set up
        session_data = SessionDetail(
            user_id='random',
            repo_name='cicd-python',
            repo_url="https://github.com/sjchin88/cicd-python",
            branch='main',
            is_remote=True,
            commit_hash="abcdef"
        )

        status, error_msg, pipeline_info = self.validate_config(
                file_name, pipeline_name, override_configs
            )

        if not status:
            return status, error_msg.strip(), pipeline_info

        # If validation passes, save to datastore
        pipeline_config = pipeline_info.pipeline_config.model_dump(by_alias=True)
        pipeline_name = pipeline_info.pipeline_name

        # MongoAdapter update_pipeline_info method will take care of initializing
        # the PipelineInfo record for new pipeline,
        # We just need to place the pipeline_config in updates, and provide
        # pipeline_name and pipeline_file_name
        # We dont use the PipelineInfo object directly as we dont want to
        # override the existing data in the db
        updates = {
            'pipeline_name': pipeline_name,
            'pipeline_file_name':pipeline_info.pipeline_file_name,
            'pipeline_config': pipeline_config,
        }
        status = self.mongo_ds.update_pipeline_info(
                repo_name=session_data.repo_name,
                repo_url=session_data.repo_url,
                branch=session_data.branch,
                pipeline_name=pipeline_name,
                updates=updates
            )
        if not status:
            error_msg = f"Fail saving pipeline config for {pipeline_name}"
            return status, error_msg, None
        return status, error_msg.strip(), pipeline_info

    def validate_config(self,
                        file_name: str = None,
                        pipeline_name: str = None,
                        override_configs:dict=None
                        ) -> tuple[bool, str, PipelineInfo]:
        """ Apply override if any and Validate a single configuration file. 
        The pipeline configuration can come from three sources: (1) file_name, 
        (2) pipeline_name and (3) any pipeline_configuration 

        Args:
            file_name (str, optional): target file_name. Defaults to None.
            pipeline_name (str, optional): target pipeline_name. Defaults to None.
            override_configs (dict, optional): override if any. Defaults to None.

        Returns:
            tuple[bool, str, PipelineInfo]: First item is indicator for success or fail. 
            second item is the error message if any. 
            third item is the PipelineInfo object. 
        """
        parser = YamlParser()
        pipeline_config = None
        pipeline_file_name = None
        # At this point will have either config_file or pipeline_name set by upstream but not both
        # check pipeline_name first
        if pipeline_name is not None:
            try:
                pipeline_info = parser.parse_yaml_by_pipeline_name(
                    pipeline_name, DEFAULT_CONFIG_DIR)
                pipeline_file_name = pipeline_info.pipeline_file_name
                pipeline_config = pipeline_info.pipeline_config
            except FileNotFoundError as fe:
            # if 'pipeline' name could not be located, return False and error message
                self.logger.error(f"error in extracting from pipeline_name, {fe}")
                return False, fe, None
        else:
            try:
                pipeline_config = parser.parse_yaml_file(file_name)
                # get the pipeline_name for ConfigChecker
                pipeline_name = pipeline_config[const.KEY_GLOBAL][const.KEY_PIPE_NAME]
                # Extract the filename without extension or path
                pipeline_file_name = os.path.basename(file_name)
            except (FileNotFoundError, YAMLError) as e:
            # if cannot extract content, return False and error message
                self.logger.error(f"error in extracting from file_name, {e}")
                return False, e, None

        #pipeline_config = parser.parse_yaml_file(file_name)
        # Process Override if have.
        if override_configs:
            pipeline_config = MongoHelper.apply_overrides(
                pipeline_config,
                override_configs)
        click.echo(f"Validating file in {pipeline_file_name}")
        # call ConfigChecker to validate the configuration
        result = self.config_checker.validate_config(pipeline_name,
                                                     pipeline_config,
                                                     pipeline_file_name,
                                                     error_lc=True)
        pipeline_info = PipelineInfo(
            pipeline_name=pipeline_name,
            pipeline_file_name=pipeline_file_name,
            pipeline_config=result.pipeline_config
        )
        # return validation result as tuple for easier processing
        return result.valid, result.error_msg, pipeline_info

    def override_config(self, pipeline_name: str, overrides: dict) -> bool:
        """Retrieve, apply overrides, validate, and update the pipeline configuration.

            Args:
                pipeline_name (str): The name of the pipeline to update.
                overrides (dict): A dictionary of overrides to apply to the pipeline configuration.

            Returns:
                bool: True if successfully updated, False otherwise.

            Raises:
                ValueError: If no pipeline configuration is found for the given pipeline name.
            """
        pipeline_config_data = self.mongo_ds.get_pipeline_config(
            "sample-repo",
            "https://github.com/sample-user/sample-repo",
            "main",
            pipeline_name)
        pipeline_config = pipeline_config_data.get('pipeline_config')
        if not pipeline_config:
            click.echo(f"No pipeline config found for '{pipeline_name}'.")
            return False
        updated_config = MongoHelper.apply_overrides(pipeline_config, overrides)
        # validate the updated pipeline configuration

        validation_res = self.config_checker.validate_config(pipeline_name,
                                                            updated_config,
                                                            error_lc=True)
        status = validation_res.valid
        resp_pipeline_config = validation_res.pipeline_config
        if not status:
            click.echo("Override pipeline configuration validation failed.")
            return False
        success = self.mongo_ds.update_pipeline_info(
            "sample-repo",
            "https://github.com/sample-user/sample-repo",
            "main",
            pipeline_name,
            {'pipeline_config':resp_pipeline_config})
        if not success:
            click.echo("Error updating pipeline configuration.")
            return False
        click.echo("Pipeline configuration updated successfully.")
        return True

    ### PIPELINE ###
    def setup_pipeline(self):
        """ setup pipeline when is called for the first time.
        command: `cid pipeline setup`
        """

    def run_pipeline(self, config_file: str, pipeline_name: str, git_details:dict,
                     dry_run:bool = False, local:bool = False, yaml_output: bool = False,
                     override_configs:dict=None
                     ) -> tuple[bool, str]:
        """Executes the job by coordinating the repository, runner, artifact store, and logger.

        Args:
            config_file (str): file path of the configuration file.
            pipeline_name (str): pipeline name to be executed.
            dry_run (bool): set dry_run = True to simulate pipeline order of execution.
            git_details (dict): details of the git repository where to use.
            local (bool): True = run pipeline locally, False = run pipeline remotely.
                By default set to false.
            yaml_output (bool): set output format to yaml
            override_configs: to override required configs

        Returns:
            tuple[bool, str]:
                bool: status
                str: message
        """

        ## TODO: Step 1 integrate with get and set repo
        status = True
        message = None
        config_dict = None

        # Step 2 - 4 extract yaml content, apply override, validate and
        # save handled by validate_n_save_config
        status, error_msg, pipeline_info = self.validate_n_save_config(
            config_file, pipeline_name, override_configs)

        # Early Return if override and validation fail
        if not status:
            return status, error_msg
        config_dict = pipeline_info.pipeline_config.model_dump(by_alias=True)

        # Step 5: check if pipeline is  running dry-run or not
        if dry_run:
            # TODO - Update dry_run to take PipelineConfig model instead of dict
            status, dry_run_msg = self.dry_run(config_dict, yaml_output)
            self.logger.debug(f"dry run status:{status}, {dry_run_msg}")
            return status, dry_run_msg

        # Step 6: Actual Pipeline Run
        status = True
        message = "Pipeline runs successfully. "
        #TODO: update method to update git_detail from step 0
        try:
            repo_data = copy.deepcopy(git_details)
            repo_data["is_remote"] = True
            repo_data['repo_name'] = "cicd-python"
            repo_data['user_id'] = os.getlogin()
            repo_data = SessionDetail.model_validate(repo_data)
            # pprint.pprint(repo_data.model_dump())
            pipeline_config = PipelineConfig.model_validate(config_dict)
            status, run_msg = self._actual_pipeline_run(repo_data, pipeline_config, local)
            message += run_msg
        except ValidationError as ve:
            message = f"validation error occur, error is {ve}\n"
            self.logger.warning(message)
            status = False

        if not status:
            message += 'Pipeline runs fail'
        return (status, message)

    def _actual_pipeline_run(self,
                             repo_data:SessionDetail,
                             pipeline_config:PipelineConfig,
                             local:bool = False) -> tuple[bool, str]:
        """ method to actually run the pipeline

        Args:
            repo_data (SessionDetail): information required to identify the repo record
            pipeline_config (PipelineConfig): validated pipeline_configuration
            local (bool, optional): flag indicate if run to be local(True) or remote(False). 
                Defaults to False.

        Raises:
            ValueError: If target pipeline already running

        Returns:
            tuple(bool, str): first flag indicate whether the overall run is 
                successful(True) or fail(False). Second str is the actual run number if success,
                or error message if fail
        """
        # Step 0: Process local flag. Note feature to run pipeline on remote is not implemented
        if local:
            click.echo("Running pipeline on local")
        else:
            click.echo("Remote run feature is not implemented, still running pipeline on local")

        # Step 1: Check if pipeline is already running
        pipeline_history = self.mongo_ds.get_pipeline_history(
            repo_data.repo_name,
            repo_data.repo_url,
            repo_data.branch,
            pipeline_config.global_.pipeline_name
        )
        try:
            his_obj = PipelineInfo.model_validate(pipeline_history)
        except ValidationError as ve:
            self.logger.warning(f"validation error for pipeline_history:{pipeline_history}"+
                                f"error is {ve}")
            return False, "Fail to retrieve pipeline history"

        # Early return if pipeline already running
        if pipeline_history['running']:
            error_msg = f"Pipeline {pipeline_config.global_.pipeline_name} Already Running. "
            error_msg += "Please Stop Before Proceed"
            return False, error_msg

        # Step 2: Insert new job record
        job_id = self.mongo_ds.insert_job(
            his_obj,
            pipeline_config.model_dump(by_alias=True)
        )
        # print(job_id)
        his_obj.job_run_history.append(job_id)
        run_number = len(his_obj.job_run_history)
        # TODO- Update pipeline config
        updates = {
            "job_run_history":his_obj.job_run_history,
            'running':True,
        }
        update_success = self.mongo_ds.update_pipeline_info(
            repo_data.repo_name,
            repo_data.repo_url,
            repo_data.branch,
            pipeline_config.global_.pipeline_name,
            updates
        )
        # if update unsuccessful, prompt user.
        if not update_success:
            click.confirm('Cannot update into db, do you want to continue?', abort=True)
        # Initialize Docker Manager
        docker_manager = DockerManager(
                repo=repo_data.repo_name,
                pipeline=pipeline_config.global_.pipeline_name,
                run=str(len(his_obj.job_run_history))
            )
        # Step 3: Iterate through all stages, for each jobs
        pipeline_status = const.STATUS_SUCCESS
        early_break = False
        for stage_name, stage_config in pipeline_config.stages.items():
            stage_status = const.STATUS_SUCCESS
            stage_config = ValidatedStage.model_validate(stage_config)
            job_logs = {}
            stage_start_time = time.asctime()
            # run the job, get the record, update job history
            for job_group in stage_config.job_groups:
                for job_name in job_group:
                    job_config = pipeline_config.jobs[job_name]
                    job_log = docker_manager.run_job(job_name, job_config)
                    click.secho(f"Stage:{stage_name} Job:{job_name} - Streaming Job Logs",
                                fg='green')
                    click.echo(job_log.job_logs)
                    job_logs[job_name] = job_log.model_dump()
                    # single fail job will switch the stage status to fail
                    if job_log.job_status == const.STATUS_FAILED:
                        stage_status = const.STATUS_FAILED
                        click.secho(f"Job:{job_name} failed\n", fg="red")
                        # Early break
                        if job_config[const.JOB_SUBKEY_ALLOW] is False:
                            early_break = True
                            break
                    else:
                        click.secho(f"Job:{job_name} success\n", fg="green")
                # If early break, skip next job group execution
                if early_break:
                    break
            self.mongo_ds.update_job_logs(
                job_id,
                stage_name,
                stage_status,
                job_logs,
                stage_time={
                    "start_time": stage_start_time,
                    "completion_time": time.asctime()
                }
            )
            # single fail stage will switch the pipeline status to fail
            if stage_status == const.STATUS_FAILED:
                pipeline_status = const.STATUS_FAILED
                click.secho(f"Stage:{stage_name} failed\n", fg="red")
            else:
                click.secho(f"Stage:{stage_name} success\n", fg="green")
            # If early break, skip next stages execution
            if early_break:
                break

        # Wrap up and return
        docker_manager.remove_vol()
        run_update = {
            "status":pipeline_status,
            "completion_time": time.asctime()
        }
        self.mongo_ds.update_job(job_id, run_update)
        final_updates = {
            'running':False
        }
        update_success = self.mongo_ds.update_pipeline_info(
            repo_data.repo_name,
            repo_data.repo_url,
            repo_data.branch,
            pipeline_config.global_.pipeline_name,
            final_updates
        )
        pipeline_pass = pipeline_status == const.STATUS_SUCCESS
        run_msg = f"run_number:{run_number}" if pipeline_pass else ""
        return pipeline_pass, run_msg

    def display_or_edit_config(self):
        """_summary_
        """


    def list_configuration(self):
        """_summary_
        """

    def dry_run(self, config_dict: dict, is_yaml_output:bool) -> tuple[bool, str]:
        """dry run methods responsible for the `--dry-run` method for pipelines.
        The function will retrieve any pipeline history from database, then validate
        the configuration file (check hash_commit), and then perform the dry_run

        Args:
            status (bool): _description_
            config_dict (dict): _description_
            is_yaml_output (bool): _description_

        Returns:
            str: _description_
        """
        # TODO - Do the clean up on doctsring and methods
        dry_run = DryRun(config_dict)
        dry_run_msg = dry_run.get_plaintext_format()
        yaml_output_msg = dry_run.get_yaml_format()
        # mongo = MongoAdapter()

        #GET TIME
        #now = datetime.now()
        #time_log = now.strftime("%Y-%m-%d %H:%M:%S")
        #pipeline_history = {"config_file": yaml_output_msg, "executed_time": time_log}

        # dry-run is not stored to mongo DB
        #pipeline_id = mongo.insert_pipeline(pipeline_history)
        #pipeline_id = "dry_run"

        # set yaml format if user specify "--yaml" flag.
        if is_yaml_output:
            dry_run_msg = yaml_output_msg

        return True, dry_run_msg

    def pipeline_history(self, pipeline_details: PipelineHist) -> tuple[bool, str]:
        """pipeline history provides user to retrieve the past pipeline runs

        Args:
            pipeline_details (PipelineHist): pydantic models that contains \
                user input to query pipeline history to database.

        Returns:
            dict:
                "is_success": boolean if
        """
        pipeline_dict = pipeline_details.model_dump()
        pipeline_name = pipeline_dict['pipeline_name']
        repo_url = pipeline_dict['repo_url']
        run_number = pipeline_dict['run']
        output_msg = ""
        try:
            #(L4.2) cid pipeline report --repo <repo> --pipeline <pipeline> --run <number>
            if pipeline_dict['run']: # --run is specified

                #TODO: refactor code to use the `get_pipeline_run_summary()` method
                history = self.mongo_ds.get_pipeline_history(pipeline_dict['repo_name'],
                repo_url, pipeline_dict['branch'], pipeline_name)
                #history = self.mongo_ds.get_pipeline_run_summary(repo_url, pipeline_name,
                #                                                 run_number=run_number)
                run_number = int(pipeline_dict['run']) - 1
                job_history = self.mongo_ds.get_job(history['job_run_history'][run_number])

                message = PrintMessage(job_history)
                output_msg = message.print(['pipeline_name', 'run_number', 'git_commit_hash',
                                        'start_time', 'completion_time'])
                output_msg += message.print_log_status()
            else:
                #L4.1. cid pipeline report --repo <repo> | get all pipelines report
                #--run flag is not specified, so list out the pipeline reports.
                #by default, "all" will return the history of all pipeline_name.
                #TODO: add --local flag seen in 4.1.2
                if pipeline_name == "all": #run all job_history
                    job_history = self.mongo_ds.get_pipeline_run_summary(repo_url)
                else:
                    job_history = self.mongo_ds.get_pipeline_run_summary(repo_url, pipeline_name)


                #validation, if job_history is empty from get_pipeline_run_summary(),
                # this means no data found in DB
                #TODO: see how to handle the exception in KeyEror
                if job_history == []:
                    is_success = False
                    err_msg = f"There is no job history for pipeline '{pipeline_name}' in {repo_url}!\n"
                    err_msg += "please ensure that the pipeline_name or repo are valid."
                    err_msg += "Please run `cid pipeline run` if no reports found"
                    return is_success, err_msg
                for job in job_history:
                    message = PrintMessage(job)
                    output_msg += message.print(['pipeline_name', 'run_number', 'git_commit_hash',
                                            'start_time', 'completion_time'])
        except KeyError as ke:
            err_msg = f"There is no job history for pipeline '{pipeline_name}' in {repo_url}!\n"
            err_msg += "please ensure that the pipeline_name or repo are valid."
            err_msg += "Please run `cid pipeline run` if no reports found"
            self.logger.warning(f"Key Error in pipeline_history: {ke}")
            is_success = False
            return is_success, err_msg
        except IndexError as ie:
            self.logger.warning(f"job_number is out of bound. error: {ie}")
            is_success = False
            err_msg = f"run_number: {pipeline_dict['run']} does not exist!\n"
            err_msg += f"do you mean --run {len(history['job_run_history'])}?"
            return is_success, err_msg

        is_success = True
        return is_success, output_msg
