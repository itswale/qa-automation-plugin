import click
from qa_plugin.core import QACore

@click.group()
def cli():
    pass

@click.command()
@click.option('--config', default='config.yaml', help='Path to config file')
@click.option('--test-type', default='all', help='Test type to run')
def run(config, test_type):
    core = QACore(config)
    results = core.run_tests(test_type)
    click.echo(f"Test Results: {results}")

cli.add_command(run)

if __name__ == '__main__':
    cli()