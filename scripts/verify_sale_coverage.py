import json, os, glob, urllib.request, time


def _load_honcho_config():
    candidates = [
        os.path.expanduser("~/.hermes/honcho.json"),
        os.path.expanduser("~/.hermes/profiles/assistant/honcho.json"),
    ] + glob.glob(os.path.expanduser("~/.hermes/profiles/*/honcho.json"))
    for path in candidates:
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                cfg = json.load(f)
            host = next(iter(cfg["hosts"].values()))
            return cfg["baseUrl"], host["workspace"], host["peerName"]
    raise FileNotFoundError("No honcho.json found in any known profile path")


BASE, WORKSPACE, PEER = _load_honcho_config()
SESSION = "agent-main-telegram-dm-879907579"


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


def verify_coverage(region):
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


if __name__ == "__main__":
    print(f"[verify_sale_coverage] node={PEER} base={BASE}")
    for region in ["asia", "latam"]:
        dates = verify_coverage(region)
        span = f"{dates[0]} -> {dates[-1]}" if dates else "(none)"
        print(f"{region}: {len(dates)} ngay | {span}")
