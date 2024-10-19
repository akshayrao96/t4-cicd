""" Test cid config command
"""
from click.testing import CliRunner
from cli import (__main__, cmd_config)


def test_config_help():
    """ Test the main config command just by calling it with --help option
    """
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, '--help')
    assert result.exit_code == 0
    assert "Usage" in result.output

def test_config():
    """ Test the main config command without subcommands. `cid config`
        Expected to parse through pipelines.yml file
    """
    runner = CliRunner()
    result = runner.invoke(cmd_config.config)
    assert result.exit_code == 0
    assert "Using config file: pipelines.yml" in result.output

def test_config_check_with_valid_file():
    """ Test config command with --check and valid config file (yml extension)
    """
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, ['--check', '--config-file', 'valid_config.yml'])
    assert result.exit_code == 0
    assert "Checking config file at: valid_config.yml" in result.output

def test_config_check_with_invalid_file():
    """ Test config command with --check and invalid config file (e.g., no .yml extension)
    """
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, ['--check', '--config-file', 'invalid.txt'])
    assert result.exit_code != 0  # Non-zero exit code means error
    assert "Invalid file format" in result.output  # Check for proper error handling


def test_config_without_check():
    """ Test `cid config --config-file valid_config.yml` without --check flag
    """
    runner = CliRunner()

    # Invoke the command without --check
    result = runner.invoke(cmd_config.config, ['--config-file', 'valid_config.yml'])

    # Check that the exit code is 0 and the config file is checked
    assert result.exit_code == 0
    assert "Using config file: valid_config.yml" in result.output
    assert "Checking config file at: valid_config.yml" in result.output

# def test_config_list():
#     """ Test list configuration
#     """
#     runner = CliRunner()
#     result = runner.invoke(cmd_config.config, 'list')
#     assert result.exit_code == 0
#     assert result.output.rstrip() == "list config files at: local"
