""" All related commands for pipeline actions """
# pylint: disable=logging-fstring-interpolation
import sys
import json
import click
from pydantic import ValidationError
from util.common_utils import (get_logger, ConfigOverride)
from util.model import (PipelineHist)
from controller.controller import (Controller)
import util.constant as c
DEFAULT_CONFIG_FILE_PATH = ".cicd-pipelines/pipelines.yml"
logger = get_logger('cli.cmd_pipeline')

@click.group()
def pipeline():
    """All commands related to pipeline"""

@pipeline.command()
@click.pass_context
@click.option('--file', 'file_path', default=DEFAULT_CONFIG_FILE_PATH, help='configuration \
file path. if --file not specified, default to .cicd-pipelines/pipelines.yml')
@click.option('--pipeline', 'pipeline_name', help='pipeline name to run' )
@click.option('-r', '--repo', 'repo', default=None, help='repository url or \
local directory path')
@click.option('-b', '--branch', 'branch', default=None, help='repository branch name')
@click.option('-c', '--commit', 'commit', default=None, help='commit hash')
@click.option('--local', 'local', help='run pipeline locally', is_flag=True)
@click.option('--dry-run', 'dry_run', help='dry-run options to simulate the pipeline\
process', is_flag=True)
@click.option('--yaml', 'yaml_output', help='print output in yaml format', is_flag=True)
@click.option('--override', 'overrides', multiple=True,
              help="Override configuration in 'key=value' format")
def run(ctx, file_path:str, pipeline_name:str, repo:str, branch:str, commit:str, local:bool,
        dry_run:bool, yaml_output:bool, overrides):
    """ Run pipeline given the configuration file. Base command is cid pipeline run, this will
    run the pipeline specified in .cicd-pipelines/pipelines.yml for current repository or 
    previously set repository. 
    
    To change the target repository, branch, commit, target pipeline by name / file path, 
    use the corresponding options. \f
    
    Args: 
        file_path (str, optional): configuration file name. 
        Default to .cicd-pipelines/pipelines.yml.
        pipeline_name (str, optional): target pipeline name. Default to None.
        repo (str, optional): repository url or local directory path. 
        Default to current working directory ('./').
        branch (str, optional): branch name of the repository. Default to main.
        commit (str, optional): specific commit hash. Default to the latest (HEAD).
        local (bool, optional): If True, execute pipeline locally. Default False.
        dry_run (bool, optional): If True, plan the pipeline without creating. Default False.
        yaml (bool, optional): If True, print output in yaml format. Default False.
    """
    source_pipeline = ctx.get_parameter_source("pipeline_name")
    filepath_pipeline = ctx.get_parameter_source("file_path")

    # --file and --pipeline are mutually exclusive, raise error if both value are provided
    if source_pipeline != click.core.ParameterSource.DEFAULT:
        if filepath_pipeline != click.core.ParameterSource.DEFAULT:
            message = "cid: invalid flag. you can only pass --file "
            message += "or --pipeline and can't be both."
            click.secho(message, fg='red')
            sys.exit(2)

    if overrides:
        try:
            overrides = ConfigOverride.build_nested_dict(overrides)
        except ValueError as e:
            click.secho(str(e), fg='red')
            sys.exit(2)
    else:
        # !! click multiple value option will construct a tuple,
        # empty override will be an empty tuple.
        overrides = None

    controller = Controller()
    status, message, repo_details = controller.handle_repo(
        repo_url=repo,
        branch=branch,
        commit_hash=commit
    )
    if not status:
        click.secho(message, fg='red')
        sys.exit(2)
    click.secho(message, fg='green')

    status, message = controller.run_pipeline(
        config_file=file_path,
        pipeline_name=pipeline_name,
        dry_run=dry_run,
        git_details=repo_details,
        local=local,
        yaml_output=yaml_output,
        override_configs=overrides)

    logger.debug(f"pipeline run status: {status}, ")
    if status:
        click.secho(f"{message}", fg='green')
    else:
        click.secho(f"{message}", fg='red')
        sys.exit(1)


@pipeline.command()
@click.pass_context
@click.option('-r', '--repo', 'repo_url', default='./', help='url of the repository (https://)')
@click.option('--local', 'local', help='retrieve local pipeline history', is_flag=True)
@click.option('--pipeline', 'pipeline_name', default=None,
              help='pipeline name to get the history')
@click.option('-b', '--branch', 'branch', default='main',
              help="branch name of the repository; default is 'main'")
@click.option('-s', '--stage', 'stage', default=None, help='stage name to view report; \
default stages options: [build, test, doc, deploy]')
@click.option('--job', 'job', default=None, help="job name to view report")
@click.option('-r', '--run', 'run_number', default=None, help='run number to get the report')
def report(ctx, repo_url:str, local:bool, pipeline_name:str, branch:str, stage:str,
           job:str, run_number:int):
    """Report pipeline provides user to retrieve the pipeline history. \f
    To retrieve which REPO_URL you currently at, run `cid config get-repo | grep "Repository URL:"`
    Example of basic usage: \f
      cid pipeline report --repo REPO_URL | list all report for a repository \f
      cid pipeline report --repo REPO_URL --pipeline PIPELINE_NAME | list all runs of the given
      PIPELINE_NAME.\f
      cid pipeline report --repo REPO_URL --pipeline PIPELINE_NAME --run RUN | list the output
      history of the run # given the PIPELINE_NAME and RUN number. \f

    Args:
        ctx (context): click context
        repo_url (str): repository url to display the report
        local (bool): (current version) everything runs locally
        pipeline_name (str): pipeline name to get the report
        branch (str): branch to get the report (default to main)
        stage (str): stage name to view the report options such as (build, test, doc, deploy)
        job (str): filter by job name for the report
        run_number (int): the run number to view the specific run report.
    """
    ctrl = Controller()
    pipeline_model = {}

    #TODO: validate if --run is specified, --pipeline needs to exist

    pipeline_model[c.FIELD_PIPELINE_NAME] = pipeline_name

    if ctx.get_parameter_source("repo_url") != click.core.ParameterSource.DEFAULT:
        #TODO: if repo location is specify as "--repo .", this needs to get the current $pwd.
        pipeline_model[c.FIELD_REPO_URL] = repo_url
        # grab repo_name from the URL
        pipeline_model[c.FIELD_REPO_NAME] = repo_url.split('/')[-1]

    # this is needed when user specify a different value than the default one.
    # this matches with the PipelineHist model.
    pipeline_model[c.FIELD_BRANCH] = branch
    pipeline_model['stage'] = stage
    pipeline_model['job'] = job
    pipeline_model['run'] = run_number
    pipeline_model[c.FIELD_IS_REMOTE] = local

    try:
        err_msg = None
        pipeline_model = PipelineHist.model_validate(pipeline_model)
    except ValidationError as ve:
        errors = json.loads(ve.json())
        for error in errors:
            err_type = error['type']
            if err_type == "int_parsing":
                err_msg = f"Unknown Input: '{error.get('input', 'N/A')}', "
                err_msg += f"Flag: {error['loc']}, Message: {error['msg']}"
            elif err_type == "missing":
                if c.FIELD_REPO_URL in error['loc']:
                    err_msg = f"missing {error['loc']} input. please run cid pipeline report"
                    err_msg += "--repo.\nFor further help, run cid pipeline report --help "
                    err_msg += "for valid usage"

            if err_msg:
                click.secho(err_msg, fg="red")
        sys.exit(2)

    #Step 2. call pipeline_history
    resp_success, resp_message = ctrl.pipeline_history(pipeline_model)
    if not resp_success:
        click.secho(resp_message, fg='red')
        sys.exit(1)

    click.secho(resp_message, fg='green')
