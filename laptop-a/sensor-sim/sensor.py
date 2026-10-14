import json
import os
import random
import time
import urllib.request

EDGE_URL = os.getenv("EDGE_URL", "http://edge-api:8000")
INTERVAL_S = float(os.getenv("INTERVAL_S", "2"))

suhu = 30.0
while True:
    # suhu bergerak pelan, seperti sensor sungguhan
    suhu = max(24.0, min(36.0, suhu + random.uniform(-0.4, 0.4)))
    badan = json.dumps({"nilai": round(suhu, 2)}).encode("utf-8")
    req = urllib.request.Request(
        EDGE_URL + "/bacaan",
        data=badan,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print("sensor ->", r.read().decode("utf-8"), flush=True)
    except Exception as e:
        print("sensor -> gagal menghubungi edge-api:", e, flush=True)
    time.sleep(INTERVAL_S)
