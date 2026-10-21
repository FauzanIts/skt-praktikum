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


# ===== [PEKAN 5] gRPC =====
# Import dibungkus try/except supaya kegagalan gRPC tidak mematikan Pekan 4.
# Bila sensor_pb2 belum ter-generate, MODE=rest tetap berfungsi normal.
try:
    import grpc
    import sensor_pb2
    import sensor_pb2_grpc
    _ADA_GRPC = True
    _ALASAN_GRPC = ""
except ImportError as _e:
    _ADA_GRPC = False
    _ALASAN_GRPC = str(_e)

PORT_GRPC = os.getenv("PORT_GRPC", "50051")


def kirim_grpc(pesan):
    """Kirim satu bacaan lewat gRPC ke cloud-api (Laptop B)."""
    if not _ADA_GRPC:
        log.error("gRPC seq=%s -> modul belum siap: %s", pesan["seq"], _ALASAN_GRPC)
        return {"terkirim": False, "coba": 0, "error": _ALASAN_GRPC}

    target = f"{CLOUD_HOST}:{PORT_GRPC}"
    for coba in range(1, MAKS_COBA + 1):
        try:
            # Kanal dibuka per percobaan agar kegagalan koneksi tertangkap
            # sebagai RpcError dan bisa di-retry, bukan menggantung di import.
            with grpc.insecure_channel(target) as kanal:
                stub = sensor_pb2_grpc.SensorStub(kanal)
                st = stub.Kirim(
                    sensor_pb2.Bacaan(
                        node_id=pesan["node_id"],
                        nilai=float(pesan["nilai"]),
                        waktu=int(pesan["waktu"]),
                        request_id=pesan["request_id"],
                        seq=int(pesan["seq"]),
                    ),
                    timeout=TIMEOUT_S,
                )
            log.info("gRPC seq=%s coba=%s -> diterima=%s duplikat=%s",
                     pesan["seq"], coba, st.diterima, st.duplikat)
            return {"terkirim": True, "coba": coba, "duplikat": st.duplikat}
        except grpc.RpcError as e:
            log.warning("gRPC seq=%s coba=%s -> gagal (%s: %s)",
                        pesan["seq"], coba, e.code().name, e.details())
    return {"terkirim": False, "coba": MAKS_COBA}


PENGIRIM["grpc"] = kirim_grpc


# ===== [PEKAN 6] MQTT =====
import json

try:
    import paho.mqtt.client as mqtt
    _ADA_MQTT = True
    _ALASAN_MQTT = ""
except ImportError as _e:
    mqtt = None
    _ADA_MQTT = False
    _ALASAN_MQTT = str(_e)

QOS = int(os.getenv("QOS", "1"))

_mqtt = None
if _ADA_MQTT:
    # client_id sengaja dipatok tetap; koneksi dibuka asinkron supaya
    # import kirim.py tidak menunggu broker hidup.
    _mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                        client_id="edge-api-publisher")
    _mqtt.connect_async(CLOUD_HOST, 1883)
    _mqtt.loop_start()


def kirim_mqtt(pesan):
    if not _ADA_MQTT:
        log.error("MQTT seq=%s -> modul belum siap: %s", pesan["seq"], _ALASAN_MQTT)
        return {"terkirim": False, "error": _ALASAN_MQTT}

    topik = f"skt/{pesan['node_id']}/suhu"
    info = _mqtt.publish(topik, json.dumps(pesan), qos=QOS)
    log.info("MQTT seq=%s -> topik=%s qos=%s rc=%s",
             pesan["seq"], topik, QOS, info.rc)
    return {"terkirim": info.rc == mqtt.MQTT_ERR_SUCCESS,
            "topik": topik, "qos": QOS}


PENGIRIM["mqtt"] = kirim_mqtt
