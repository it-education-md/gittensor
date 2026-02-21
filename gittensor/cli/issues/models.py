# The MIT License (MIT)
# Copyright © 2025 Entrius

"""Data models for issues feature commands."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class IssuesContext:
    """Resolved network/contract context used by issues read commands."""

    contract_addr: str
    ws_endpoint: str
    network_name: str


@dataclass(frozen=True)
class IssueSummary:
    """Normalized issue payload used by issue presenters."""

    id: int
    repository_full_name: str
    issue_number: int
    bounty_amount: int
    target_bounty: int
    status: str


@dataclass(frozen=True)
class BountyPoolData:
    """Computed issue bounty-pool totals."""

    total_bounty_pool: int
    issue_count: int


@dataclass(frozen=True)
class PendingHarvestData:
    """Computed pending-harvest totals."""

    treasury_stake: int
    total_bounty_pool: int
    pending_harvest: int
    issue_count: int


@dataclass(frozen=True)
class IssueRegistrationData:
    """Preflight data needed for issue registration flow."""

    repo: str
    issue_number: int
    issue_is_open: bool
    bounty_amount: int
    bounty_alpha: Decimal
    github_url: str
    context: IssuesContext
