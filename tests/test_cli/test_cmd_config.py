""" Test cid config command
"""
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from cli import (__main__, cmd_config)
from util.common_utils import (get_logger)
from util.db_mongo import MongoAdapter

logger = get_logger("tests.test_cmd_config")


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
       return_value=(True, "", {}))
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


@patch("cli.cmd_config.Controller.validate_config", return_value=(True, "", {}))
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


@patch("cli.cmd_config.Controller.validate_configs", return_value={})
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


@patch("cli.cmd_config.Controller.get_repo", return_value=(True, "./t4-cicd"))
def test_get_repo_in_git_directory(mock_controller):
    """ Test when in a Git repo directory """
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, ['get-repo'])
    assert result.exit_code == 0
    assert "Using current directory." in result.output
    assert "Current repository configured: ./t4-cicd" in result.output


@patch("cli.cmd_config.Controller.set_repo", return_value=(True,
       "Repository set successfully: https://github.com/github/docs"))
def test_set_repo(mock_controller):
    """ Test setting a repository after no repo is configured """
    runner = CliRunner()
    result = runner.invoke(
        cmd_config.config, [
            'set-repo', 'https://github.com/github/docs'])

    # Ensure the set_repo command was called successfully
    assert result.exit_code == 0
    assert "Repository set successfully: https://github.com/github/docs" in result.output

@patch("cli.cmd_config.Controller.get_repo", return_value=(False, "https://github.com/github/docs"))
def test_get_repo_with_last_set_repo(mock_controller):
    """ Test when a repository has already been set and retrieved from MongoDB """
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, ['get-repo'])

    assert result.exit_code == 0
    assert "Fetching last set repo..." in result.output
    assert "Repository configured: https://github.com/github/docs" in result.output


@patch("cli.cmd_config.Controller.override_config", return_value=True)
@patch("cli.cmd_config.ConfigOverrides.build_nested_dict", return_value={"global": {"docker": {"image": "gradle:jdk8"}}})
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
@patch("cli.cmd_config.ConfigOverrides.build_nested_dict", return_value={"global": {"docker": {"image": "gradle:jdk8"}}})
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

@patch("cli.cmd_config.ConfigOverrides.build_nested_dict", side_effect=ValueError("Invalid override format"))
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
@patch("cli.cmd_config.ConfigOverrides.build_nested_dict", return_value={"global": {"docker": {"image": "gradle:jdk8"}}})
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