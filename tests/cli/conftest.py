# The MIT License (MIT)
# Copyright © 2025 Entrius

"""Shared pytest fixtures for CLI tests."""

import json
from urllib.error import HTTPError, URLError

import pytest

import gittensor.cli.issue_commands.helpers as issue_helpers


@pytest.fixture
def mock_github_repo_exists(monkeypatch):
    """Mock GitHub repository check to return HTTP 200."""

    class _Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(issue_helpers, 'urlopen', lambda *_args, **_kwargs: _Response())


@pytest.fixture
def fail_if_github_called(monkeypatch):
    """Fail the test if GitHub HTTP is called."""

    monkeypatch.setattr(
        issue_helpers,
        'urlopen',
        lambda *_args, **_kwargs: pytest.fail('urlopen should not be called for this validation path'),
    )


@pytest.fixture
def mock_github_repo_404(monkeypatch):
    """Mock GitHub repository check to return HTTP 404."""

    def _raise_404(*_args, **_kwargs):
        raise HTTPError(
            url='https://api.github.com/repos/entrius/missing-repo',
            code=404,
            msg='Not Found',
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(issue_helpers, 'urlopen', _raise_404)


@pytest.fixture
def mock_github_unreachable(monkeypatch):
    """Mock GitHub repository check to raise a network URLError."""

    def _raise_unreachable(*_args, **_kwargs):
        raise URLError('Temporary failure in name resolution')

    monkeypatch.setattr(issue_helpers, 'urlopen', _raise_unreachable)


@pytest.fixture
def mock_github_http_500(monkeypatch):
    """Mock GitHub repository check to return HTTP 500."""

    def _raise_500(*_args, **_kwargs):
        raise HTTPError(
            url='https://api.github.com/repos/entrius/gittensor',
            code=500,
            msg='Server Error',
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(issue_helpers, 'urlopen', _raise_500)


@pytest.fixture
def mock_github_issue_open(monkeypatch):
    """Mock GitHub issue endpoint to return an open issue."""

    class _Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({'state': 'open'}).encode('utf-8')

    monkeypatch.setattr(issue_helpers, 'urlopen', lambda *_args, **_kwargs: _Response())


@pytest.fixture
def mock_github_issue_closed(monkeypatch):
    """Mock GitHub issue endpoint to return a closed issue."""

    class _Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({'state': 'closed'}).encode('utf-8')

    monkeypatch.setattr(issue_helpers, 'urlopen', lambda *_args, **_kwargs: _Response())


@pytest.fixture
def mock_github_issue_pr(monkeypatch):
    """Mock GitHub issue endpoint to return a pull request payload."""

    class _Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({'state': 'open', 'pull_request': {'url': 'https://api.github.com/repos/o/r/pulls/1'}}).encode(
                'utf-8'
            )

    monkeypatch.setattr(issue_helpers, 'urlopen', lambda *_args, **_kwargs: _Response())


@pytest.fixture
def mock_github_issue_404(monkeypatch):
    """Mock GitHub issue endpoint to return HTTP 404."""

    def _raise_404(*_args, **_kwargs):
        raise HTTPError(
            url='https://api.github.com/repos/entrius/gittensor/issues/9999',
            code=404,
            msg='Not Found',
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(issue_helpers, 'urlopen', _raise_404)
