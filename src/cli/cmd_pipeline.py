""" All related commands for pipeline actions
"""
# pylint: disable=logging-fstring-interpolation
import click
from util.common_utils import get_logger
from controller.controller import (Controller)

logger = get_logger('cli.cmd_pipeline')
control = Controller()

@click.group()
def pipeline():
    """
    All commands related to pipeline
    """
    # pass


@pipeline.command()
@click.option('--name', default='Team 4', help='name to greet')
def greet(name: str):
    """ simple cli command to test the command line interface

    Args:
        name (str): name of person to greet
    """
    click.echo(f'Hello {name}')
    logger.debug(f'Hello {name}')

@pipeline.command()
@click.argument('config_file')
@click.option('-r', '--repo-url', 'repo_url', help='repository url', default='local')
@click.option('--dry-run', 'dry_run', help='dry-run options to simulate pipeline\
process via output message', default=False, show_default=True)

def run(config_file: str, repo_url: str, dry_run: bool):
    """ Run pipeline given the configuration file
    """
    # Pseudocode:
    #   call controller that is able to read the config file
    click.echo(dry_run)

    if dry_run:
        click.echo(f"\nThis executes the dry-run when dry-run flag is set to true\
(--dry-run={dry_run})\n")
        return

    #call run_pipeline
    click.echo(f'Run config file called {config_file} at repo {repo_url}')

    control.run_pipeline(config_file=config_file, repo_url=repo_url, dry_run=dry_run)
