""" test the ContainerManager and all subclass
"""
import copy
import unittest
from unittest.mock import patch
from botocore.exceptions import ClientError
from docker.errors import DockerException
import util.constant as c
from util.container import (DockerManager)
from util.common_utils import (get_logger)

logger = get_logger("tests.test_util.test_container")

TEST_LOG = "success"
TEST_LOG_ERROR = "sh: 1: git: not found"


class MockContainer:
    '''A fake Docker API container object.'''
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def wait(self) -> None:
        """ Mock the container.wait() method
        """

    def logs(self, *args, **kwargs) -> bytes:
        """ Mock the container.wait() method
        return a fake logs message

        Returns:
            bytes: bytes representation of logs
        """
        return bytes(TEST_LOG, encoding='utf-8')

    def remove(self) -> None:
        """ Mock the container.remove method

        Returns:
            _type_: _description_
        """

    def stop(self) -> None:
        """ Mock the container.stop method

        Returns:
            _type_: _description_
        """

    def get_archive(self, *args, **kwargs):
        """ Mock the get_archive method

        Raises:
            DockerException: _description_

        Returns:
            _type_: _description_
        """
        return "", ""

class MockFailContainer(MockContainer):
    def logs(self, *args, **kwargs) -> bytes:
        """ Mock the container.wait() method
        return a fake logs message

        Returns:
            bytes: bytes representation of logs
        """
        return bytes(TEST_LOG_ERROR, encoding='utf-8')

    def get_archive(self, *args, **kwargs):
        """ Mock the get_archive method

        Raises:
            DockerException: _description_

        Returns:
            _type_: _description_
        """
        raise DockerException()

class MockContainersApi:
    '''A fake Docker API with containers calls.'''
    def __init__(self, success:bool=True, throw:bool=False):
        """ If success=False will return a container with fail run 
        message"""
        if success:
            self.container = MockContainer
        else:
            self.container = MockFailContainer
        self.throw = throw

    def run(self, *args, **kwargs):
        if self.throw:
            raise DockerException()
        return self.container(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.container(*args, **kwargs)

class MockVolume:
    """ Fake Docker Volume"""
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def remove(self):
        return True

class MockVolumesApi:
    '''A fake Docker API with volumes calls.'''
    def __init__(self):
        self.volume = MockVolume
    def create(self, *args, **kwargs):
        return self.volume(*args, **kwargs)

class MockDockerApi:
    '''A fake Docker API.'''
    def __init__(self, success:bool=True, throw:bool=False):
        """ Constructor, customize behaviour base on success & throw flag
        
        Args:
            success (bool, optional): If success=False will return a ContainerApi 
                with fail run message. Defaults to True.
            throw (bool, optional): If throw=True, will return a ContainerApi
                that throw DockerException everytime run is called. Defaults to False.
        """
        self.containers = MockContainersApi(success, throw)
        self.volumes = MockVolumesApi()

class TestDockerManager(unittest.TestCase):
    """ Test suite for the container

    Args:
        unittest.TestCase (class): base class
    """
    def setUp(self):
        self.sample_job_config = {
            c.JOB_SUBKEY_STAGE: 'stage',
            c.JOB_SUBKEY_ALLOW: True,
            c.JOB_SUBKEY_NEEDS: [],
            c.KEY_DOCKER:{
                c.KEY_DOCKER_REG: 'dockerhub',
                c.KEY_DOCKER_IMG: "sjchin88/python-git-poetry:latest"
            },
            c.KEY_ARTIFACT_PATH: 'path',
            c.JOB_SUBKEY_SCRIPTS:[
                                'git clone https://github.com/sjchin88/cicd-python',
                                'ls -la',
                                ],
        }

    def test_docker_manager_run_job(self):
        """ test run_job method of docker manager using MockDockerApi"""
        docker_manager = DockerManager(client=MockDockerApi())
        test_job_name = "sample_job"
        job_log = docker_manager.run_job(test_job_name, self.sample_job_config)
        job_log = job_log.model_dump()
        assert job_log[c.REPORT_KEY_JOBNAME] == test_job_name
        assert job_log[c.REPORT_KEY_JOBLOG] == TEST_LOG
        assert job_log[c.REPORT_KEY_JOBSTATUS] == c.STATUS_SUCCESS

    def test_docker_manager_run_job_failwithincontainer(self):
        """ test run_job method of docker manager using for case where 
        job fail inside the container
        """
        docker_manager = DockerManager(client=MockDockerApi(success=False))
        test_job_name = "sample_job"
        job_log = docker_manager.run_job(test_job_name, self.sample_job_config)
        job_log = job_log.model_dump()
        assert job_log[c.REPORT_KEY_JOBNAME] == test_job_name
        assert job_log[c.REPORT_KEY_JOBLOG] == TEST_LOG_ERROR
        assert job_log[c.REPORT_KEY_JOBSTATUS] == c.STATUS_FAILED

    def test_docker_manager_run_job_failwithdockerAPI(self):
        docker_manager = DockerManager(client=MockDockerApi(throw=True))
        test_job_name = "sample_job"
        job_log = docker_manager.run_job(test_job_name, self.sample_job_config)
        job_log = job_log.model_dump()
        assert job_log[c.REPORT_KEY_JOBNAME] == test_job_name
        assert job_log[c.REPORT_KEY_JOBSTATUS] == c.STATUS_FAILED

    @patch("util.container.DockerManager._upload_artifact", return_value=(False, "error"))
    def test_docker_manager_run_job_withfail_artifact(self, mock_upload):
        docker_manager = DockerManager(client=MockDockerApi())
        test_job_name = "sample_job"
        job_config_with_upload = copy.deepcopy(self.sample_job_config)
        job_config_with_upload[c.JOB_SUBKEY_ARTIFACT] = {
            c.ARTIFACT_SUBKEY_ONSUCCESS:True, 
            c.ARTIFACT_SUBKEY_PATH:['cicd-python']
        }
        job_log = docker_manager.run_job(test_job_name, job_config_with_upload)
        job_log = job_log.model_dump()
        assert job_log[c.REPORT_KEY_JOBSTATUS] == c.STATUS_FAILED

    def test_check_status_from_log(self):
        """ test the check_status from log
        """
        docker_manager = DockerManager(client=MockDockerApi())
        stderr = "sh: 1: poetry: not found"
        assert docker_manager._check_status_from_log(stderr) == False
        stderr = "sh: 0:"
        assert docker_manager._check_status_from_log(stderr) == True
        stderr = "sh: 0: \n sh: 1:"
        assert docker_manager._check_status_from_log(stderr) == False

    def test_upload_artifact_fail(self):
        """ test exception catching of _upload_artifact method
        """
        # Note the job will fail due to error log return, but as we set artifact[on_success_only]
        # to False, the upload artifact method will be called, which will throw the Exception when 
        # calling get_archive method of our container
        docker_manager = DockerManager(client=MockDockerApi(success=False))
        test_job_name = "sample_job"
        job_config_with_upload = copy.deepcopy(self.sample_job_config)
        job_config_with_upload[c.JOB_SUBKEY_ARTIFACT] = {
            c.ARTIFACT_SUBKEY_ONSUCCESS:False,
            c.ARTIFACT_SUBKEY_PATH:['cicd-python']
        }
        job_log = docker_manager.run_job(test_job_name, job_config_with_upload)
        job_log = job_log.model_dump()
        assert job_log[c.REPORT_KEY_JOBSTATUS] == c.STATUS_FAILED

    @patch("util.container.S3Client")
    @patch("util.container.os.remove")
    @patch("util.container.tarfile.open")
    @patch("util.container.open")
    @patch("util.container.Path")
    def test_upload_artifact_fail_s3(self, mock_path, mock_open, mock_tar, mock_os, mock_client):
        """ Test the exception handling and status return when upload to s3 fail

        Args:
            mock_path (MagicMock): mock path object and all required method
            mock_open (MagicMock): mock the open method
            mock_tar (MagicMock): mock tarfile.open method
            mock_os (MagicMock): mock the os.remove method
            mock_client (MagicMock): mock the s3Client
        """
        mock_path_obj = mock_path.return_value
        mock_path_obj.is_dir.return_value = False
        mock_path_obj.cwd.return_value = ""
        mock_path_obj.joinpath.return_value = ""
        mock_path_obj.mkdir.return_value = ""
        mock_open_obj = mock_open.return_value
        mock_open_obj.write.return_value = ""
        mock_tar_obj = mock_tar.return_value
        mock_tar_obj.extractall.return_value = ""
        mock_client.side_effect = ClientError(
            error_response={
                'Error':{
                    'Code':'Any'
                }
            },
            operation_name='create_bucket'
        )
        docker_manager = DockerManager(client=MockDockerApi())
        test_job_name = "sample_job"
        job_config_with_upload = copy.deepcopy(self.sample_job_config)
        job_config_with_upload[c.JOB_SUBKEY_ARTIFACT] = {
            c.ARTIFACT_SUBKEY_ONSUCCESS:False,
            c.ARTIFACT_SUBKEY_PATH:['cicd-python']
        }
        job_log = docker_manager.run_job(test_job_name, job_config_with_upload)
        job_log = job_log.model_dump()
        assert job_log[c.REPORT_KEY_JOBSTATUS] == c.STATUS_FAILED

    def test_stop_container(self):
        docker_manager = DockerManager(client=MockDockerApi())
        docker_manager.stop_job("sample_job")
        assert True
