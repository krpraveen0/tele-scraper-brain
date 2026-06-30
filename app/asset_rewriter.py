from __future__ import annotations

import subprocess
from typing import Protocol

import requests

from app.asset_generator import GeneratedAsset
from app.config import Settings
from app.models import StoredSignal


class AssetRewriter(Protocol):
    def rewrite(self, signal: StoredSignal, asset: GeneratedAsset) -> GeneratedAsset:
        ...


def build_rewrite_prompt(signal: StoredSignal, asset: GeneratedAsset) -> str:
    return f"""
You are rewriting an asset draft for Praveen Kumar.

Praveen's goals:
- Grow as a senior AI engineer.
- Build practical agentic AI, RAG, memory, context management, and local LLM systems.
- Create human-sounding LinkedIn and Medium content.
- Build teaching examples for Python, GenAI, FastAPI, and real projects.
- Improve leadership communication and spoken English.

Task:
Rewrite the asset below so it is clearer, more useful, more natural, and less generic.
Keep the same asset type and intent.
Do not invent facts beyond the provided signal.
Return only Markdown content. Do not wrap in code fences.

Asset type: {asset.asset_type}
Signal category: {signal.analysis.category}
Signal source: {signal.source_title}
Signal summary: {signal.analysis.summary or signal.analysis.reason}
Original signal text:
{signal.message_text[:2000]}

Draft asset:
{asset.render()}
""".strip()


class OllamaAssetRewriter:
    def __init__(self, base_url: str, model: str, timeout_seconds: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def rewrite(self, signal: StoredSignal, asset: GeneratedAsset) -> GeneratedAsset:
        prompt = build_rewrite_prompt(signal, asset)
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_ctx": 8192},
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        text = str(response.json().get("response", "")).strip()
        if not text:
            raise RuntimeError("Ollama returned an empty rewrite.")
        return _asset_from_markdown(asset, text)


class OpenCodeAssetRewriter:
    def __init__(self, model: str = "", attach_url: str = "", timeout_seconds: int = 180) -> None:
        self.model = model
        self.attach_url = attach_url
        self.timeout_seconds = timeout_seconds

    def rewrite(self, signal: StoredSignal, asset: GeneratedAsset) -> GeneratedAsset:
        prompt = build_rewrite_prompt(signal, asset)
        command = ["opencode", "run"]
        if self.attach_url:
            command.extend(["--attach", self.attach_url])
        if self.model:
            command.extend(["--model", self.model])
        command.append(prompt)

        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or "unknown OpenCode error"
            raise RuntimeError(f"OpenCode failed with exit code {completed.returncode}: {stderr}")
        text = completed.stdout.strip()
        if not text:
            raise RuntimeError("OpenCode returned an empty rewrite.")
        return _asset_from_markdown(asset, text)


def create_asset_rewriter(settings: Settings) -> AssetRewriter:
    if settings.llm_provider == "opencode":
        return OpenCodeAssetRewriter(
            model=settings.opencode_model,
            attach_url=settings.opencode_attach_url,
            timeout_seconds=settings.opencode_timeout_seconds,
        )
    return OllamaAssetRewriter(base_url=settings.ollama_url, model=settings.ollama_model)


def _asset_from_markdown(original: GeneratedAsset, markdown: str) -> GeneratedAsset:
    lines = [line.rstrip() for line in markdown.strip().splitlines()]
    title = original.title
    body_lines = lines
    if lines and lines[0].startswith("# "):
        title = lines[0].lstrip("#").strip() or original.title
        body_lines = lines[1:]
        if body_lines and not body_lines[0].strip():
            body_lines = body_lines[1:]
    body = "\n".join(body_lines).strip() or original.body
    return GeneratedAsset(signal_id=original.signal_id, asset_type=original.asset_type, title=title, body=body)
