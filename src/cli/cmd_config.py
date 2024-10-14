""" All related commands for config actions
"""
# pylint: disable=logging-fstring-interpolation
import click
import pprint
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
    """Lists the global configuration of the repository .cicd-pipelines/pipeline.yml 
    of the specified repository location

    Args:
        repo_location (str): repository location
    """
    click.echo(f"list config files at: {repo}")
    logger.debug("list config files at: %s", repo)

@config.command()
@click.option('--file_name', default='valid_config.yml',help="location of the file")
def check_config_file(file_name:str):
    """Lists the global configuration of the repository .cicd-pipelines/pipeline.yml 
    of the specified repository location

    Args:
        repo_location (str): repository location
    """
    click.echo(f"checking config files at: {file_name}")
    logger.debug("list config files at: %s", file_name)
    controller = Controller()
    passed, error_msg, processed_config = controller.validate_config(file_name)
    click.echo(f"check pass or fail = {passed}")
    click.echo(f"error message if any = {error_msg}")
    click.echo(f"printing processed_config")
    pprint.pprint(processed_config)

@config.command()
# @click.option('--file_name', default='valid_config.yml',help="location of the file")
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
        controller = Controller()
        controller.set_repo(repo_url)
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
    controller = Controller()
    repo_url = controller.get_repo()
    print(repo_url)
    if repo_url:
        click.echo(f"Current repository set to: {repo_url}")
    else:
        click.echo("No repository is currently set.")
