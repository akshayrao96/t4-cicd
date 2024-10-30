""" Test cid pipeline command
"""
from click.testing import CliRunner
from cli import (__main__, cmd_pipeline)


def test_cid():
    """ Test the main cid command just by calling it with --help option
    """
    runner = CliRunner()
    result = runner.invoke(__main__.cid, '--help')
    # 0 exit code mean successful
    assert result.exit_code == 0


def test_pipeline_help():
    """ Test the main pipeline command just by calling it with --help option
    """
    runner = CliRunner()
    result = runner.invoke(cmd_pipeline.pipeline, '--help')
    # 0 exit code mean successful
    assert result.exit_code == 0

# def test_pipeline_no_argument():
#     """ Test the main pipeline command (`cid pipeline`) with no argument, which
#       should perform the dry-run that has the same effect as 
#       `cid pipeline --check --config-file <config>
#     """
#     runner = CliRunner()
#     result = runner.invoke(cmd_pipeline.pipeline)

#     # 0 exit code mean successful
#     assert result.exit_code == 0
#     assert result.output.rstrip() == 'Run pipeline check with default config \
# file path=.cicd-pipelines/pipeline.yml' 

def test_pipeline_run():
    """Test the `cid pipeline run` command with no argument. This should
        return error as it expects CONFIG_FILE argument
    """
    runner = CliRunner()
    result = runner.invoke(cmd_pipeline.pipeline, 'run')

    assert result.exit_code == 0

def test_pipeline_dry_run():
    """Test the `cid pipeline run --dry-run` command with no argument. This should
        return error as it expects CONFIG_FILE argument
    """

    runner = CliRunner()
    result = runner.invoke(cmd_pipeline.pipeline, ['run', '--dry-run'])

    assert result.exit_code == 0

def test_pipeline_multi_flag():
    """test if --file and --pipeline are passed as arguments. it should return error
    as it can't be both.
    """
    runner = CliRunner()
    result = runner.invoke(cmd_pipeline.pipeline, ['run', '--pipeline', 'valid_pipeline_default',
                                                   '--file', '.cicd-pipelines/pipelines.yml'])
    
    assert result.exit_code == 0
    assert result.output.rstrip() == "cid: invalid flag. you can only pass --file or \
--pipeline and can't be both."

def test_pipeline_log():
    """call pipeline log
    """
    runner = CliRunner()
    result = runner.invoke(cmd_pipeline.pipeline, ['log'])

    assert result.exit_code == 0

def test_pipeline_local():
    """set flag --local for cid pipeline run. For future, validate the response
    when pipeline runs successfully.
    """
    runner = CliRunner()
    result = runner.invoke(cmd_pipeline.pipeline, ['run', '--local'])

    assert result.exit_code == 0

def test_pipeline_run_output_yaml():
    """set cid pipeline run --yaml flag to format the output as valid yaml
    """
    runner = CliRunner()
    result = runner.invoke(cmd_pipeline.pipeline, ['run', '--dry-run', '--yaml'])

    assert result.exit_code == 0

# def test_pipeline_greet():
#     """ Test the greet function
#     """
#     runner = CliRunner()
#     result = runner.invoke(cmd_pipeline.greet)

#     assert result.exit_code == 0
#     # result.output will have newline ending, need to strip it
#     # we didnt pass any argument, so the output should use default value
#     assert result.output.rstrip() == 'Hello Team 4'

# def test_pipeline_log():
#     """ Test the `cid pipeline log` command.
#     """
#     runner = CliRunner()
#     result = runner.invoke(cmd_pipeline.pipeline, ['log', '--tail', '5'])

#     assert result.exit_code == 0

#     output = result.output.splitlines()

#     # Check hashcode is shown
#     assert output[1].startswith("Pipeline Hash: ")
