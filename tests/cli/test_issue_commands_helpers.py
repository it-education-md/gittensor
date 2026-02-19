# The MIT License (MIT)
# Copyright © 2025 Entrius

"""Unit tests for issue command helpers."""

import click
import pytest

from gittensor.cli.issue_commands.helpers import (
    ALPHA_RAW_UNIT,
    MIN_BOUNTY_RAW,
    validate_bounty_amount,
)

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
