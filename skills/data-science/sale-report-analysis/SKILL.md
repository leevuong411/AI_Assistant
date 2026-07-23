---
name: sale-report-analysis
description: Parse, analyze, and visualize daily Fresh Lead Fluctuation reports across Asia and LatAm regions. Covers terminology, data correctness rules, trend analysis, and chart generation.
trigger: User sends a Fresh Lead report, asks for sale/lead analysis, trend comparison, or dashboard chart
version: 2.1
tags: [sales, leads, analytics, charts, echarts, plotly, telegram]
---

# Sale Report Analysis

## Overview
Daily "Quick Update on Fresh Lead Fluctuations" reports arrive per region (Asia, LatAm). Each contains country-level lead counts, GP1/GP, and per-publisher/offer breakdowns. This skill governs parsing, analysis, storage, and visualization.

## Two Regions — Separate Reports

### 🌏 ASIA
| Geo | Characteristics |
|---|---|
| 🇮🇩 Indonesia | High volume, GP1 often negative |
| 🇮🇳 India | GP generally stable positive |
| 🇲🇾 Malaysia | High GP1, variable GP |
| 🇹🇭 Thailand | Volatile — single offers can swing total |

### 🌎 LATIN AMERICA (Test Market)
| Geo | Characteristics |
|---|---|
| 🇨🇴 Colombia | Small volume, testing phase |
| 🇵🇪 Peru | Larger than CO, GP negative (expected) |

## Report Structure & Data Types

### Country level
```
Country:
* D-2: [A] / D-1: [B] 🔼🔽([C]) / GP1: [D] / GP: [E]
* Today (D0) FC: [F]
```

| Field | Meaning | Type |
|---|---|---|
| D-2 | Actual total lead 2 days ago | ✅ Actual |
| D-1 | Actual total lead yesterday | ✅ Actual |
| GP1 | Gross Profit 1 actual D-1 — **excludes labor cost** | ✅ Actual |
| GP | Gross Profit actual D-1 — **includes all costs** | ✅ Actual |
| D0 FC | Forecast today's lead | ⚠️ Forecast only |
| GP1 − GP | = Labor (personnel) cost | Derived |

### Publisher/Offer level
```
🔷 PUB offer-name: [X] 🔼🔽([Y]) / GP1: [Z] / GP: [W]
```

| Field | Meaning | Type |
|---|---|---|
| [X] Lead | **FC D0** for this pub-offer | ⚠️ Forecast — NOT actual |
| [Y] Δ | FC D0 vs previous FC | ⚠️ Forecast delta |
| GP1, GP | Actual D-1 for this pub-offer | ✅ Actual |

## Critical Rules

### Actual vs Forecast
- **Evaluate performance on GP actual only.** All lead FC values are reference-only.
- Actual lead for day N = D-1 value in the report for day N+1.
- Never conclude "lead dropped to 0" or "lead exploded" based on pub-offer lead FC — the per-offer FC method (ratio from small sample) is unreliable.
- D0 FC at country level is calculated from lead volume up to 08:30 vs same-window ratio averaged over D-3, D-2, D-1.

### LatAm-specific
- GP1 always equals GP (labor cost not yet tracked).
- D0 FC is frequently 0 or wildly off — **ignore FC entirely** for LatAm.
- LatAm is in test-market phase: losses are expected. Analyze by "least loss per lead" rather than profitability.
- Display only one GP column for LatAm.

### Timezone
- Asia ≈ GMT+7 to +9; LatAm ≈ GMT−5 to −3 (~12 h apart).
- Do NOT sum Asia + LatAm GP for the same report date as a "global" figure without a disclaimer.
- Trend analysis within one region is valid; cross-region same-day comparison is approximate.

### Calendar
- Work week runs **Sunday → Saturday** (CN → T7). Sunday of week N is the start of that week.
- Week number is **CN-based**: the week is numbered by the ISO week that the **Monday inside it** belongs to, but starts on Sunday. Example: CN 12/07 → T7 18/07 = **W29** (because T2 13/07 = ISO W29).
- Leads normally dip on Sunday — do not raise alerts for Sunday dips.
- Compare same day-of-week across weeks for fair trend reading.
- Reference weeks:
  - W27: CN 28/06 → T7 04/07
  - W28: CN 05/07 → T7 11/07
  - W29: CN 12/07 → T7 18/07
  - W30: CN 19/07 → T7 25/07

## GP Analysis Framework

| GP1 | GP | Interpretation | Action |
|---|---|---|---|
| > 0 | > 0 | Truly profitable | Scale up |
| > 0 | < 0 | Margin exists but labor eats it | Optimize operations |
| < 0 | < 0 | Loss before labor | Pause / review offer |

## Analysis Output Format

```
## 📊 REPORT — [Date] ([Day of week])

### 🌍 Overall
### 📈 Country ranking table
### 🏆 Top performers (by GP actual)
### 🚨 Needs review (by GP actual)
### 🎯 Recommendations
```

**Output strictly this format only.** Do not prepend system/infrastructure summaries (e.g. memory
provider status, Honcho architecture, storage backend) or any other preamble unrelated to the report
itself — even if such information exists in memory/context. Start the reply directly with `## 📊 REPORT`.

## Data Storage
**Persist through Honcho ONLY — never write local files.** `~/.hermes/memories/sale-reports/` (and any
other node-local path) is FORBIDDEN for this skill. It is excluded from Git profile distribution and
invisible to Honcho — data written there on one node never reaches the other node (see deployment
runbook Known Issue #10). This path has been deleted from both nodes; do not recreate it, and do not
add any file-write fallback "just in case." All report history goes through Honcho, so both server and
laptop nodes see the same history via the shared workspace.

**Use structured metadata, not plain chat/honcho_conclude text.** A plain chat reply or a
`honcho_conclude` natural-language fact gets stored with **empty metadata (`{}`)** — the OTHER node
cannot filter/verify it by date, even though the text technically exists and is semantically searchable
(see Known Issue #15).

**Both nodes MUST run the exact code below, verbatim — do not improvise your own script, and do not
hand-type `BASE`/`PEER`.** Two distinct failures already happened from manual substitution: (a) improvised
per-day loops with a different HTTP client caused false "missing data" reports when timeouts mid-loop
were mis-read as "not found" (Known Issue #16), and (b) the laptop node once hard-coded `BASE =
"http://localhost:8000"` (copied verbatim from a stale example) — `localhost` has no Honcho on the
laptop, every call failed, and the failure was silently swallowed into a bare `False` instead of
surfacing an error (Known Issue #17). **`BASE`/`PEER`/`WORKSPACE` must be read from this node's own
`honcho.json`** — never typed manually — so the exact same code is 100% portable across both nodes with
zero edits:

```python
import json, os, glob, urllib.request, time

def _load_honcho_config():
    candidates = [
        os.path.expanduser("~/.hermes/honcho.json"),                       # server: profile default
        os.path.expanduser("~/.hermes/profiles/assistant/honcho.json"),    # laptop: profile assistant
    ] + glob.glob(os.path.expanduser("~/.hermes/profiles/*/honcho.json"))
    for path in candidates:
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                cfg = json.load(f)
            host = next(iter(cfg["hosts"].values()))
            return cfg["baseUrl"], host["workspace"], host["peerName"]
    raise FileNotFoundError("No honcho.json found in any known profile path")

BASE, WORKSPACE, PEER = _load_honcho_config()
SESSION = "agent-main-telegram-dm-<chat_id>"   # the real production session, not a throwaway one

def _post(path, payload, retries=3):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{BASE}{path}", data=data,
                                  headers={"Content-Type": "application/json"}, method="POST")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                return json.loads(resp.read())
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2)

def persist_report(region, date, full_report_text):
    """region: 'asia' | 'latam'.  date: 'YYYY-MM-DD'.  full_report_text: the RAW pasted report, unmodified."""
    content = f"[SALE-REPORT-{region.upper()}] [DATE:{date}] [REGION:{region.upper()}]\n{full_report_text}"
    return _post(f"/v3/workspaces/{WORKSPACE}/sessions/{SESSION}/messages", {
        "messages": [{
            "peer_id": PEER,
            "content": content,
            "metadata": {
                "date": date,
                "type": f"sale-report-{region}",
                "region": region,
                "source": "file-import-v2",       # keep this literal value for cross-node consistency
                "day_label": f"Report {date}",
                "searchable_date": date.replace("-", "/"),
            },
        }]
    })

def verify_coverage(region):
    """Exact metadata filter — NOT semantic search. Returns every matching date, paginated fully."""
    all_items, page = [], 1
    while True:
        resp = _post(f"/v3/workspaces/{WORKSPACE}/sessions/{SESSION}/messages/list", {
            "page": page, "size": 50,
            "filters": {"metadata": {"region": region, "source": "file-import-v2"}},
        })
        all_items += resp["items"]
        if len(resp["items"]) < 50:
            break
        page += 1
    return sorted(set(m["metadata"]["date"] for m in all_items))

# Usage:
# persist_report("asia", "2026-07-19", full_report_text)   # one call per region/date, FULL raw text
# for region in ["asia", "latam"]:
#     print(region, verify_coverage(region))
```
- One `persist_report` call per region/date, with the FULL original report text (not a compressed
  summary) — metadata alone is not enough, the raw figures must stay retrievable too.
- **Any request to check/verify/count data by date MUST call `verify_coverage()` and report its output
  directly** — never `honcho_search`/`honcho_context` for this purpose (see Known Issue #15), and never a
  hand-written alternative (Known Issue #16). `verify_coverage()` is a hard DB filter, not a ranked
  top-K search — it returns every matching row regardless of semantic relevance.
- To read history for open-ended trend analysis (a real user question, approximate is fine), `honcho_search`
  with a query naming the region/country is acceptable — do NOT assume `honcho_context` (session-scoped)
  will surface older reports, especially ones logged from the other node.

## Chart Generation
See `references/chart-generation.md` for Plotly and ECharts dashboard templates.
See `references/echarts-dashboard-template.md` for a complete working ECharts HTML dashboard template with KPI cards.
Country color scheme (consistent across all charts):
- 🇮🇩 Indonesia: `#F44336` (red)
- 🇮🇳 India: `#4CAF50` (green)
- 🇲🇾 Malaysia: `#FF9800` (orange)
- 🇹🇭 Thailand: `#9C27B0` (purple)
- 🇨🇴 Colombia: `#FFC107` (gold)
- 🇵🇪 Peru: `#E91E63` (pink)
- Asia overall: `#2196F3` (blue)
- LatAm overall: `#FF9800` (orange)

## Linked Files
- `references/chart-generation.md` — Library comparison, Selenium screenshot patterns, Telegram delivery, dependency list.
- `references/echarts-dashboard-template.md` — Complete working ECharts HTML dashboard template with KPI cards, data injection, setOption patterns, and full screenshot+delivery pipeline.
- `references/hermes-dual-bot-setup.md` — Dual Telegram bot architecture, rsync sync, Hermes Agent install (server + macOS), toolset enabling, skills marketplace.

## D0 FC Calculation Detail
- Country-level FC: `lead_early_D0 ÷ avg(lead_early_Dn / total_lead_Dn)` for n in {D-3, D-2, D-1}
- "lead_early" = lead volume from midnight to 08:30
- Pub-offer FC uses the same formula but only for that pub-offer's data → small sample → unreliable
- Cannot reverse-engineer actual lead_early from FC alone (missing the per-day ratios)

## Pitfalls
1. **Pub-offer lead is FC, not actual.** This was a major early mistake — we reported "lead crashed to 0" when it was just a bad forecast. GP actual is the only reliable signal at offer level.
2. **Indonesia drags overall GP.** Always calculate "overall GP excluding ID" to show the picture without the structural loss.
3. **Single-offer catastrophes** (e.g., KRK2 fitarin-cpl-th losing −9,683 in 2 days) can mask otherwise healthy countries. Always break out the worst offender.
4. **Sunday dip is normal.** Don't flag it as a problem.
5. **LatAm FC = 0 is normal.** Don't interpret as "no leads."
6. **When reading .env for TG bot token, skip lines starting with `#`.** The file often has a commented-out token above the real one — naive parsing grabs the wrong line.
7. **`hermes tools list` shows CLI toolsets, not Telegram toolsets.** Tools like code_execution/skills/memory may appear disabled in CLI but work fine on Telegram via `platform_toolsets.telegram`. Don't assume a tool is unavailable based on CLI output alone.
8. **Run commands directly when tools are available.** Don't tell the user to run commands manually if terminal/code_execution tools are enabled — execute them. The user explicitly expects autonomous execution.
6. **Telegram token comment trap.** The `.env` file may have `# TELEGRAM_BOT_TOKEN=...` above the real line. Always skip `#` lines when parsing. The `hermes send` CLI is unreliable for file delivery — use `requests.post` to `api.telegram.org/bot{token}/sendPhoto` directly.
7. **ECharts CDN in headless Chrome.** PyEcharts' default render uses a CDN `<script>` tag. In headless Chrome with no internet or slow DNS, the JS never loads and the screenshot is blank. Fix: include `<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js">` explicitly in the HTML head, and wait ≥6 seconds after `driver.get()` before screenshotting. Alternatively, download `echarts.min.js` locally.
8. **PyEcharts render_embed vs hand-built HTML.** For dashboards with KPI cards and multiple charts, hand-building the HTML with raw ECharts `init()`/`setOption()` calls is far more flexible than PyEcharts' Python API. Inject data as `var DATA = {json.dumps(...)};` in a `<script>` block — avoids all template-replacement collisions.
9. **Long chart scripts timeout in terminal heredoc.** Security-scan approval on CDN URLs can cause the heredoc to timeout. Always `write_file` the script to `/tmp/dashboard_xxx.py` first, then run `python3 /tmp/dashboard_xxx.py` in a separate terminal call.
10. **execute_code sandbox misses pip packages.** Libraries like matplotlib, selenium, plotly are installed in the hermes-agent venv but not available in the `execute_code` sandbox. Use `terminal` to run chart scripts, not `execute_code`.
11. **Cannot restart gateway from inside gateway.** `systemctl restart hermes-gateway` from a bot-initiated terminal is blocked — SIGTERM propagates and kills the command before it completes. Config changes (e.g., `hermes config set memory.memory_enabled true`) take effect only after a manual restart from a separate SSH session: `hermes gateway restart` or `systemctl restart hermes-gateway`.
12. **`hermes tools list` shows CLI toolsets only.** Telegram may have different (more) tools enabled via `platform_toolsets.telegram` in config.yaml. Don't rely on `hermes tools list` output to determine what's available during a Telegram session.
