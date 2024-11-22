""" Test cid pipeline command
"""
import json
import os
import pytest
from click.testing import CliRunner
from cli import (__main__, cmd_pipeline)
from docker.errors import DockerException
from pydantic import ValidationError
from unittest import TestCase
from unittest.mock import MagicMock, patch
from bson import ObjectId
from util.model import (PipelineConfig, SessionDetail, ValidationResult, PipelineHist)
from util.common_utils import get_logger

def test_cid():
    """ Test the main cid command just by calling it with --help option
    """
    runner = CliRunner()
    result = runner.invoke(__main__.cid, '--help')
    # 0 exit code mean successful
    assert result.exit_code == 0


def test_pipeline_help():
    """ Test the main pipeline command just by calling it with --help option
    """
    runner = CliRunner()
    result = runner.invoke(cmd_pipeline.pipeline, '--help')
    # 0 exit code mean successful
    assert result.exit_code == 0

class TestPipelineRun(TestCase):
    """ Test class to perform integration test between the cli cmd 
    cid pipeline run and corresponding controller method of 
    run_pipeline(). The downstream method will be patched whenever 
    necessary

    Args:
        TestCase (class): base class
    """
    def setUp(self):
        self.runner = CliRunner()
        self.logger = get_logger("tests.test_cli.test_cmd_pipeline.TestPipelineRun")
        
        # Load sample validation result from json file
        validation_result_path = os.path.join(os.path.dirname(__file__),'sample_validation_res.json')
        with open(validation_result_path, 'r', encoding='utf-8') as openfile:
            # Reading from json file
            validation_result_dict = json.load(openfile)
        self.session_data = SessionDetail(
            user_id='random',
            repo_name='cicd-python',
            repo_url="https://github.com/sjchin88/cicd-python",
            branch='main',
            is_remote=True,
            commit_hash="abcdef"
        )
        self.fail_validation = ValidationResult(valid=False, error_msg="", pipeline_config={})
        self.success_validation_res = ValidationResult.model_validate(validation_result_dict)
        pipeline_config_dict = self.success_validation_res.pipeline_config
        self.success_validation_res.pipeline_config = PipelineConfig.model_validate(pipeline_config_dict)
        self.mock_pipeline_config = pipeline_config_dict
        #self.logger.debug(self.success_validation_res)
        
    #Test input check logics
    def test_both_pipeline_name_file_path(self):
        """test if --file and --pipeline are passed as arguments. it should return error
        as it can't be both.
        """
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run', '--pipeline', 'valid_pipeline_default',
                                                    '--file', '.cicd-pipelines/pipelines.yml'])
        # Common exit code for invalid argument is 2
        assert result.exit_code == 2
        assert result.output.rstrip() == "cid: invalid flag. you can only pass --file or --pipeline and can't be both."
    
    def test_invalid_override(self):
        """ test if error correctly caught when invalid override value is passed on
        """
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run', '--override', 'no_value_key'])
        assert result.exit_code == 2
    
    @patch("controller.controller.Controller.handle_repo")
    def test_error_handling_repo(self, mock_handle):
        """ test if exit correctly when handling repo return false
        Args:
            mock_handle (MagicMock): mock the Controller.handle_repo function
        """
        mock_handle.return_value = (False, "error", None)
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run'])
        assert result.exit_code == 2
    
    @patch("controller.controller.YamlParser.parse_yaml_by_pipeline_name", side_effect=FileNotFoundError())
    @patch("controller.controller.Controller.handle_repo")
    def test_fail_yaml_parsing_from_pipeline_name(self, mock_handle, mock_parse):
        """ test the case when attempting to parse pipeline config based on pipeline_name but fail
        
        Args:
            mock_handle (MagicMock): mock the Controller.handle_repo function
            mock_parse (MagicMock): mock the parse_yaml_by_pipeline_name function
        """
        mock_handle.return_value = (True, "", self.session_data)
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run', '--pipeline', 'no_value_key'])
        assert result.exit_code == 1
    
    @patch("controller.controller.YamlParser.parse_yaml_file", side_effect=FileNotFoundError())
    @patch("controller.controller.Controller.handle_repo")
    def test_fail_yaml_parsing_from_file_path(self, mock_handle, mock_parse):
        """ test the case when attempting to parse pipeline config based on file_path but fail
        
        Args:
            mock_handle (MagicMock): mock the Controller.handle_repo function
            mock_parse (MagicMock): mock the parse_yaml_file function
        """
        mock_handle.return_value = (True, "", self.session_data)
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run'])
        assert result.exit_code == 1
    
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.YamlParser.parse_yaml_file")
    @patch("controller.controller.Controller.handle_repo")
    def test_fail_validation(self, mock_handle, mock_parse, mock_validate):
        """ Test the case where the run_pipeline execution reach the validation stage
        but fail

        Args:
            mock_handle (MagicMock): mock the Controller.handle_repo function
            mock_validate (MagicMock): mock the validate_config function
            mock_parse (MagicMock): mock the parse_yaml_file function
        """
        mock_handle.return_value = (True, "", self.session_data)
        mock_parse.return_value = self.mock_pipeline_config
        mock_validate.return_value = self.fail_validation
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run'])
        assert result.exit_code == 1
            
    @patch("controller.controller.Controller.dry_run")
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.YamlParser.parse_yaml_file")
    @patch("controller.controller.Controller.handle_repo")
    def test_fail_dry_run(self, mock_handle, mock_parse, mock_validate, mock_dry_run):
        """ Test the case where the run_pipeline execution reach the dry run stage
        but fail

        Args:
            mock_handle (MagicMock): mock the Controller.handle_repo function
            mock_parse (MagicMock): mock the parse_yaml_file method
            mock_validate (MagicMock): mock the validate_config method
            mock_dry_run(MagicMock): mock the dry_run method 
        """
        mock_handle.return_value = (True, "", self.session_data)
        mock_parse.return_value = self.mock_pipeline_config
        mock_validate.return_value = self.success_validation_res
        mock_dry_run.return_value = (False, "")
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run', '--dry-run'])
        assert result.exit_code == 1
    
    @patch("controller.controller.MongoAdapter.update_pipeline_info")
    @patch("controller.controller.Controller.dry_run")
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.YamlParser.parse_yaml_file")
    @patch("controller.controller.Controller.handle_repo")
    def test_success_dry_run_with_mock(
        self, mock_handle, mock_parse, mock_validate, mock_dry_run, mock_update):
        """ Test the case where the run_pipeline execution reach the dry_run
        and success

        Args:
            mock_handle (MagicMock): mock the Controller.handle_repo function
            mock_parse (MagicMock): mock the parse_yaml_file method
            mock_validate (MagicMock): mock the validate_config method
            mock_dry_run (MagicMock): mock the dry_run method 
            mock_update (MagicMock): mock the MongoAdapter.update_pipeline_info
        """
        mock_handle.return_value = (True, "", self.session_data)
        mock_parse.return_value = self.mock_pipeline_config
        mock_validate.return_value = self.success_validation_res
        mock_dry_run.return_value = (True, "")
        mock_update.return_value = True
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run', '--dry-run'])
        assert result.exit_code == 0
    
    @patch("controller.controller.MongoAdapter.update_pipeline_info")
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.YamlParser.parse_yaml_file")
    @patch("controller.controller.Controller.handle_repo")
    def test_success_integrated_dry_run(self, mock_handle, mock_parse, mock_validate, mock_update):
        """ Test the case where the run_pipeline execution reach the dry_run
        and success, with integration test on dry run util class

        Args:
            mock_handle (MagicMock): mock the Controller.handle_repo function
            mock_parse (MagicMock): mock the parse_yaml_file method
            mock_validate (MagicMock): mock the validate_config method
            mock_update (MagicMock): mock the MongoAdapter.update_pipeline_info
        """
        mock_handle.return_value = (True, "", self.session_data)
        mock_parse.return_value = self.mock_pipeline_config
        mock_validate.return_value = self.success_validation_res
        mock_update.return_value = True
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run', '--dry-run','--yaml'])
        assert result.exit_code == 0

    @patch("controller.controller.Controller._actual_pipeline_run")
    @patch("controller.controller.os.getlogin", return_value='user')
    @patch("controller.controller.MongoAdapter.update_pipeline_info")
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.YamlParser.parse_yaml_file")
    @patch("controller.controller.Controller.handle_repo")
    def test_success_actual_run(
        self, mock_handle, mock_parse, mock_validate,mock_update,
        mock_getlogin, mock_actual_run):
        """ Test the case where the run_pipeline execution reach the 
        actual run and success

        Args:
            mock_handle (MagicMock): mock the Controller.handle_repo function
            mock_parse (MagicMock): mock the parse_yaml_file method
            mock_validate (MagicMock): mock the validate_config method
            mock_update (MagicMock): mock the MongoAdapter.update_pipeline_info
            mock_getlogin (MagicMock): mock the os.getlogin() method
            mock_actual_run(MagicMock): mock the actual_run method 
        """
        mock_handle.return_value = (True, "", self.session_data)
        mock_parse.return_value = self.mock_pipeline_config
        mock_validate.return_value = self.success_validation_res
        mock_update.return_value = True
        mock_actual_run.return_value = (True, "")
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run'])
        assert result.exit_code == 0

    @patch("controller.controller.Controller._actual_pipeline_run")
    @patch("controller.controller.os.getlogin", return_value='user')
    @patch("controller.controller.MongoAdapter.update_pipeline_info")
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.YamlParser.parse_yaml_file")
    @patch("controller.controller.Controller.handle_repo")
    def test_fail_actual_run(
        self, mock_handle, mock_parse, mock_validate,mock_update,
        mock_getlogin, mock_actual_run):
        """ Test the case where the run_pipeline execution reach the 
        actual run and fail

        Args:
            mock_handle (MagicMock): mock the Controller.handle_repo function
            mock_parse (MagicMock): mock the parse_yaml_file method
            mock_validate (MagicMock): mock the validate_config method
            mock_update (MagicMock): mock the MongoAdapter.update_pipeline_info
            mock_getlogin (MagicMock): mock the os.getlogin() method
            mock_actual_run(MagicMock): mock the actual_run method
        """
        mock_handle.return_value = (True, "", self.session_data)
        mock_parse.return_value = self.mock_pipeline_config
        mock_validate.return_value = self.success_validation_res
        mock_update.return_value = True
        mock_actual_run.return_value = (False, "")
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run'])
        assert result.exit_code == 1

        mock_actual_run.side_effect = ValidationError.from_exception_data("",[])
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run'])
        assert result.exit_code == 1
        
        mock_actual_run.side_effect = DockerException()
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run'])
        assert result.exit_code == 1

    # Integration test
    @patch("controller.controller.Controller._actual_pipeline_run")
    @patch("controller.controller.os.getlogin", return_value='user')
    @patch("controller.controller.MongoAdapter.update_pipeline_info")
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.YamlParser.parse_yaml_file")
    @patch("controller.controller.Controller.handle_repo")
    def test_success_actual_run_with_override(
        self, mock_handle, mock_parse, mock_validate,mock_update,
        mock_getlogin, mock_actual_run):
        """ Test the case where the run_pipeline execution reach the 
        actual run and success, with overrides apply

        Args:
            mock_handle (MagicMock): mock the Controller.handle_repo function
            mock_parse (MagicMock): mock the parse_yaml_file method
            mock_validate (MagicMock): mock the validate_config method
            mock_update (MagicMock): mock the MongoAdapter.update_pipeline_info
            mock_getlogin (MagicMock): mock the os.getlogin() method
            mock_actual_run(MagicMock): mock the actual_run method
        """
        mock_handle.return_value = (True, "", self.session_data)
        mock_parse.return_value = self.mock_pipeline_config
        mock_validate.return_value = self.success_validation_res
        mock_update.return_value=True
        mock_actual_run.return_value = (True, "")
        cmd_list = ['run', '--override', 'global.docker.image=gradle:jdk8']
        result = self.runner.invoke(cmd_pipeline.pipeline, cmd_list)
        assert result.exit_code == 0

def test_pipeline_log():
    """call pipeline log
    """
    runner = CliRunner()
    result = runner.invoke(cmd_pipeline.pipeline, ['log'])

    assert result.exit_code == 0

class TestPipelineHistory(TestCase):
    """Test class to handle `cid pipeline history` command that
    validates the cli and controller class for report history

    Args:
        TestCase (BaseClass): BaseClass
    """
    def setUp(self):
        self.runner = CliRunner()
        self.logger = get_logger("tests.test_cli.test_cmd_pipeline.TestPipelineHistory")

    @patch("controller.controller.MongoAdapter.get_pipeline_run_summary")
    def test_report_full_summary(self, mock_pipeline_summary):
        """L4.1 success test scenario that returns the whole pipeline history

        Args:
            mock_pipeline_summary (MagicMock): mock MongoAdapter.get_pipeline_run_summary func.
        """
        # pipeline_hist_dict = PipelineHist(
        #     repo_name='cicd-python',
        #     repo_url='https://github.com/sjchin88/cicd-python',
        #     pipeline_name=None,
        #     branch="main",
        #     stage=None,
        #     job=None,
        #     run=None,
        #     is_remote=False
        # )
        #success_validate_hist = PipelineHist.model_validate(pipeline_hist_dict)
        #mock_pipeline_history.return_value = (True, "all pipeline report")

        mock_pipeline_summary.return_value = [
          {'_id': ObjectId('673139d61c77e7e99afd88ce'), 'pipeline_name': 'cicd_pipeline',
          'run_number': 1, 'git_commit_hash': '16adc46', 'status': 'success',
          'start_time': 'Sun Nov 10 17:33:33 2024', 'completion_time':
          'Sun Nov 10 17:33:48 2024'}, 
          {'_id': ObjectId('673139d61c77e7e99afd88ce'),'pipeline_name': 'cicd_pipeline2',
          'run_number': 1, 'git_commit_hash': '16adc46', 'status': 'success',
          'start_time': 'Tue Nov 12 15:25:11 2024', 'completion_time': 'Tue Nov 12 15:25:26 2024'},
          {'_id': ObjectId('673139d61c77e7e99afd88ce'), 'pipeline_name': 'cicd_pipeline2',
           'run_number': 2, 'git_commit_hash': '16adc46', 'status': 'success', 'start_time':
           'Tue Nov 12 18:26:15 2024', 'completion_time': 'Tue Nov 12 18:26:30 2024'}]

        cmd_list = ['report', '--repo', 'https://github.com/sjchin88/cicd-python']
        result = self.runner.invoke(cmd_pipeline.pipeline, cmd_list)
        assert result.exit_code == 0

    @patch("controller.controller.MongoAdapter.get_pipeline_run_summary")
    def test_report_fail_invalid_pipeline_name(self, mock_pipeline_summary):
        """_summary_

        Args:
            mock_pipeline_summary (MagicMock): mock MongoAdapter.get_pipeline_run_summary func.
        """
        mock_pipeline_summary.return_value = []

        cmd_list = ['report', '--repo', 'https://github.com/sjchin88/cicd-python', '--pipeline',
                    'asdf']
        result = self.runner.invoke(cmd_pipeline.pipeline, cmd_list)

        assert result.exit_code == 1
        assert result.stdout.rstrip() == "invalid pipeline_name (--pipeline) or run_number \
(--run). Please try again"

    def test_report_no_stage_given(self):
        """fail if --job is specified but no --stage is given.
        """
        cmd_list = ['report', '--repo', 'https://github.com/sjchin88/cicd-python', '--pipeline',
                    'cicd_pipeline', '--job', 'checkout']
        result = self.runner.invoke(cmd_pipeline.pipeline, cmd_list)

        exp_msg = "missing flag. --stage flag must be given along with --job"

        assert result.exit_code == 1
        assert result.stdout.rstrip() == exp_msg

    def test_report_invalid_type_run(self):
        """throw error if --run is not an integer (invalid type)
        """
        cmd_list = ['report', '--repo', 'https://github.com/sjchin88/cicd-python', '--pipeline',
                    'cicd_pipeline', '--run', 'asdf']
        result = self.runner.invoke(cmd_pipeline.pipeline, cmd_list)
        exp_msg = "Unknown Input: 'asdf', Flag: ['run'], Message: Input should be a valid "
        exp_msg += "integer, unable to parse string as an integer"

        assert result.exit_code == 2
        assert result.stdout.rstrip() == exp_msg

    def test_report_missing_flag(self):
        """throw error --pipeline is provided but --repo is not given
        """
        cmd_list = ['report', '--pipeline', 'cicd_pipeline']
        result = self.runner.invoke(cmd_pipeline.pipeline, cmd_list)

        assert result.exit_code == 2

    @patch("controller.controller.MongoAdapter.get_pipeline_run_summary")
    def test_report_stage_build(self, mock_pipeline_summary):
        """Test L4.3 Stage Summary and L4.4 Job Summary

        Args:
            mock_pipeline_summary (MagicMock): mock MongoAdapter.get_pipeline_run_summary func.
        """
        mock_pipeline_summary.return_value = [
            {'_id': ObjectId('673139d61c77e7e99afd88ce'), 'pipeline_name': 'cicd_pipeline',
             'run_number': 1, 'git_commit_hash': '16adc46', 'status': 'success',
             'start_time': 'Sun Nov 10 17:33:33 2024', 'completion_time':
             'Sun Nov 10 17:33:48 2024', 
             'logs': [{'stage_name': 'build', 'stage_status': 'success', 
                       'jobs': [{'job_name': 'checkout', 'job_status': 'success',
                                 'allows_failure': False, 'start_time': 'Sun Nov 10 17:33:35 2024',
                                 'completion_time': 'Sun Nov 10 17:33:37 2024'},
                                {'job_name': 'compile', 'job_status': 'success',
                                 'allows_failure': False, 'start_time':'Sun Nov 10 17:33:37 2024',
                                 'completion_time': 'Sun Nov 10 17:33:41 2024'
                                }]
                    }]},
            {'_id': ObjectId('673139d61c77e7e99afd88ce'), 'pipeline_name': 'cicd_pipeline',
             'run_number': 2, 'git_commit_hash': '16adc46', 'status': 'success',
             'start_time': 'Sun Nov 10 19:30:03 2024', 'completion_time':
             'Sun Nov 10 19:30:18 2024',
             'logs': [{'stage_name': 'build', 'stage_status': 'success',
                       'jobs': [{'job_name': 'checkout', 'job_status': 'success',
                                 'allows_failure': False, 'start_time': 'Sun Nov 10 19:30:05 2024',
                                 'completion_time': 'Sun Nov 10 19:30:06 2024'},
                                {'job_name': 'compile', 'job_status': 'success',
                                 'allows_failure': False, 'start_time': 'Sun Nov 10 19:30:06 2024',
                                 'completion_time': 'Sun Nov 10 19:30:11 2024'}]
                    }]}
        ]
        cmd_list = ['report', '--repo', 'https://github.com/sjchin88/cicd-python', '--pipeline',
                    'cicd_pipeline', '--stage', 'build']

        result = self.runner.invoke(cmd_pipeline.pipeline, cmd_list)
        assert result.exit_code == 0

        cmd_list = ['report', '--repo', 'https://github.com/sjchin88/cicd-python', '--pipeline',
                    'cicd_pipeline', '--stage', 'build', '--job', 'checkout']

        result = self.runner.invoke(cmd_pipeline.pipeline, cmd_list)
        assert result.exit_code == 0
