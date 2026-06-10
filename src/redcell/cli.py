"""redcell command-line interface.

``redcell scan <url>`` wires the pieces together: resolve auth, disclose what leaves the
machine, show the scope notice, load probe cases, run the deterministic checks, and print
findings as evidence plus a paste-ready fix directive for any disclosure.

Scope: test only endpoints you own or are explicitly authorized to test.

Note: this module deliberately does NOT use ``from __future__ import annotations`` so Typer
introspects real annotation objects (avoids stringized-annotation edge cases).
"""

from urllib.parse import urlsplit

import typer

from redcell import __version__
from redcell.config import CANARY_DEFAULT, resolve_auth_token, transport_disclosure
from redcell.probes.corpus import load_cases
from redcell.probes.run import run_checks
from redcell.report.findings import Finding
from redcell.report.fix_prompt import build_fix_prompt
from redcell.target.adapter import EndpointAdapter
from redcell.target.auth import build_auth_headers

app = typer.Typer(
    name="redcell",
    add_completion=False,
    no_args_is_help=True,
    help="redcell — pre-launch red-team scanner for LLM apps. Test ONLY endpoints you own.",
)

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}

SCOPE_NOTICE = (
    "SCOPE: redcell tests ONLY endpoints you own or have explicit written permission to "
    "test. Staying within that authorization is your responsibility."
)


@app.callback()
def _root() -> None:
    """redcell CLI — run `redcell scan <url>`."""
    # A callback (plus the extra `version` command) keeps `scan` an explicit subcommand;
    # a lone command with no callback would collapse to `redcell <url>`.


@app.command()
def version() -> None:
    """Print the redcell version."""
    typer.echo(f"redcell {__version__}")


def _parse_headers(headers: list[str]) -> dict[str, str]:
    """Parse repeatable ``--header 'Key: Value'`` strings into a dict."""
    parsed: dict[str, str] = {}
    for item in headers:
        if ":" not in item:
            raise typer.BadParameter(f"--header must be 'Key: Value', got: {item!r}")
        key, _, value = item.partition(":")
        parsed[key.strip()] = value.strip()
    return parsed


def _truncate(text: str, limit: int = 1000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [+{len(text) - limit} more chars]"


def _render_finding(finding: Finding) -> str:
    return (
        f"[turn {finding.turn_count}] probe {finding.case_id or 'n/a'} — {finding.verdict}\n"
        f"    input    : {finding.test_input}\n"
        f"    response : {_truncate(finding.raw_response)}"
    )


@app.command()
def scan(
    url: str = typer.Argument(
        ...,
        help="Target endpoint URL you own, e.g. http://127.0.0.1:8000/chat",
    ),
    canary: str = typer.Option(
        CANARY_DEFAULT, "--canary", help="Canary token the judge searches the response for."
    ),
    auth_bearer: str = typer.Option(
        None, "--auth-bearer", help="Bearer token for the target (else taken from env)."
    ),
    header: list[str] = typer.Option(
        [], "--header", "-H", help="Extra request header 'Key: Value' (repeatable)."
    ),
    corpus: str = typer.Option(
        None, "--corpus", help="Path to a corpus YAML file (default: packaged system_prompt_leak v0)."
    ),
    timeout: float = typer.Option(
        30.0, "--timeout", help="Per-request timeout in seconds."
    ),
    i_own_this: bool = typer.Option(
        False, "--i-own-this", help="Record that you own / are authorized to test this target."
    ),
) -> None:
    """Run the system-prompt-disclosure check against a target you own."""
    extra_headers = _parse_headers(header)
    token = resolve_auth_token(auth_bearer)
    request_headers = build_auth_headers(auth_bearer, extra_headers=extra_headers)

    # 1. Transport disclosure — what leaves this machine (auth shown masked).
    typer.echo("== transport disclosure (what leaves this machine) ==")
    for line in transport_disclosure(url, auth_token=token, timeout=timeout):
        typer.echo(f"  {line}")

    # 2. Scope notice + optional acknowledgement (non-blocking banner + ack model).
    typer.echo("")
    typer.echo(SCOPE_NOTICE)
    host = urlsplit(url).hostname or ""
    if i_own_this:
        typer.echo("  scope_acknowledged: true (--i-own-this)")
    else:
        typer.echo(
            "  scope_acknowledged: false — pass --i-own-this to record authorization (non-blocking)."
        )
        if host not in LOCAL_HOSTS:
            typer.echo("  WARNING: target is not localhost. Only continue if you are authorized.")

    # 3. Load probe cases.
    typer.echo("")
    try:
        cases = load_cases(path=corpus) if corpus else load_cases()
    except Exception as exc:  # clean CLI error instead of a traceback
        typer.echo(f"failed to load corpus: {exc}", err=True)
        raise typer.Exit(code=2)

    if not cases:
        typer.echo("no cases loaded — corpus is empty; nothing to run.")
        return

    # 4. Run the deterministic checks.
    typer.echo(f"loaded {len(cases)} case(s); searching responses for canary {canary!r}")
    typer.echo(f"running against {url} ...")
    adapter = EndpointAdapter(url, headers=request_headers, timeout=timeout)
    try:
        findings = run_checks(adapter, cases, canary)
    except Exception as exc:  # transport/connection failure -> clean message, no traceback
        typer.echo(f"could not complete checks against {url}: {exc!r}", err=True)
        raise typer.Exit(code=2)

    # 5. Print findings as evidence.
    typer.echo("")
    typer.echo("== evidence ==")
    for finding in findings:
        typer.echo(_render_finding(finding))

    # 6. Result + a fix directive for any disclosed finding.
    disclosed = [f for f in findings if f.verdict == "disclosed"]
    ack = str(i_own_this).lower()
    typer.echo("")
    typer.echo("== result ==")
    if not disclosed:
        typer.echo(
            f"NO DISCLOSURE: canary not surfaced across {len(findings)} probe(s). "
            f"scope_acknowledged={ack}"
        )
        return

    first = disclosed[0]
    typer.echo(
        f"DISCLOSURE: canary surfaced on turn {first.turn_count} "
        f"(probe {first.case_id or 'n/a'}). scope_acknowledged={ack}"
    )
    for finding in disclosed:
        fix = build_fix_prompt(finding)
        if fix:
            typer.echo("")
            typer.echo("== suggested fix (paste into your system prompt) ==")
            typer.echo(fix)
    # A disclosure is a finding: exit non-zero so CI/automation can detect it.
    raise typer.Exit(code=1)


def main() -> None:
    """Console-script entry point (pyproject: redcell = 'redcell.cli:main')."""
    app()


if __name__ == "__main__":
    main()
