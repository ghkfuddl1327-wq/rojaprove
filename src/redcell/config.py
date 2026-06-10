"""redcell configuration: bring-your-own-key (BYOK) loading, secret masking, and
transport disclosure (what leaves this machine during a scan).

No secrets are persisted. Auth tokens are read from the environment at runtime and are
only ever shown in masked form.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from urllib.parse import urlsplit

# Default canary token the judge searches for. MUST match the demo target's CANARY in
# examples/demo_target/app.py (kept in sync manually; a unit test will guard this).
CANARY_DEFAULT = "RC-CANARY-7Q2X-9F4K-DEMO"

# Environment variable names for BYOK auth against a target you own or are authorized to test.
ENV_AUTH_BEARER = "REDCELL_AUTH_BEARER"
ENV_TARGET_API_KEY = "REDCELL_TARGET_API_KEY"

# Local hostnames that don't warrant a cleartext-transport warning.
_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def mask_secret(secret: str | None) -> str:
    """Return a display-safe form of a secret: reveal only the last 4 characters.

    Returns "<none>" for empty input and fully masks anything 4 characters or shorter.
    Never returns the raw value.
    """
    if not secret:
        return "<none>"
    if len(secret) <= 4:
        return "****"
    return "****" + secret[-4:]


def resolve_auth_token(
    cli_bearer: str | None = None,
    env: Mapping[str, str] | None = None,
) -> str | None:
    """Load the bearer token to send to the target (BYOK), by precedence:

    explicit CLI value > REDCELL_AUTH_BEARER > REDCELL_TARGET_API_KEY > None.
    """
    env = os.environ if env is None else env
    if cli_bearer:
        return cli_bearer
    return env.get(ENV_AUTH_BEARER) or env.get(ENV_TARGET_API_KEY) or None


def transport_disclosure(
    url: str,
    *,
    auth_token: str | None = None,
    header_name: str = "Authorization",
    timeout: float | None = None,
) -> list[str]:
    """Build human-readable lines disclosing what will leave this machine during a scan:
    the target URL, whether the connection is encrypted, and whether (masked) auth is sent.

    Intended to be printed before any request is made.
    """
    parts = urlsplit(url)
    host = parts.hostname or ""
    is_local = host in _LOCAL_HOSTS

    lines = [f"Target: {url}"]
    if parts.scheme == "https":
        lines.append("Transport: HTTPS (encrypted).")
    elif is_local:
        lines.append("Transport: HTTP to localhost (not encrypted; stays on this machine).")
    else:
        lines.append(
            "Transport: HTTP — NOT encrypted. Inputs and any auth travel in cleartext."
        )

    if auth_token:
        lines.append(f"Auth: {header_name} bearer {mask_secret(auth_token)} (sent to target).")
    else:
        lines.append("Auth: none attached.")

    if timeout is not None:
        lines.append(f"Per-request timeout: {timeout:g}s")

    return lines
