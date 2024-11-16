""" All related commands for config actions
"""
# pylint: disable=logging-fstring-interpolation
import os
import pprint
import click
# import util.constant as const
from util.common_utils import (get_logger, MongoHelper)
from controller.controller import Controller

logger = get_logger('cli.cmd_config')


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--check', is_flag=True, default=False,
              help="checks the validity of the YAML configuration file.")
@click.option('--check-all', is_flag=True,
              help="checks validity of all YAML configuration files")
@click.option('--no-set', is_flag=True,
              help="validate the config/configs without setting the repo and\
              saving the validated info to datastore")
@click.option('--config-file', default='pipelines.yml', show_default=True, type=str,
              help="specifies the YAML configuration file to check. used with --check flag")
@click.option('--dir', default='.cicd-pipelines', show_default=True,
              type=str,
              help="specify the directory to check all configuration files.\
                  used with --check-all flag")
def config(
        ctx,
        check: bool,
        check_all: bool,
        no_set: bool,
        config_file: str,
        dir: str):
    """
    Command working with pipeline and repo configurations

    This command allows you to manage and validate configuration files used in 
    pipeline executions. You can run this to check the configuration files in 
    default location or pass a custom file/directory to check. 
    \f
    Example usage:

    To set up repo, check and save the default config file (pipelines.yml):

    - cid config / cid config --check --config-file pipelines.yml

    To set up repo, check and save a specific config file located in
    .cicd-pipelines folder:

    - cid config --check --config-file <filename.yml>

    To set up repo, check and save all config file located in
    .cicd-pipelines folder:

    - cid config --check-all

    To check a specific config file only without repo set up and saving:

    - cid config --check --config-file <absolute path to config.yml> --no-set


    To check config files in a directory only without repo set up and saving:

    - cid config --check-all --dir <absolute path to directory> --no-set
    """
    # If subcommand is called return so it called the subcommand instead
    if ctx.invoked_subcommand is not None:
        return

    if not config_file.endswith(('.yml', '.yaml')):
        err = f"Invalid file format: '{config_file}' must have a .yml or .yaml extension."
        logger.error(err)
        raise click.ClickException(err)
    controller = Controller()
    passed = True
    err = ""
    if check_all:
        config_dir_path = dir
        if not os.path.isdir(config_dir_path):
            click.echo(f"Invalid directory:{config_dir_path}")
            return
        click.echo(config_dir_path)
        if no_set:
            click.echo(f"checking all config files in directory {dir}")
            results = controller.validate_n_save_configs(dir, saving=False)
        else:
            click.echo(
                f"set repo, checking and saving all config files in directory {dir}")
            results = controller.validate_n_save_configs(dir)
        for pipeline_name, res in results.items():
            valid = res.valid
            err = res.error_msg
            click.echo(
                f"\nStatus for {pipeline_name}: {
                    'passed' if valid else 'failed'}")
            if not valid:
                click.echo(f"error message:\n{err}")
            else:
                click.echo("printing top 10 lines of processed config:")
                pipe_config = res.pipeline_config.model_dump(by_alias=True)
                config_str = pprint.pformat(pipe_config)
                for line in config_str.splitlines()[:10]:
                    click.echo(line)
    else:
        # Temp steps to ensure the path to the file is valid
        config_file_path = config_file
        if not os.path.isfile(config_file):
            # assume it will be in .cicd-pipelines folder
            config_file_path = os.path.join(
                os.getcwd(), '.cicd-pipelines', config_file)
        if not os.path.isfile(config_file_path):
            click.echo(f"Invalid config_file_path:{config_file_path}")
            return
        if check or ctx.invoked_subcommand is None:
            if no_set:
                click.echo(f"checking config file at: {dir}/{config_file}")
                # logger.debug("Checking config file at: %s", config_file)
                passed, err, pipeline_info = controller.validate_config(
                    config_file_path)
            else:
                msg = f"set repo, checking and saving config file at: {dir}/{config_file}"
                click.echo(msg)
                passed, err, pipeline_info = controller.validate_n_save_config(
                    config_file_path)

        # Print Validation Results
        click.echo(f"Check passed = {passed}")
        click.echo(f"Error message (if any) =\n{err}")
        click.echo("Printing processed_config")
        # Note pydantic model can dump json straight with model_dump()
        # click.echo(pipeline_info.pipeline_config.model_dump_json(by_alias=True))
        pprint.pprint(pipeline_info.pipeline_config.model_dump(by_alias=True))


@config.command()
@click.argument('repo_url', required=True)
@click.option('--branch', default="main", help="Specify the branch to retrieve.\
 If not given, 'main' is used.")
@click.option('--commit', default=None, help="Specify the commit hash to retrieve.\
 If not given, latest commit is used.")
def set_repo(repo_url: str, branch: str, commit: str) -> None:
    """Sets a new repository for pipeline checks.

    Args:
        repo_url (str): The repository URL or path that must be provided.
        branch (str): Optional branch name; defaults to 'main'.
        commit (str): Optional commit hash; if not provided, the latest commit is used.
    """

    # Checks if user has not given a repo. Return to user error, terminate
    if not repo_url:
        click.echo("Error: No repository provided. Please specify a repository URL.")
        return

    controller = Controller()

    try:
        # Call the set_repo method

        # success = true is repo is successfully set, otherwise, false if error occurred
        # message = success if repo is set, otherwise, specific error message of what the error is
        # repo_details = SessionDetails if success, otherwise, none

        status, message, repo_details = controller.handle_repo(repo_url, branch=branch, commit_hash=commit)

        # Display the result message
        click.echo(f"{message}\n")

        # If successful, display detailed repository information
        if status and repo_details:
            click.echo("Current working directory configured:\n")
            click.echo(f"Repository URL: {repo_details.repo_url}")
            click.echo(f"Repository Name: {repo_details.repo_name}")
            click.echo(f"Branch: {repo_details.branch}")
            click.echo(f"Commit Hash: {repo_details.commit_hash}\n")

    except Exception as e:
        click.echo(f"An unexpected error occurred: {str(e)}")


@config.command()
def get_repo():
    """
    Display information about the currently configured repository.

    This command retrieves and displays details of the currently configured Git repository,
    either from the current working directory if it is a Git repository, or from the last
    set repository stored in the system.

    Behavior:
        - If the current directory is a Git repository, it displays the URL, branch, and latest commit hash.
        - If the current directory is not a Git repository but a previous repository configuration exists,
          it retrieves and displays details of the last configured repository.
        - If no repository is configured, it provides guidance for setting a repository.

    Output:
        Information about the repository is displayed in the console, including:
        - Repository URL
        - Repository name
        - Branch name
        - Commit hash of the latest commit

    Example Usage:
        $ cid config get-repo
    """

    controller = Controller()

    status, message, repo_details = controller.handle_repo()

    if status and repo_details:
        click.echo(message)
        click.echo("Current repository configured:\n")
        click.echo(f"Repository URL: {repo_details.repo_url}")
        click.echo(f"Repository Name: {repo_details.repo_name}")
        click.echo(f"Branch: {repo_details.branch}")
        click.echo(f"Commit Hash: {repo_details.commit_hash}\n")

    elif repo_details:
        click.echo(f"{message}")
        click.echo("Last set repo details:\n")
        click.echo(f"Repository URL: {repo_details.repo_url}")
        click.echo(f"Repository Name: {repo_details.repo_name}")
        click.echo(f"Branch: {repo_details.branch}")
        click.echo(f"Commit Hash: {repo_details.commit_hash}\n")

    else:
        click.echo("\nNo repository has been configured previously.")
        click.echo("Run the command with specifying repo path in an empty working directory:\n")
        click.echo("OR")
        click.echo("Run the command without specifying repo path in the repository root\n")


@config.command()
@click.option('--pipeline', required=True, help="pipeline name to update")
@click.option('--override', 'overrides', multiple=True, 
              help="Override configuration in 'key=value' format")
def override(pipeline, overrides):
    """
    Apply configuration overrides to a pipeline and optionally save to the database. 
    Override configurations in 'key=value' format. Multiple overrides can be provided.

    Example usage:
        cid config override --pipeline pipeline_name --override "global.docker.image=gradle:jdk8"
    """
    try:
        updates = MongoHelper.build_nested_dict(overrides)
    except ValueError as e:
        click.echo(str(e))
        return
    # Prompt the user to confirm storing in the database
    if click.confirm("Do you want to apply these overrides and save them to the database?"):
        control = Controller()
        success = control.override_config(pipeline, updates)
        if success:
            click.echo(f"Pipeline '{pipeline}' updated successfully with overrides: {updates}")
        else:
            click.echo(f"Failed to update pipeline '{pipeline}'.")
    else:
        click.echo("No changes were made to the configuration.")
