"""Per-token prices, fetched live from the provider's /models endpoint.

Nebius Token Factory (and other OpenAI-compatible gateways that follow the
OpenRouter convention) expose ``pricing`` per model when ``verbose=true`` is
passed. Prices are USD per token, as strings.
"""

from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Price:
    model: str
    prompt: float  # USD per uncached input token
    cached_prompt: float | None  # USD per cached input token, None = no discount
    completion: float  # USD per output token

    def cost(self, prompt_tokens: int, cached_tokens: int, completion_tokens: int) -> float:
        cached = max(0, min(cached_tokens, prompt_tokens))
        uncached = prompt_tokens - cached
        cached_rate = self.cached_prompt if self.cached_prompt else self.prompt
        return uncached * self.prompt + cached * cached_rate + completion_tokens * self.completion

    def per_million(self) -> str:
        cache = f", cached ${self.cached_prompt * 1e6:.3f}" if self.cached_prompt else ""
        return f"${self.prompt * 1e6:.2f} in{cache}, ${self.completion * 1e6:.2f} out per 1M tokens"


def _f(value: object) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def fetch_prices(base_url: str, api_key: str, cache_file: Path | None = None) -> dict[str, Price]:
    """Fetch the live catalog and return {model_id: Price}.

    The raw catalog (prices only, never the key) is written to ``cache_file``
    so every run folder records the prices it was billed at.
    """
    url = base_url.rstrip("/") + "/models?verbose=true"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    prices: dict[str, Price] = {}
    snapshot = []
    for m in data.get("data", []):
        p = m.get("pricing") or {}
        price = Price(
            model=m["id"],
            prompt=_f(p.get("prompt")),
            cached_prompt=_f(p.get("input_cache_read")) or None,
            completion=_f(p.get("completion")),
        )
        prices[m["id"]] = price
        snapshot.append(
            {
                "id": m["id"],
                "prompt": p.get("prompt"),
                "input_cache_read": p.get("input_cache_read"),
                "completion": p.get("completion"),
                "context_length": m.get("context_length"),
                "supported_features": m.get("supported_features"),
            }
        )
    if cache_file is not None:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(
            json.dumps(
                {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "source": url, "models": snapshot},
                indent=1,
            )
            + "\n"
        )
    return prices
