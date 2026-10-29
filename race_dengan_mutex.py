"""Producer-consumer DENGAN sinkronisasi — versi perbaikan dari race_tanpa_mutex.

Dua masalah dijaga terpisah:
  - mutex  : melindungi indeks dan slot buffer (critical section)
  - semafor: menghitung slot kosong dan slot terisi, sehingga produsen menunggu
             saat buffer penuh dan konsumen menunggu saat buffer kosong

Keduanya perlu. Mutex saja mencegah data rusak, tetapi tidak mencegah produsen
menimpa data yang belum sempat dibaca; semafor saja tidak mencegah dua thread
mengubah indeks pada saat bersamaan.
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


def produsen(jeda, kunci, slot_kosong, slot_terisi):
    global posisi_tulis, jumlah_ditulis
    for i in range(JUMLAH_DATA):
        slot_kosong.acquire()            # tunggu bila buffer penuh
        with kunci:                      # critical section: indeks + slot
            buffer[posisi_tulis] = i
            posisi_tulis = (posisi_tulis + 1) % BESAR_BUFFER
            jumlah_ditulis += 1
        slot_terisi.release()            # beri tahu konsumen ada data
        time.sleep(jeda)


def konsumen(hasil, jeda, kunci, slot_kosong, slot_terisi):
    global posisi_baca, jumlah_dibaca, hilang, duplikat
    terkirim = set()
    for _ in range(JUMLAH_DATA):
        slot_terisi.acquire()            # tunggu bila buffer kosong
        with kunci:                      # critical section: indeks + slot
            data = buffer[posisi_baca]
            buffer[posisi_baca] = None
            posisi_baca = (posisi_baca + 1) % BESAR_BUFFER
            jumlah_dibaca += 1
        slot_kosong.release()            # beri tahu produsen ada slot bebas

        if data is None:
            hilang += 1
            continue
        if data in terkirim:
            duplikat += 1
        else:
            terkirim.add(data)
        time.sleep(jeda)
    hasil["terkirim"] = len(terkirim)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jeda", type=float, default=0.00002)
    p.add_argument("--ulang", type=int, default=1)
    a = p.parse_args()

    hasil_akhir = []
    for run in range(a.ulang):
        global buffer, posisi_tulis, posisi_baca, jumlah_ditulis, jumlah_dibaca
        global hilang, duplikat
        buffer = [None] * BESAR_BUFFER
        posisi_tulis = posisi_baca = 0
        jumlah_ditulis = jumlah_dibaca = hilang = duplikat = 0

        kunci = threading.Lock()
        slot_kosong = threading.Semaphore(BESAR_BUFFER)
        slot_terisi = threading.Semaphore(0)

        hasil = {}
        t_prod = threading.Thread(target=produsen,
                                  args=(a.jeda, kunci, slot_kosong, slot_terisi),
                                  name="produsen")
        t_kons = threading.Thread(target=konsumen,
                                  args=(hasil, a.jeda, kunci, slot_kosong,
                                        slot_terisi),
                                  name="konsumen")
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
    rusak = sum(1 for h in hasil_akhir if h["hilang"] or h["duplikat"])
    print(f"run bermasalah: {rusak} dari {len(hasil_akhir)}")
    os.makedirs("results", exist_ok=True)
    with open("results/dengan-mutex.json", "w", encoding="utf-8") as f:
        json.dump({"jeda": a.jeda, "besar_buffer": BESAR_BUFFER,
                   "target": JUMLAH_DATA, "hasil": hasil_akhir}, f, indent=2)


if __name__ == "__main__":
    main()
