"""redcell demo target — a minimal, deterministic mock chat app (NOT a real LLM).

This is a local FIXTURE used to exercise `redcell scan` end-to-end without calling any
external model. It is intentionally tiny: one POST /chat endpoint that returns a fixed
reply, plus a secret "canary" token held in a module-level variable (this stands in for
a secret that a real app would embed in its system prompt).

Scope reminder: redcell and this demo are for endpoints you own or are authorized to test.

Run (after `pip install -e ".[demo]"`):
    uvicorn examples.demo_target.app:app --host 127.0.0.1 --port 8000

NOTE: This is the minimal Step 1 stub — it always returns the same fixed reply. The
deterministic mock behavior (revealing the canary on extraction-style inputs unless a
defense directive is present in the system prompt) is added in Step 2.
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

# Secret "canary" token. In a real app this would be embedded in the system prompt; here
# it lives in a variable so the demo needs no real model. This is a known fixture value,
# NOT a real credential.
# MUST match redcell.config.CANARY_DEFAULT (kept in sync manually; a unit test will guard
# this in Step 2).
CANARY = "RC-CANARY-7Q2X-9F4K-DEMO"

# The "fixed reply" the stub returns. Step 2 replaces the handler with mock leak/defense
# logic; for now the canary is held but never returned.
FIXED_REPLY = "Hello! I'm the redcell demo assistant. How can I help you today?"

app = FastAPI(title="redcell demo target", version="0.1.0")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Minimal stub: return a fixed reply regardless of input.

    Step 2 replaces this with deterministic mock-LLM behavior keyed off the presence of a
    defense directive in the system prompt.
    """
    return ChatResponse(reply=FIXED_REPLY)
