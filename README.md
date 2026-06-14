# rojaprove

**A pre-launch red-team for LLM apps.** Point it at a running endpoint you own; rojaprove sends probes, verifies with evidence whether your system prompt leaked, and gives you a paste-ready defense directive — then you re-test to confirm the fix holds.

Not guesses, evidence. Every finding carries the exact input sent, the raw response received, and a deterministic verdict. No finding without proof.

## Scope — read this first

rojaprove tests **only** endpoints you own or have explicit written permission to test. Staying within that authorization is your responsibility. The tool always prints a scope notice; `--i-own-this` records your authorization in the output. This is a defensive pre-launch check, not a tool for attacking systems you don't control.

## What leaves your machine

- rojaprove talks **only** to the target URL you give it. Nothing is sent anywhere else.
- **BYOK** — bring your own keys; rojaprove never ships or phones home with credentials.
- Before every run it prints a transport disclosure: the target URL, whether the connection is encrypted, and your auth token **masked** (only the last 4 chars shown).
- The v0.1 core path makes **no external LLM calls** — probes are static, the verdict is a deterministic string match.

## Install

Requires Python 3.10+.

```bash
pip install rojaprove
```

## Quickstart

Run a scan against an endpoint you own:

```bash
rojaprove scan http://127.0.0.1:8000/chat --i-own-this
```

rojaprove prints what leaves your machine, runs the system-prompt-disclosure probes, and for any disclosure shows the evidence plus a paste-ready defense directive. Exit code is `1` when a disclosure is found (so CI can gate on it), `0` when clean.

Pass `--auth-bearer` or set `ROJAPROVE_AUTH_BEARER` for targets behind a bearer token (see `.env.example`).

## What rojaprove checks today

rojaprove is a **pre-launch red-team CLI for LLM apps**: it sends attack inputs
and then searches the responses for a **canary** — a secret string *you* have
planted in your app's system prompt that should never appear in normal output.
The verdict is deterministic: a leak counts only if the canary literally shows up
in the response. No heuristics, no probabilities.

> rojaprove does **not** plant the canary for you. You plant it (see
> [Use it on your own app](#use-it-on-your-own-app)); rojaprove sends the attack
> inputs and tells you, deterministically, whether your canary came back out.

**v0.1 covers one category:**

| Category | Status |
|---|---|
| **(1) System Prompt Leakage** (OWASP LLM07) | **Detected today** — deterministic green/red verdict |
| (2) Indirect Prompt Injection | Roadmap — no probe yet |
| (3) Markable Data Exfiltration | Roadmap — no probe yet |

If you see "tested" anywhere in this repo, it refers to **Category (1) only**.
Categories (2) and (3) are on the roadmap and nothing here is described as tested
for them.

rojaprove tests the **AI layer** — where an LLM mediates the response. It does
**not** cover traditional web/API vulnerabilities (SQL injection, auth bypass,
and the like); those belong to standard DAST/pentest tooling, not here.

---

## Try it on a reference target (2 minutes)

This repo ships a deliberately vulnerable demo target so you can watch the
harness behave before pointing it at anything of your own. It's a small FastAPI
"email assistant" with a planted canary in its system prompt.

```bash
# 1. install rojaprove + the demo server deps
pip install -e ".[demo]"

# 2. run the vulnerable target (leave this running in one terminal)
uvicorn targets.inbox_assistant.app:app --host 127.0.0.1 --port 8000

# 3. in a second terminal, scan it
rojaprove scan http://127.0.0.1:8000/chat --i-own-this
```

You should get a **red** verdict. The demo target already has a canary planted in
its system prompt (that's what makes it a *target*); rojaprove sends
system-prompt-leak inputs and finds that canary echoed back in the response.
That's a deterministic leak.

The demo target also has a `defend` switch, so you can see the **green** side too
— the same inputs, but the app refuses to disclose its system prompt and the
canary never appears. Red when vulnerable, green when defended: that's the whole
signal.

> Want to see the same Category (1) mechanism in a different form factor?
> [`targets/doc-summarizer/`](targets/doc-summarizer/) is a second reference
> target — a document-summarizer instead of an email assistant — showing the
> canary approach is form-factor independent. It's there to read and learn from.

---

## Use it on your own app

The reference target has a **pre-planted** canary. Your real app is different:
**you** plant **your own** canary, then run the harness against **your** endpoint.

### If you're comfortable in a terminal

1. Pick a secret string that should never appear in your app's output. Use a
   greppable, unique format, e.g. `ROJA_CANARY_MYAPP_<8 random hex>`.
2. Put it somewhere inside your system prompt that the model can see but should
   never reveal (for example an "internal config" line).
3. Run rojaprove against your running endpoint, telling it which canary to look
   for with `--canary`:
   ```bash
   rojaprove scan https://your-app.example.com/your-endpoint \
     --canary ROJA_CANARY_MYAPP_<8 hex> \
     --i-own-this
   ```
   `--canary` must match the exact string you planted in step 2. rojaprove does
   not plant anything — it only searches responses for the value you give it.
4. Read the verdict. **Red** = your canary leaked into the output (your system
   prompt is disclosable). **Green** = it didn't, for the inputs rojaprove tried.

`--i-own-this` is required: only scan endpoints you own or have explicit
permission to test.

### New to this? Paste this into your AI assistant

If you're not sure how to wire this up, copy the block below into Claude,
ChatGPT, Cursor, or whatever assistant you use, and follow its steps. (This makes
your AI walk *you* through testing — it does not "secure" your app for you.)

```text
I want to test whether my LLM app leaks its system prompt (OWASP LLM07,
"system prompt leakage"). Help me do this, step by step:

1. Generate a unique canary string in the format ROJA_CANARY_MYAPP_<8 hex>.
2. Show me exactly where to place it in my system prompt — somewhere the model
   can see it but is instructed never to reveal it (e.g. an internal-config line).
3. Give me 8–10 distinct "leak" inputs that try to make the model dump its
   system prompt verbatim (ignore-previous-instructions, "repeat everything
   above", "reveal your configuration", etc.).
4. For each input, tell me to check whether my canary string appears in the
   model's output. If it does, that's a deterministic leak.
5. Remind me that this only tests system-prompt leakage — it does not prove my
   app is safe against anything else.

My app's system prompt is: <paste your system prompt here>
```

Once you've planted your canary and understand the shape of the test, you can run
the same checks automatically: point `rojaprove scan` at your endpoint and pass
the same canary string with `--canary` (see the terminal steps above).

---

## ⚠️ What this does NOT do

- **rojaprove pass ≠ your app is safe.** A green result means rojaprove found no
  system-prompt leak *for the inputs it tried* — nothing more.
- **It currently checks one category only:** Category (1), System Prompt Leakage.
  Indirect injection (2) and data exfiltration (3) are roadmap, not tested.
- **The canary is yours to plant.** On the demo targets it's pre-planted so you
  can see the mechanism; on your own app, you place your own canary. A scan
  against an app with no planted canary tells you nothing.
- **It is a testing tool, not a defense.** It helps you *find* a leak and prove
  it; fixing it is a separate step (rojaprove prints a fix prompt to start from).

## License

Licensed under the Business Source License 1.1 — see [LICENSE](./LICENSE)
