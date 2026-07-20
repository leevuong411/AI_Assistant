# Chart Generation for Sale Reports

## Libraries Tested

| Library | Quality | Export PNG | Setup | Recommendation |
|---|---|---|---|---|
| **ECharts (via PyEcharts + Selenium)** | ⭐⭐⭐⭐⭐ | HTML → Chrome screenshot | Medium | 🏆 Best visual quality |
| **Plotly** | ⭐⭐⭐⭐ | Via Kaleido + Chrome | Easy | Good default |
| **Matplotlib** | ⭐⭐ | Native | Trivial | Fallback only |

## Preferred: ECharts HTML Dashboard

### Why ECharts wins
- KPI cards with styled HTML (rounded corners, shadows, gradients)
- Richer chart interactions (markPoint, markLine, visualMap)
- Modern look matching React-style dashboards
- Full CSS control over layout

### Architecture
1. Build HTML page with ECharts JS charts + CSS KPI cards + scorecard
2. Use Selenium + headless Chrome to screenshot full page
3. Send PNG via Telegram Bot API

### Chrome location on server
```
/root/.local/share/choreographer/deps/chrome-linux64/chrome
```
Installed via `plotly_get_chrome` (reusable by Selenium).

### Selenium screenshot pattern
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

chrome_path = "/root/.local/share/choreographer/deps/chrome-linux64/chrome"
options = Options()
options.binary_location = chrome_path
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1500,1600")

driver = webdriver.Chrome(options=options)
driver.get("file:///tmp/dashboard.html")
time.sleep(6)  # Wait for ECharts JS to render

# Auto-size to full page height
height = driver.execute_script("return document.body.scrollHeight")
driver.set_window_size(1500, height + 50)
time.sleep(2)

driver.save_screenshot("/tmp/dashboard.png")
driver.quit()
```

### Sending to Telegram
```python
# Read token — skip commented lines
token = None
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        line = line.strip()
        if line.startswith("#"): continue
        if "TELEGRAM_BOT_TOKEN" in line:
            token = line.split("=", 1)[1].strip()
            break

url = f"https://api.telegram.org/bot{token}/sendPhoto"
with open("/tmp/dashboard.png", "rb") as photo:
    r = requests.post(url,
        data={"chat_id": "879907579", "caption": "..."},
        files={"photo": photo})
```

**Pitfall:** The `.env` file may have a commented-out `# TELEGRAM_BOT_TOKEN=...` line above the real one. Always skip lines starting with `#`.

## Plotly Fallback

If Selenium is unavailable, Plotly + Kaleido works:
```python
fig.write_image("/tmp/chart.png", scale=2)
```
Requires Chrome at the Kaleido-managed path (installed via `plotly_get_chrome`).

## Dashboard Layout (ECharts)

Standard dashboard structure:
1. **KPI row** — 4-5 key metrics as styled cards
2. **Row 1** — Overall GP trend + GP by country bar chart
3. **Row 2** — Indonesia GP1 trend + India GP streak
4. **Row 3** — Top/Bottom offers horizontal bar + Scorecard table

CSS framework: flexbox rows with `.chart-box` (white bg, border-radius 12px, box-shadow).

## Dependencies
```bash
pip3 install plotly kaleido pyecharts selenium requests matplotlib numpy
# Chrome: plotly_get_chrome (or install manually)
```
