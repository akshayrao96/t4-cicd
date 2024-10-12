""" All related commands for config actions
"""
# pylint: disable=logging-fstring-interpolation
import click
from util.common_utils import get_logger

logger = get_logger('cli.cmd_config')

@click.group(invoke_without_command=True)
@click.pass_context
#@click.option('--check', show_default = True, default = False, help='check configuration')
def config(ctx):
    """All commands related to config

    Args:
        ctx (_Any_): click context
    """
    if ctx.invoked_subcommand is None:
        click.echo("Running the parent command!")

    #logger.debug(f"config name: {config_name}")
    # pass

# TODO: find a click command to have the command `cid config list` but
#   able to change the function name to adhere to pyLint.
#   warning message: "list is a built-in command"
@config.command()
@click.option('--repo-location', default='local', help="repository url for remote repository \
or directory path for local repository")
def list(repo_location:str):
    """list all configuration of the repository of the specified repository location

    Args:
        repo_location (str): repository location
    """
    click.echo(f"list config files at: {repo_location}")
    logger.debug("list config files at: %s", repo_location)
