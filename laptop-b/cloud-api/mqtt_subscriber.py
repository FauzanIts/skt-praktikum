import json
import logging
import os

import paho.mqtt.client as mqtt

import penyimpanan as db

# [PEKAN 6] Subscriber MQTT milik cloud-api.
#
# Sesi persisten (C.12) bergantung pada TIGA hal yang harus sama-sama benar:
#   1. client_id tetap        -> broker mengenali kita sebagai sesi yang sama
#   2. clean_session=False    -> broker menyimpan sesi saat kita memutus koneksi
#   3. subscribe dengan qos=1 -> pesan yang tertahan selama kita offline ikut diantar
# Kalau salah satu diubah, pesan yang dikirim saat cloud-api mati akan hilang.
#
# Ingat juga: QoS efektif = min(QoS publisher, QoS subscriber). Jadi walau
# subscriber minta QoS 1, pesan tetap bisa hilang bila Laptop A mengirim QoS 0.

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
log = logging.getLogger("uvicorn.error")
_klien = None


def _saat_terhubung(client, userdata, flags, reason_code, properties):
    # session_present=True berarti broker memulihkan sesi lama beserta
    # langganan yang tersimpan -- inilah bukti C.12 berhasil.
    log.info("MQTT terhubung (session_present=%s)", flags.session_present)
    client.subscribe("skt/+/suhu", qos=1)


def _saat_pesan(client, userdata, msg):
    pesan = json.loads(msg.payload)
    hasil = db.simpan(pesan, jalur="mqtt")
    log.info("MQTT seq=%s -> %s", pesan["seq"], hasil)


def mulai_mqtt():
    global _klien
    _klien = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id="cloud-api-subscriber",
                         clean_session=False)
    _klien.on_connect = _saat_terhubung
    _klien.on_message = _saat_pesan
    # connect_async + loop_start tidak memblokir startup FastAPI: broker boleh
    # belum siap, paho akan menyambung ulang sendiri (reconnect_on_failure).
    _klien.connect_async(MQTT_HOST, 1883)
    _klien.loop_start()
