"""Morning reports (one per night) and the bench summary table."""

from __future__ import annotations

import collections
import json
import statistics
from pathlib import Path


def _dur(seconds: float) -> str:
    seconds = int(round(seconds))
    m, s = divmod(seconds, 60)
    return f"{m}m {s:02d}s" if m else f"{s}s"


def _quote(text: str, limit: int = 1800) -> str:
    text = text.strip() or "(the agent did not leave a summary)"
    if len(text) > limit:
        text = text[:limit].rstrip() + " ..."
    return "\n".join("> " + line if line.strip() else ">" for line in text.splitlines())


def headline(r: dict) -> str:
    s = r["stats"]
    d = r["diff"]
    tests = "tests green" if r["tests_after"]["ok"] else "tests RED"
    change = f"{d['files']} file{'s' if d['files'] != 1 else ''} changed (+{d['added']} -{d['removed']})" if r["commit"] else "no change"
    parts = [f"**{r['verdict']}**", tests, change, f"${s['usd']:.4f}", f"{_dur(s['wall_seconds'])} of a {_dur(r['timer'])} budget"]
    if r.get("acceptance") is not None:
        parts.insert(1, "hidden check PASS" if r["acceptance"]["ok"] else "hidden check FAIL")
    return " · ".join(parts)


def render_run(r: dict) -> str:
    s = r["stats"]
    branch = r["branch"]
    base = r["base"]["ref"]
    tools = ", ".join(f"{k} {v}" for k, v in sorted(s["tool_calls"].items(), key=lambda kv: -kv[1])) or "none"
    cmds = collections.Counter(s["commands"])
    cmd_lines = "\n".join(f"- `{c}`" + (f" ×{n}" if n > 1 else "") for c, n in cmds.most_common(12)) or "- (no shell commands)"
    rows = [
        ("Chore", f"`{r['chore']['id']}`"),
        ("Branch", f"`{branch}` (from `{base}` @ `{r['base']['sha'][:7]}`)"),
        ("Agent", f"{r['agent']}, headless (`--print --timer {r['timer']}`)"),
        ("Model", f"`{r['model']['id']}` ({r['model']['price']})"),
        ("Stopped by", f"{s['stopped_by']} (exit {s['exit_code']}); hard stop at {_dur(r['timer'] + r['grace'])}, cap ${r['per_run_cap_usd']:.2f}"),
        ("Model calls", f"{s['model_calls']}"),
        ("Tokens", f"{s['prompt_tokens']:,} in ({s['cached_tokens']:,} cached) · {s['completion_tokens']:,} out"),
        ("Cost", f"${s['usd']:.4f}"),
        ("Tests before", ("pass" if r["tests_before"]["ok"] else "FAIL") + f": {r['tests_before']['summary']}"),
        ("Tests after", ("pass" if r["tests_after"]["ok"] else "FAIL") + f": {r['tests_after']['summary']}"),
    ]
    if r.get("acceptance") is not None:
        rows.append(("Hidden acceptance check", "PASS" if r["acceptance"]["ok"] else "FAIL"))
    table = "| | |\n|---|---|\n" + "\n".join(f"| {k} | {v} |" for k, v in rows)

    out = [
        f"# Morning report: {r['chore']['id']}",
        "",
        f"_{r['date']} · {r['repo']}_",
        "",
        headline(r),
        "",
        "## The chore",
        "",
        _quote(r["chore"]["text"], 1200),
        "",
        "## Night at a glance",
        "",
        table,
        "",
        "## What changed",
        "",
        ("```\n" + r["diff"]["stat"] + "\n```") if r["commit"] else "Nothing. The branch is identical to its base.",
        "",
        "## What the agent says it did",
        "",
        _quote(s["final_message"]),
        "",
        "## What it ran",
        "",
        cmd_lines,
        "",
        f"Tool calls: {tools}." + (f" {s.get('tool_errors', 0)} of them failed." if s.get("tool_errors") else ""),
    ]
    if s["errors"]:
        out += ["", "## Errors", ""] + [f"- {e}" for e in s["errors"][:5]]
    if not r["tests_after"]["ok"]:
        out += ["", "## Test output (tail)", "", "```", r["tests_after"]["tail"], "```"]
    if r.get("acceptance") is not None and not r["acceptance"]["ok"]:
        out += ["", "## Hidden check output (tail)", "", "```", r["acceptance"]["output"], "```"]
    out += [
        "",
        "## Your move",
        "",
        "```sh",
        f"git diff {base}...{branch}      # read it",
        f"git merge --no-ff {branch}      # keep it",
        f"git branch -D {branch}          # or bin it",
        "```",
        "",
        "Nothing was merged or pushed. The sloth only works on its own branch.",
        "",
        "Full agent session: [TRANSCRIPT.md](TRANSCRIPT.md) (readable) · `events.jsonl` (raw R-CLI JSON events) · "
        "`diff.patch` · `run.json`.",
        "",
    ]
    return "\n".join(out)


def load_runs(out_dir: Path) -> list[dict]:
    runs = []
    for p in sorted(out_dir.glob("*/run.json")):
        try:
            runs.append(json.loads(p.read_text()))
        except json.JSONDecodeError:
            continue
    return runs


def render_summary(runs: list[dict], ledger_total: float, cap: float) -> str:
    if not runs:
        return "# Bench summary\n\nNo runs yet.\n"
    by_model: dict[str, list[dict]] = collections.defaultdict(list)
    for r in runs:
        by_model[r["model"]["id"]].append(r)
    chores = sorted({r["chore"]["id"] for r in runs})

    lines = [
        "# Bench summary",
        "",
        "Same chores, same repo, same prompt, same R-CLI build; only the model changes.",
        "A chore counts as **done** when the repo's own tests pass *and* a hidden acceptance check",
        "(never shown to the agent) passes on the sloth branch.",
        "",
        "| Model | Price (per 1M tokens) | Done | Tests green | Stopped early | Median wall time | Total cost | Cost per done chore |",
        "|---|---|---|---|---|---|---|---|",
    ]
    def _done(r: dict) -> bool:
        return bool(r["tests_after"]["ok"] and (r.get("acceptance") or {}).get("ok"))

    def _rank(model: str) -> tuple:
        rs = by_model[model]
        done = sum(_done(r) for r in rs)
        cost = sum(r["stats"]["usd"] for r in rs)
        return (-done, cost / done if done else float("inf"), model)

    order = sorted(by_model, key=_rank)
    for model in order:
        rs = by_model[model]
        done = sum(_done(r) for r in rs)
        green = sum(1 for r in rs if r["tests_after"]["ok"] and r["commit"])
        early = sum(1 for r in rs if r["stats"]["stopped_by"] != "agent finished")
        cost = sum(r["stats"]["usd"] for r in rs)
        med = statistics.median(r["stats"]["wall_seconds"] for r in rs)
        per = f"${cost / done:.4f}" if done else "n/a"
        lines.append(
            f"| `{model}` | {rs[0]['model']['price'].replace(' per 1M tokens', '')} | {done}/{len(rs)} | {green}/{len(rs)} | {early} | {_dur(med)} | ${cost:.4f} | {per} |"
        )
    lines += ["", "## Chore by chore", "", "| Chore | " + " | ".join(f"`{m.split('/')[-1]}`" for m in order) + " |"]
    lines.append("|---|" + "---|" * len(by_model))
    for chore in chores:
        cells = []
        for model in order:
            rs = [r for r in by_model[model] if r["chore"]["id"] == chore]
            if not rs:
                cells.append("-")
                continue
            r = rs[-1]
            ok = r["tests_after"]["ok"] and (r.get("acceptance") or {}).get("ok")
            mark = "done" if ok else ("partial" if r["tests_after"]["ok"] and r["commit"] else "failed")
            cells.append(f"[{mark}]({r['run_id']}/MORNING_REPORT.md) · {_dur(r['stats']['wall_seconds'])} · ${r['stats']['usd']:.4f}")
        lines.append(f"| `{chore}` | " + " | ".join(cells) + " |")
    total_runs = sum(r["stats"]["usd"] for r in runs)
    lines += [
        "",
        f"The {len(runs)} runs on this page cost **${total_runs:.4f}** in total. "
        f"The spend ledger (every model call made with this ledger, including smoke tests and discarded runs) "
        f"stands at **${ledger_total:.4f}** of a ${cap:.2f} cap.",
        "",
        "Legend: **done** = tests green and hidden check passes; **partial** = tests green but the hidden check fails;"
        " **failed** = no change, or tests red.",
        "",
    ]
    return "\n".join(lines)


def _clip(text: str, limit: int) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit].rstrip() + " ..."


def render_transcript(events_path: Path, title: str) -> str:
    """A readable account of one R-CLI session, built from its JSON event stream."""
    out = [f"# R-CLI session: {title}", "", "Rendered from `events.jsonl` (R-CLI `--format json`). Long tool inputs and outputs are clipped.", ""]
    calls = 0
    for line in events_path.read_text(errors="replace").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        t, p = rec.get("type"), rec.get("payload") or {}
        if t == "user:message":
            out += ["## Prompt", "", "```text", _clip(str(p.get("text", "")), 3000), "```", ""]
        elif t == "assistant:message" and (p.get("text") or "").strip():
            out += ["**Agent:** " + _clip(p["text"], 1500).replace("\n", "\n> "), ""]
        elif t == "tool:requested":
            for c in p.get("calls") or []:
                calls += 1
                args = json.dumps(c.get("input") or {}, ensure_ascii=False)
                out.append(f"{calls}. `{c.get('name') or '(empty name)'}` {_clip(args, 400)}")
        elif t == "tool:result":
            out.append(f"   - result: {_clip(str(p.get('title', '')), 200)}")
        elif t == "tool:error":
            out.append(f"   - **error:** {_clip(str(p.get('error', '')).splitlines()[0] if p.get('error') else '', 200)}")
        elif t == "run:error":
            out += ["", f"**Run error:** {_clip(str(p.get('error')), 300)}", ""]
        elif t == "turn:end":
            out += ["", f"_Turn ended: {p.get('status')} after {round((p.get('durationMs') or 0) / 1000)}s._", ""]
    return "\n".join(out) + "\n"
