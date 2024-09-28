""" All related commands for pipeline actions
"""
import click

@click.group()
def pipeline():
    """ All commands related to pipeline
    """
    # pass

@pipeline.command()
@click.option('--name', default='Team 4', help='name to greet')
def greet(name:str):
    """ simple cli command just to test the command line interface

    Args:
        name (str): name of person to greet
    """
    click.echo(f'Hello {name}')
