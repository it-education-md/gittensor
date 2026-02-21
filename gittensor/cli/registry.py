# The MIT License (MIT)
# Copyright © 2025 Entrius

"""Central CLI command registry."""

import click

from gittensor.cli.help import StyledGroup

@click.group(name='issues', cls=StyledGroup)
def issues_group():
    """Issue management commands."""
    pass


def register_commands(cli):
    """Register CLI feature commands on the root CLI group."""
    # Import here to keep module import side effects localized.
    from gittensor.cli.issue_commands.admin import admin
    from gittensor.cli.issue_commands.mutations import issue_harvest
    from gittensor.cli.issue_commands.view import admin_info
    from gittensor.cli.issue_commands.vote import vote
    from gittensor.cli.issues import (
        issue_register,
        issues_bounty_pool,
        issues_list,
        issues_pending_harvest,
    )

    issues_group.add_command(issues_list, name='list')
    issues_group.add_command(issue_register, name='register')
    issues_group.add_command(issues_bounty_pool, name='bounty-pool')
    issues_group.add_command(issues_pending_harvest, name='pending-harvest')

    admin.add_command(admin_info, name='info')

    cli.add_command(issues_group, name='issues')
    if hasattr(cli, 'add_alias'):
        cli.add_alias('issues', 'i')

    cli.add_command(issue_harvest, name='harvest')
    cli.add_command(vote, name='vote')
    cli.add_command(admin)
    if hasattr(cli, 'add_alias'):
        cli.add_alias('admin', 'a')
