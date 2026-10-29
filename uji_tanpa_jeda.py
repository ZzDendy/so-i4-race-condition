"""Uji race condition tanpa jeda buatan — bukti bahwa race bukan efek time.sleep.

Pada mesin satu inti Python, jeda buatan bukan penyebab race; ia hanya
mempermudah pengamatan. Skrip ini mempersempit jatah giliran antar thread
(sys.setswitchinterval) supaya perpindahan thread terjadi sesering mungkin,
lalu membandingkan buffer tanpa penjagaan dengan buffer bermutex.
"""
import json
import os
import sys
import threading

sys.setswitchinterval(0.000001)

BESAR = 8
N = 20000


def jalankan(pakai_mutex):
    buf = [None] * BESAR
    pt = pb = 0
    ditulis = dibaca = duplikat = hilang = 0
    kunci = threading.Lock() if pakai_mutex else None
    kirim = threading.Semaphore(0)
    kosong = threading.Semaphore(BESAR)

    def prod():
        nonlocal pt, ditulis
        for i in range(N):
            if pakai_mutex:
                kosong.acquire()
                with kunci:
                    buf[pt] = i
                    pt = (pt + 1) % BESAR
                    ditulis += 1
                kirim.release()
            else:
                s = pt
                pt = (pt + 1) % BESAR
                buf[s] = i
                ditulis += 1

    ter = set()

    def kons():
        nonlocal pb, dibaca, duplikat, hilang
        for _ in range(N):
            if pakai_mutex:
                kirim.acquire()
                with kunci:
                    d = buf[pb]
                    buf[pb] = None
                    pb = (pb + 1) % BESAR
                    dibaca += 1
                kosong.release()
            else:
                s = pb
                pb = (pb + 1) % BESAR
                d = buf[s]
                if d is None:
                    hilang += 1
                    continue
                dibaca += 1
            if d in ter:
                duplikat += 1
            else:
                ter.add(d)

    a = threading.Thread(target=prod, name="produsen")
    b = threading.Thread(target=kons, name="konsumen")
    a.start()
    b.start()
    a.join()
    b.join()
    return {"ditulis": ditulis, "dibaca": dibaca, "hilang": hilang,
            "duplikat": duplikat, "unik": len(ter)}


if __name__ == "__main__":
    ulang = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    hasil = {"tanpa_mutex": [], "dengan_mutex": []}
    for _ in range(ulang):
        hasil["tanpa_mutex"].append(jalankan(False))
        hasil["dengan_mutex"].append(jalankan(True))

    for k, v in hasil.items():
        print(f"=== {k} ===")
        for h in v:
            print(json.dumps(h))
        unik_rata = sum(x["unik"] for x in v) / len(v)
        print(f"rata-rata unik terkirim: {unik_rata:.1f} dari {N} "
              f"({unik_rata / N * 100:.1f}%)")

    os.makedirs("results", exist_ok=True)
    with open("results/uji-tanpa-jeda.json", "w", encoding="utf-8") as f:
        json.dump({"target": N, "ulang": ulang, "hasil": hasil}, f, indent=2)
    print("tersimpan: results/uji-tanpa-jeda.json")
