"""This is Controller class that integrates the CLI with the other class components
    such as DataStore, Docker, Config file validation (ConfigChecker), and
    other related class.
"""

from datetime import datetime
import copy
import os
import time
from pathlib import Path

import click
from docker.errors import DockerException
from pydantic import ValidationError
from ruamel.yaml import YAMLError
import util.constant as c
from util.container import (DockerManager)
from util.model import (JobLog, SessionDetail, PipelineConfig, ValidatedStage, PipelineInfo, PipelineHist)
from util.common_utils import (get_logger, ConfigOverride, DryRun, PipelineReport)
from util.repo_manager import (RepoManager)
from util.db_mongo import (MongoAdapter)
from util.yaml_parser import YamlParser
from util.config_tools import (ConfigChecker)

# pylint: disable=logging-fstring-interpolation
# pylint: disable=logging-not-lazy

class Controller:
    """Controller class that integrates the CLI with the other class components"""

    def __init__(self):
        """Initialize the controller class
        """
        self.repo_manager = RepoManager()
        self.mongo_ds = MongoAdapter()
        self.config_checker = ConfigChecker()
        self.logger = get_logger('cli.controller')

    def handle_repo(self, repo_url: str = None,
                    branch: str = None,
                    commit_hash: str = None) -> tuple[bool, str, SessionDetail | None]:
        """
        Handles repository setup and retrieval depending on the input parameters.

        Args:
            repo_url (str, optional): URL of the Git repository to configure. Defaults to None.
            branch (str, optional): The branch to use. Defaults to None.
            commit_hash (str, optional): Specific commit hash to check out. Defaults to None.

        Returns:
            tuple: (bool, str, SessionDetail | None)
                - bool: True if successful, False otherwise.
                - str: Message about the result.
                - SessionDetail or None: Repository details if available, otherwise None.
        """
        if repo_url:
            # Set up the repository by doing a clone of the given repo_url
            if branch is None:
                branch = c.DEFAULT_BRANCH
            return self.set_repo(repo_url=repo_url, branch=branch, commit_hash=commit_hash)
        if branch or commit_hash:
            # Check out with specified branch or commit
            return self.checkout_repo(branch=branch, commit_hash=commit_hash)

        # Get the current repository details, or last set repo from user
        return self.get_repo()

    def set_repo(self, repo_url: str = None, branch: str = c.DEFAULT_BRANCH,
                 commit_hash: str = None) -> tuple[bool, str, SessionDetail | None]:
        """
        Configure and save a Git repository for CI/CD checks.

        Clones the specified Git repository to the current working directory,
        with an optional branch and commit.
        If the current directory is already a Git repository, it returns an error.

        Args:
            repo_url (str): URL of the Git repository to configure.
            branch (str, optional): The branch to use, defaults to 'main'.
            commit_hash (str, optional): Specific commit hash to check out,
            defaults to the latest commit.

        Returns:
            tuple: (bool, str, SessionDetail | None)
                - bool: True if the repository was successfully configured, False otherwise.
                - str: Message indicating the result.
                - SessionDetail or None: Session details if successful, or None if it failed.
        """

        # Check : User's $PWD is a git repo. Return failure, error message, and none
        in_git_repo, message, repo_name = self.repo_manager.is_current_dir_repo()
        if in_git_repo:
            return (False,
                    f"Currently in a Git repository: '{repo_name}'. "
                    f"Please navigate to an empty directory.", None)

        is_valid, is_remote, message = self.repo_manager.is_valid_git_repo(repo_url)

        if not is_valid:
            return False, message, None

        # Check : User has cloned a repo successfully, branch and commit are valid
        is_valid, message, repo_details = self.repo_manager.set_repo(
            repo_url, is_remote, branch, commit_hash)

        # If not, return failure, error message, and none
        if not is_valid:
            return False, message, None

        if not is_remote:
            repo_url = str(Path(repo_url).resolve())

        time_log = datetime.now().strftime(c.DATETIME_FORMAT)
        user_id = os.getlogin()

        # Put the information into a SessionDetail Object.
        # Returns true, message, and the SessionDetail if successful
        # Else: If not, return false, message, and none
        try:
            repo_data = SessionDetail.model_validate({
                c.FIELD_USER_ID: user_id,
                c.FIELD_REPO_URL: repo_url,
                c.FIELD_REPO_NAME: repo_details[c.FIELD_REPO_NAME],
                c.FIELD_BRANCH: repo_details[c.FIELD_BRANCH],
                c.FIELD_COMMIT_HASH: repo_details[c.FIELD_COMMIT_HASH],
                c.FIELD_IS_REMOTE: is_remote,
                c.FIELD_TIME: time_log
            })

            inserted_id = self.mongo_ds.update_session(repo_data.model_dump())
            if not inserted_id:
                return False, "Failed to store repository details in MongoDB.", None

            # Successful execution of repo being cloned and configured in $PWD
            return True, "Repository set successfully.", repo_data

        except ValidationError as e:
            return False, f"Data validation error: {e}", None

    def checkout_repo(self, branch: str = None,
                      commit_hash: str = None) -> tuple[bool, str, SessionDetail | None]:
        """
          Checks out a specific branch and/or commit in the current repository.

          This method validates the current directory as a Git repository and attempts to
          check out the specified branch and/or commit. If no branch or commit is provided,
          it defaults to checking out the latest commit on the default branch.

          Upon successful execution, the method updates the session details in the database.

          Args:
              branch (str, optional): The branch to check out. If None, stays on the current branch.
              commit_hash (str, optional): The specific commit hash to check out. If None, defaults
                                           to the latest commit on the given or current branch.

          Returns:
              tuple[bool, str, SessionDetail | None]:
                  - bool: True if the operation was successful, False otherwise.
                  - str: A message describing the result of the operation.
                  - SessionDetail or None: The repository details if successful,
                    or None if the operation failed.

          Exceptions:
              - ValidationError: Raised if the session data fails validation.
              - Exception: Catches unexpected errors and returns
              them as part of the failure message.
          """
        in_git_repo, is_in_root, _ = self.repo_manager.is_current_dir_repo()

        if not in_git_repo:
            return False, "Current directory is not a Git repository.", None

        if not is_in_root:
            return False, "Please navigate to root of repository before executing command.", None

        user_id = os.getlogin()

        # Perform the checkout operation
        try:
            success, message = self.repo_manager.checkout_branch_and_commit(branch, commit_hash)
            if not success:
                return False, message, None

            repo_details = self.repo_manager.get_current_repo_details()

            if not repo_details or not repo_details.get(c.FIELD_REPO_URL):
                return False, "Failed to retrieve repository details.", None

            time_log = datetime.now().strftime(c.DATETIME_FORMAT)

            # Retrieve existing session
            existing_session = self.mongo_ds.get_session(user_id)
            existing_is_remote = existing_session.get(c.FIELD_IS_REMOTE) \
                if existing_session and c.FIELD_IS_REMOTE in existing_session else False

            repo_data = SessionDetail.model_validate({
                c.FIELD_USER_ID: user_id,
                c.FIELD_REPO_URL: str(Path(repo_details[c.FIELD_REPO_URL]).resolve()),
                c.FIELD_REPO_NAME: repo_details[c.FIELD_REPO_NAME],
                c.FIELD_BRANCH: repo_details[c.FIELD_BRANCH],
                c.FIELD_COMMIT_HASH: repo_details[c.FIELD_COMMIT_HASH],
                c.FIELD_IS_REMOTE: existing_is_remote,
                c.FIELD_TIME: time_log
            })

            # Save the session details in the database
            self.mongo_ds.update_session(repo_data.model_dump())

            return True, "Repository checked out successfully.", repo_data

        except ValidationError as e:
            return False, f"Data validation error: {e}", None
        except Exception as e:
            return False, f"Unexpected error: {e}", None

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
        in_git_repo, is_in_root, _ = self.repo_manager.is_current_dir_repo()

        user_id = os.getlogin()

        if in_git_repo:

            if not is_in_root:
                return False, ("Not in the root of the repository. "
                               "Please navigate to the root of the repo and try again."), None

            repo_details = self.repo_manager.get_current_repo_details()

            time_log = datetime.now().strftime(c.DATETIME_FORMAT)

            try:
                existing_session = self.mongo_ds.get_session(user_id)
                existing_is_remote = existing_session.get(c.FIELD_IS_REMOTE) \
                    if existing_session and c.FIELD_IS_REMOTE in existing_session else False

                repo_data = SessionDetail.model_validate({
                    c.FIELD_USER_ID: user_id,
                    c.FIELD_REPO_URL: repo_details[c.FIELD_REPO_URL],
                    c.FIELD_REPO_NAME: repo_details[c.FIELD_REPO_NAME],
                    c.FIELD_BRANCH: repo_details[c.FIELD_BRANCH],
                    c.FIELD_COMMIT_HASH: repo_details[c.FIELD_COMMIT_HASH],
                    c.FIELD_IS_REMOTE: existing_is_remote,
                    c.FIELD_TIME: time_log
                })

                # Save the session details in the database
                self.mongo_ds.update_session(repo_data.model_dump())

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
        return False, ("Working directory is not a git repository. "
                       "No previous repository has been set."), None

    ### CONFIG ###
    def validate_n_save_configs(self,
                                directory: str,
                                saving:bool = True,
                                session_data:SessionDetail = None) -> dict:
        """ Set Up repo, validate config, and save the config into datastore

        Args:
            directory (str): valid directory containing pipeline configuration
            saving (optional, bool): whether to save the result to db.
            Default to True

        Raises:
            FileNotFoundError: if the directory does not exist
            ValueError: for duplicate pipeline_name
            
        Returns:
            dict: dictionary of {pipeline_name:single validation results}
        """
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
                    c.FIELD_PIPELINE_NAME: pipeline_name,
                    c.FIELD_PIPELINE_FILE_NAME:values.pipeline_file_name,
                    c.FIELD_PIPELINE_CONFIG: response.pipeline_config.model_dump(by_alias=True),
                    c.FIELD_LAST_COMMIT_HASH: session_data.commit_hash
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
        return results

    def validate_n_save_config(
        self, file_name: str = None,
        pipeline_name: str = None,
        override_configs:dict = None,
        session_data:SessionDetail = None,
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
            c.FIELD_PIPELINE_NAME: pipeline_name,
            c.FIELD_PIPELINE_FILE_NAME:pipeline_info.pipeline_file_name,
            c.FIELD_PIPELINE_CONFIG: pipeline_config,
            c.FIELD_LAST_COMMIT_HASH: session_data.commit_hash
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
                    pipeline_name, c.DEFAULT_CONFIG_DIR)
                pipeline_file_name = pipeline_info.pipeline_file_name
                pipeline_config = pipeline_info.pipeline_config
            except (ValueError, FileNotFoundError) as fe:
            # if 'pipeline' name could not be located, return False and error message
                self.logger.error(f"error in extracting from pipeline_name, {fe}")
                return False, str(fe), None
        else:
            try:
                pipeline_config = parser.parse_yaml_file(file_name)
                # get the pipeline_name for ConfigChecker
                pipeline_name = pipeline_config[c.KEY_GLOBAL][c.KEY_PIPE_NAME]
                # Extract the filename without extension or path
                pipeline_file_name = os.path.basename(file_name)
            except (FileNotFoundError, YAMLError) as e:
            # if cannot extract content, return False and error message
                self.logger.error(f"error in extracting from file_name, {e}")
                return False, str(e), None

        # Process Override if have.
        if override_configs:
            pipeline_config = ConfigOverride.apply_overrides(
                pipeline_config,
                override_configs)
        click.echo(f"Validating file in {pipeline_file_name}")
        # call ConfigChecker to validate the configuration
        result = self.config_checker.validate_config(pipeline_name,
                                                     pipeline_config,
                                                     pipeline_file_name,
                                                     error_lc=True)
        # Early return
        if not result.valid:
            return result.valid, result.error_msg, None

        pipeline_info = PipelineInfo(
            pipeline_name=pipeline_name,
            pipeline_file_name=pipeline_file_name,
            pipeline_config=result.pipeline_config
        )
        # return validation result as tuple for easier processing
        return result.valid, result.error_msg, pipeline_info

    def override_config(self,
                        pipeline_name: str,
                        overrides: dict,
                        session_data:SessionDetail = None,
                        save: bool = False) -> tuple[bool, str, PipelineConfig]:
        """Retrieve, apply overrides, validate, and update the pipeline configuration.

            Args:
                pipeline_name (str): The name of the pipeline to update.
                overrides (dict): A dictionary of overrides to apply to the pipeline configuration.

            Returns:
                tuple[bool, str, PipelineInfo]: First item is indicator for success or fail.
                second item is the error message if any.
                third item is the PipelineInfo object.

            Raises:
                ValueError: If no pipeline configuration is found for the given pipeline name.
            """
        pipeline_history = self.mongo_ds.get_pipeline_history(
            repo_name=session_data.repo_name,
            repo_url=session_data.repo_url,
            branch=session_data.branch,
            pipeline_name=pipeline_name
        )
        try:
            his_obj = PipelineInfo.model_validate(pipeline_history)
        except ValidationError:
            err = f"No pipeline config found for '{pipeline_name}'."
            return False, err, None

        pipeline_config = his_obj.pipeline_config.model_dump(by_alias=True)
        updated_config = ConfigOverride.apply_overrides(pipeline_config, overrides)
        # validate the updated pipeline configuration
        validation_res = self.config_checker.validate_config(pipeline_name,
                                                            updated_config,
                                                            error_lc=False)
        status = validation_res.valid

        # Early return if validation fail
        if not status:
            return False, validation_res.error_msg, None

        resp_pipeline_config = validation_res.pipeline_config.model_dump(by_alias=True)
        # Save only if required
        if save:
            success = self.mongo_ds.update_pipeline_info(
                repo_name=session_data.repo_name,
                repo_url=session_data.repo_url,
                branch=session_data.branch,
                pipeline_name=pipeline_name,
                # Update for last_commit_hash is not required, as original
                # config came from data store
                updates={c.FIELD_PIPELINE_CONFIG:resp_pipeline_config})
            if not success:
                err = "Validation passed, but error in saving"
                return False, err, validation_res.pipeline_config

        # Return true if reach this stage
        return True, "", validation_res.pipeline_config

    def run_pipeline(self, config_file: str, pipeline_name: str, git_details:SessionDetail,
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
        status = True
        message = None
        config_dict = None

        # Step 2 - 4 extract yaml content, apply override, validate and
        # save handled by validate_n_save_config
        status, error_msg, pipeline_info = self.validate_n_save_config(
            config_file, pipeline_name, override_configs, git_details)

        # Early Return if override and validation fail
        if not status:
            return status, error_msg
        config_dict = pipeline_info.pipeline_config.model_dump(by_alias=True)

        # Step 5: check if pipeline is running dry-run or not
        if dry_run:
            status, dry_run_msg = self.dry_run(config_dict, yaml_output)
            self.logger.debug(f"dry run status:{status}, {dry_run_msg}")
            return status, dry_run_msg

        # Step 6: Actual Pipeline Run
        status = True
        message = ""

        try:
            pipeline_config = PipelineConfig.model_validate(config_dict)
            status, run_msg = self._actual_pipeline_run(git_details, pipeline_config, local)
            message += run_msg
        except ValidationError as ve:
            status = False
            message = f"validation error occur, error is {str(ve)}\n"
            self.logger.warning(message)
        except DockerException as de:
            status = False
            message = f"Error with docker service. error is {str(de)}\n"
            self.logger.warning(message)

        if not status:
            message += '\nPipeline runs fail'
        else:
            message += "\nPipeline runs successfully. "
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
        if his_obj.running:
            error_msg = f"Pipeline {pipeline_config.global_.pipeline_name} Already Running. "
            error_msg += "Please Stop Before Proceed"
            return False, error_msg

        # Step 2: Insert new job record
        job_id = self.mongo_ds.insert_job(
            his_obj,
            pipeline_config.model_dump(by_alias=True)
        )

        his_obj.job_run_history.append(job_id)
        run_number = len(his_obj.job_run_history)
        updates = {
            c.FIELD_JOB_RUN_HISTORY:his_obj.job_run_history,
            c.FIELD_RUNNING:True,
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

        pipeline_status = c.STATUS_PENDING
        try:
            # Initialize Docker Manager
            docker_manager = DockerManager(
                    repo=repo_data.repo_name,
                    pipeline=pipeline_config.global_.pipeline_name,
                    run=str(len(his_obj.job_run_history))
                )
            # Step 3: Iterate through all stages, for each jobs
            early_break = False
            for stage_name, stage_config in pipeline_config.stages.items():
                stage_status = c.STATUS_PENDING
                stage_config = ValidatedStage.model_validate(stage_config)
                job_logs = {}
                stage_start_time = time.asctime()
                try:
                    # run the job, get the record, update job history
                    for job_group in stage_config.job_groups:
                        for job_name in job_group:
                            job_config = pipeline_config.jobs[job_name]
                            try:
                                job_log = docker_manager.run_job(job_name, job_config)
                                click.secho(f"Stage:{stage_name} Job:{job_name} - Streaming Job Logs",
                                                fg='green')
                                click.echo(job_log.job_logs)
                                job_logs[job_name] = job_log.model_dump()
                                # single fail job will switch the stage status to fail
                                if job_log.job_status == c.STATUS_FAILED:
                                    stage_status = c.STATUS_FAILED
                                    click.secho(f"Job:{job_name} failed\n", fg="red")
                                    # Early break
                                    if job_config[c.JOB_SUBKEY_ALLOW] is False:
                                        early_break = True
                                        break
                                else:
                                    click.secho(f"Job:{job_name} success\n", fg="green")
                            except KeyboardInterrupt:
                                # Only create a job_log if current job not yet saved
                                if job_name not in job_logs:
                                    job_log_info = copy.deepcopy(job_config)
                                    job_log_info[c.REPORT_KEY_JOBNAME] = job_name
                                    job_log_info[c.REPORT_KEY_START] = time.asctime()
                                    job_log = JobLog.model_validate(job_log_info)
                                    job_log.job_status = c.STATUS_CANCELLED
                                    job_log.completion_time = time.asctime()
                                    job_logs[job_name] = job_log.model_dump()
                                if stage_status != c.STATUS_FAILED:
                                    stage_status = c.STATUS_CANCELLED  
                                raise
                            # If early break, skip next job group execution
                            if early_break:
                                break
                    # If we reach this step, if stage status still pending, update to success
                    if stage_status == c.STATUS_PENDING:
                        stage_status = c.STATUS_SUCCESS
                finally:
                    # Ensure job logs always updated regardless exception thrown
                    self.mongo_ds.update_job_logs(
                        job_id,
                        stage_name,
                        stage_status,
                        job_logs,
                        stage_time={
                            c.FIELD_START_TIME: stage_start_time,
                            c.FIELD_COMPLETION_TIME: time.asctime()
                        }
                    )
                    # single fail stage will switch the pipeline status to fail
                    if stage_status == c.STATUS_FAILED:
                        pipeline_status = c.STATUS_FAILED
                        click.secho(f"Stage:{stage_name} failed\n", fg="red")
                    elif stage_status == c.STATUS_CANCELLED:
                        # Fail status take precedence
                        if pipeline_status != c.STATUS_FAILED:
                            pipeline_status = c.STATUS_CANCELLED
                        click.secho(f"Stage:{stage_name} cancelled\n", fg="yellow")
                    else:
                        click.secho(f"Stage:{stage_name} success\n", fg="green")
                # If early break, skip next stages execution
                if early_break:
                    break
        finally:
            #if stage status still pending, update to success
            if pipeline_status == c.STATUS_PENDING:
                pipeline_status = c.STATUS_SUCCESS
            # Ensure always Wrap up and return
            run_update = {
                c.FIELD_STATUS:pipeline_status,
                c.FIELD_COMPLETION_TIME: time.asctime()
            }
            self.mongo_ds.update_job(job_id, run_update)
            final_updates = {
                c.FIELD_RUNNING:False
            }
            update_success = self.mongo_ds.update_pipeline_info(
                repo_data.repo_name,
                repo_data.repo_url,
                repo_data.branch,
                pipeline_config.global_.pipeline_name,
                final_updates
            )
            if not update_success:
                click.secho(f"Failed to update pipeline status, please do manual update\n", fg="red")
            docker_manager.remove_vol()
        pipeline_pass = pipeline_status == c.STATUS_SUCCESS
        run_msg = f"run_number:{run_number}" if pipeline_pass else ""
        return pipeline_pass, run_msg

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
        dry_run = DryRun(config_dict)
        dry_run_msg = dry_run.get_plaintext_format()
        yaml_output_msg = dry_run.get_yaml_format()

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
            tuple[bool, str]:
                "is_success: bool": true if report is successfully generated
                "output_msg: str": pipeline report return to user CLI
        """
        pipeline_dict = pipeline_details.model_dump()
        pipeline_name = pipeline_dict[c.FIELD_PIPELINE_NAME]
        repo_url = pipeline_dict[c.FIELD_REPO_URL]
        job = pipeline_dict['job']
        run_number = pipeline_dict['run']
        stage = pipeline_dict['stage']
        output_msg = ""

        try:
            # L4.1 Show summary all past pipeline runs for a repository
            # L4.2 Show pipeline run summary
            if not stage and not job:
                history = self.mongo_ds.get_pipeline_run_summary(repo_url,
                                                            pipeline_name, run_number=run_number)
                report = PipelineReport(history)
                output_msg = report.print_pipeline_summary()
            else:
                if not stage:
                    is_success = False
                    output_msg = "missing flag. --stage flag must be given along with --job"
                    return is_success, output_msg
                #L4.3 Show Stage Summary
                if not job:
                    #run_number by default is None. if not defined, it will query all runs
                    history = self.mongo_ds.get_pipeline_run_summary(repo_url, pipeline_name,
                                                        stage_name=stage, run_number=run_number)
                    report = PipelineReport(history)
                    output_msg = report.print_stage_summary()

                #L4.4 Show Job Summary
                else:
                    history = self.mongo_ds.get_pipeline_run_summary(repo_url,
                                        pipeline_name, stage_name=stage, job_name=job,
                                        run_number=run_number)
                    report = PipelineReport(history)
                    output_msg = report.print_job_summary()
        except IndexError as ie:
            self.logger.warning(f"job_number is out of bound. error: {ie}")
            is_success = False
            err_msg = f"No Report found on database for {repo_url}\nPlease ensure you have valid"
            err_msg += " flags (--pipeline, --run, and/or --repo) and execute cid pipeline run"
            err_msg += " to generate pipeline report."
            return is_success, err_msg
        is_success = True
        return is_success, output_msg
