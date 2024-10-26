""" main entry point for the program commands
"""
import click
from cli import (cmd_pipeline, cmd_config)


@click.group(invoke_without_command=True)
@click.option('--version', '-v', is_flag=True,
              help="Displays version of cid tool")
@click.pass_context
def cid(ctx, version):
    """ Main command to run cid
    """
    if version:
        click.echo("cid version 1.0.0")
        ctx.exit()

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Add all sub commands to the main cid group
cid.add_command(cmd_pipeline.pipeline)
cid.add_command(cmd_config.config)
