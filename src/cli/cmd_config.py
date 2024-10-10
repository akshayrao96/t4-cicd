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
def show():
    """ show configuration of the  """
