""" All related commands for pipeline actions """
# pylint: disable=logging-fstring-interpolation
import hashlib
import time
import click
from util.common_utils import get_logger
from controller.controller import (Controller)

DEFAULT_CONFIG_FILE_PATH = ".cicd-pipelines/pipeline.yml"

logger = get_logger('cli.cmd_pipeline')
control = Controller()

@click.group(invoke_without_command=True)
@click.pass_context
def pipeline(ctx):
    """
    All commands related to pipeline
    """
    if ctx.invoked_subcommand is None:
        click.echo(f"Run pipeline check with default config file path={DEFAULT_CONFIG_FILE_PATH}")
        click.echo(ctx.get_help())

@pipeline.command()
@click.option('--config-file', default='pipeline.yml', help='configuration file name')
@click.option('-r', '--repo-url', 'repo_url', default='local', help='repository url')
@click.option('--dry-run', 'dry_run', help='dry-run options to simulate the pipeline\
process', default=False, show_default=True)
def run(config_file: str, repo_url: str, dry_run: bool):
    """ Run pipeline given the configuration file. 
        Command to run `cid pipeline run <config_file>`
    """
    if dry_run:
        click.echo(f"This executes the dry-run when dry-run flag is set \
to true (--dry-run={dry_run})")
        return

    #call run_pipeline
    click.echo(f'Run config file called {config_file} at repo {repo_url}')

    pipeline_details = control.run_pipeline(config_file=config_file,
                                            repo_url=repo_url, dry_run=dry_run)

    logger.debug(f"pipeline run response: {pipeline_details}")
    click.echo(f"pipeline run response: {pipeline_details}")

# Pipeline logs
@pipeline.command()
@click.option('--repo', default='local', help="Obtain logs for this repo")
@click.option('--tail', default=20, help="Number of log lines to display")
def log(tail: str, repo:str):
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
