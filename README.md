# redcell

**A pre-launch red-team for LLM apps.** Point it at a running endpoint you own; redcell sends probes, verifies with evidence whether your system prompt leaked, and gives you a paste-ready defense directive — then you re-test to confirm the fix holds.

Not guesses, evidence. Every finding carries the exact input sent, the raw response received, and a deterministic verdict. No finding without proof.

## Scope — read this first

redcell tests **only** endpoints you own or have explicit written permission to test. Staying within that authorization is your responsibility. The tool always prints a scope notice; `--i-own-this` records your authorization in the output. This is a defensive pre-launch check, not a tool for attacking systems you don't control.

## What leaves your machine

- redcell talks **only** to the target URL you give it. Nothing is sent anywhere else.
- **BYOK** — bring your own keys; redcell never ships or phones home with credentials.
- Before every run it prints a transport disclosure: the target URL, whether the connection is encrypted, and your auth token **masked** (only the last 4 chars shown).
- The v0.1 core path makes **no external LLM calls** — probes are static, the verdict is a deterministic string match.

## Install

Requires Python 3.10+.

```bash
pip install redcell
```

## Quickstart

Run a scan against an endpoint you own:

```bash
redcell scan http://127.0.0.1:8000/chat --i-own-this
```

redcell prints what leaves your machine, runs the system-prompt-disclosure probes, and for any disclosure shows the evidence plus a paste-ready defense directive. Exit code is `1` when a disclosure is found (so CI can gate on it), `0` when clean.

Pass `--auth-bearer` or set `REDCELL_AUTH_BEARER` for targets behind a bearer token (see `.env.example`).

## What redcell covers

redcell tests the **AI layer** — where an LLM mediates the response. v0.1 focuses on **system prompt disclosure**. It does **not** cover traditional web/API vulnerabilities (SQL injection, auth bypass, etc.) — those belong to standard DAST/pentest tooling.

## License

BSL 1.1 — full text and licensor pending (see LICENSE).
