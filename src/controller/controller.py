"""This is Controller class that integrates the CLI with the other class components
    such as DataStore, Docker, Config file validation (ConfigChecker), and
    other related class.
"""


from datetime import datetime
import copy
import os
from typing import Any
import pprint
import click
import git.exc
from pydantic import ValidationError
import util.constant as const
from util.container import (DockerManager)
from util.model import (SessionDetail, PipelineConfig, ValidatedStage, PipelineInfo, PipelineHist)
from util.common_utils import (get_logger, ConfigOverrides, DryRun)
from util.repo_manager import (RepoManager)
from util.db_mongo import (MongoAdapter)
from util.yaml_parser import YamlParser
from util.config_tools import (ConfigChecker)

REPO_SOURCE = ""
REPO_TARGET_PATH = ""
REPO_BRANCH_NAME = "main"
MONGO_PIPELINES_TABLE = "repo_configs"

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
        self.repo_manager = RepoManager(REPO_SOURCE)
        self.mongo_ds = MongoAdapter()  # init DataStore (MongoDB, Postgres)
        self.config_checker = ConfigChecker()  # init Configuration Checker
        # ..and many more
        self.logger = get_logger('cli.controller')

    def set_repo(self, repo_url: str) -> tuple[bool, str]:
        """Set the repository URL, validate it, and store in MongoDB.

        Args:
            repo_url (str): The repository URL provided by the user.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """

        mongo = MongoAdapter()

        # Check if the current directory is a Git repository using get_repo
        try:
            repo = git.Repo(os.getcwd(), search_parent_directories=True)
            repo_name = os.path.basename(repo.working_tree_dir)
            return False, (
                f"You are currently in a current working directory Git repository: '{repo_name}'.\n"
                "Please navigate out of the current working directory repository and try again\n"
                "cid config set-repo <repository>."
            )
        except git.exc.InvalidGitRepositoryError:
            self.logger.info(
                f"Proceeding to configure for repository {repo_url}.")

        # Validate the provided repo URL
        if not self._is_valid_repo(repo_url):
            return False, "The provided URL is not a valid URL or a valid Git repository."

        repo_name = self.repo_manager._extract_repo_name_from_url(repo_url)

        # Default to 'main' branch for now
        branch = "main"

        # Log the current time
        now = datetime.now()
        time_log = now.strftime("%Y-%m-%d %H:%M:%S")

        # Data to insert into MongoDB
        repo_data = {
            "user_id": "random",  # random user session for now
            "repo_url": repo_url,
            "repo_name": repo_name,
            "branch": branch,
            "commit_hash": "random hash for now",
            "is_remote": True,  # can only set remote repo for now
            "last_temp_working_dir": None,  # placeholder for now
            "time": time_log
        }

        # Insert the repo data into MongoDB
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

    def get_repo(self) -> tuple[Any, str] | str:
        """Check if the current directory is a Git repository.

        Returns:
            str: Repository's name if current working directory is a Git repo, None otherwise.
        """
        mongo = MongoAdapter()
        try:
            repo = git.Repo(os.getcwd(), search_parent_directories=True)
            repo_name = os.path.basename(repo.working_tree_dir)
            return True, repo_name
        except git.exc.InvalidGitRepositoryError:
            last_repo = mongo.get_last_set_repo()
            if last_repo:
                return False, last_repo.get('repo_url', '')
            else:
                return False, ""

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
    def validate_n_save_configs(self, directory: str) -> dict:
        """ Set Up repo, validate config, and save the config into datastore

        Args:
            directory (str): valid directory containing pipeline configuration

        Returns:
            dict: dictionary of {<pipeline_name>:<single validation results>}
        """
        # stub response for repo set up
        click.echo("Setting Up Repo")
        validation_results = self.validate_configs(directory)
        # stub response for save
        click.echo("Saving into datastore")
        results = {}
        for pipeline_name, validation_result in validation_results.items():
            status = validation_result.get('valid')
            error_msg = validation_result.get('error_msg')
            pipeline_config = validation_result.get('pipeline_config')
            if status:
                file_path = os.path.join(directory, f"{pipeline_name}.yml")
                # Pass the pre-validated config and skip validation
                status, error_msg, saved_config = self.validate_n_save_config(
                    file_path, pipeline_config=pipeline_config, skip_validation=True
                )
                validation_result.update({
                    'valid': status,
                    'error_msg': error_msg,
                    'pipeline_config': saved_config
                })
            else:
                click.echo(f"Validation failed for {pipeline_name}: {error_msg}")
            results[pipeline_name] = validation_result
        return results

    def validate_n_save_config(
        self, file_name: str, pipeline_config: dict = None, skip_validation: bool = False
    ) -> tuple[bool, str, dict]:
        """ Set Up repo, validate config, and save the config into datastore

        Args:
            file_name (str): full absolute path of the file to be validated

        Returns:
            tuple[bool, str, dict]: status of the config validation and output message
        """
        status = True
        error_msg = ""
        resp_pipeline_config = pipeline_config
        # stub response for repo set up
        if not skip_validation:
            status, error_msg, resp_pipeline_config = self.validate_config(file_name)
        # If validation passes, save to datastore
        if status:
            pipeline_name = resp_pipeline_config['global'].get('pipeline_name')
            #TODO: replace stubs
            repo_data = self.mongo_ds.get_repo(
                "sample-repo", "https://github.com/sample-user/sample-repo", "main"
            )
            # Case 1: No Repo Exists - Create New Repo with Pipeline
            #TODO: replace stubs
            if not repo_data:
                new_repo_data = {
                    "repo_name": "sample-repo",
                    "repo_url": "https://github.com/sample-user/sample-repo",
                    "branch": "main",
                    "pipelines": [
                        self.mongo_ds.create_pipeline_document(
                            pipeline_name, file_name, resp_pipeline_config
                        )
                    ]
                }
                # TODO: schema improvement https://github.com/CS6510-SEA-F24/t4-cicd/issues/105
                # new_repo_data = {
                #     "repo_name": "cicd-python",
                #     "repo_url": "https://github.com/sjchin88/cicd-python",
                #     "branch": "main",
                #     "pipelines": self.mongo_ds.create_pipeline_document(
                #             pipeline_name, file_name, resp_pipeline_config
                #         )
                # }
                repo_id = self.mongo_ds.insert_repo(
                    new_repo_data, collection_name=MONGO_PIPELINES_TABLE
                )
                if not repo_id:
                    return False, "Error saving repo to datastore.", resp_pipeline_config

            # # Case 2: Existing Repo - Append Pipeline
            else:
                existing_pipeline = next(
                    #(p_name for p_name in repo_data["pipelines"] if p_name == pipeline_name),
                    (p for p in repo_data["pipelines"] if p["pipeline_name"] == pipeline_name),
                    None
                )
                if not existing_pipeline:
                    new_pipeline_document = self.mongo_ds.create_pipeline_document(
                        pipeline_name, file_name, resp_pipeline_config
                    )
                    repo_data["pipelines"].append(new_pipeline_document)
                    #repo_data["pipelines"].update(new_pipeline_document)
                    success = self.mongo_ds.update_pipeline(repo_data)
                    if not success:
                        error_msg = f"Error add new '{pipeline_name}' to datastore."
                        status = False
                else:
                    error_msg = (
                        f"Pipeline '{pipeline_name}' already exists in datastore. "
                        "Use --override to update."
                    )
                    status = False
        return status, error_msg.strip(), resp_pipeline_config

    def validate_configs(self, directory: str) -> dict:
        """ Validate configuration file in a directory

        Args:
            directory (str): valid directory containing pipeline configuration

        Returns:
            dict: dictionary of {<pipeline_name>:<single validation results>}
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
        pipeline = self.mongo_ds.get_pipeline_config(
            "sample-repo",
            "https://github.com/sample-user/sample-repo",
            "main",
            pipeline_name)
        if not pipeline.get('pipeline_config'):
            click.echo(f"No pipeline config found for '{pipeline_name}'.")
            return False
        data = self.mongo_ds.get_pipeline(
            pipeline.get('_id'), collection_name=MONGO_PIPELINES_TABLE)
        data['pipeline_config'] = ConfigOverrides.apply_overrides(
            pipeline['pipeline_config'], overrides)
        # validate the updated pipeline configuration
        response_dict = self.config_checker.validate_config(pipeline_name,
                                                            data['pipeline_config'],
                                                            error_lc=True)
        status = response_dict.get('valid')
        resp_pipeline_config = response_dict.get('pipeline_config')
        if not status:
            click.echo("Override pipeline configuration validation failed.")
            return False
        success = self.mongo_ds.update_pipeline_config(
            "sample-repo",
            "https://github.com/sample-user/sample-repo",
            "main",
            "valid_pipeline",
            resp_pipeline_config)
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

    def run_pipeline(self, config_file: str, pipeline: str, git_details:dict, dry_run:bool = False,
                     local:bool = False, yaml_output: bool = False, override_configs:dict=None
                     ) -> tuple[bool, str, str]:
        """Executes the job by coordinating the repository, runner, artifact store, and logger.

        Args:
            config_file (str): file path of the configuration file.
            pipeline (str): pipeline name to be executed.
            dry_run (bool): set dry_run = True to simulate pipeline order of execution.
            git_details (dict): details of the git repository where to use.
            local (bool): True = run pipeline locally, False = run pipeline remotely.
                By default set to false.
            yaml_output (bool): set output format to yaml
            override_configs: to override required configs

        Returns:
            tuple[bool, str, str]:
                bool: status
                str: message
                str: pipeline_id -- empty string if pipeline is not being run 
                or failed (dry_run = True)
        """
        ## TODO: validate the repo has the valid branch name and commit hash
        # repo_source = git_details.get('repo_url')
        # branch = git_details.get('branch')
        # commit = git_details.get('commit_hash')

        ## Step 0: Clone the repo
        # remote_repo = git_details.get('remote_url')
        # repo_manager = RepoManager(repo_source)
        # repo_manager.setup_repo()
        # TODO: create method in repo_manager to get cloned folder path

        ## Step 1: check for valid branch / commit
        ## check for valid git commit / branch to run the pipeline
        ## this is part of usecase 1 a/b

        status = True
        message = None
        config_dict = None
        # for --pipeline, need to call YamlParser to retrieve the pipeline_name
        # for every config. Currently set default_path to find the config_files
        # to .cicd-pipelines/
        if pipeline:
            parser = YamlParser()
            default_path = '.cicd-pipelines/'
            dict_yaml = parser.parse_yaml_directory(default_path)
            config_dict = dict_yaml.get(pipeline) #get pipeline config
            # if 'pipeline' name could not be located, return False and
            # ask user to re-run the command.
            if config_dict is None:
                status = False
                message = f"\ncid: pipeline_name '{pipeline}' is not a valid name."
                message += " Please re-run the command: cid pipeline run"
                message += " --pipeline <valid_pipeline_name>"
                pipeline_id = ""
                return status, message, pipeline_id

            #get the filename and set the configuration file to be use for validate_config.
            config_file = default_path + config_dict.get('pipeline_file_name')

        # perform config validation given the config_file/file_path (not pipeline_name).
        # by default it is set to '.cicd-pipelines/pipelines.yml'
        status, message, config_dict = self.validate_config(config_file)

        # Process Override if have
        if override_configs:
            combined_config = ConfigOverrides.apply_overrides(
                config_dict,
                override_configs)
            # validate the updated pipeline configuration
            response_dict = self.config_checker.validate_config(
                config_dict[const.KEY_GLOBAL][const.KEY_PIPE_NAME],
                combined_config)
            # Update status and config_dict
            status = response_dict.get('valid')
            config_dict = response_dict.get('pipeline_config')

        # Early Return
        if not status:
            pipeline_id = ""
            return status, message, pipeline_id
        # Step 2: check if pipeline is  running dry-run or not
        if dry_run:
            status, dry_run_msg, pipeline_id = self.dry_run(config_dict, yaml_output)
            return status, dry_run_msg, pipeline_id

        # Step 3: Perform pipeline run steps
        #TODO: need to validate if run local
        #TODO: need to move local to top so dry-run can also be included if we want
        # to do local execution
        if local:
            print("Flag --local is set. run pipeline locally.")

        status = True
        message = "Pipeline runs successfully"
        pipeline_id = "run_number"
        #TODO: update method to update git_detail
        try:
            repo_data = copy.deepcopy(git_details)
            repo_data["is_remote"] = True
            repo_data['repo_name'] = "cicd-python"
            repo_data['user_id'] = os.getlogin()
            repo_data = SessionDetail.model_validate(repo_data)
            # pprint.pprint(repo_data.model_dump())
            pipeline_config = PipelineConfig.model_validate(config_dict)
            status, pipeline_id = self._actual_pipeline_run(repo_data, pipeline_config, local)
        except ValidationError as ve:
            self.logger.warning(f"validation error occur, error is {ve}")
            click.secho("Error in running pipeline", fg="red")
            status = False

        if not status:
            message = 'Pipeline runs fail'

        return tuple([status, message, pipeline_id])

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
                successful(True) or fail(False). Second str is the actual run number
        """
        # TODO - Process local flag
        if local:
            click.echo("Running pipeline on local")
        else:
            click.echo("Should run pipeline on remote, right now still local")

        # Check if pipeline is already running
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
            raise ve

        # pprint.pprint(his_obj.model_dump())
        if pipeline_history['running']:
            raise ValueError(f"Pipeline {pipeline_config.global_.pipeline_name} Already Running,"+
                             "Please Stop Before Proceed")
        # pprint.pprint(pipeline_history)
        # TODO - Delete
        # pipeline_config_with_id = self.mongo_ds.get_pipeline_config(
        #     repo_data.repo_name,
        #     repo_data.repo_url,
        #     repo_data.branch,
        #     pipeline_config.global_.pipeline_name
        # )
        # Insert new job record
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
        update_success = self.mongo_ds.update_pipeline_history(
            repo_data.repo_name,
            repo_data.repo_url,
            repo_data.branch,
            pipeline_config.global_.pipeline_name,
            updates
        )
        # TODO - if update unsuccessful, prompt user.
        if not update_success:
            click.confirm('Cannot update into db, do you want to continue?', abort=True)
        # Initialize Docker Manager
        docker_manager = DockerManager(
                repo=repo_data.repo_name,
                pipeline=pipeline_config.global_.pipeline_name,
                run=str(len(his_obj.job_run_history))
            )
        # Iterate through all stages, for each jobs
        # TODO - Update pipeline_status with cancel case
        pipeline_status = const.STATUS_SUCCESS
        early_break = False
        for stage_name, stage_config in pipeline_config.stages.items():
            stage_status = const.STATUS_SUCCESS
            stage_config = ValidatedStage.model_validate(stage_config)
            job_logs = {}
            # run the job, get the record, update job history
            for job_group in stage_config.job_groups:
                for job_name in job_group:
                    job_config = pipeline_config.jobs[job_name]
                    #print(job_name)
                    #pprint.pprint(job_config)
                    job_log = docker_manager.run_job(job_name, job_config)
                    click.secho(f"Stage:{stage_name} Job:{job_name} - Streaming Job Logs",
                                fg='green')
                    click.echo(job_log.job_logs)
                    # click.echo("\n")
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
            self.mongo_ds.update_job_logs(job_id, stage_name, stage_status, job_logs)
            # single fail stage will switch the pipeline status to fail
            if stage_status == const.STATUS_FAILED:
                pipeline_status = const.STATUS_FAILED
                click.secho(f"Stage:{stage_name} failed\n", fg="red")
            else:
                click.secho(f"Stage:{stage_name} success\n", fg="green")
            # If early break, skip next stages execution
            if early_break:
                break
            #pprint.pprint(job_logs)
        # Wrap up and return
        docker_manager.remove_vol()
        run_update = {
            "success":pipeline_status
        }
        self.mongo_ds.update_job(job_id, run_update)
        final_updates = {
            'running':False
        }
        update_success = self.mongo_ds.update_pipeline_history(
            repo_data.repo_name,
            repo_data.repo_url,
            repo_data.branch,
            pipeline_config.global_.pipeline_name,
            final_updates
        )
        pipeline_pass = pipeline_status == const.STATUS_SUCCESS
        return pipeline_pass, f"run_number:{run_number}"


    # def stop_job(self):
    #     """_summary_
    #     """


    def display_or_edit_config(self):
        """_summary_
        """


    def list_configuration(self):
        """_summary_
        """

    def dry_run(self, config_dict: dict, is_yaml_output:bool) -> tuple[bool, str, str]:
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
        # mongo = MongoAdapter()

        #GET TIME
        #now = datetime.now()
        #time_log = now.strftime("%Y-%m-%d %H:%M:%S")
        #pipeline_history = {"config_file": yaml_output_msg, "executed_time": time_log}

        # dry-run is not stored to mongo DB
        #pipeline_id = mongo.insert_pipeline(pipeline_history)
        pipeline_id = "dry_run"

        # set yaml format if user specify "--yaml" flag.
        if is_yaml_output:
            dry_run_msg = yaml_output_msg

        return True, dry_run_msg, pipeline_id

    def pipeline_history(self, repo_url: str, repo_name: str, branch: str = "main",
                         pipeline_name:str = 'cicd_pipeline') -> bool:
        query_data = {}
        try:
            query_data['repo_url'] = repo_url
            query_data['repo_name'] = repo_name
            query_data['pipeline_name'] = pipeline_name
            #query_data['branch'] = "main" #optional
            query_data = PipelineHist.model_validate(query_data)
        except ValidationError as ve:
            self.logger.warning(f"validation error occur, error is {ve}")
            click.secho("Error in running pipeline", fg="red")
            status = False
            return status

        pipeline_dict = self.mongo_ds.get_pipeline_history(repo_name, repo_url,
                                                           branch, pipeline_name)

        #print(pipeline_dict)
        #TODO from here, you can just go through the keys and format the output accordingly
        #   if need to format to yaml
        print(pipeline_dict.keys())
