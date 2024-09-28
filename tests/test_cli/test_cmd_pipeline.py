""" This shows how a test can be written for a cli command
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

def test_pipeline():
    """ Test the main pipeline command just by calling it with --help option
    """
    runner = CliRunner()
    result = runner.invoke(cmd_pipeline.pipeline, '--help')
    # 0 exit code mean successful
    assert result.exit_code == 0
    
def test_pipeline_greet():
    """ Test the greet function
    """
    runner = CliRunner()
    result = runner.invoke(cmd_pipeline.greet)
    
    assert result.exit_code == 0
    # result.output will have newline ending, need to strip it
    # we didnt pass any argument, so the output should use default value
    assert result.output.rstrip() == 'Hello Team 4'