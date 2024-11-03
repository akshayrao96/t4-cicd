""" test the ContainerManager and all subclass
"""
import util.constant as c 
from util.container import (DockerManager)

TEST_LOG = "success"

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

class MockContainersApi:
    '''A fake Docker API with containers calls.'''
    def run(self, *args, **kwargs):
        return MockContainer(*args, **kwargs)

class MockVolumesApi:
    '''A fake Docker API with volumes calls.'''
    def create(self, *args, **kwargs):
        return "volume created"
    
class MockDockerApi:
    '''A fake Docker API.'''
    def __init__(self):
        self.containers = MockContainersApi()
        self.volumes = MockVolumesApi()

def test_docker_manager_run_job():
    """ test run_job method of docker manager using MockDockerApi"""
    docker_manager = DockerManager(client=MockDockerApi())
    sample_job_config = {
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
    test_job_name = "sample_job"
    job_log = docker_manager.run_job(test_job_name, sample_job_config)
    assert job_log[c.REPORT_KEY_JOBNAME] == test_job_name
    assert job_log[c.REPORT_KEY_JOBLOG] == TEST_LOG
    assert job_log[c.REPORT_KEY_JOBSTATUS] == c.STATUS_SUCCESS
    
    
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
#                               'git clone https://github.com/sjchin88/cicd-python'
#                               'ls -la',
#                               ],
#     }
#     job_log = docker_manager.run_job("sample_job", sample_job_config)
#     print(job_log)
# test_run_job_docker()