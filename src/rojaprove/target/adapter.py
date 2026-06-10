"""HTTP transport for the target endpoint under test.

Sends one input to the target's chat endpoint and captures the raw response text. This is
transport only — it carries no check content of its own; inputs come from the probe corpus.
Default contract matches the demo target:  POST {"message": <str>}  ->  {"reply": <str>}.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass
class TargetResponse:
    """The captured result of one request to the target."""

    status_code: int
    raw_text: str  # full response body as text — what the judge scans for the canary


class EndpointAdapter:
    """Minimal HTTP adapter that POSTs one message to the target and returns raw text.

    The request field name defaults to the demo contract ("message") but is parameterized
    so other endpoint shapes can be supported later without changing call sites.
    """

    def __init__(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        request_field: str = "message",
    ) -> None:
        self.url = url
        self.headers = {"Content-Type": "application/json", **(headers or {})}
        self.timeout = timeout
        self.request_field = request_field

    def send(self, text: str) -> TargetResponse:
        """POST a single input to the target and capture the raw response text.

        Returns the HTTP status code and the full response body as text regardless of
        status, so error bodies are preserved as evidence. JSON parsing is intentionally
        left to the caller/judge so nothing in the body is lost.
        """
        body = {self.request_field: text}
        response = httpx.post(
            self.url, json=body, headers=self.headers, timeout=self.timeout
        )
        return TargetResponse(status_code=response.status_code, raw_text=response.text)
