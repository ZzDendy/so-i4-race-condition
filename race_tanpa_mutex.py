"""Producer-consumer TANPA sinkronisasi — memperlihatkan race condition.

Buffer data sensor dipakai bersama oleh thread pembaca (producer) dan thread
pengirim (consumer). Tidak ada mutex, tidak ada semaphore, dan tidak ada
penjagaan indeks. Jalankan berulang; hasilnya tidak selalu sama.

Skrip ini sengaja menyisipkan jeda kecil di antara "baca indeks" dan "tulis
data" supaya celah waktunya cukup lebar untuk diamati. Tanpa jeda itu,
race condition tetap ada tetapi lebih sulit muncul.
"""
import argparse
import json
import os
import threading
import time

BESAR_BUFFER = 8
JUMLAH_DATA = 2000

buffer = [None] * BESAR_BUFFER
posisi_tulis = 0
posisi_baca = 0
jumlah_ditulis = 0
jumlah_dibaca = 0
hilang = 0
duplikat = 0


def produsen(jeda):
    global posisi_tulis, jumlah_ditulis
    for i in range(JUMLAH_DATA):
        # critical section dimulai
        slot = posisi_tulis
        posisi_tulis = (posisi_tulis + 1) % BESAR_BUFFER
        time.sleep(jeda)                 # celah: thread lain bisa ikut masuk
        buffer[slot] = i
        jumlah_ditulis += 1
        # critical section selesai
        time.sleep(jeda)


def konsumen(hasil, jeda):
    global posisi_baca, jumlah_dibaca, hilang, duplikat
    terkirim = set()
    percobaan = 0
    while jumlah_dibaca + hilang < JUMLAH_DATA and percobaan < JUMLAH_DATA * 40:
        percobaan += 1
        slot = posisi_baca
        posisi_baca = (posisi_baca + 1) % BESAR_BUFFER
        time.sleep(jeda * 0.5)
        data = buffer[slot]
        if data is None:
            hilang += 1
            continue
        if data in terkirim:
            duplikat += 1
        else:
            terkirim.add(data)
        jumlah_dibaca += 1
        time.sleep(jeda * 0.5)
    hasil["terkirim"] = len(terkirim)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jeda", type=float, default=0.00002,
                   help="lebar celah critical section (detik)")
    p.add_argument("--ulang", type=int, default=1)
    a = p.parse_args()

    hasil_akhir = []
    for run in range(a.ulang):
        global buffer, posisi_tulis, posisi_baca, jumlah_ditulis, jumlah_dibaca
        global hilang, duplikat
        buffer = [None] * BESAR_BUFFER
        posisi_tulis = posisi_baca = 0
        jumlah_ditulis = jumlah_dibaca = hilang = duplikat = 0

        hasil = {}
        t_prod = threading.Thread(target=produsen, args=(a.jeda,), name="produsen")
        t_kons = threading.Thread(target=konsumen, args=(hasil, a.jeda), name="konsumen")
        t_prod.start()
        t_kons.start()
        t_prod.join()
        t_kons.join()

        hasil_akhir.append({
            "run": run + 1,
            "ditulis": jumlah_ditulis,
            "dibaca": jumlah_dibaca,
            "hilang": hilang,
            "duplikat": duplikat,
            "unik": hasil.get("terkirim", 0),
        })

    for h in hasil_akhir:
        print(json.dumps(h))
    if a.ulang > 1:
        rusak = sum(1 for h in hasil_akhir if h["hilang"] or h["duplikat"])
        print(f"run bermasalah: {rusak} dari {a.ulang}")
    os.makedirs("results", exist_ok=True)
    with open("results/tanpa-mutex.json", "w", encoding="utf-8") as f:
        json.dump({"jeda": a.jeda, "besar_buffer": BESAR_BUFFER,
                   "target": JUMLAH_DATA, "hasil": hasil_akhir}, f, indent=2)


if __name__ == "__main__":
    main()
