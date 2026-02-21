# The MIT License (MIT)
# Copyright © 2025 Entrius

"""Business logic for issue registration commands."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from gittensor.cli.issue_commands.helpers import (
    ensure_github_issue_for_registration,
    ensure_github_repository_exists,
    load_config,
    validate_bounty_amount,
    print_hint
)

from .models import IssueRegistrationData, IssuesContext
from .service import build_context


def _emit_progress(progress_callback: Callable[[str], None] | None, message: str) -> None:
    if progress_callback is not None:
        progress_callback(message)


def prepare_registration_data(
    repo: str,
    issue_number: int,
    bounty: str,
    network: str | None,
    rpc_url: str | None,
    contract: str,
) -> IssueRegistrationData:
    """Validate and build preflight data for issue registration."""
    ensure_github_repository_exists(repo)
    issue_is_open = ensure_github_issue_for_registration(repo, issue_number)
    bounty_amount, bounty_alpha = validate_bounty_amount(bounty)
    github_url = f'https://github.com/{repo}/issues/{issue_number}'
    context = build_context(network, rpc_url, contract)
    return IssueRegistrationData(
        repo=repo,
        issue_number=issue_number,
        issue_is_open=issue_is_open,
        bounty_amount=bounty_amount,
        bounty_alpha=bounty_alpha,
        github_url=github_url,
        context=context,
    )


def build_registration_preview(registration: IssueRegistrationData) -> str:
    """Build registration preview text for CLI confirmation."""
    contract_addr = registration.context.contract_addr or '(not configured)'
    return '\n'.join(
        [
            f'[cyan]Repository:[/cyan] {registration.repo}',
            f'[cyan]Issue Number:[/cyan] #{registration.issue_number}',
            f'[cyan]GitHub URL:[/cyan] {registration.github_url}',
            f'[cyan]Target Bounty:[/cyan] {registration.bounty_alpha:.2f} ALPHA',
            f'[cyan]Network:[/cyan] {registration.context.network_name}',
            f'[cyan]RPC Endpoint:[/cyan] {registration.context.ws_endpoint}',
            f'[cyan]Contract:[/cyan] {contract_addr}',
        ]
    )


def register_issue_on_chain(
    context: IssuesContext,
    repo: str,
    issue_number: int,
    bounty_amount: int,
    github_url: str,
    wallet_name: str,
    wallet_hotkey: str,
    *,
    progress_callback: Callable[[str], None] | None = None,
) -> Any:
    """Submit register_issue transaction and return contract exec result."""
    import bittensor as bt
    from substrateinterface import Keypair, SubstrateInterface
    from substrateinterface.contracts import ContractInstance

    substrate = SubstrateInterface(url=context.ws_endpoint)
    print_hint(f"Connected to {context.ws_endpoint}")
    
    config = load_config()
    effective_wallet = wallet_name if wallet_name != 'default' else config.get('wallet', wallet_name)
    effective_hotkey = wallet_hotkey if wallet_hotkey != 'default' else config.get('hotkey', wallet_hotkey)

    if context.network_name.lower() == 'local' and effective_wallet == 'default' and effective_hotkey == 'default':
        # _emit_progress(progress_callback, '[dim]Using //Alice for local development (no config set)...[/dim]')
        print_hint("Used //Alice for local development (no config set)")
        keypair = Keypair.create_from_uri('//Alice')
    else:
        # _emit_progress(progress_callback, f'[dim]Loading wallet {effective_wallet}/{effective_hotkey}...[/dim]')
        print_hint(f'Loaded wallet {effective_wallet}/{effective_hotkey}')
        wallet = bt.Wallet(name=effective_wallet, hotkey=effective_hotkey)
        print_hint('')
        keypair = wallet.coldkey

    contract_metadata = (
        Path(__file__).parent.parent.parent.parent
        / 'smart-contracts'
        / 'issues-v0'
        / 'target'
        / 'ink'
        / 'issue_bounty_manager.contract'
    )
    if not contract_metadata.exists():
        raise FileNotFoundError(f'Contract metadata not found at {contract_metadata}')

    contract = ContractInstance.create_from_address(
        contract_address=context.contract_addr,
        metadata_file=str(contract_metadata),
        substrate=substrate,
    )

    # _emit_progress(progress_callback, '[yellow]Calling register_issue on contract...[/yellow]')
    return contract.exec(
        keypair,
        'register_issue',
        args={
            'github_url': github_url,
            'repository_full_name': repo,
            'issue_number': issue_number,
            'target_bounty': bounty_amount,
        },
        gas_limit={'ref_time': 10_000_000_000, 'proof_size': 1_000_000},
    )
