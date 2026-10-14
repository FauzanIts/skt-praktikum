from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

import penyimpanan as db


@asynccontextmanager
async def lifespan(app):
    # [PEKAN 5] jalankan server gRPC di port 50051
    # from grpc_server import mulai_grpc
    # mulai_grpc()

    # [PEKAN 6] jalankan subscriber MQTT
    # from mqtt_subscriber import mulai_mqtt
    # mulai_mqtt()
    yield


app = FastAPI(title="cloud-api", lifespan=lifespan)

# [PEKAN 6] pasang endpoint GraphQL di /graphql
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
