import logging
import os
from concurrent import futures

import grpc

import penyimpanan as db
import sensor_pb2
import sensor_pb2_grpc

PORT_GRPC = int(os.getenv("PORT_GRPC", "50051"))
PEKERJA_GRPC = 10
log = logging.getLogger("uvicorn.error")

_server = None


class SensorServicer(sensor_pb2_grpc.SensorServicer):
    def Kirim(self, request, context):
        pesan = {
            "request_id": request.request_id,
            "node_id": request.node_id,
            "seq": request.seq,
            "nilai": request.nilai,
            "waktu": request.waktu,
        }
        hasil = db.simpan(pesan, jalur="grpc")
        log.info("gRPC seq=%s node=%s -> tersimpan=%s duplikat=%s",
                 request.seq, request.node_id,
                 hasil["tersimpan"], hasil["duplikat"])
        return sensor_pb2.Status(diterima=True, duplikat=hasil["duplikat"])


def mulai_grpc(port=None):
    global _server
    port = port or PORT_GRPC
    _server = grpc.server(futures.ThreadPoolExecutor(max_workers=PEKERJA_GRPC))
    sensor_pb2_grpc.add_SensorServicer_to_server(SensorServicer(), _server)
    _server.add_insecure_port(f"0.0.0.0:{port}")  # ingat pelajaran Praktikum 1
    _server.start()
    log.info("gRPC server siap di port %s", port)
    return _server
