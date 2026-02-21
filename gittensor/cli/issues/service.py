# The MIT License (MIT)
# Copyright © 2025 Entrius

"""Business logic for issues commands."""

from __future__ import annotations

from typing import Any

from gittensor.cli.issue_commands.helpers import (
    _read_issues_from_child_storage,
    get_contract_address,
    read_issues_from_contract,
    resolve_network,
)

from .models import BountyPoolData, IssuesContext, IssueSummary, PendingHarvestData


def _to_int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _normalize_status(value: Any) -> str:
    if isinstance(value, dict):
        return str(list(value.keys())[0]) if value else 'Unknown'
    if isinstance(value, str):
        return value.capitalize()
    return str(value)


def build_context(network: str | None, rpc_url: str | None, contract: str) -> IssuesContext:
    """Resolve command context from flags/config."""
    contract_addr = get_contract_address(contract)
    ws_endpoint, network_name = resolve_network(network, rpc_url)
    return IssuesContext(contract_addr=contract_addr, ws_endpoint=ws_endpoint, network_name=network_name)


def has_contract(context: IssuesContext) -> bool:
    """Check if contract address is configured."""
    return bool(context.contract_addr)


def fetch_issues(context: IssuesContext, verbose: bool, strict: bool = False) -> list[IssueSummary]:
    """Load and normalize all issues from contract storage."""
    if strict:
        from substrateinterface import SubstrateInterface

        substrate = SubstrateInterface(url=context.ws_endpoint)
        raw_issues = _read_issues_from_child_storage(substrate, context.contract_addr, verbose)
    else:
        raw_issues = read_issues_from_contract(context.ws_endpoint, context.contract_addr, verbose)

    issues: list[IssueSummary] = []
    for item in raw_issues:
        issues.append(
            IssueSummary(
                id=_to_int_or_zero(item.get('id')),
                repository_full_name=str(item.get('repository_full_name', '')),
                issue_number=_to_int_or_zero(item.get('issue_number')),
                bounty_amount=_to_int_or_zero(item.get('bounty_amount')),
                target_bounty=_to_int_or_zero(item.get('target_bounty')),
                status=_normalize_status(item.get('status', 'unknown')),
            )
        )
    return issues


def get_issue_by_id(issues: list[IssueSummary], issue_id: int) -> IssueSummary | None:
    """Find a specific issue in an issue list."""
    return next((item for item in issues if item.id == issue_id), None)


def fetch_bounty_pool(context: IssuesContext, verbose: bool) -> BountyPoolData:
    """Compute total bounty pool for all issues."""
    from substrateinterface import SubstrateInterface

    substrate = SubstrateInterface(url=context.ws_endpoint)
    issues = _read_issues_from_child_storage(substrate, context.contract_addr, verbose)
    total_bounty_pool = sum(_to_int_or_zero(issue.get('bounty_amount', 0)) for issue in issues)
    return BountyPoolData(total_bounty_pool=total_bounty_pool, issue_count=len(issues))


def fetch_pending_harvest(context: IssuesContext, verbose: bool) -> PendingHarvestData:
    """Compute pending harvest = treasury stake - allocated bounty pool."""
    import bittensor as bt
    from substrateinterface import SubstrateInterface

    from gittensor.validator.issue_competitions.contract_client import (
        IssueCompetitionContractClient,
    )

    subtensor = bt.Subtensor(network=context.ws_endpoint)
    client = IssueCompetitionContractClient(
        contract_address=context.contract_addr,
        subtensor=subtensor,
    )
    treasury_stake = _to_int_or_zero(client.get_treasury_stake())

    substrate = SubstrateInterface(url=context.ws_endpoint)
    issues = _read_issues_from_child_storage(substrate, context.contract_addr, verbose)
    total_bounty_pool = sum(_to_int_or_zero(issue.get('bounty_amount', 0)) for issue in issues)

    pending_harvest = max(0, treasury_stake - total_bounty_pool)

    return PendingHarvestData(
        treasury_stake=treasury_stake,
        total_bounty_pool=total_bounty_pool,
        pending_harvest=pending_harvest,
        issue_count=len(issues),
    )
