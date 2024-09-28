""" main entry point for the program commands
"""
import click
from cli import cmd_pipeline

@click.group()
def cid():
    """ Main command to run the cicd system
    """
    # pass

# Add all sub commands to the main cid group
cid.add_command(cmd_pipeline.pipeline)
