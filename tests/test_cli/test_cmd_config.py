""" Test cid config command
"""
import json
import os
import unittest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from cli import (__main__, cmd_config)
from util.common_utils import (get_logger)
from util.model import (PipelineConfig, PipelineInfo, SessionDetail, ValidationResult)
import util.constant as c

logger = get_logger("tests.test_cmd_config")

def test_cid_help():
    """ Test the main pipeline command just by calling it with --help option
    """
    runner = CliRunner()
    result = runner.invoke(__main__.cid)
    # 0 exit code mean successful
    assert result.exit_code == 0

class TestConfig(unittest.TestCase):
    """ Test class to test the logic handling of cid config commands.
    The downstream method will be patched whenever necessary.

    Args:
        unittest.TestCase (class): base class
    """
    def setUp(self):
        # Load sample validation result from json file
        validation_result_path = os.path.join(os.path.dirname(__file__),
                                              'sample_validation_res.json')
        with open(validation_result_path, 'r', encoding='utf-8') as openfile:
            # Reading from json file
            self.validation_result_dict = json.load(openfile)
        # Single Validation result forConfigChecker.validate_config
        self.success_validation_res = ValidationResult.model_validate(self.validation_result_dict)
        self.fail_validation_res = ValidationResult(valid=False,
                                                    error_msg="error", pipeline_config={})
        self.pipeline_config_dict = self.success_validation_res.pipeline_config
        self.success_validation_res.pipeline_config = PipelineConfig.model_validate(self.pipeline_config_dict)
        self.sample_pipeline_info = PipelineInfo(
            pipeline_name="test_pipeline",
            pipeline_file_name="test_pipeline.yml",
            pipeline_config=self.pipeline_config_dict
        )
        # Single validation result for Controller.validate_config/validate_n_save_config
        self.controller_validate_res = (True, "", self.sample_pipeline_info)
        self.session_data = SessionDetail(
            user_id='random',
            repo_name='cicd-python',
            repo_url="https://github.com/sjchin88/cicd-python",
            branch=c.DEFAULT_BRANCH,
            is_remote=True,
            commit_hash="abcdef"
        )
        self.handle_repo_return = (True, "", self.session_data)
        self.mock_save_configs_return = {
            "test_pipeline":self.success_validation_res,
            "test_fail_pipeline": self.fail_validation_res
        }
        self.runner = CliRunner()

    def test_config_help(self):
        """ Test the main config command just by calling it with --help option
        """
        result = self.runner.invoke(cmd_config.config, '--help')
        assert result.exit_code == 0
        assert "Usage" in result.output

    def test_config_check_with_both_check_n_checkall(self):
        """ Test config command with --check and --check-all flag
        """
        result = self.runner.invoke(
            cmd_config.config, ['--check', '--check-all'])
        assert result.exit_code == 2  # Non-zero exit code means error
        assert "Please select only one option between --check and --check-all" in result.output

    def test_config_check_with_invalid_file(self):
        """ Test config command with --check and invalid config file (e.g., no .yml extension)
        """
        result = self.runner.invoke(
            cmd_config.config, ['--check', '--config-file', 'invalid.txt'])
        assert result.exit_code == 2  # Non-zero exit code means error
        assert "Invalid file format:" in result.output

    @patch("cli.cmd_config.Controller.handle_repo")
    def test_fail_repo_check(self, mock_handle):
        """ Test if the handle_repo return false

        Args:
            mock_handle (MagicMock): mock the handle_repo function
        """
        mock_handle.return_value = (False, "", None)
        result = self.runner.invoke(cmd_config.config)
        assert result.exit_code == 2

    @patch("cli.cmd_config.os.path.isdir", return_value=False)
    def test_config_check_all_faildir(self, mock_isdir):
        """ Test config command with --check-all and invalid dir

        Args:
            mock_isdir (MagicMock): mock the os.path.isdir method
        """
        result = self.runner.invoke(cmd_config.config, ['--check-all', '--no-set'])
        assert result.exit_code == 2
        assert f"Invalid directory:" in result.output

    @patch("cli.cmd_config.Controller.validate_n_save_configs")
    @patch("cli.cmd_config.os.path.isdir", return_value=True)
    def test_config_check_all_duplicate_pipeline_name(self, mock_isdir, mock_validates):
        """ Test config command with --check-all but caught ValueError
        due to duplicate pipeline name
        
        Args:
            mock_isdir (MagicMock): mock the os.path.isdir method
            mock_validates (MagicMock): mock the validate_n_save_configs
        """
        mock_validates.side_effect = ValueError()
        result = self.runner.invoke(
            cmd_config.config, ['--check-all', '--dir', dir, '--no-set'])
        assert result.exit_code == 1

    @patch("cli.cmd_config.Controller.validate_n_save_configs", return_value={})
    @patch("cli.cmd_config.os.path.isdir", return_value=True)
    def test_config_check_all_no_set(self, mock_isdir, mock_validates):
        """ Test config command with --check-all and --no-set
        Args:
            mock_isdir (MagicMock): mock the os.path.isdir method
            mock_validates (MagicMock): mock the validate_n_save_configs
        """
        dir = '.cicd-pipelines'
        result = self.runner.invoke(
            cmd_config.config, ['--check-all', '--dir', dir, '--no-set'])
        assert result.exit_code == 0
        assert f"checking all config files in directory {dir}" in result.output

    # Patch the validate_n_save_configs of Controller method in cli.cmd_config
    # module
    @patch("cli.cmd_config.Controller.validate_n_save_configs")
    @patch("cli.cmd_config.os.path.isdir", return_value=True)
    @patch("cli.cmd_config.Controller.handle_repo")
    def test_config_check_all(self, mock_handle, mock_isdir, mock_validates):
        """ Test config command with --check-all
        
        Args:
            mock_handle (MagicMock): mock the handle_repo function
            mock_isdir (MagicMock): mock the os.path.isdir method
            mock_validates (MagicMock): mock the validate_n_save_configs
        """
        mock_handle.return_value = self.handle_repo_return
        mock_validates.return_value = self.mock_save_configs_return
        result = self.runner.invoke(cmd_config.config, ['--check-all'])
        assert result.exit_code == 0

    @patch("cli.cmd_config.os.path.isfile", return_value=False)
    def test_config_check_config_file_invalid_file(self, mock_isfile):
        """ Test invalid file handling when using --check --config-file

        Args:
            mock_isfile (MagicMock): mock the os.path.isfile method
        """
        result = self.runner.invoke(
            cmd_config.config, ['--check', '--config-file', 'invalid.yml', '--no-set'])
        assert result.exit_code == 2  # Non-zero exit code means error
        assert "Invalid config_file_path:" in result.output

    # Patch the validate_n_save_config of Controller method in cli.cmd_config
    # module
    @patch("cli.cmd_config.Controller.validate_n_save_config")
    @patch("cli.cmd_config.os.path.isfile", return_value=True)
    @patch("cli.cmd_config.Controller.handle_repo")
    def test_config_check_valid_config_file(self, mock_handle, mock_isfile, mock_validate):
        """ Test the  `cid config` command with single file
            
        Args:
            mock_handle (MagicMock): mock the handle_repo function
            mock_isfile (MagicMock): mock the os.path.isfile method
            mock_validate (MagicMock): mock the validate_n_save_config method
        """
        mock_handle.return_value = self.handle_repo_return
        mock_validate.return_value = self.controller_validate_res
        # main cmd
        result = self.runner.invoke(cmd_config.config)
        assert result.exit_code == 0
        assert "set repo, checking and saving config file at:" in result.output

        # custom yaml file
        yaml_file_name = 'valid_config.yml'
        result = self.runner.invoke(
            cmd_config.config, [
                '--check', '--config-file', yaml_file_name])
        assert result.exit_code == 0
        assert f"set repo, checking and saving config file at: " in result.output

    @patch("cli.cmd_config.Controller.validate_config")
    @patch("cli.cmd_config.os.path.isfile", return_value=True)
    @patch("cli.cmd_config.Controller.handle_repo")
    def test_config_check_valid_file_no_set(self, mock_handle, mock_isfile, mock_validate):
        """ Test config command with --check and valid config file (yml extension)
        Args:
            mock_handle (MagicMock): mock the handle_repo function
            mock_isfile (MagicMock): mock the os.path.isfile method
            mock_validate (MagicMock): mock the validate_n_save_config method
        """
        mock_handle.return_value = self.handle_repo_return
        mock_validate.return_value = self.controller_validate_res
        yaml_file_name = 'valid_config.yml'
        result = self.runner.invoke(
            cmd_config.config, [
                '--check', '--config-file', yaml_file_name, '--no-set'])
        assert result.exit_code == 0
        assert f"checking config file at: " in result.output

    @patch("cli.cmd_config.Controller.validate_config")
    @patch("cli.cmd_config.os.path.isfile", return_value=True)
    @patch("cli.cmd_config.Controller.handle_repo")
    def test_config_check_valid_file_fail_validation(self, mock_handle, mock_isfile, mock_validate):
        """Test config command with --check and valid config file (yml extension). But 
        error during validation. 
        
        Args:
            mock_handle (MagicMock): mock the handle_repo function
            mock_isfile (MagicMock): mock the os.path.isfile method
            mock_validate (MagicMock): mock the validate_n_save_config method
        """
        mock_handle.return_value = self.handle_repo_return
        mock_validate.return_value = (False, "error", None)
        yaml_file_name = 'valid_config.yml'
        result = self.runner.invoke(
            cmd_config.config, [
                '--check', '--config-file', yaml_file_name, '--no-set'])
        assert result.exit_code == 1
        assert "error" in result.output

class TestConfigOverride(unittest.TestCase):
    """ Test the logic handling of cid config override

    Args:
        unittest.TestCase (class): base class
    """
    def setUp(self):
        self.runner = CliRunner()
        validation_result_path = os.path.join(os.path.dirname(__file__),
                                              'sample_validation_res.json')
        with open(validation_result_path, 'r', encoding='utf-8') as openfile:
            # Reading from json file
            self.validation_result_dict = json.load(openfile)
        # Single Validation result forConfigChecker.validate_config
        self.success_validation_res = ValidationResult.model_validate(self.validation_result_dict)
        self.fail_validation_res = ValidationResult(valid=False, 
                                                    error_msg="error", pipeline_config={})
        self.pipeline_config_dict = self.success_validation_res.pipeline_config
        self.success_validation_res.pipeline_config = PipelineConfig.model_validate(self.pipeline_config_dict)
        self.pipeline_info = PipelineInfo(
            pipeline_name="test_pipeline",
            pipeline_file_name="test_pipeline.yml",
            pipeline_config=self.pipeline_config_dict
        )
        self.session_data = SessionDetail(
            user_id='random',
            repo_name='cicd-python',
            repo_url="https://github.com/sjchin88/cicd-python",
            branch=c.DEFAULT_BRANCH,
            is_remote=True,
            commit_hash="abcdef"
        )
        self.handle_repo_return = (True, "", self.session_data)

    @patch("cli.cmd_config.ConfigOverride.build_nested_dict",
           side_effect=ValueError("Invalid override format"))
    def test_override_value_error(self, mock_build_nested_dict):
        """ Test override command when a ValueError is raised """
        result = self.runner.invoke(
            cmd_config.config,
            ['override', '--pipeline', 'test_pipeline', '--override', 'invalid_override_format']
        )
        # Check that the command exited correctly and the error message was printed
        assert result.exit_code == 2
        assert "Invalid override format" in result.output
        mock_build_nested_dict.assert_called_once_with(('invalid_override_format',))

    @patch("cli.cmd_config.Controller.handle_repo")
    def test_override_invalid_repo(self, mock_handle):
        """ Test handling of invalid repo result

        Args:
            mock_handle (MagicMock): mock the handle_repo function
        """
        mock_handle.return_value = (False, "", None)
        result = self.runner.invoke(
            cmd_config.config,
            ['override', '--pipeline', 'test_pipeline',
             '--override', "global.docker.image=gradle:jdk8"])
        assert result.exit_code == 2

    @patch("cli.cmd_config.Controller.override_config")
    @patch("cli.cmd_config.Controller.handle_repo")
    def test_override_failed_ops(self, mock_handle, mock_override):
        """ Test the handling of fail controller.override_config operation

        Args:
            mock_handle (MagicMock): mock the handle_repo function
            mock_override (MagicMock): mock the controller.override_config function
        """
        mock_handle.return_value = self.handle_repo_return
        mock_override.return_value = (False, 'error', None)
        result = self.runner.invoke(
            cmd_config.config,
            ['override', '--pipeline', 'test_pipeline',
             '--override', "global.docker.image=gradle:jdk8"])
        assert result.exit_code == 1

    @patch("cli.cmd_config.Controller.override_config")
    @patch("cli.cmd_config.Controller.handle_repo")
    def test_override_success_ops(self, mock_handle, mock_override):
        """ Test the handling of success controller.override_config operation

        Args:
            mock_handle (MagicMock): mock the handle_repo function
            mock_override (MagicMock): mock the controller.override_config function
        """
        mock_handle.return_value = self.handle_repo_return
        mock_override.return_value = (True, "", self.success_validation_res.pipeline_config)
        result = self.runner.invoke(
            cmd_config.config,
            ['override', '--pipeline', 'test_pipeline',
             '--override', "global.docker.image=gradle:jdk8", '--json'])
        assert result.exit_code == 0

    ## The rest of test cases are Integration tests with Controller.override_config
    @patch("controller.controller.MongoAdapter.get_pipeline_history")
    @patch("cli.cmd_config.Controller.handle_repo")
    def test_override_no_pipeline_found(self, mock_handle, mock_get_hist):
        """ Test the case where no pipeline config found for target pipeline name

        Args:
            mock_handle (MagicMock): mock the handle_repo function
            mock_get_hist (MagicMock): mock the get_pipeline_history
        """
        mock_handle.return_value = self.handle_repo_return
        mock_get_hist.return_value = {}
        result = self.runner.invoke(
            cmd_config.config,
            ['override', '--pipeline', 'test_pipeline',
             '--override', "global.docker.image=gradle:jdk8", '--json'])
        assert result.exit_code == 1

    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.MongoAdapter.get_pipeline_history")
    @patch("cli.cmd_config.Controller.handle_repo")
    def test_override_fail_validation(self, mock_handle, mock_get_hist, mock_validate):
        """ Test the case where pipeline config overrided but fail 
        the validation 

        Args:
            mock_handle (MagicMock): mock the handle_repo function
            mock_get_hist (MagicMock): mock the get_pipeline_history
            mock_validate (MagicMock): mock the ConfigChecker.validate_config
        """
        mock_handle.return_value = self.handle_repo_return
        mock_get_hist.return_value = self.pipeline_info
        mock_validate.return_value = self.fail_validation_res
        result = self.runner.invoke(
            cmd_config.config,
            ['override', '--pipeline', 'test_pipeline', 
             '--override', "global.docker.image=gradle:jdk8", '--json'])
        assert result.exit_code == 1

    @patch("controller.controller.MongoAdapter.update_pipeline_info")
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.MongoAdapter.get_pipeline_history")
    @patch("cli.cmd_config.Controller.handle_repo")
    def test_override_fail_save_to_db(self, mock_handle, mock_get_hist, mock_validate, mock_update):
        """ Test override command scenario where pipeline configuration 
        overrided and validated but fail to save into db
        
        Args:
            mock_handle (MagicMock): mock the handle_repo function
            mock_get_hist (MagicMock): mock the get_pipeline_history
            mock_validate (MagicMock): mock the ConfigChecker.validate_config
        """
        mock_handle.return_value = self.handle_repo_return
        mock_get_hist.return_value = self.pipeline_info
        mock_validate.return_value = self.success_validation_res
        mock_update.return_value = False
        result = self.runner.invoke(
            cmd_config.config,
            ['override', '--pipeline', 'test_pipeline',
             '--override', "global.docker.image=gradle:jdk8", '--save'])
        assert result.exit_code == 1

    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.MongoAdapter.get_pipeline_history")
    @patch("cli.cmd_config.Controller.handle_repo")
    def test_success_override(self, mock_handle, mock_get_hist, mock_validate):
        """ Test successful override scenario without saving 
        
        Args:
            mock_handle (MagicMock): mock the handle_repo function
            mock_get_hist (MagicMock): mock the get_pipeline_history
            mock_validate (MagicMock): mock the ConfigChecker.validate_config
        """
        mock_handle.return_value = self.handle_repo_return
        mock_get_hist.return_value = self.pipeline_info
        mock_validate.return_value = self.success_validation_res
        result = self.runner.invoke(
            cmd_config.config,
            ['override', '--pipeline', 'test_pipeline', 
             '--override', "global.docker.image=gradle:jdk8"])
        assert result.exit_code == 0

@patch("cli.cmd_config.Controller.handle_repo", return_value=(True, "Repository set successfully", MagicMock()))
def test_set_repo_success(mock_handle_repo):
    """Test `set-repo` command with successful repository setup."""
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, [
        'set-repo', 'https://github.com/example/repo.git', 
        '--branch', c.DEFAULT_BRANCH, '--commit', '123abc'
    ])

    assert result.exit_code == 0
    assert "Repository set successfully" in result.output
    mock_handle_repo.assert_called_once_with("https://github.com/example/repo.git",
                                             branch=c.DEFAULT_BRANCH, commit_hash="123abc")


# Test case for `set_repo` command with failure in repository setup
@patch("cli.cmd_config.Controller.handle_repo", return_value=(False, "Failed to set repository", None))
def test_set_repo_failure(mock_handle_repo):
    """Test `set-repo` command with a failure in repository setup."""
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, [
        'set-repo', 'https://github.com/example/repo.git', '--branch',
        'invalid', '--commit', 'unknown_commit'
    ])

    assert result.exit_code == 0
    assert "Failed to set repository" in result.output
    mock_handle_repo.assert_called_once_with("https://github.com/example/repo.git",
                                             branch="invalid", commit_hash="unknown_commit")


# Test case for `set_repo` command when no repository URL is provided
def test_set_repo_no_repo_given():
    """Test `set-repo` command when no repository URL is provided."""
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, ['set-repo'])

    assert result.exit_code != 0  # Command should fail due to missing argument
    assert "Error: Missing argument 'REPO_URL'." in result.output


# Test case for `get_repo` command when a repository is configured in the current directory
@patch("cli.cmd_config.Controller.get_repo", return_value=(
    True,
    "Repository is configured in current directory",
    MagicMock(repo_url="https://github.com/example/repo.git",
              repo_name="example_repo", branch=c.DEFAULT_BRANCH, commit_hash="123abc")
))
def test_get_repo_success(mock_get_repo):
    """Test `get-repo` command when a repository is configured in the current directory."""
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, ['get-repo'])

    assert result.exit_code == 0
    assert "Repository is configured in current directory" in result.output
    assert "Repository URL: https://github.com/example/repo.git" in result.output
    assert "Repository Name: example_repo" in result.output
    assert "Branch: main" in result.output
    assert "Commit Hash: 123abc" in result.output
    mock_get_repo.assert_called_once()


@patch("cli.cmd_config.Controller.get_repo", return_value=(
    False,
    "Current working directory is not a git repository",
    MagicMock(repo_url="https://github.com/example/last-repo.git",
              repo_name="last_repo", branch=c.DEFAULT_BRANCH, commit_hash="456def")
))
def test_get_repo_last_set_repo(mock_get_repo):
    """Test `get-repo` command retrieving the last set repository."""
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, ['get-repo'])

    assert result.exit_code == 0
    assert "Current working directory is not a git repository" in result.output
    assert "Repository URL: https://github.com/example/last-repo.git" in result.output
    assert "Repository Name: last_repo" in result.output
    assert "Branch: main" in result.output
    assert "Commit Hash: 456def" in result.output
    mock_get_repo.assert_called_once()

@patch("cli.cmd_config.Controller.handle_repo",
       return_value=(False,
                     "Working directory is not a git repository. "
                     "No previous repository has been set.",
                     None))
def test_get_repo_no_repo_set(mock_handle_repo):
    """Test `get-repo` command when no repository is configured."""
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, ['get-repo'])

    assert result.exit_code == 0
    assert ("Working directory is not a git repository. "
            "No previous repository has been set") in result.output
