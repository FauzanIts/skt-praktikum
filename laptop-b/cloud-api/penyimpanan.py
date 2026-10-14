import os
import random
import sqlite3
import threading
import time

DB_PATH = os.getenv("DB_PATH", "/data/cloud.db")
IDEMPOTEN = os.getenv("IDEMPOTEN", "0") == "1"
LAMBAT_PERSEN = int(os.getenv("LAMBAT_PERSEN", "0"))
LAMBAT_MS = int(os.getenv("LAMBAT_MS", "1500"))

_kunci = threading.Lock()
_db = sqlite3.connect(DB_PATH, check_same_thread=False)
_db.row_factory = sqlite3.Row
_db.execute("""
    CREATE TABLE IF NOT EXISTS bacaan (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT,
        node_id    TEXT,
        seq        INTEGER,
        nilai      REAL,
        waktu      INTEGER,
        jalur      TEXT
    )""")


def simpan(p, jalur):
    duplikat = False
    with _kunci:
        if IDEMPOTEN:
            sudah_ada = _db.execute(
                "SELECT 1 FROM bacaan WHERE request_id = ?",
                (p["request_id"],)).fetchone()
            duplikat = sudah_ada is not None
        if not duplikat:
            _db.execute(
                "INSERT INTO bacaan (request_id, node_id, seq, nilai, waktu, jalur)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (p["request_id"], p["node_id"], p["seq"],
                 p["nilai"], p["waktu"], jalur))
            _db.commit()
    # simulasi server sibuk: data SUDAH tersimpan, tetapi balasannya terlambat
    if random.randint(1, 100) <= LAMBAT_PERSEN:
        time.sleep(LAMBAT_MS / 1000)
    return {"tersimpan": not duplikat, "duplikat": duplikat}


def statistik():
    with _kunci:
        total, unik = _db.execute(
            "SELECT COUNT(*), COUNT(DISTINCT request_id) FROM bacaan").fetchone()
    return {"baris_tersimpan": total, "request_id_unik": unik,
            "data_ganda": total - unik}


def ambil(terakhir=10, node_id=None, jalur=None):
    with _kunci:
        baris = _db.execute(
            "SELECT * FROM bacaan"
            " WHERE (? IS NULL OR node_id = ?) AND (? IS NULL OR jalur = ?)"
            " ORDER BY id DESC LIMIT ?",
            (node_id, node_id, jalur, jalur, terakhir)).fetchall()
    return [dict(b) for b in baris]


def ringkasan(node_id=None):
    with _kunci:
        n, rata, mn, mx = _db.execute(
            "SELECT COUNT(*), AVG(nilai), MIN(nilai), MAX(nilai) FROM bacaan"
            " WHERE (? IS NULL OR node_id = ?)", (node_id, node_id)).fetchone()
    return {"jumlah": n, "rata_rata": rata, "minimum": mn, "maksimum": mx}
