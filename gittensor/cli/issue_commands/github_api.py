# The MIT License (MIT)
# Copyright © 2025 Entrius

"""GitHub API request helpers for issue commands."""

import json
from dataclasses import dataclass
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

GITHUB_API_BASE_URL = 'https://api.github.com'


@dataclass(frozen=True, slots=True)
class GitHubApiResponse:
    """GitHub API response."""

    status: Optional[int]
    body: Optional[bytes] = None
    network_error: Optional[str] = None


def _build_github_request(path: str) -> Request:
    return Request(
        f'{GITHUB_API_BASE_URL}{path}',
        headers={
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'gittensor-cli',
        },
    )


def _github_api_request(
    path: str,
    timeout_seconds: int,
    opener=urlopen,
    read_body: bool = False,
) -> GitHubApiResponse:
    request = _build_github_request(path)

    try:
        with opener(request, timeout=timeout_seconds) as response:
            status = getattr(response, 'status', 200)
            body = response.read() if read_body else None
            return GitHubApiResponse(status=status, body=body)
    except HTTPError as exc:
        return GitHubApiResponse(status=exc.code)
    except URLError as exc:
        reason = getattr(exc, 'reason', exc)
        return GitHubApiResponse(status=None, network_error=str(reason))


def github_api_get_status(
    path: str,
    timeout_seconds: int = 10,
    opener=urlopen,
) -> tuple[Optional[int], Optional[str]]:
    """
    Execute a GitHub API GET request.

    Args:
        path: API path beginning with '/' (e.g., '/repos/owner/repo').
        timeout_seconds: HTTP timeout for the request.
        opener: URL opener function (injected for testing).

    Returns:
        Tuple of (status_code, network_error).
    """
    response = _github_api_request(
        path,
        timeout_seconds=timeout_seconds,
        opener=opener,
        read_body=False,
    )
    return response.status, response.network_error


def github_api_get_json(
    path: str,
    timeout_seconds: int = 10,
    opener=urlopen,
) -> tuple[Optional[int], Optional[dict[str, Any]], Optional[str]]:
    """
    Execute a GitHub API GET request and decode JSON body.

    Args:
        path: API path beginning with '/'.
        timeout_seconds: HTTP timeout for the request.
        opener: URL opener function (injected for testing).

    Returns:
        Tuple of (status_code, payload, network_error).
    """
    response = _github_api_request(
        path,
        timeout_seconds=timeout_seconds,
        opener=opener,
        read_body=True,
    )

    if response.network_error is not None:
        return None, None, response.network_error

    json_data = None

    if response.body:
        try:
            json_data = json.loads(response.body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    return response.status, json_data, None
