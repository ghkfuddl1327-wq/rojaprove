"""Run routine: send each probe case to the target and judge the response.

Iterates loaded Case objects, sends each test input via the EndpointAdapter, applies the
deterministic canary judge to the raw response, and accumulates Findings with an
incrementing turn count. Optionally stops at the first disclosure.
"""

from __future__ import annotations

from collections.abc import Sequence

from rojaprove.judge.canary import judge
from rojaprove.probes.corpus import Case
from rojaprove.report.findings import Finding
from rojaprove.target.adapter import EndpointAdapter


def run_checks(
    adapter: EndpointAdapter,
    cases: Sequence[Case],
    canary: str,
    *,
    stop_on_first_disclosure: bool = True,
) -> list[Finding]:
    """Send each case to the target, judge it, and collect Findings.

    ``turn_count`` is 1-based and increments per case sent. When
    ``stop_on_first_disclosure`` is True (default), the run halts after the first case
    whose response discloses the canary, so the last Finding's ``turn_count`` is the number
    of turns it took to disclose.
    """
    findings: list[Finding] = []
    for turn, case in enumerate(cases, start=1):
        response = adapter.send(case.test_input)
        # Scan matches case-insensitively: a real leak may re-case the canary. The pure
        # judge() default stays case-sensitive (test_case_sensitive_by_default).
        verdict = judge(response.raw_text, canary, case_sensitive=False)
        findings.append(
            Finding(
                case_id=case.id,
                test_input=case.test_input,
                raw_response=response.raw_text,
                verdict=verdict,
                turn_count=turn,
            )
        )
        if stop_on_first_disclosure and verdict == "disclosed":
            break
    return findings
