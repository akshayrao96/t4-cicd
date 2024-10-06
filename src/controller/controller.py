""" All related Controller
"""
import click
from util.common_utils import (get_logger)



class Controller:
    """This is class controller
    """
    def __init__(self):
        self.logger = get_logger('cli.cmd_pipeline')

    def run_pipeline(self, **kwargs):
        """
        Executes the job by coordinating the repository, runner, artifact store, and logger.
        """
        click.echo("I called this run_pipeline command with the following args:")
        ## Option #1: Loop through kwargs ##
        #for key, value in kwargs.items():
        #    click.echo(f"{key} = {value}")

        ## Option #2: get key of the kwargs ##
        click.echo(f"config_file = {kwargs.get('config_file')}")
        click.echo(f"repo_url = {kwargs.get('repo_url')}")
        click.echo(f"dry_run = {kwargs.get('dry_run')}")

    def setup_pipeline(self):
        """
        setup pipeline when `cid pipeline setup` is called for the first time.
        """
        #TODO: future implementation
