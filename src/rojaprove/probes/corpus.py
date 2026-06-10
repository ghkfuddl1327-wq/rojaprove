"""Loader and schema for the probe corpus.

Reads check cases from a packaged YAML file (e.g. corpus/system_prompt_leak.v0.yaml) into
typed Case models. The corpus holds neutral check inputs only; no judgment logic lives here.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import yaml
from pydantic import BaseModel


class Case(BaseModel):
    """One probe case: a single test input plus its metadata."""

    id: str
    category: str
    test_input: str
    notes: str | None = None


def load_cases(
    path: str | Path | None = None,
    *,
    name: str = "system_prompt_leak",
    version: str = "v0",
) -> list[Case]:
    """Load probe cases into typed Case models.

    By default reads the packaged corpus ``rojaprove/corpus/<name>.<version>.yaml`` via
    importlib.resources. Pass ``path`` to read a corpus file from the filesystem instead.

    The YAML is expected to be a top-level list of case mappings. An empty or comment-only
    file yields an empty list.
    """
    if path is not None:
        text = Path(path).read_text(encoding="utf-8")
    else:
        resource = files("rojaprove.corpus").joinpath(f"{name}.{version}.yaml")
        text = resource.read_text(encoding="utf-8")

    raw = yaml.safe_load(text) or []
    return [Case.model_validate(item) for item in raw]
