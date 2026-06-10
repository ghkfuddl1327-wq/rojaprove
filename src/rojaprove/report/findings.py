"""Evidence model for rojaprove findings.

A ``Finding`` is the per-probe evidence record: the input that was sent, the raw response
captured from the target, the deterministic verdict, and the turn count at which it
occurred. Pydantic gives validation and easy JSON serialization for reports.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from rojaprove.judge.canary import Verdict


class Finding(BaseModel):
    """One probe's evidence: what was sent, what came back, and the verdict."""

    case_id: str | None = Field(
        None,
        description="Identifier of the probe case that produced this finding (Case.id), if known.",
    )
    test_input: str = Field(
        ..., description="The probe input that was sent to the target."
    )
    raw_response: str = Field(
        ..., description="The raw response text captured from the target."
    )
    verdict: Verdict = Field(
        ..., description="'disclosed' if the canary appeared in the response, else 'not_disclosed'."
    )
    turn_count: int = Field(
        ...,
        ge=1,
        description="1-based turn number: the running count of probes sent up to and including this one.",
    )
