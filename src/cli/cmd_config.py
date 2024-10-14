""" All related commands for config actions
"""
# pylint: disable=logging-fstring-interpolation
import click
from util.common_utils import get_logger
from controller.controller import Controller

logger = get_logger('cli.cmd_config')

@click.group(invoke_without_command=True)
@click.pass_context
#@click.option('--check', show_default = True, default = False, help='check configuration')
def config(ctx):
    """
    All commands related to pipeline
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

# TODO: find a click command to have the command `cid config list` but
#   able to change the function name to adhere to pyLint.
#   warning message: "list is a built-in command"

@config.command()
@click.option('--repo', default='local', help="repository url for remote repository \
or directory path for local repository")
def list(repo:str):
    """Lists the global configuration of the repository .cicd-pipelines/pipeline.yml of the specified repository location

    Args:
        repo_location (str): repository location
    """
    click.echo(f"list config files at: {repo}")
    logger.debug("list config files at: %s", repo)

@config.command()
@click.argument('repo_url')
def set_repo(repo_url: str) -> None:
    """Sets a new repository for pipeline checks.

    Args:
        repo_url (str): The repository URL or path that must be provided.
    """

    if not repo_url:
        click.echo("Error: No repository provided. Please specify a repository URL.")
        return
    
    # run the controller set repo with the given repo url
    # Controller.set_repo(repo_url)

    try:
        success: bool = True  # controller logic result
        if success:
            click.echo(f"Repository set to: {repo_url}")
        else:
            raise ValueError("Error occurred while setting repository")
    
    except ValueError as e:
        # Log the error and show a message to the user
        logger.debug(f"Error: {str(e)}")
        click.echo(f"Error: Unable to set repository. {str(e)}")

    except Exception as e:
        # Handle unexpected errors
        logger.debug(f"Unexpected error: {str(e)}")
        click.echo(f"An unexpected error occurred: {str(e)}")

@config.command()
def get_repo():
    """Gets the currently set repository."""

    # Gets the currently set repo from the controller

    if repo_url:
        click.echo(f"Current repository set to: {repo_url}")
    else:
        click.echo("No repository is currently set.")
