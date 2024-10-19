""" All related commands for config actions
"""
# pylint: disable=logging-fstring-interpolation
import pprint
import click
from util.common_utils import get_logger
from controller.controller import Controller

logger = get_logger('cli.cmd_config')


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--check', is_flag=True,
              help="Checks the validity of the YAML configuration file.")
@click.option('--config-file', default='pipelines.yml',
              help="Specifies the YAML configuration file to check.")
def config(ctx, check, config_file: str):
    """
    Configuration commands for pipelines.

    This command allows you to manage and validate configuration files used
    in pipeline executions. File provided must be in .cicd-pipelines directory

    Example usage:

        - To check the default config file (pipelines.yml):
            cid config

        - To check a specific config file:
            cid config --check --config-file valid_config.yml
    """
    if not config_file.endswith(('.yml', '.yaml')):
        error_msg = f"Invalid file format: '{config_file}' must have a .yml or .yaml extension."
        logger.error(error_msg)
        raise click.ClickException(error_msg)

    if ctx.invoked_subcommand is None:
        click.echo(f"Using config file: {config_file}")

        if check or ctx.invoked_subcommand is None:
            click.echo(f"Checking config file at: {config_file}")
            logger.debug("Checking config file at: %s", config_file)
            controller = Controller()
            passed, error_msg, processed_config = controller.validate_config(
                config_file)
            click.echo(f"Check pass or fail = {passed}")
            click.echo(f"Error message (if any) =\n{error_msg}")
            click.echo("Printing processed_config")
            pprint.pprint(processed_config)
        else:
            click.echo(
                "No check was performed. Use --check to validate the config file.")


@config.command()
@click.option('--repo', default='local',
              help="repository url for remote repository \
or directory path for local repository")
def list(repo: str):
    """Lists the global configuration of the repository .cicd-pipelines/pipeline.yml
    of the specified repository location

    Args:
        repo_location (str): repository location
    """
    click.echo(f"list config files at: {repo}")
    logger.debug("list config files at: %s", repo)


@config.command()
# @click.option('--file_name', default='valid_config.yml',help="location of the file")
@click.argument('repo_url')
def set_repo(repo_url: str) -> None:
    """Sets a new repository for pipeline checks.

    Args:
        repo_url (str): The repository URL or path that must be provided.
    """

    if not repo_url:
        click.echo(
            "Error: No repository provided. Please specify a repository URL.")
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
