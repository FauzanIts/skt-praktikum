import strawberry
from strawberry.fastapi import GraphQLRouter

import penyimpanan as db

# [PEKAN 6] Skema GraphQL cloud-api.
#
# Catatan penamaan: Strawberry mengubah nama field snake_case Python menjadi
# camelCase di sisi GraphQL. Jadi "rata_rata" dipanggil sebagai "rataRata" dan
# "node_id" sebagai "nodeId" dari dalam query. Ini BUKAN bug -- jangan diubah
# di sisi Python, sesuaikan saja penulisan query-nya.
#
# Field "waktu" sengaja TIDAK ada di type Bacaan. Menambahkannya adalah bagian
# dari Tugas 7 (lihat Kode 2.45 di modul).


@strawberry.type
class Bacaan:
    request_id: str
    node_id: str
    seq: int
    nilai: float
    jalur: str


@strawberry.type
class Ringkasan:
    # rata_rata/minimum/maksimum boleh None: AVG/MIN/MAX atas tabel kosong
    # mengembalikan NULL, sehingga /graphql menampilkan null sebelum ada data.
    jumlah: int
    rata_rata: float | None
    minimum: float | None
    maksimum: float | None


@strawberry.type
class Query:
    @strawberry.field
    def bacaan(self, terakhir: int = 10, node_id: str | None = None,
               jalur: str | None = None) -> list[Bacaan]:
        return [
            Bacaan(request_id=b["request_id"], node_id=b["node_id"],
                   seq=b["seq"], nilai=b["nilai"], jalur=b["jalur"])
            for b in db.ambil(terakhir, node_id, jalur)
        ]

    @strawberry.field
    def ringkasan(self, node_id: str | None = None) -> Ringkasan:
        return Ringkasan(**db.ringkasan(node_id))


graphql_app = GraphQLRouter(strawberry.Schema(query=Query))
