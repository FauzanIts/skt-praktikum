from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

import penyimpanan as db


@asynccontextmanager
async def lifespan(app):
    # [PEKAN 5] jalankan server gRPC di port 50051
    from grpc_server import mulai_grpc
    mulai_grpc()

    # [PEKAN 6] jalankan subscriber MQTT
    from mqtt_subscriber import mulai_mqtt
    mulai_mqtt()
    yield


app = FastAPI(title="cloud-api", lifespan=lifespan)

# [PEKAN 6] pasang endpoint GraphQL di /graphql
#
# SENGAJA MASIH TERKOMENTAR (mengikuti urutan modul): Kode 2.41 meminta baris
# GraphQL belum diaktifkan saat mengerjakan C.11-C.12, supaya bila cloud-api
# gagal start penyebabnya pasti dari MQTT dan bukan dari GraphQL.
#
# Aktifkan dua baris di bawah saat masuk C.13, dengan DUA SYARAT:
#   1. hapus tanda '#' di awal kedua baris
#   2. kedua baris harus mulai di KOLOM 0 (di luar lifespan). Bila ikut
#      ter-indentasi 4 spasi seperti blok di atas, FastAPI gagal boot
#      dengan IndentationError.
#
# from graphql_schema import graphql_app
# app.include_router(graphql_app, prefix="/graphql")


class Bacaan(BaseModel):
    request_id: str
    node_id: str
    seq: int
    nilai: float
    waktu: int


@app.post("/bacaan", status_code=201)
def terima_bacaan(b: Bacaan):
    return db.simpan(b.model_dump(), jalur="rest")


@app.get("/bacaan")
def daftar_bacaan(terakhir: int = 10):
    return db.ambil(terakhir)


@app.get("/statistik")
def statistik():
    return db.statistik()
