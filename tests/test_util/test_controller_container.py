""" test the controller integration with container
"""
import os
import copy
import unittest
from unittest.mock import patch
import json
from docker.errors import DockerException
import util.constant as c
from controller.controller import Controller
from util.model import (SessionDetail, PipelineConfig, ValidationResult)
from util.db_mongo import MongoAdapter
from util.yaml_parser import YamlParser
from util.config_tools import ConfigChecker
from util.container import (DockerManager)
from util.common_utils import (get_logger)

logger = get_logger("tests.test_util.test_controller_container")

parser = YamlParser()
def load_pipeline() -> ValidationResult:
    pipeline_file_path = os.path.join(os.path.dirname(__file__), 'test_data/test_run/pipelines.yml')
    extracted = parser.parse_yaml_file(pipeline_file_path)
    
    checker = ConfigChecker()
    result = checker.validate_config("cicd_pipeline", extracted, "pipelines.yml", error_lc=True)
    result_dict = result.model_dump(by_alias=True)
    return result

# def insert_pipeline_config():
#     mongo_adapter = MongoAdapter()
#     sample_repo_path = os.path.join(os.path.dirname(__file__), 'test_data/test_run/sample_repo.json')
#     with open(sample_repo_path, 'r') as openfile:
#        sample_repo_data = json.load(openfile)
#     mongo_adapter.insert_repo_pipelines(sample_repo_data)

# def actual_pipeline_run():
#     controller = Controller()
#     sample_session = {
#             c.FIELD_USER_ID:"random",
#             c.FIELD_REPO_NAME: "cicd-python",
#             c.FIELD_REPO_URL: "https://github.com/sjchin88/cicd-python",
#             c.FIELD_BRANCH: c.DEFAULT_BRANCH,
#             c.FIELD_COMMIT_HASH: "random",
#             c.FIELD_IS_REMOTE: True, 
#         }
#     repo_data = SessionDetail.model_validate(sample_session)
#     pipeline_config = PipelineConfig.model_validate(load_pipeline()[c.KEY_PIPE_CONFIG])
#     controller._actual_pipeline_run(repo_data, pipeline_config)

# Preparing data for mock return
pipeline_config = load_pipeline().pipeline_config
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

    def get_archive(self, *args, **kwargs):
        """ Mock the get_archive method

        Raises:
            DockerException: _description_

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
        
class TestRunJob(unittest.TestCase):
    """ Class to test the Controller._actual_pipeline_run() and 
    container method 

    Args:
        unittest.TestCase (class): base class
    """
    def setUp(self):
        self.sample_session = {
            c.FIELD_USER_ID:"random",
            c.FIELD_REPO_NAME: "cicd-python",
            c.FIELD_REPO_URL: "https://github.com/sjchin88/cicd-python",
            c.FIELD_BRANCH: c.DEFAULT_BRANCH,
            c.FIELD_COMMIT_HASH: "random",
            c.FIELD_IS_REMOTE: True,
        }
        self.pipeline_config = load_pipeline().pipeline_config
        self.mock_running_pipeline_history = {
            c.FIELD_PIPELINE_NAME: "sample_pipeline",
            c.FIELD_PIPELINE_FILE_NAME: "sample_pipeline.yml",
            c.FIELD_LAST_COMMIT_HASH: "random",
            c.FIELD_PIPELINE_CONFIG:pipeline_config,
            c.FIELD_RUNNING: True
        }

    @patch("controller.controller.MongoAdapter.get_pipeline_history")
    def test_actual_pipeline_run_no_pipeline_history(self, mock_get):
        """ Test the case where no pipeline history return

        Args:
            mock_get (MagicMock): mock the get_pipeline_history method
        """
        mock_get.return_value = None
        controller = Controller()
        repo_data = SessionDetail.model_validate(self.sample_session)
        pipeline_config = PipelineConfig.model_validate(self.pipeline_config)
        status, _ = controller._actual_pipeline_run(repo_data, pipeline_config, True)
        assert status == False

    @patch("controller.controller.MongoAdapter.get_pipeline_history")
    def test_actual_pipeline_run_already_running(self, mock_get):
        """ Test the case where pipeline is already running

        Args:
            mock_get (MagicMock): mock the get_pipeline_history method
        """
        mock_get.return_value = self.mock_running_pipeline_history
        controller = Controller()
        repo_data = SessionDetail.model_validate(self.sample_session)
        pipeline_config = PipelineConfig.model_validate(self.pipeline_config)
        status, _ = controller._actual_pipeline_run(repo_data, pipeline_config)
        assert status == False

    @patch("controller.controller.MongoAdapter.update_job")
    @patch("controller.controller.MongoAdapter.update_job_logs")
    @patch("controller.controller.DockerManager._upload_artifact")
    @patch("controller.controller.DockerManager", return_value=DockerManager(client=MockDockerApi(success=False)))
    @patch("controller.controller.MongoAdapter.update_pipeline_info", return_value=True)
    @patch("controller.controller.MongoAdapter.insert_job", return_value=123)
    @patch("controller.controller.MongoAdapter.get_pipeline_history")
    def test_actual_pipeline_run_fail_job(
            self,
            mock_get_pl_history,
            mock_insert_job,
            mock_update_pl_info,
            mock_docker_manager,
            mock_upload_artifact,
            mock_update_job_logs,
            mock_update_job,
        ):
        """ Test the case where running job but failed due to upload_artifact

        Args:
            mock_get_pl_history (MagicMock): mock get_pipeline_history
            mock_insert_job (MagicMock): mock the insert_job
            mock_update_pl_info (MagicMock): mock update_pipeline_info
            mock_docker_manager (MagicMock): mock DockerManager constructor
            mock_upload_artifact (MagicMock): mock _upload_artifact method
            mock_update_job_logs (MagicMock): mock update_job_logs method
            mock_update_job (MagicMock): mock_update_job method
        """
        mock_history = copy.deepcopy(self.mock_running_pipeline_history)
        mock_history[c.FIELD_RUNNING] = False
        mock_get_pl_history.return_value = mock_history
        mock_upload_artifact.return_value = False, "error"
        controller = Controller()
        repo_data = SessionDetail.model_validate(self.sample_session)
        pipeline_config = PipelineConfig.model_validate(self.pipeline_config)
        pipeline_status, _ = controller._actual_pipeline_run(repo_data, pipeline_config)
        assert pipeline_status == False

    @patch("controller.controller.MongoAdapter.update_job")
    @patch("controller.controller.MongoAdapter.update_job_logs")
    @patch("util.container.DockerManager.run_job", side_effect=KeyboardInterrupt)
    @patch("controller.controller.DockerManager", return_value=DockerManager(client=MockDockerApi()))
    @patch("controller.controller.MongoAdapter.update_pipeline_info", return_value=True)
    @patch("controller.controller.MongoAdapter.insert_job", return_value=123)
    @patch("controller.controller.MongoAdapter.get_pipeline_history")
    def test_actual_pipeline_run_Keyboard_Interrupt(
            self,
            mock_get_pl_history,
            mock_insert_job,
            mock_update_pl_info,
            mock_docker_manager,
            mock_run,
            mock_update_job_logs,
            mock_update_job,
        ):
        """ Test the case where running job but interrupted when running job

        Args:
            mock_get_pl_history (MagicMock): mock get_pipeline_history
            mock_insert_job (MagicMock): mock the insert_job
            mock_update_pl_info (MagicMock): mock update_pipeline_info
            mock_docker_manager (MagicMock): mock DockerManager constructor
            mock_run (MagicMock): mock DockerManager.run_job, will throw KeyboardInterrupt
            mock_update_job_logs (MagicMock): mock update_job_logs method
            mock_update_job (MagicMock): mock_update_job method
        """
        try:
            mock_history = copy.deepcopy(self.mock_running_pipeline_history)
            mock_history[c.FIELD_RUNNING] = False
            mock_get_pl_history.return_value = mock_history
            #mock_upload_artifact.side_effect = KeyboardInterrupt
            controller = Controller()
            repo_data = SessionDetail.model_validate(self.sample_session)
            pipeline_config = PipelineConfig.model_validate(self.pipeline_config)
            pipeline_status, _ = controller._actual_pipeline_run(repo_data, pipeline_config)
            assert False
        except KeyboardInterrupt:
            assert True