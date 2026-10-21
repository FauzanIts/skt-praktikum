import json
import os
import statistics
import time
import uuid

import grpc
import httpx

import sensor_pb2
import sensor_pb2_grpc

CLOUD_HOST = os.environ["CLOUD_HOST"]
JUMLAH = 200

def pesan_contoh(i):
    return {"request_id": str(uuid.uuid4()), "node_id": "uji-ukur",
            "seq": i, "nilai": 29.75, "waktu": int(time.time() * 1000)}

def ringkas(nama, data_ms):
    data_ms.sort()
    p50 = statistics.median(data_ms)
    p95 = data_ms[int(0.95 * len(data_ms)) - 1]
    print(f"{nama:<5} RTT p50 = {p50:6.2f} ms   p95 = {p95:6.2f} ms")

contoh = pesan_contoh(0)
ukuran_json = len(json.dumps(contoh).encode("utf-8"))
ukuran_pb = len(sensor_pb2.Bacaan(**contoh).SerializeToString())
print(f"ukuran satu pesan : JSON = {ukuran_json} byte, Protobuf = {ukuran_pb} byte")

# REST: satu koneksi dipakai ulang agar adil
with httpx.Client(timeout=5) as klien:
    url = f"http://{CLOUD_HOST}:9090/bacaan"
    klien.post(url, json=pesan_contoh(0))  # pemanasan
    hasil = []
    for i in range(1, JUMLAH + 1):
        t1 = time.perf_counter()
        klien.post(url, json=pesan_contoh(i))
        hasil.append((time.perf_counter() - t1) * 1000)
    ringkas("REST", hasil)

# gRPC: satu channel dipakai ulang
with grpc.insecure_channel(f"{CLOUD_HOST}:50051") as kanal:
    stub = sensor_pb2_grpc.SensorStub(kanal)
    stub.Kirim(sensor_pb2.Bacaan(**pesan_contoh(0)))  # pemanasan
    hasil = []
    for i in range(1, JUMLAH + 1):
        t1 = time.perf_counter()
        stub.Kirim(sensor_pb2.Bacaan(**pesan_contoh(i)))
        hasil.append((time.perf_counter() - t1) * 1000)
    ringkas("gRPC", hasil)
