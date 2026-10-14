import logging
import os

import httpx

CLOUD_HOST = os.environ["CLOUD_HOST"]
TIMEOUT_S = float(os.getenv("TIMEOUT_S", "1"))
MAKS_COBA = int(os.getenv("MAKS_COBA", "3"))
log = logging.getLogger("uvicorn.error")


def kirim_rest(pesan):
    url = f"http://{CLOUD_HOST}:9090/bacaan"
    for coba in range(1, MAKS_COBA + 1):
        try:
            r = httpx.post(url, json=pesan, timeout=TIMEOUT_S)
            log.info("REST seq=%s coba=%s -> %s %s",
                     pesan["seq"], coba, r.status_code, r.text)
            return {"terkirim": True, "coba": coba}
        except httpx.TimeoutException:
            log.warning("REST seq=%s coba=%s -> timeout, kirim ulang",
                        pesan["seq"], coba)
        except httpx.TransportError as e:
            log.warning("REST seq=%s coba=%s -> gagal terhubung (%s)",
                        pesan["seq"], coba, type(e).__name__)
    return {"terkirim": False, "coba": MAKS_COBA}


PENGIRIM = {"rest": kirim_rest}
