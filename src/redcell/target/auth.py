"""Build request headers (bearer-token auth) for the target under test.

Uses the BYOK token resolved by redcell.config.resolve_auth_token. The token is sent only
to the target you specify and is never logged in raw form (see config.mask_secret).
"""

from __future__ import annotations

from collections.abc import Mapping

from redcell.config import resolve_auth_token


def build_auth_headers(
    cli_bearer: str | None = None,
    *,
    extra_headers: Mapping[str, str] | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build request headers for the target.

    Resolves the bearer token via config.resolve_auth_token (explicit CLI value, then env),
    adds it as an ``Authorization: Bearer ...`` header when present, then merges any extra
    headers. Returns an empty dict when there is no token and no extra headers.
    """
    headers: dict[str, str] = {}
    token = resolve_auth_token(cli_bearer, env)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra_headers:
        headers.update(extra_headers)
    return headers
