""" All related commands for pipeline actions """
# pylint: disable=logging-fstring-interpolation
import hashlib
import time
import click
from util.common_utils import (get_logger,MongoHelper)
from controller.controller import (Controller)

DEFAULT_CONFIG_FILE_PATH = ".cicd-pipelines/pipelines.yml"
logger = get_logger('cli.cmd_pipeline')
# pylint: disable=fixme
@click.group()
def pipeline():
    """All commands related to pipeline"""

#https://click.palletsprojects.com/en/stable/arguments/#file-path-arguments
#TODO: to delete. this is a click function where I can validate if filename
# @pipeline.command()
# @click.argument('filename', type=click.Path(exists=True))
# def touch(filename):
#     """Print FILENAME if the file exists."""
#     click.echo(click.format_filename(filename))

#TODO: add exception when user cancel the pipeline job
# https://click.palletsprojects.com/en/stable/exceptions/
@pipeline.command()
@click.pass_context
@click.option('--file', 'file_path', default=DEFAULT_CONFIG_FILE_PATH, help='configuration \
file path. if --file not specified, default to .cicd-pipelines/pipelines.yml')
@click.option('--pipeline', 'pipeline', help='pipeline name to run' )
@click.option('-r', '--repo', 'repo', default='./', help='repository url or \
local directory path')
@click.option('-b', '--branch', 'branch', default='main', help='repository branch name')
@click.option('-c', '--commit', 'commit', default='HEAD', help='commit hash')
@click.option('--local', 'local', help='run pipeline locally', is_flag=True)
@click.option('--dry-run', 'dry_run', help='dry-run options to simulate the pipeline\
process', is_flag=True)
@click.option('--yaml', 'yaml_output', help='print output in yaml format', is_flag=True)
@click.option('--override', 'overrides', multiple=True,
              help="Override configuration in 'key=value' format")
def run(ctx, file_path:str, pipeline:str, repo:str, branch:str, commit:str, local:bool,
        dry_run:bool, yaml_output:bool, overrides):
    """Run pipeline given the configuration file. 

    Command to run `cid pipeline run <config_filename>`
    Command for dry-run `cid pipeline run --dry-run --repo <repo> --branch <branch_name> 
    --commit <commit_hash>`
    Args:
        name (str): configuration file name
        repo (str): repository url or local directory path
        branch (str): branch name of the repository
        commit (str): specific commit hash. by default, it is the latest (HEAD).
        local (bool): execute pipeline locally.
        dry_run (bool): plan the pipeline without creating 
        yaml (bool): print output in yaml format
    """
    source_pipeline = ctx.get_parameter_source("pipeline")
    filepath_pipeline = ctx.get_parameter_source("file_path")

    # --file and --pipeline are mutually exclusive, raise error if both value are provided
    if source_pipeline != click.core.ParameterSource.DEFAULT:
        if filepath_pipeline != click.core.ParameterSource.DEFAULT:
            click.echo("cid: invalid flag. you can only pass --file or --pipeline \
and can't be both.")
            return

    if overrides:
        try:
            overrides = MongoHelper.build_nested_dict(overrides)
            # print(override_configs)
        except ValueError as e:
            click.secho(str(e), fg='red')
            return
    control = Controller()

    # TODO - Del 2024-11-04 Update Note and Fix
    # To follow the key naming in SessionDetail
    # change repo_source to repo_url
    # local flag is to indicate if the run is local or remote.
    # remote_repo is indicate if the repo itself is on local and remote,
    git_details = {
        "repo_url": repo,
        "branch": branch,
        "commit_hash": commit,
        "remote_repo": local,
    }

    status, message, pipeline_id = control.run_pipeline(config_file=file_path, pipeline=pipeline,
                    dry_run=dry_run, git_details=git_details,
                    local=local, yaml_output=yaml_output,
                    override_configs=overrides)

    logger.debug(f"pipeline run status: {status}, ")
    #logger.debug(f"pipeline_id: {pipeline_id}")
    if status:
        click.secho(f"{message}", fg='green')
    else:
        click.secho(f"{message}", fg='red')
    # TODO - To Discuss, why do we need to show pipeline_id to user
    click.echo(f"pipeline_id: {pipeline_id}")

@pipeline.command()
@click.option('--repo', default='local', help="Obtain logs for this repo")
@click.option('--tail', default=20, help="Number of log lines to display")
def log(tail:str, repo:str):
    """ Obtains logs of pipeline run attached to current repository

    Args:
        repo (str): Repository given by user for previous logs
        tail (str): Last lines to be obtained by user
    """

    current_time = str(time.time())
    hash_object = hashlib.md5(current_time.encode())
    pipeline_hash = hash_object.hexdigest()[:8]

    # Mock output of logs for now
    log_output = [
        "[2024-10-01 10:00:00] Starting pipeline 'Build and Test'",
        "[2024-10-01 10:00:10] Build: Success",
        "[2024-10-01 10:00:20] Test: Running tests...",
        "[2024-10-01 10:01:00] Test: Success",
        "[2024-10-01 10:02:00] Deploy: Success",
        "[2024-10-01 10:03:00] Pipeline 'Build and Test' completed."
    ]

    mock_log = log_output[-tail:]

    # Formatting nicely for better user view
    click.echo(f"\nLast pipeline command output: {repo} : {pipeline_hash}")
    click.echo("")
    click.echo("\n".join(mock_log))
    click.echo(f"\n[{pipeline_hash}] Pipeline 'Build and Test' completed.\n")
    # Optionally log this action for debugging
    # logger.debug(f"Showing the last {tail} lines of the pipeline log with hash {pipeline_hash}")
