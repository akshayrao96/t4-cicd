""" main entry point for the program commands
"""
import click
from cli import (cmd_pipeline, cmd_config)


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(package_name='t4-cicd')
def cid(ctx):
    """ Main command to run cid
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Add all sub commands to the main cid group
cid.add_command(cmd_pipeline.pipeline)
cid.add_command(cmd_config.config)
