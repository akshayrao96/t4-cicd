""" Test cid config command
"""
from click.testing import CliRunner
from cli import (__main__, cmd_config)

def test_config_help():
    """ Test the main config command just by calling it with --help option
    """
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, '--help')
    # 0 exit code mean successful
    assert result.exit_code == 0

# def test_config():
#     """ Test the main config command without subcommands. `cid config`
#     """
#     runner = CliRunner()
#     result = runner.invoke(cmd_config.config)
#     # 0 exit code mean successful
#     assert result.exit_code == 0
#     assert result.output.rstrip() == "Running the parent command!" 

def test_config_list():
    """ Test list configuration
    """
    runner = CliRunner()
    result = runner.invoke(cmd_config.config, 'list')
    assert result.exit_code == 0
    assert result.output.rstrip() == "list config files at: local"
