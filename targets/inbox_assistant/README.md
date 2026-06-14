# InboxAssistant — rojaprove reference target

A deliberately vulnerable, **deterministic** email-assistant bot used as a
reference **target** for rojaprove.

It demonstrates **Category (1): System Prompt Leakage (OWASP LLM07)** over an HTTP
endpoint, so you can run `rojaprove scan` against it end-to-end and watch the
red/green verdict flip. The companion target
[`doc-summarizer`](../doc-summarizer/) shows the *same* Category (1) mechanism in
a different form factor — proving the canary approach is form-factor independent.

> ⚠️ This app is intentionally insecure. It exists only as a target to run a
> detection harness against. Do not deploy it.

---

## What this is / is not

- **This is a TARGET (fixture).** It exposes an HTTP endpoint with a canary
  planted in its system prompt. That's all.
- **This is NOT a probe.** It contains zero detection logic. rojaprove (external)
  does the probing. This repo ships no new detection capability.

---

## Run it (Codespaces-friendly)

```bash
# install rojaprove + the demo server deps
pip install -e ".[demo]"

# vulnerable mode (default) — leave running in one terminal
uvicorn targets.inbox_assistant.app:app --host 127.0.0.1 --port 8000

# in a second terminal, scan it
rojaprove scan http://127.0.0.1:8000/chat --i-own-this
```

Expected: a **red** verdict — the canary planted in the system prompt is echoed
back when the leak inputs hit, and rojaprove finds it in the response.

To see the **green** side, restart the server in defended mode:

```bash
ROJAPROVE_DEMO_DEFENSE=1 uvicorn targets.inbox_assistant.app:app \
  --host 127.0.0.1 --port 8000
```

Now the same scan returns **no disclosure** (exit 0): the app refuses to reveal
its system prompt, so the canary never appears. Red when vulnerable, green when
defended — that's the whole signal.

---

## Detection status — what is tested vs. roadmap

| Category | This target | rojaprove today | Can we say "tested"? |
|---|---|---|---|
| **(1) System Prompt Leakage** | planted here | **detects it** (green/red) | **Yes — tested / proven** |
| (2) Indirect Prompt Injection | not in this target | roadmap | No |
| (3) Markable Data Exfiltration | not in this target | roadmap | No |

This target covers **only Category (1)**. For Category (1), rojaprove produces a
real green/red verdict, so "tested" is justified here. Categories (2) and (3) are
**roadmap** — no probe exists for them yet, and nothing here is "tested" for them.

---

## ⚠️ rojaprove pass ≠ your app is safe

This is a reference target with a **pre-planted** canary. Your real app is
different: **you** plant **your own** canary and run the harness against **your**
system.

**rojaprove pass ≠ app safe. rojaprove currently checks only Category (1)
(System Prompt Leakage).** A clean result means *this one category* found no leak
— it says nothing about categories not yet covered.

---

## Scope (what this target deliberately does NOT contain)

To stay inside Category (1), this target has **no** tools, **no** file reads,
**no** authz/access-control logic, and **no** web-channel exfiltration. The only
sensitive datum is the system-prompt canary, and the only exit path is the model
echoing it into the HTTP response. The verdict reduces to a single deterministic
question: *did the canary appear in the model's output?*
