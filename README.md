# SKT Praktikum — Sistem Komputasi Terdistribusi

Praktikum mata kuliah **Sistem Komputasi Terdistribusi (F09252022)** — Program Studi S1 Teknik Informatika, Universitas Tadulako.

Sistem ini adalah simulasi *edge–cloud* yang berjalan di **dua laptop** yang saling terhubung melalui **hotspot ad-hoc** (bukan Wi-Fi kampus, karena *client isolation* membuat kedua host tidak dapat saling menjangkau).

| Node | Peran | Isi |
|------|-------|-----|
| **Laptop B** | Penyedia hotspot + *cloud* | `cloud-api` (REST :9090, gRPC :50051, subscriber MQTT, GraphQL) |
| **Laptop A** | *Edge* / klien | `edge-api` (:8080 → :8000) + `sensor-sim` |

Alur data:

```
sensor-sim ──HTTP──▶ edge-api ──(rest | grpc | mqtt)──▶ cloud-api
 (Laptop A)          (Laptop A)                        (Laptop B)
```

---

## Struktur Repositori

```
skt-praktikum/
├── echo-service/              # Praktikum 1 — echo service (verifikasi interkoneksi)
│   ├── echo_service.py
│   └── Dockerfile
└── laptop-a/                  # Modul 2 — sisi edge
    ├── .env.example           # templat konfigurasi (salin jadi .env)
    ├── docker-compose.yml     # service: edge-api + sensor-sim
    ├── edge-api/
    │   ├── app.py             # GET /  (echo)  ·  POST /bacaan
    │   ├── kirim.py           # pengirim REST (timeout 1 s, maks 3 coba)
    │   ├── requirements.txt
    │   └── Dockerfile
    └── sensor-sim/
        ├── sensor.py          # kirim bacaan suhu tiap 2 detik
        └── Dockerfile
```

> `modul*.txt` dan berkas `.env` **tidak** diunggah ke repositori ini.
> Materi modul adalah milik dosen; `.env` berisi alamat jaringan kelompok.

---

## Prasyarat

- Docker Desktop (diuji pada Docker 29.8.2 / Compose v5.5.1)
- Dua laptop dalam satu hotspot ad-hoc
- Image dasar sudah di-*pull* **selagi ada internet** (hotspot antar-laptop tidak stabil):

```powershell
docker pull python:3.12-slim
docker pull eclipse-mosquitto:2
```

---

## Menjalankan Laptop A (sisi edge)

```powershell
cd laptop-a
Copy-Item .env.example .env      # lalu sesuaikan CLOUD_HOST
docker compose up -d --build
docker compose logs -f edge-api
```

`.env` yang perlu diperiksa:

| Variabel | Arti |
|----------|------|
| `CLOUD_HOST` | IPv4 Laptop B — cek dengan `ipconfig` di Laptop B (bawaan hotspot Windows: `192.168.137.1`) |
| `NODE_ID` | Identitas node, muncul di log dan topik MQTT |
| `MODE` | `rest` (Pekan 4) · `grpc` (Pekan 5) · `mqtt` (Pekan 6) |
| `TIMEOUT_S` | Batas tunggu satu percobaan kirim, detik |
| `MAKS_COBA` | Jumlah maksimum percobaan kirim ulang |

Log yang diharapkan bila `cloud-api` hidup:

```
REST seq=1 coba=1 -> 201 {"tersimpan":true,"duplikat":false}
```

Bila `cloud-api` mati, `edge-api` akan mencoba 3 kali lalu melaporkan `terkirim: false` — ini perilaku yang benar dan menjadi bahan percobaan idempotensi (C.6).

---

## Endpoint

| Node | Endpoint | Keterangan |
|------|----------|------------|
| Laptop A | `GET  http://<ip-laptop-a>:8080/` | echo: hostname + waktu (dipakai juga untuk ukur RTT) |
| Laptop A | `POST http://<ip-laptop-a>:8080/bacaan` | terima bacaan dari `sensor-sim`, teruskan ke cloud |
| Laptop B | `POST http://<ip-laptop-b>:9090/bacaan` | simpan bacaan (idempoten bila `IDEMPOTEN=1`) |
| Laptop B | `GET  http://<ip-laptop-b>:9090/bacaan?terakhir=N` | ambil N bacaan terakhir |

---

## Kendala Umum

| Gejala | Sebab & solusi |
|--------|----------------|
| Kedua laptop tidak bisa saling `ping` | Terhubung ke Wi-Fi kampus (*client isolation*). Pakai hotspot ad-hoc Laptop B. |
| Service tidak bisa diakses dari seberang | Proses *bind* ke `127.0.0.1`, bukan `0.0.0.0`. |
| `UNAVAILABLE` saat mode gRPC | Port 50051 di Laptop B tidak terjangkau — cek firewall. |
| `docker compose` gagal membaca `.env` | Notepad menyimpan sebagai `.env.txt`. Pakai VS Code. |
| `timeout coba=1,2,3` terus-menerus | `CLOUD_HOST` salah, atau `cloud-api` belum jalan / belum terhubung ke hotspot yang sama. |
| Port 8080 sudah dipakai | Hentikan container lama: `docker ps` lalu `docker stop <nama>`. |
