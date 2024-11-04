""" docker module provide all class and method required to interact with docker engine
for execution of pipeline job
"""
from pathlib import Path
import copy
import os
import tarfile
import time
from abc import ABC, abstractmethod
import docker
import docker.errors
from docker.models.containers import Container
import util.constant as c
from util.common_utils import (get_logger)
from util.model import (JobConfig, JobLog)

# pylint: disable=fixme
logger = get_logger("util.docker")

DEFAULT_DOCKER_DIR = '/app'

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

    def __init__(self, client:docker.DockerClient=docker.from_env(),
                 log_tool=logger, repo:str="Repo", pipeline:str="pipeline", run:str="run"):
        """ Initialize the DockerManager

        Args:
            client (docker.DockerClient, optional): client for the DockerEngine. 
                Defaults to docker.from_env().
            log_tool (_type_, optional): logging tool. Defaults to logger.
            repo (str, optional): repo name, use to uniquely identify the volume used. 
                Defaults to "Repo".
            pipeline (str, optional): pipeline name, use to uniquely identify the volume used. 
                Defaults to "pipeline".
            run (str, optional): run, use to uniquely identify the volume used. Defaults to "run".
        """
        self.client = client
        self.logger = log_tool
        self.vol_name = repo + '-' + pipeline + '-' + run
        self.docker_vol = None

    def run_job(self, job_name:str, job_config: dict) -> dict:
        """ run a single job and return its output

        Args:
            job_name (str): name of the job
            job_config (dict): a complete job configuration. with information
                defined in design_doc_config: jobs section, single job

        Returns:
            dict: records of a job run, as specified in designdoc_data_scheme:job. 
            will contain {
                    job_name
                    job_status
                    allows_failure
                    start_time
                    completion_time
                    logs & error output
                }
        """
        # Validate input data
        JobConfig.model_validate(job_config)
        # create the vol for the first time
        if self.docker_vol is None:
            self.docker_vol = self.client.volumes.create(self.vol_name)

        # Extract important values
        container_name = self.vol_name + '-' + job_name
        # TODO - test different docker_reg
        docker_reg = job_config[c.KEY_DOCKER][c.KEY_DOCKER_REG]
        docker_img = job_config[c.KEY_DOCKER][c.KEY_DOCKER_IMG]
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
                    }
                )
            # container.exec_run(
            #     cmd=f"sh -c '{' && '.join(commands)}'",
            #     detach=True,
            # )

            # Wait for the container to finish, required as we are running in detach mode
            container.wait()

            # Retrieve the output from logs, default options will contain both
            # stdout and stderr, we want to also check the stderr
            output = container.logs().decode('utf-8')
            output_stderr = container.logs(stdout=False).decode('utf-8')
            print(output)
            print(f"err:{output_stderr}")

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

        return job_log.model_dump()

    def _check_status_from_log(self, stderr:str)->bool:
        """ Check the stderr for job status

        Args:
            stderr (str): error log extracted from containers

        Returns:
            bool: indicator if job success or failure
        """
        if "fatal" in stderr:
            return False
        if "error" in stderr:
            return False
        return True

    def _upload_artifact(self, container:Container,
                         upload_path:str, extract_paths:list[str]) -> tuple[bool,str]:
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
            for path in extract_paths:
                bits, stat = container.get_archive(f"{DEFAULT_DOCKER_DIR}/{path}")
                # Write the archive to the host filesystem
                upload_path_obj = Path(upload_path)
                if not upload_path_obj.is_dir():
                    parent_path = Path.cwd()
                    print(parent_path)
                    upload_path_obj = parent_path.joinpath(upload_path_obj)
                    print(upload_path_obj)
                    upload_path_obj.mkdir()
                with open(f"{upload_path}/volume_contents.tar", "wb") as f:
                    for chunk in bits:
                        f.write(chunk)
                # Extract the contents of the archive
                with tarfile.open(f"{upload_path}/volume_contents.tar", "r") as tar:
                    tar.extractall(path=upload_path)
                os.remove(f"{upload_path}/volume_contents.tar")
            return True, ""
        except (docker.errors.DockerException, FileNotFoundError) as de:
            return False, str(de)

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
