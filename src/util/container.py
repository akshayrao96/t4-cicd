""" docker module provide all class and method required to interact with docker engine
for execution of pipeline job
"""
from pathlib import Path
import copy
import os
import re
import tarfile
import time
from abc import ABC, abstractmethod
from shutil import make_archive
import docker
import docker.errors
from botocore.exceptions import ClientError
from docker.models.containers import Container
import util.constant as c
from util.common_utils import (get_logger)
from util.db_artifact import S3Client
from util.model import (JobConfig, JobLog)

logger = get_logger("util.docker")

DEFAULT_DOCKER_DIR = '/app'
REGEX_SHELL_ERR = r'(sh:\s?)(\d+)(:)'

class ContainerManager(ABC):
    """ Abstract base class for Container Management

    Args:
        ABC (ABC): Abstract Base Class
    """
    @abstractmethod
    def run_job(self, job_name:str, job_config:dict) -> dict:
        """ Abstract method to run a job, to be implemented by subclass

        Args:
            job_name (str): name of the job
            job_config (dict): dictionary contains a job configuration

        Returns:
            dict: single job run record that can be recorded into the db
        """

    @abstractmethod
    def stop_job(self, job_name:str) -> str:
        """ Abstract method to stop a job, to be implemented by subclass

        Args:
            job_name (str): name of the job

        Returns:
            str: latest container log
        """

class DockerManager(ContainerManager):
    """ DockerManager to run all jobs for all stages in a single pipeline. 
    There should be one DockerManager object for each pipeline run
    """

    def __init__(self, client:docker.DockerClient=None,
                 log_tool=logger, repo:str="Repo", pipeline:str="pipeline", run:str="run"):
        """ Initialize the DockerManager

        Args:
            client (docker.DockerClient, optional): client for the DockerEngine. 
                Defaults to None.
            log_tool (_type_, optional): logging tool. Defaults to logger.
            repo (str, optional): repo name, use to uniquely identify the volume used. 
                Defaults to "Repo".
            pipeline (str, optional): pipeline name, use to uniquely identify the volume used. 
                Defaults to "pipeline".
            run (str, optional): run, use to uniquely identify the volume used. Defaults to "run".
        """
        if client is None:
            self.client = docker.from_env()
        else:
            self.client = client
        self.logger = log_tool
        self.vol_name = repo + '-' + pipeline + '-' + run
        self.docker_vol = None

    def run_job(self, job_name:str, job_config: dict) -> JobLog:
        """ run a single job and return its output

        Args:
            job_name (str): name of the job
            job_config (dict): a complete job configuration. with information
                defined in design_doc_config: jobs section, single job

        Returns:
            JobLog: records of a job run, as specified in designdoc_data_scheme:job
                and JobLog model.
        """
        # Validate input data
        JobConfig.model_validate(job_config)
        # create the vol for the first time
        if self.docker_vol is None:
            self.docker_vol = self.client.volumes.create(self.vol_name)

        # Extract important values
        container_name = self.vol_name + '-' + job_name
        docker_reg = job_config[c.KEY_DOCKER][c.KEY_DOCKER_REG]
        docker_img = job_config[c.KEY_DOCKER][c.KEY_DOCKER_IMG]
        # Update docker_img based on docker_reg value
        if docker_reg != c.DEFAULT_DOCKER_REGISTRY:
            docker_img = docker_reg + '/' + docker_img
        upload_path = job_config[c.KEY_ARTIFACT_PATH]
        commands = job_config[c.JOB_SUBKEY_SCRIPTS]

        # Prepare return
        job_log_info = copy.deepcopy(job_config)
        job_log_info[c.REPORT_KEY_JOBNAME] = job_name
        job_log_info[c.REPORT_KEY_START] = time.asctime()
        job_log = JobLog.model_validate(job_log_info)
        output = ""
        try:
            container = self.client.containers.run(
                    image=docker_img,
                    name=container_name,
                    command=f"sh -c '{' && '.join(commands)}'",
                    detach=True,
                    volumes={
                        self.vol_name:{
                            'bind': DEFAULT_DOCKER_DIR,
                            'mode': 'rw'
                        }
                    },
                    working_dir=DEFAULT_DOCKER_DIR
                )

            # Wait for the container to finish, required as we are running in detach mode
            container.wait()

            # Retrieve the output from logs, default options will contain both
            # stdout and stderr, we want to also check the stderr
            output = container.logs().decode('utf-8')
            output_stderr = container.logs(stdout=False).decode('utf-8')

            # Note docker container will store some status log in stderr, currently
            # only way to check if error in execution is to look for the keyword
            # using the custom _check_status_from_log function
            job_success = False
            if self._check_status_from_log(output_stderr):
                job_success = True

            if c.JOB_SUBKEY_ARTIFACT in job_config:
                upload_config = job_config[c.JOB_SUBKEY_ARTIFACT]
                if job_success or not upload_config[c.ARTIFACT_SUBKEY_ONSUCCESS]:
                    indicator, msg = self._upload_artifact(container,
                                                        upload_path,
                                                        upload_config[c.ARTIFACT_SUBKEY_PATH]
                                                        )
                    job_success = job_success and indicator
                    output += msg
            if job_success:
                job_log.job_status = c.STATUS_SUCCESS
            # Clean up container
            container.remove()
        except docker.errors.DockerException as de:
            # If caught DockerException
            self.logger.warning(f"Job run fail for {job_name}, exception is {de}")
        # Add completion time and log to job_log
        job_log.completion_time = time.asctime()
        job_log.job_logs = output

        return job_log

    def _check_status_from_log(self, stderr:str)->bool:
        """ Check the stderr for job status

        Args:
            stderr (str): error log extracted from containers

        Returns:
            bool: indicator if job success or failure
        """
        # Look for sh exit status from the log
        # any sh: <number>: with number != 0 is error
        shell_results = re.finditer(REGEX_SHELL_ERR, stderr)
        for match in shell_results:
            if int(match.group(2)) != 0:
                return False
        return True

    def _upload_artifact(self,
                         container:Container,
                         upload_path:str,
                         extract_paths:list[str]) -> tuple[bool,str]:
        """ Move the artifacts from container to target upload path

        Args:
            container (Container): docker container object
            upload_path (str): target upload_path, can be absolute or relative
            extract_paths (list[str]): List of paths to extract artifact

        Returns:
            tuple[bool,str]: tuple of boolean indicator if upload success and 
            a str for potential error message
        """
        try:
            # First extract the contents in extract_paths from the docker
            for path in extract_paths:
                bits, _ = container.get_archive(f"{DEFAULT_DOCKER_DIR}/{path}")
                # Write the archive to the host filesystem
                upload_path_obj = Path(upload_path)
                if not upload_path_obj.is_dir():
                    parent_path = Path.cwd()
                    #print(parent_path)
                    upload_path_obj = parent_path.joinpath(upload_path_obj)
                    #print(upload_path_obj)
                    # recursively make dir for parents if not exist
                    upload_path_obj.mkdir(parents=True)
                with open(f"{upload_path}/volume_contents.tar", "wb") as f:
                    for chunk in bits:
                        f.write(chunk)
                # Extract the contents of the archive
                with tarfile.open(f"{upload_path}/volume_contents.tar", "r") as tar:
                    tar.extractall(path=upload_path)
                os.remove(f"{upload_path}/volume_contents.tar")

            # Try upload to s3
            status, err = self._upload_to_s3(container.name, upload_path)
            return status, err
        except (docker.errors.DockerException, FileNotFoundError, AttributeError) as de:
            return False, str(de)

    def _upload_to_s3(self, file_name:str, upload_path:str) -> tuple[bool,str]:
        """ Zip the artifacts in upload_path and upload into s3

        Args:
            file_name (str): file name to save in s3
            upload_path (str): target upload_path to zip

        Returns:
            tuple[bool,str]: tuple of boolean indicator if upload success and 
            a str for potential error message
        """
        error_msg = f"Fail to upload to s3 for {file_name}"
        try:
            s3_client = S3Client(bucket_name=upload_path)
            archive_name = make_archive(file_name, 'zip', root_dir=upload_path)
            s3_client.upload_file(archive_name)
            os.remove(archive_name)
            return True, ""
        except (ClientError, OSError) as e:
            self.logger.warning(str(e))
            error_msg += f"\nReason: {e}"
            return False, error_msg

    def stop_job(self, job_name: str) -> str:
        """ stop a job

        Args:
            job_name (str): name of the job
        Returns:
            str: latest container logs
        """
        # Reconstruct container name
        container_name = self.vol_name + '-' + job_name
        container = self.client.containers.get(container_name)
        container.stop()
        container.wait()
        output = container.logs().decode('utf-8')
        return output

    def remove_vol(self) -> bool:
        """ Remove the volume associated 

        Returns:
            bool: if removal is successful
        """
        if not self.docker_vol:
            return True
        try:
            self.docker_vol.remove()
            self.docker_vol = None
            return True
        except docker.errors.APIError as ae:
            error_msg = f"failed to remove volume for {self.vol_name}"
            error_msg += f"exception is {ae}"
            self.logger.warning(error_msg)
            return False
