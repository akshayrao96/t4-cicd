""" Test cid config command
"""
import json
import os
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from cli import (__main__, cmd_config)
from util.common_utils import (get_logger)
from util.db_mongo import MongoAdapter
from util.model import (PipelineInfo, ValidationResult)

logger = get_logger("tests.test_cmd_config")

# Load sample validation result from json file
validation_result_path = os.path.join(os.path.dirname(__file__),'sample_validation_res.json')
with open(validation_result_path, 'r', encoding='utf-8') as openfile:
    # Reading from json file
    validation_result_dict = json.load(openfile)
success_validation_res = ValidationResult.model_validate(validation_result_dict)
pipeline_config_dict = success_validation_res.pipeline_config 
sample_pipeline_info = PipelineInfo(
    pipeline_name="test_pipeline",
    pipeline_file_name="test_pipeline.yml",
    pipeline_config=pipeline_config_dict
)

def test_config_help():
    """ Test the main config command just by calling it with --help option
    """
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, '--help')
    assert result.exit_code == 0
    assert "Usage" in result.output

# Patch the validate_n_save_config of Controller method in cli.cmd_config
# module


@patch("cli.cmd_config.Controller.validate_n_save_config",
       return_value=(True, "", sample_pipeline_info))
def test_config_check_config_file(mock_controller):
    """ Test the main config command without subcommands. `cid config`
        Expected to parse through pipelines.yml file
    """
    runner = CliRunner()
    # main cmd
    result = runner.invoke(cmd_config.config)
    assert result.exit_code == 0
    assert "set repo, checking and saving config file at: .cicd-pipelines/pipelines.yml" in result.output
    # logger.debug(result.output)

    # custom yaml file
    yaml_file_name = 'valid_config.yml'
    result = runner.invoke(
        cmd_config.config, [
            '--check', '--config-file', yaml_file_name])
    assert result.exit_code == 0
    assert f"set repo, checking and saving config file at: .cicd-pipelines/{yaml_file_name}" in result.output

# Patch the validate_config of Controller method in cli.cmd_config module


@patch("cli.cmd_config.Controller.validate_n_save_configs", return_value=(True, "", sample_pipeline_info))
def test_config_check_with_valid_file_no_set(mock_controller):
    """ Test config command with --check and valid config file (yml extension)
    """
    runner = CliRunner()
    yaml_file_name = 'valid_config.yml'
    result = runner.invoke(
        cmd_config.config, [
            '--check', '--config-file', yaml_file_name, '--no-set'])
    assert result.exit_code == 0
    assert f"checking config file at: .cicd-pipelines/{yaml_file_name}" in result.output

# Patch the validate_n_save_configs of Controller method in cli.cmd_config
# module


@patch("cli.cmd_config.Controller.validate_n_save_configs", return_value={})
def test_config_check_all(mock_controller):
    """ Test config command with --check and valid config file (yml extension)
    """
    runner = CliRunner()
    dir = '.cicd-pipelines'
    result = runner.invoke(cmd_config.config, ['--check-all'])
    assert result.exit_code == 0
    assert f"set repo, checking and saving all config files in directory {dir}" in result.output

# Patch the validate_configs of Controller method in cli.cmd_config module


@patch("cli.cmd_config.Controller.validate_n_save_configs", return_value={})
@patch("cli.cmd_config.click.Path", return_value="")
def test_config_check_all_no_set(mock_controller, mock_path):
    """ Test config command with --check and valid config file (yml extension)
    """
    runner = CliRunner()
    dir = '.cicd-pipelines'
    result = runner.invoke(
        cmd_config.config, [
            '--check-all', '--dir', dir, '--no-set'])
    logger.debug(result.output)
    assert result.exit_code == 0
    assert f"checking all config files in directory {dir}" in result.output


def test_config_check_with_invalid_file():
    """ Test config command with --check and invalid config file (e.g., no .yml extension)
    """
    runner = CliRunner()
    result = runner.invoke(
        cmd_config.config, [
            '--check', '--config-file', 'invalid.txt'])
    logger.debug(result.output)
    assert result.exit_code != 0  # Non-zero exit code means error
    assert "Invalid file format" in result.output  # Check for proper error handling


# def test_config_without_check():
#     """ Test `cid config --config-file valid_config.yml` without --check flag
#     """
#     runner = CliRunner()

#     # Invoke the command without --check
#     result = runner.invoke(cmd_config.config, ['--config-file', 'valid_config.yml'])

#     # Check that the exit code is 0 and the config file is checked
#     assert result.exit_code == 0
#     assert "Using config file: valid_config.yml" in result.output
#     assert "Checking config file at: valid_config.yml" in result.output

# def test_config_list():
#     """ Test list configuration
#     """
#     runner = CliRunner()
#     result = runner.invoke(cmd_config.config, 'list')
#     assert result.exit_code == 0
#     assert result.output.rstrip() == "list config files at: local"

#     assert result.exit_code == 0
#     # result.output will have newline ending, need to strip it

@patch("cli.cmd_config.Controller.override_config", return_value=True)
@patch("cli.cmd_config.MongoHelper.build_nested_dict", return_value={"global": {"docker": {"image": "gradle:jdk8"}}})
def test_override_save_to_db(mock_build_nested_dict, mock_override_config):
    """ Test override command with confirmation to save changes to the database """
    runner = CliRunner()
    result = runner.invoke(
        cmd_config.config, 
        ['override', '--pipeline', 'test_pipeline', '--override', 'global.docker.image=gradle:jdk8'],
        input="y\n"  # Simulate 'yes' to confirm saving to DB
    )
    assert result.exit_code == 0
    assert "Pipeline 'test_pipeline' updated successfully with overrides" in result.output
    mock_build_nested_dict.assert_called_once_with(('global.docker.image=gradle:jdk8',))
    mock_override_config.assert_called_once_with('test_pipeline', {"global": {"docker": {"image": "gradle:jdk8"}}})

@patch("cli.cmd_config.Controller.override_config", return_value=True)
@patch("cli.cmd_config.MongoHelper.build_nested_dict", return_value={"global": {"docker": {"image": "gradle:jdk8"}}})
def test_override_decline_save_to_db(mock_build_nested_dict, mock_override_config):
    """ Test override command without saving changes to the database """
    runner = CliRunner()
    result = runner.invoke(
        cmd_config.config, 
        ['override', '--pipeline', 'test_pipeline', '--override', 'global.docker.image=gradle:jdk8'],
        input="n\n"  # Simulate 'no' to decline saving to DB
    )
    assert result.exit_code == 0
    assert "No changes were made to the configuration." in result.output
    mock_build_nested_dict.assert_called_once_with(('global.docker.image=gradle:jdk8',))
    mock_override_config.assert_not_called()

@patch("cli.cmd_config.MongoHelper.build_nested_dict", side_effect=ValueError("Invalid override format"))
def test_override_value_error(mock_build_nested_dict):
    """ Test override command when a ValueError is raised """
    runner = CliRunner()
    result = runner.invoke(
        cmd_config.config, 
        ['override', '--pipeline', 'test_pipeline', '--override', 'invalid_override_format']
    )
    # Check that the command exited correctly and the error message was printed
    assert result.exit_code == 0
    assert "Invalid override format" in result.output
    mock_build_nested_dict.assert_called_once_with(('invalid_override_format',))

@patch("cli.cmd_config.Controller.override_config", return_value=False)
@patch("cli.cmd_config.MongoHelper.build_nested_dict", return_value={"global": {"docker": {"image": "gradle:jdk8"}}})
def test_override_save_to_db_failure(mock_build_nested_dict, mock_override_config):
    """ Test override command when the save to database fails """
    runner = CliRunner()
    result = runner.invoke(
        cmd_config.config, 
        ['override', '--pipeline', 'test_pipeline', '--override', 'global.docker.image=gradle:jdk8'],
        input="y\n"  # Simulate 'yes' to confirm saving to DB
    )
    assert result.exit_code == 0
    assert "Failed to update pipeline 'test_pipeline'." in result.output
    mock_build_nested_dict.assert_called_once_with(('global.docker.image=gradle:jdk8',))
    mock_override_config.assert_called_once_with('test_pipeline', {"global": {"docker": {"image": "gradle:jdk8"}}})


@patch("cli.cmd_config.Controller.handle_repo", return_value=(True, "Repository set successfully", MagicMock()))
def test_set_repo_success(mock_handle_repo):
    """Test `set-repo` command with successful repository setup."""
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, [
        'set-repo', 'https://github.com/example/repo.git', '--branch', 'main', '--commit', '123abc'
    ])

    assert result.exit_code == 0
    assert "Repository set successfully" in result.output
    mock_handle_repo.assert_called_once_with("https://github.com/example/repo.git", branch="main", commit_hash="123abc")


# Test case for `set_repo` command with failure in repository setup
@patch("cli.cmd_config.Controller.handle_repo", return_value=(False, "Failed to set repository", None))
def test_set_repo_failure(mock_handle_repo):
    """Test `set-repo` command with a failure in repository setup."""
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, [
        'set-repo', 'https://github.com/example/repo.git', '--branch', 'invalid', '--commit', 'unknown_commit'
    ])

    assert result.exit_code == 0
    assert "Failed to set repository" in result.output
    mock_handle_repo.assert_called_once_with("https://github.com/example/repo.git", branch="invalid", commit_hash="unknown_commit")


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
    MagicMock(repo_url="https://github.com/example/repo.git", repo_name="example_repo", branch="main", commit_hash="123abc")
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
    MagicMock(repo_url="https://github.com/example/last-repo.git", repo_name="last_repo", branch="main", commit_hash="456def")
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

@patch("cli.cmd_config.Controller.get_repo", return_value=(False, "No repository has been configured previously.", None))
def test_get_repo_no_repo_set(mock_get_repo):
    """Test `get-repo` command when no repository is configured."""
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, ['get-repo'])

    assert result.exit_code == 0
    assert "No repository has been configured previously." in result.output
    mock_get_repo.assert_called_once()

