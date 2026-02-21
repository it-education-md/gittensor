# The MIT License (MIT)
# Copyright © 2025 Entrius

"""Presentation helpers for issues read commands."""

from rich.panel import Panel
from rich.table import Table

from gittensor.cli.issue_commands.helpers import console, emit_json, emit_json_error, format_alpha

from .models import BountyPoolData, IssueSummary, IssuesContext, PendingHarvestData


def _issue_to_json(issue: IssueSummary) -> dict:
    fill_pct = (issue.bounty_amount / issue.target_bounty * 100) if issue.target_bounty > 0 else 0.0
    return {
        'id': issue.id,
        'repository_full_name': issue.repository_full_name,
        'issue_number': issue.issue_number,
        'bounty_amount_raw': issue.bounty_amount,
        'target_bounty_raw': issue.target_bounty,
        'fill_percent': round(fill_pct, 2),
        'status': issue.status,
    }


def show_missing_contract(json_output: bool = False) -> None:
    """Render missing-contract guidance."""
    if json_output:
        emit_json_error(
            'Contract address not configured.',
            hint='Set via: gitt config set contract_address <ADDR>',
        )
        return
    console.print('[red]Error: Contract address not configured.[/red]')
    console.print('[dim]Set via: gitt config set contract_address <ADDR>[/dim]')


def show_context(context: IssuesContext, truncate_contract: bool = False, json_output: bool = False) -> None:
    """Render command context header."""
    if json_output:
        return
    console.print(f'[dim]Network: {context.network_name} ({context.ws_endpoint})[/dim]')
    contract = context.contract_addr
    if truncate_contract:
        contract = f'{contract[:20]}...'
    console.print(f'[dim]Contract: {contract}[/dim]\n')


def show_issue_not_found(issue_id: int, json_output: bool = False) -> None:
    """Render issue-not-found warning."""
    if json_output:
        emit_json({'issue_id': issue_id, 'found': False})
        return
    console.print(f'[yellow]Issue {issue_id} not found.[/yellow]')


def show_issue_detail(
    context: IssuesContext,
    issue_id: int,
    issue: IssueSummary | None,
    json_output: bool = False,
) -> None:
    """Render single issue detail panel."""
    if json_output:
        emit_json(
            {
                'network': context.network_name,
                'rpc_url': context.ws_endpoint,
                'contract': context.contract_addr,
                'issue_id': issue_id,
                'found': issue is not None,
                'issue': _issue_to_json(issue) if issue else None,
            }
        )
        return

    if issue is None:
        show_issue_not_found(issue_id)
        return

    fill_pct = (issue.bounty_amount / issue.target_bounty * 100) if issue.target_bounty > 0 else 0

    console.print(
        Panel(
            f'[cyan]ID:[/cyan] {issue.id}\n'
            f'[cyan]Repository:[/cyan] {issue.repository_full_name}\n'
            f'[cyan]Issue Number:[/cyan] #{issue.issue_number}\n'
            f'[cyan]Bounty Amount:[/cyan] {format_alpha(issue.bounty_amount, decimals=4)} ALPHA\n'
            f'[cyan]Target Bounty:[/cyan] {format_alpha(issue.target_bounty, decimals=4)} ALPHA\n'
            f'[cyan]Fill %:[/cyan] {fill_pct:.1f}%\n'
            f'[cyan]Status:[/cyan] {issue.status}',
            title=f'Issue #{issue_id}',
            border_style='green',
        )
    )


def _format_bounty_display(issue: IssueSummary) -> str:
    if issue.target_bounty > 0:
        fill_pct = (issue.bounty_amount / issue.target_bounty) * 100
        if fill_pct >= 100:
            return f'{format_alpha(issue.bounty_amount, decimals=2)} (100%)'
        if issue.bounty_amount > 0:
            return (
                f'{format_alpha(issue.bounty_amount, decimals=2)}/{format_alpha(issue.target_bounty, decimals=2)}'
                f' ({fill_pct:.0f}%)'
            )
        return f'0.00/{format_alpha(issue.target_bounty, decimals=2)} (0%)'
    return format_alpha(issue.bounty_amount, decimals=2)


def show_issue_list(context: IssuesContext, issues: list[IssueSummary], json_output: bool = False) -> None:
    """Render issue list table."""
    if json_output:
        emit_json(
            {
                'network': context.network_name,
                'rpc_url': context.ws_endpoint,
                'contract': context.contract_addr,
                'count': len(issues),
                'issues': [_issue_to_json(issue) for issue in issues],
            }
        )
        return

    console.print('[bold cyan]Available Issues[/bold cyan]\n')

    table = Table(show_header=True, header_style='bold magenta')
    table.add_column('ID', style='cyan', justify='right')
    table.add_column('Repository', style='green')
    table.add_column('Issue #', style='yellow', justify='right')
    table.add_column('Bounty Pool', style='magenta', justify='right')
    table.add_column('Status', style='blue')

    if issues:
        for issue in issues:
            table.add_row(
                str(issue.id),
                issue.repository_full_name,
                f'#{issue.issue_number}',
                _format_bounty_display(issue),
                issue.status,
            )
        console.print(table)
        console.print(f'\n[dim]Showing {len(issues)} issue(s)[/dim]')
        console.print('[dim]Bounty Pool shows: filled/target (percentage)[/dim]')
    else:
        console.print('[yellow]No issues found. Register an issue with:[/yellow]')
        console.print('[dim]  gitt issues register --repo owner/repo --issue 1 --bounty 100[/dim]')


def show_bounty_pool(context: IssuesContext, data: BountyPoolData, json_output: bool = False) -> None:
    """Render bounty pool summary."""
    if json_output:
        emit_json(
            {
                'network': context.network_name,
                'rpc_url': context.ws_endpoint,
                'contract': context.contract_addr,
                'issue_count': data.issue_count,
                'bounty_pool_raw': data.total_bounty_pool,
                'bounty_pool_alpha': format_alpha(data.total_bounty_pool, decimals=4),
            }
        )
        return

    console.print(
        f'[green]Issue Bounty Pool:[/green] '
        f'{format_alpha(data.total_bounty_pool, decimals=4)} ALPHA ({data.total_bounty_pool} raw)'
    )
    console.print(f'[dim]Sum of bounty amounts from {data.issue_count} issue(s)[/dim]')


def show_pending_harvest(context: IssuesContext, data: PendingHarvestData, json_output: bool = False) -> None:
    """Render pending harvest summary."""
    if json_output:
        emit_json(
            {
                'network': context.network_name,
                'rpc_url': context.ws_endpoint,
                'contract': context.contract_addr,
                'issue_count': data.issue_count,
                'treasury_stake_raw': data.treasury_stake,
                'allocated_bounties_raw': data.total_bounty_pool,
                'pending_harvest_raw': data.pending_harvest,
                'treasury_stake_alpha': format_alpha(data.treasury_stake, decimals=4),
                'allocated_bounties_alpha': format_alpha(data.total_bounty_pool, decimals=4),
                'pending_harvest_alpha': format_alpha(data.pending_harvest, decimals=4),
            }
        )
        return

    console.print(f'[green]Treasury Stake:[/green] {format_alpha(data.treasury_stake, decimals=4)} ALPHA')
    console.print(f'[green]Allocated to Bounties:[/green] {format_alpha(data.total_bounty_pool, decimals=4)} ALPHA')
    console.print(f'[green]Pending Harvest:[/green] {format_alpha(data.pending_harvest, decimals=4)} ALPHA')


def show_error(message: str, json_output: bool = False) -> None:
    """Render generic command error."""
    if json_output:
        emit_json_error(message)
        return
    console.print(f'[red]Error: {message}[/red]')


def show_missing_dependency(error: Exception, json_output: bool = False) -> None:
    """Render dependency-missing error."""
    if json_output:
        emit_json_error(f'Missing dependency - {error}')
        return
    console.print(f'[red]Error: Missing dependency - {error}[/red]')
