""" All related commands for config actions
"""
# pylint: disable=logging-fstring-interpolation
import click
from util.common_utils import get_logger

logger = get_logger('cli.cmd_config')

@click.group(invoke_without_command=True)
@click.pass_context
def config(ctx):
    """
    All commands related to config
    """
    if ctx.invoked_subcommand is None:
        click.echo("Running the parent command!")

    #logger.debug(f"config name: {config_name}")
    # pass

@config.command()
@click.option('--repo-location', default='local', help="repository url for remote repository \
or directory path for local repository")
def list(repo_location:str):
    """ list all configuration of the repository"""
    click.echo(f"list config files at: {repo_location}")
    logger.debug("list config files at: %s", repo_location)
