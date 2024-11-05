""" test the ContainerManager and all subclass
"""
import copy
import unittest
from unittest.mock import MagicMock, patch
from docker.errors import DockerException
import util.constant as c
from util.container import (DockerManager)
from util.common_utils import (get_logger)
from util.model import (JobLog)

logger = get_logger("tests.test_util.test_container")

TEST_LOG = "success"
TEST_LOG_ERROR = "error"


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
        stderr = "fatal"
        docker_manager = DockerManager(client=MockDockerApi())
        assert docker_manager._check_status_from_log(stderr) == False
        stderr = "error"
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
    
    def test_stop_container(self):
        docker_manager = DockerManager(client=MockDockerApi())
        docker_manager.stop_job("sample_job")
        assert True
""" with more set up of python image file
    
def test_run_job_docker():
    docker_manager = DockerManager()
    sample_job_config = {
        c.JOB_SUBKEY_STAGE: 'stage',
        c.JOB_SUBKEY_ALLOW: True,
        c.JOB_SUBKEY_NEEDS: [],
        c.KEY_DOCKER:{
            c.KEY_DOCKER_REG: 'dockerhub',
            c.KEY_DOCKER_IMG: "python:3.12-slim"
        },
        c.KEY_ARTIFACT_PATH: 'path',
        c.JOB_SUBKEY_SCRIPTS:[
                              'apt update',
                              'apt-get install -y git',
                              'pip install poetry',
                              'cd app',
                              'ls -la',
                              ],
    }
    docker_manager.run_job("sample_job", sample_job_config)
"""

# Test run with preset python-git-poetry image
# def test_run_job_docker():
#     docker_manager = DockerManager()
#     sample_job_config = {
#         c.JOB_SUBKEY_STAGE: 'stage',
#         c.JOB_SUBKEY_ALLOW: True,
#         c.JOB_SUBKEY_NEEDS: [],
#         c.KEY_DOCKER:{
#             c.KEY_DOCKER_REG: 'dockerhub',
#             c.KEY_DOCKER_IMG: "sjchin88/python-git-poetry:latest"
#         },
#         c.KEY_ARTIFACT_PATH: 'path',
#         c.JOB_SUBKEY_SCRIPTS:[
#                               'git clone https://github.com/sjchin88/cicd-python',
#                               'ls -la',
#                               ],
#     }
#     job_log = docker_manager.run_job("sample_job", sample_job_config)
#     print(job_log)
# test_run_job_docker()

# Test run with preset python-git-poetry image and upload path
# def test_run_job_docker():
#     docker_manager = DockerManager()
#     sample_job_config = {
#         c.JOB_SUBKEY_STAGE: 'stage',
#         c.JOB_SUBKEY_ALLOW: True,
#         c.JOB_SUBKEY_NEEDS: [],
#         c.KEY_DOCKER:{
#             c.KEY_DOCKER_REG: 'dockerhub',
#             c.KEY_DOCKER_IMG: "sjchin88/python-git-poetry:latest"
#         },
#         c.KEY_ARTIFACT_PATH: 'D:/OneDrive/DevOps/PlayGround/yaml/test_upload',
#         c.JOB_SUBKEY_SCRIPTS:[
#                               'git clone https://github.com/sjchin88/cicd-python',
#                               'ls -la',
#                               #'sleep 500' # Uncomment this line for stop testing
#                               ],
#         c.JOB_SUBKEY_ARTIFACT:{
#             c.ARTIFACT_SUBKEY_ONSUCCESS:False,
#             c.ARTIFACT_SUBKEY_PATH:[
#                 'cicd-python/src','cicd-python/tests'
#             ]
#         }
#     }
#     job_log = docker_manager.run_job("sample_job", sample_job_config)
#     print(job_log)
# test_run_job_docker()
