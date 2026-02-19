# The MIT License (MIT)
# Copyright © 2025 Entrius

"""Unit tests for issue command helpers."""

import click
import pytest

from gittensor.cli.issue_commands.helpers import (
    ALPHA_RAW_UNIT,
    ISSUE_INPUT_MAX,
    ISSUE_INPUT_MIN,
    MIN_BOUNTY_RAW,
    ensure_github_issue_for_registration,
    ensure_github_repository_exists,
    validate_bounty_amount,
)

# ============================================================================
# Repository Validation Tests
# ============================================================================


@pytest.mark.parametrize(
    'value',
    ['entrius/gittensor', 'entrius/my_repo', 'entrius/my.repo', 'entrius/my-repo'],
)
def test_ensure_github_repository_exists_accepts_valid_repo_names(value, mock_github_repo_exists):
    ensure_github_repository_exists(value)


@pytest.mark.parametrize(
    'value',
    [
        '',
        '   ',
        '//btcli',
        'a/b/c/d',
        ' /repo',
        'opentensor/',
        '/btcli',
        'open tensor/btcli',
        'opentensor/bt cli',
        'open_tensor/btcli',
        'open.tensor/btcli',
        'open*tensor/btcli',
        'opentensor/btcli?',
    ],
)
def test_ensure_github_repository_exists_rejects_invalid_repo_names(value, fail_if_github_called):
    with pytest.raises(click.BadParameter):
        ensure_github_repository_exists(value)


def test_ensure_github_repository_exists_rejects_404(mock_github_repo_404):
    with pytest.raises(click.BadParameter, match="Repository 'entrius/missing-repo' not found on GitHub"):
        ensure_github_repository_exists('entrius/missing-repo')


def test_ensure_github_repository_exists_handles_unreachable_github(mock_github_unreachable):
    with pytest.raises(click.ClickException, match='GitHub is currently unreachable'):
        ensure_github_repository_exists('entrius/gittensor')


def test_ensure_github_repository_exists_handles_non_404_http_errors(mock_github_http_500):
    with pytest.raises(click.ClickException, match='Could not verify repository on GitHub'):
        ensure_github_repository_exists('entrius/gittensor')


# ============================================================================
# Issue Validation Tests
# ============================================================================


@pytest.mark.parametrize('value', [0, -1, 1_000_000])
def test_ensure_github_issue_for_registration_rejects_out_of_range_without_network(value, fail_if_github_called):
    with pytest.raises(click.BadParameter, match=f'between {ISSUE_INPUT_MIN} and {ISSUE_INPUT_MAX}'):
        ensure_github_issue_for_registration('entrius/gittensor', value)


def test_ensure_github_issue_for_registration_accepts_open_issue(mock_github_issue_open):
    assert ensure_github_issue_for_registration('entrius/gittensor', 210) is True


@pytest.mark.parametrize('value', [ISSUE_INPUT_MIN, ISSUE_INPUT_MAX])
def test_ensure_github_issue_for_registration_accepts_range_boundaries(value, mock_github_issue_open):
    assert ensure_github_issue_for_registration('entrius/gittensor', value) is True


def test_ensure_github_issue_for_registration_warns_path_for_closed_issue(mock_github_issue_closed):
    assert ensure_github_issue_for_registration('entrius/gittensor', 210) is False


def test_ensure_github_issue_for_registration_rejects_pull_request(mock_github_issue_pr):
    with pytest.raises(click.BadParameter, match='#210 is a pull request, not an issue'):
        ensure_github_issue_for_registration('entrius/gittensor', 210)


def test_ensure_github_issue_for_registration_rejects_404(mock_github_issue_404):
    with pytest.raises(click.BadParameter, match='Issue #210 not found on GitHub'):
        ensure_github_issue_for_registration('entrius/gittensor', 210)


def test_ensure_github_issue_for_registration_handles_unreachable_github(mock_github_unreachable):
    with pytest.raises(click.ClickException, match='GitHub is currently unreachable'):
        ensure_github_issue_for_registration('entrius/gittensor', 210)


def test_ensure_github_issue_for_registration_handles_non_404_http_errors(mock_github_http_500):
    with pytest.raises(click.ClickException, match='Could not verify issue on GitHub'):
        ensure_github_issue_for_registration('entrius/gittensor', 210)


# ============================================================================
# Validate Bounty Amount Tests
# ============================================================================


def test_validate_bounty_amount_accepts_integer_value():
    raw, bounty = validate_bounty_amount('10')
    assert raw == MIN_BOUNTY_RAW
    assert str(bounty) == '10'


def test_validate_bounty_amount_accepts_nine_decimals():
    raw, _ = validate_bounty_amount('10.123456789')
    assert raw == 10_123_456_789


def test_validate_bounty_amount_rejects_more_than_nine_decimals():
    with pytest.raises(click.BadParameter, match='up to 9 decimal places'):
        validate_bounty_amount('10.12345678911')


def test_validate_bounty_amount_rejects_below_minimum():
    with pytest.raises(click.BadParameter, match='Minimum bounty is 10 ALPHA'):
        validate_bounty_amount('9.999999999')


@pytest.mark.parametrize('value', ['', '   '])
def test_validate_bounty_amount_rejects_empty_input(value):
    with pytest.raises(click.BadParameter, match='Bounty is required'):
        validate_bounty_amount(value)


def test_validate_bounty_amount_accepts_exact_minimum_with_trailing_zeroes():
    raw, _ = validate_bounty_amount('10.000000000')
    assert raw == MIN_BOUNTY_RAW


@pytest.mark.parametrize('value', ['0', '-1'])
def test_validate_bounty_amount_rejects_non_positive_values(value):
    with pytest.raises(click.BadParameter, match='Minimum bounty is 10 ALPHA'):
        validate_bounty_amount(value)


def test_validate_bounty_amount_accepts_scientific_notation_for_minimum():
    raw, _ = validate_bounty_amount('1e1')
    assert raw == MIN_BOUNTY_RAW


def test_validate_bounty_amount_accepts_very_large_value():
    raw, _ = validate_bounty_amount('1000000000.123456789')
    assert raw == 1_000_000_000_123_456_789


def test_validate_bounty_amount_rejects_invalid_input():
    with pytest.raises(click.BadParameter, match='Invalid bounty amount'):
        validate_bounty_amount('not-a-number')


def test_validate_bounty_amount_rejects_non_finite_values():
    with pytest.raises(click.BadParameter, match='finite number'):
        validate_bounty_amount('NaN')
    with pytest.raises(click.BadParameter, match='finite number'):
        validate_bounty_amount('Infinity')


def test_validate_bounty_amount_raw_units_match_alpha_constant():
    raw, _ = validate_bounty_amount('11')
    assert raw == 11 * ALPHA_RAW_UNIT
