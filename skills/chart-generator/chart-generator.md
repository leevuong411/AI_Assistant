---
name: chart-generator
description: Tao chart trend tu du lieu sale report va gui qua Telegram
trigger: Khi user yeu cau tao chart, bieu do, trend, hoac visualize du lieu sale
version: 1.0
---

# Skill: Chart Generator

## Quy trinh
1. Tao HTML dashboard voi ECharts (Apache ECharts JS)
2. Screenshot bang Selenium + Chrome headless
3. Gui PNG qua Telegram Bot API

## Thu vien uu tien
1. **ECharts** (mac dinh) — dep nhat, KPI cards, rounded corners, shadows
2. Plotly — backup neu ECharts loi
3. Matplotlib — fallback cuoi

## Chrome path
- /root/.local/share/choreographer/deps/chrome-linux64/chrome

## Template ECharts Dashboard
- KPI cards row (HTML/CSS styled)
- Charts dung echarts.init() + setOption()
- Data inject qua JS variable: var DATA = {...}
- Screenshot: Selenium headless, wait 8s cho JS render
- Window size: 1500 x auto (full page height)
- Background: #f5f7fa, chart boxes: white, border-radius: 12px, box-shadow

## Mau sac quoc gia
- Indonesia: #F44336 (do)
- India: #4CAF50 (xanh la)
- Malaysia: #FF9800 (cam)
- Thailand: #9C27B0 (tim)
- Colombia: #FFC107 (vang)
- Peru: #E91E63 (hong)

## Gui Telegram
- Doc token tu ~/.hermes/.env (skip dong comment #)
- Chat ID: 879907579
- Dung requests.post sendPhoto
