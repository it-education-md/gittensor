# The MIT License (MIT)
# Copyright © 2025 Entrius

"""Click command wiring for issues read commands."""

import click
import re

from gittensor.cli.help import StyledCommand
from gittensor.cli.issue_commands.helpers import (
    console,
    print_error,
    print_preview,
    print_warning,
    print_hint,
    with_waiting
)

from . import presenter, register_service, service


def _simplify_error_message(error: Exception) -> str:
    """Normalize noisy runtime errors into concise user-facing messages."""
    message = str(error).strip()

    # Drop generic wrappers added by upstream libraries.
    for prefix in ('Generic error: ', 'Error: ', 'Registering issue: '):
        if message.startswith(prefix):
            message = message[len(prefix) :].strip()

    # Unwrap nested wrappers like FileNotFound("...") -> ...
    message = re.sub(r"\b\w+\(\"([^\"]+)\"\)", r'\1', message)
    message = re.sub(r"\b\w+\('([^']+)'\)", r'\1', message)

    return message


@click.command('register', cls=StyledCommand)
@click.option(
    '--repo',
    required=True,
    help='Repository in owner/repo format (e.g., opentensor/btcli)',
)
@click.option(
    '--issue',
    'issue_number',
    required=True,
    type=int,
    help='GitHub issue number',
)
@click.option(
    '--bounty',
    required=True,
    type=str,
    help='Bounty amount in ALPHA tokens',
)
@click.option(
    '--network',
    '-n',
    default=None,
    type=click.Choice(['finney', 'test', 'local'], case_sensitive=False),
    help='Network (finney/test/local)',
)
@click.option(
    '--rpc-url',
    default=None,
    help='Subtensor RPC endpoint (overrides --network)',
)
@click.option(
    '--contract',
    default='',
    help='Contract address (uses default if empty)',
)
@click.option(
    '--wallet-name',
    '--wallet.name',
    '--wallet',
    default='default',
    help='Wallet name (must be contract owner)',
)
@click.option(
    '--wallet-hotkey',
    '--wallet.hotkey',
    '--hotkey',
    default='default',
    help='Hotkey name',
)
def issue_register(
    repo: str,
    issue_number: int,
    bounty: str,
    network: str,
    rpc_url: str,
    contract: str,
    wallet_name: str,
    wallet_hotkey: str,
):
    """Register a new issue with a bounty (owner only)."""
    # console.print('\n[bold cyan]Register Issue for Bounty[/bold cyan]\n')
    try:
        with with_waiting('Validating the issue for boundy...'):
            registration = register_service.prepare_registration_data(
                repo=repo,
                issue_number=issue_number,
                bounty=bounty,
                network=network,
                rpc_url=rpc_url,
                contract=contract,
            )
    except Exception as e:
        print_error(_simplify_error_message(e))
        return

    print_preview(register_service.build_registration_preview(registration), title='Issue Registration')

    if not registration.issue_is_open:
        print_warning(f'The issue is already closed')

    if not bool(registration.context.contract_addr):
        console.print()
        print_error('contract address not configured.')
        print_hint('Run ./up.sh --issues to deploy the contract first.')
        return

    if not click.confirm('\nProceed with registration?', default=True):
        print_warning('Registration cancelled')
        return

    try:
        with with_waiting("Submitting on-chain transaction to contract..."):
            result = register_service.register_issue_on_chain(
                context=registration.context,
                repo=registration.repo,
                issue_number=registration.issue_number,
                bounty_amount=registration.bounty_amount,
                github_url=registration.github_url,
                wallet_name=wallet_name,
                wallet_hotkey=wallet_hotkey,
                progress_callback=console.print,
            )

        if hasattr(result, 'is_success') and not result.is_success:
            console.print('\n[red]Transaction failed: Contract rejected the request[/red]')

            error_info = getattr(result, 'error_message', None)
            is_revert = error_info and isinstance(error_info, dict) and error_info.get('name') == 'ContractReverted'

            if is_revert:
                console.print('[yellow]Possible reasons:[/yellow]')
                console.print('  • Issue already registered (same repo + issue number)')
                console.print('  • Bounty too low (minimum 10 ALPHA)')
                console.print('  • Invalid repository format (must be owner/repo)')
                console.print('  • Caller is not the contract owner')
                console.print('[dim]Use "gitt view issues" to check existing issues[/dim]')
            elif error_info:
                print_error(str(error_info))

            console.print(f'[cyan]Transaction Hash:[/cyan] {result.extrinsic_hash}')
            return

        console.print('\n[green]Issue registered successfully![/green]')
        console.print(f'[cyan]Transaction Hash:[/cyan] {result.extrinsic_hash}')
        console.print('[dim]Issue will be visible once bounty is funded via harvest_emissions()[/dim]')

    except FileNotFoundError as e:
        print_error(str(e))
    except ImportError as e:
        print_error(f'Missing dependency - {e}')
        print_hint('Install with: pip install substrate-interface bittensor')
    except Exception as e:
        error_message = e.args[0] if e.args else str(e)
        if 'ContractReverted' in error_message:
            print_error('\n[red]Transaction failed; contract rejected the request[/red]')
            print_warning('Possible reasons:')
            console.print('  • Issue already registered (same repo + issue number)')
            console.print('  • Bounty too low (minimum 10 ALPHA)')
            console.print('  • Invalid repository format (must be owner/repo)')
            console.print('  • Caller is not the contract owner')
            print_hint('Use "gitt view issues" to check existing issues')
        else:
            print_error(error_message)

@click.command('list', cls=StyledCommand)
@click.option(
    '--id',
    'issue_id',
    default=None,
    type=int,
    help='View a specific issue by ID',
)
@click.option(
    '--network',
    '-n',
    default=None,
    type=click.Choice(['finney', 'test', 'local'], case_sensitive=False),
    help='Network (finney/test/local)',
)
@click.option(
    '--rpc-url',
    default=None,
    help='Subtensor RPC endpoint (overrides --network)',
)
@click.option(
    '--contract',
    default='',
    help='Contract address (uses default if empty)',
)
@click.option('--json', 'json_output', is_flag=True, help='Output machine-friendly JSON')
@click.option('--verbose', '-v', is_flag=True, help='Show debug output for contract reads')
def issues_list(issue_id: int, network: str, rpc_url: str, contract: str, verbose: bool, json_output: bool):
    """
    [bold white]List issues or view a specific issue.[/bold white]
    [dim]
    Shows all issues with their status and bounty amounts.
    Use --id to view details for a specific issue.

    USAGE
    List all issues:
        [green]$[/green] gitt issues list

    Query a specific network:
        [green]$[/green] gitt i list --network test

    View a specific issue:
        [green]$[/green] gitt i list --id 1

    [bold]NOTE[/bold]:
    - Use [cyan]--id[/cyan] to inspect a single issue in detail.
    - Use [cyan]--verbose[/cyan] for contract-read debugging.
    [/dim]
    """
    context = service.build_context(network, rpc_url, contract)
    if not service.has_contract(context):
        presenter.show_missing_contract(json_output=json_output)
        return

    presenter.show_context(context, truncate_contract=True, json_output=json_output)
    try:
        issues = service.fetch_issues(context, verbose, strict=json_output)
    except ImportError as e:
        presenter.show_missing_dependency(e, json_output=json_output)
        return
    except Exception as e:
        presenter.show_error(str(e), json_output=json_output)
        return

    if issue_id is not None:
        issue = service.get_issue_by_id(issues, issue_id)
        presenter.show_issue_detail(context, issue_id, issue, json_output=json_output)
        return

    presenter.show_issue_list(context, issues, json_output=json_output)


@click.command('bounty-pool', cls=StyledCommand)
@click.option(
    '--network',
    '-n',
    default=None,
    type=click.Choice(['finney', 'test', 'local'], case_sensitive=False),
    help='Network (finney/test/local)',
)
@click.option(
    '--rpc-url',
    default=None,
    help='Subtensor RPC endpoint (overrides --network)',
)
@click.option(
    '--contract',
    default='',
    help='Contract address (uses config if empty)',
)
@click.option('--verbose', '-v', is_flag=True, help='Show debug output')
@click.option('--json', 'json_output', is_flag=True, help='Output machine-friendly JSON')
def issues_bounty_pool(network: str, rpc_url: str, contract: str, verbose: bool, json_output: bool):
    """View total bounty pool (sum of all issue bounty amounts)."""
    context = service.build_context(network, rpc_url, contract)
    if not service.has_contract(context):
        presenter.show_missing_contract(json_output=json_output)
        return

    presenter.show_context(context, json_output=json_output)
    try:
        result = service.fetch_bounty_pool(context, verbose)
        presenter.show_bounty_pool(context, result, json_output=json_output)
    except ImportError as e:
        presenter.show_missing_dependency(e, json_output=json_output)
    except Exception as e:
        presenter.show_error(str(e), json_output=json_output)


@click.command('pending-harvest', cls=StyledCommand)
@click.option(
    '--network',
    '-n',
    default=None,
    type=click.Choice(['finney', 'test', 'local'], case_sensitive=False),
    help='Network (finney/test/local)',
)
@click.option(
    '--rpc-url',
    default=None,
    help='Subtensor RPC endpoint (overrides --network)',
)
@click.option(
    '--contract',
    default='',
    help='Contract address (uses config if empty)',
)
@click.option('--verbose', '-v', is_flag=True, help='Show debug output')
@click.option('--json', 'json_output', is_flag=True, help='Output machine-friendly JSON')
def issues_pending_harvest(network: str, rpc_url: str, contract: str, verbose: bool, json_output: bool):
    """View pending harvest (treasury stake minus allocated bounties)."""
    context = service.build_context(network, rpc_url, contract)
    if not service.has_contract(context):
        presenter.show_missing_contract(json_output=json_output)
        return

    presenter.show_context(context, json_output=json_output)
    try:
        result = service.fetch_pending_harvest(context, verbose)
        presenter.show_pending_harvest(context, result, json_output=json_output)
    except ImportError as e:
        presenter.show_missing_dependency(e, json_output=json_output)
    except Exception as e:
        presenter.show_error(str(e), json_output=json_output)
