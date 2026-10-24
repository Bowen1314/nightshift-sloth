# Bench summary

Same chores, same repo, same prompt, same R-CLI build; only the model changes.
A chore counts as **done** when the repo's own tests pass *and* a hidden acceptance check
(never shown to the agent) passes on the sloth branch.

| Model | Price (per 1M tokens) | Done | Tests green | Stopped early | Median wall time | Total cost | Cost per done chore |
|---|---|---|---|---|---|---|---|
| `MiniMaxAI/MiniMax-M3.1-Flash` | $0.15 in, cached $0.015, $0.60 out | 6/6 | 6/6 | 0 | 50s | $0.0684 | $0.0114 |
| `deepseek-ai/DeepSeek-V4-Flash-0731` | $0.14 in, cached $0.010, $0.28 out | 5/6 | 6/6 | 0 | 13s | $0.0130 | $0.0026 |
| `Qwen/Qwen3-235B-A22B-Instruct-2507` | $0.20 in, $0.60 out | 3/6 | 6/6 | 0 | 16s | $0.0931 | $0.0310 |
| `openai/gpt-oss-120b` | $0.15 in, $0.60 out | 3/6 | 3/6 | 5 | 11s | $0.2163 | $0.0721 |

## Chore by chore

| Chore | `MiniMax-M3.1-Flash` | `DeepSeek-V4-Flash-0731` | `Qwen3-235B-A22B-Instruct-2507` | `gpt-oss-120b` |
|---|---|---|---|---|
| `fix-empty-report` | [done](20261024-112501-fix-empty-report-minimax-m3.1-flash/MORNING_REPORT.md) · 44s · $0.0083 | [done](20261024-112444-fix-empty-report-deepseek-v4-flash/MORNING_REPORT.md) · 16s · $0.0026 | [done](20261024-112545-fix-empty-report-qwen3-235b/MORNING_REPORT.md) · 17s · $0.0130 | [done](20261024-112602-fix-empty-report-gpt-oss-120b/MORNING_REPORT.md) · 1m 18s · $0.1373 |
| `readme-usage-drift` | [done](20261024-113444-readme-usage-drift-minimax-m3.1-flash/MORNING_REPORT.md) · 57s · $0.0112 | [done](20261024-113429-readme-usage-drift-deepseek-v4-flash/MORNING_REPORT.md) · 15s · $0.0022 | [partial](20261024-113542-readme-usage-drift-qwen3-235b/MORNING_REPORT.md) · 16s · $0.0067 | [done](20261024-113558-readme-usage-drift-gpt-oss-120b/MORNING_REPORT.md) · 32s · $0.0379 |
| `rename-calcualte` | [done](20261024-113916-rename-calcualte-minimax-m3.1-flash/MORNING_REPORT.md) · 37s · $0.0096 | [done](20261024-113905-rename-calcualte-deepseek-v4-flash/MORNING_REPORT.md) · 11s · $0.0018 | [partial](20261024-113954-rename-calcualte-qwen3-235b/MORNING_REPORT.md) · 16s · $0.0161 | [failed](20261024-114011-rename-calcualte-gpt-oss-120b/MORNING_REPORT.md) · 3s · $0.0045 |
| `report-json` | [done](20261024-113659-report-json-minimax-m3.1-flash/MORNING_REPORT.md) · 1m 14s · $0.0139 | [done](20261024-113631-report-json-deepseek-v4-flash/MORNING_REPORT.md) · 27s · $0.0038 | [done](20261024-113814-report-json-qwen3-235b/MORNING_REPORT.md) · 44s · $0.0402 | [failed](20261024-113859-report-json-gpt-oss-120b/MORNING_REPORT.md) · 6s · $0.0098 |
| `test-parse-amount` | [done](20261024-113339-test-parse-amount-minimax-m3.1-flash/MORNING_REPORT.md) · 25s · $0.0057 | [done](20261024-113332-test-parse-amount-deepseek-v4-flash/MORNING_REPORT.md) · 6s · $0.0012 | [done](20261024-113404-test-parse-amount-qwen3-235b/MORNING_REPORT.md) · 13s · $0.0057 | [done](20261024-113418-test-parse-amount-gpt-oss-120b/MORNING_REPORT.md) · 11s · $0.0130 |
| `utcnow-deprecation` | [done](20261024-114101-utcnow-deprecation-minimax-m3.1-flash/MORNING_REPORT.md) · 1m 52s · $0.0197 | [partial](20261024-112721-utcnow-deprecation-deepseek-v4-flash/MORNING_REPORT.md) · 8s · $0.0013 | [partial](20261024-113300-utcnow-deprecation-qwen3-235b/MORNING_REPORT.md) · 19s · $0.0113 | [failed](20261024-113319-utcnow-deprecation-gpt-oss-120b/MORNING_REPORT.md) · 12s · $0.0138 |

The 24 runs on this page cost **$0.3907** in total. The spend ledger (every model call made with this ledger, including smoke tests and discarded runs) stands at **$0.4501** of a $3.00 cap.

Legend: **done** = tests green and hidden check passes; **partial** = tests green but the hidden check fails; **failed** = no change, or tests red.
