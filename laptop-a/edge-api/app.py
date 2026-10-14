import itertools
import os
import socket
import time
import uuid

from fastapi import FastAPI
from pydantic import BaseModel

from kirim import PENGIRIM

MODE = os.getenv("MODE", "rest")
NODE_ID = os.getenv("NODE_ID", "laptop-a")
nomor_urut = itertools.count(1)

app = FastAPI(title="edge-api")


class BacaanSensor(BaseModel):
    nilai: float


@app.get("/")
def echo():
    # echo service dari Praktikum 1 tetap dipertahankan
    return {
        "host": socket.gethostname(),
        "waktu_unix": time.time(),
        "waktu_lokal": time.strftime("%H:%M:%S"),
    }


@app.post("/bacaan")
def terima_dari_sensor(b: BacaanSensor):
    pesan = {
        "request_id": str(uuid.uuid4()),  # tetap sama walau dikirim ulang
        "node_id": NODE_ID,
        "seq": next(nomor_urut),
        "nilai": b.nilai,
        "waktu": int(time.time() * 1000),
    }
    hasil = PENGIRIM[MODE](pesan)
    return {"mode": MODE, "seq": pesan["seq"], **hasil}
