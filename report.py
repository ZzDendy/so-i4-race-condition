"""Merakit laporan I-4 dari template jurusan dan hasil uji race condition."""
import json
import os
import platform
import subprocess
import sys

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.shared import Cm, Pt

sys.path.insert(0, "../tools")
from docx_kit import (baca_berkas, bersihkan, bullet, caption, gambar, h1, h2,
                      header_dokumen, kode, nomor_halaman, par, sampul, tabel)

TEMPLATE = "../template/Template Laporan Tugas Individu.docx"
OUT = "results/Laporan_I-4_Race_Condition.docx"
NAMA = "Dendy Zainal Mutaqien"
NIM = "250660121068"
KELAS = "IF-3C"
KODE = "I-4"
BUKTI = "results/bukti"
REPO = "https://github.com/ZzDendy/so-i4-race-condition"


def baca(nama):
    with open(f"results/{nama}.json", encoding="utf-8") as f:
        return json.load(f)


def fakta_sistem():
    def jalankan(cmd):
        try:
            return subprocess.run(cmd, shell=True, capture_output=True,
                                  text=True).stdout.strip()
        except OSError:
            return ""

    with open("/etc/os-release", encoding="utf-8") as f:
        osr = {}
        for baris in f:
            if "=" in baris:
                k, v = baris.rstrip().split("=", 1)
                osr[k] = v.strip('"')
    return {
        "kernel": platform.release(),
        "distro": osr.get("PRETTY_NAME", "Linux"),
        "cpu": jalankan("lscpu | grep -m1 'Model name' | cut -d: -f2").strip(),
        "jumlah_cpu": os.cpu_count(),
        "python": platform.python_version(),
        "switch_interval": jalankan(
            "python3 -c 'import sys; print(sys.getswitchinterval())'"),
    }


def rata2(daftar, kunci):
    return sum(h[kunci] for h in daftar) / len(daftar)


def sampul_i4(d):
    sampul(
        d,
        "LAPORAN TUGAS INDIVIDU",
        "Analisis Race Condition dan Sinkronisasi\npada Buffer Data Sensor",
        [
            ("Kode dan judul tugas", "I-4 Analisis Race Condition dan Sinkronisasi"),
            ("Kelas / tema", f"{KELAS} — IoT dan Smart Farming"),
            ("Nama", NAMA),
            ("NIM", NIM),
            ("Nama host", "INFINIX-ElementaryOS"),
            ("Minggu / tanggal kumpul", "Minggu ke-6 / 5 November 2026"),
            ("Kepingan puzzle", "Kepingan #6 → Level 4 Puzzle UTS"),
            ("Dosen pengampu", "Muhammad Agreindra Helmiawan, S.Kom., M.T"),
        ],
        "I-4",
    )


def pendahuluan(d, k, tanpa, dengan):
    h1(d, "1. Pendahuluan")

    h2(d, "1.1 Latar belakang kasus")
    par(d, "Pada layanan sensor kebun pintar, data mengalir dari pembaca ke pengirim melalui "
           "sebuah buffer di memori. Pembaca menaruh data, pengirim mengambilnya. Keduanya "
           "berjalan sebagai thread dalam satu proses supaya pertukaran datanya murah — inilah "
           "yang sudah dibuktikan pada tugas I-3. Namun justru karena ruang alamatnya dipakai "
           "bersama, keduanya juga bisa saling menimpa.")
    par(d, f"Hasil pengujian memperlihatkannya dengan jelas. Dari {tanpa['target']} rekaman yang "
           f"ditulis, versi tanpa penjagaan hanya mengirim "
           f"{rata2(tanpa['hasil'], 'unik'):.0f} data unik — sekitar "
           f"{rata2(tanpa['hasil'], 'unik') / tanpa['target'] * 100:.1f} persen. Versi yang "
           f"memakai mutex dan semafor mengirim {rata2(dengan['hasil'], 'unik'):.0f} dari "
           f"{dengan['target']}, seluruhnya, pada setiap percobaan. Perbedaan itu bukan soal "
           f"keberuntungan; ia adalah akibat langsung dari tidak adanya penjagaan pada bagian "
           f"kode yang mengubah keadaan bersama.")
    par(d, "Laporan ini membedah di mana tepatnya bagian berbahaya itu, mengapa ia berbahaya, dan "
           "mengapa perbaikannya memerlukan dua alat sekaligus — mutex dan semafor — bukan salah "
           "satunya saja.")

    h2(d, "1.2 Tujuan tugas")
    par(d, "Capaian pembelajaran yang diukur adalah Sub-CPMK-6 (CPMK042, CPMK043, CPMK081, "
           "CPMK101, CPMK111). Tujuannya:")
    bullet(d, "membuat program producer-consumer pada buffer data sensor yang benar-benar "
              "memperlihatkan race condition, bukan hanya mengklaimnya;", "Pertama, ")
    bullet(d, "memperbaiki program itu dengan mutex dan semafor, lalu membuktikan perbaikannya "
              "lewat eksekusi berulang;", "Kedua, ")
    bullet(d, "membandingkan hasil sebelum dan sesudah perbaikan serta menjelaskan batas critical "
              "section-nya.", "Ketiga, ")

    h2(d, "1.3 Ruang lingkup")
    par(d, f"Program dijalankan dengan Python {k['python']} pada mesin {k['distro']} "
           f"{k['jumlah_cpu']} CPU logis. Buffer berukuran {tanpa['besar_buffer']} slot dan setiap "
           f"percobaan memindahkan {tanpa['target']} rekaman dari produsen ke konsumen. Setiap "
           f"konfigurasi dijalankan sepuluh kali.")
    par(d, "Yang tidak dikerjakan: pengujian pada memori bersama antarproses (shared memory), "
           "analisis race pada program berbahasa C tanpa pengelola memori otomatis, dan "
           "pengukuran overhead sinkronisasi dengan perf.")


def dasar_teori(d):
    h1(d, "2. Dasar Teori Singkat")
    par(d, "Race condition terjadi ketika hasil akhir program bergantung pada urutan waktu "
           "eksekusi antar thread, dan urutan itu tidak dijamin. Silberschatz dkk. (2018) "
           "menyebutnya sebagai keadaan ketika beberapa proses mengakses dan memanipulasi data "
           "bersama secara bersamaan, sehingga nilainya bergantung pada siapa yang selesai "
           "terakhir.")
    par(d, "Pada kasus buffer sensor, bahaya bukan pada penulisan satu slot, melainkan pada urutan "
           "langkah. Produsen menjalankan tiga langkah: membaca posisi tulis, menaikkan posisi "
           "tulis, lalu menaruh data pada slot yang tadi dibaca. Konsumen menjalankan tiga langkah "
           "serupa pada posisi baca. Kalau produsen sudah menaikkan posisi tulis tetapi belum "
           "menaruh data, konsumen bisa membaca slot itu dan menemukannya masih kosong. Kalau "
           "produsen berputar penuh satu lingkaran sebelum konsumen sempat membaca, data lama "
           "tertimpa data baru yang belum dibaca.")
    par(d, "Critical section adalah bagian kode yang mengakses keadaan bersama dan karena itu "
           "harus dijalankan oleh paling banyak satu thread pada satu waktu. Pada kasus ini "
           "critical section mencakup pembacaan indeks, perubahan indeks, dan penulisan slot "
           "buffer — ketiganya harus menjadi satu kesatuan. Kalau hanya indeks yang dijaga tetapi "
           "penulisan slot berada di luar, race tetap terjadi.")
    par(d, "Mutex (mutual exclusion) adalah kunci yang hanya boleh dipegang satu thread. Di "
           "Python, threading.Lock menyediakan acquire dan release, dan bentuk with kunci "
           "menjamin pelepasan kunci meski terjadi kesalahan. Semafor adalah penghitung yang "
           "menahan thread ketika nilainya nol. Dengan dua semafor — satu menghitung slot kosong, "
           "satu menghitung slot terisi — produsen dan konsumen tidak perlu lagi memeriksa berulang "
           "apakah buffer penuh atau kosong.")
    par(d, "Keduanya menjawab persoalan berbeda. Mutex menjawab \"siapa yang boleh menyentuh "
           "keadaan bersama sekarang\". Semafor menjawab \"apakah pekerjaannya bisa dilakukan "
           "sekarang\". Mutex tanpa semafor tetap bisa menimpa data yang belum dibaca; semafor "
           "tanpa mutex tetap bisa merusak indeks. Karena itu perbaikan yang benar memakai "
           "keduanya.")


def lingkungan(d, k):
    h1(d, "3. Lingkungan Praktik")
    tabel(d, ["Komponen", "Keterangan"], [
        ("Laptop (host)", f"{k['distro']}, {k['cpu']}, kernel {k['kernel']}"),
        ("Hypervisor", "Tidak dipakai — pengujian langsung pada host"),
        ("VM / host", f"INFINIX-ElementaryOS, {k['jumlah_cpu']} CPU logis"),
        ("Perangkat lain", "Tidak berlaku — data sensor dibangkitkan secara sintetis"),
        ("Bahasa dan alat", f"Python {k['python']}; modul threading (Lock, Semaphore); "
                            "matplotlib dan python-docx untuk laporan"),
        ("Jatah giliran thread", f"sys.getswitchinterval() = {k['switch_interval']} detik "
                                 "pada uji tanpa jeda"),
        ("Percobaan", "10 kali per konfigurasi, masing-masing 2000 rekaman"),
    ], lebar=[4.2, 11.0])

    par(d, "Satu catatan penting sebelum membaca hasilnya. Python memakai global interpreter lock "
           "(GIL), yang membuat hanya satu thread menjalankan bytecode pada satu waktu. GIL "
           "mengurangi race pada operasi tunggal, tetapi tidak menghilangkannya: rangkaian "
           "beberapa operasi tetap bisa disela karena Python memindahkan giliran antar thread "
           "pada interval tertentu. Justru itulah yang dimanfaatkan uji pada Bagian 4.5, dengan "
           "mempersempit interval giliran supaya perpindahan terjadi sesering mungkin.")


def langkah(d, k, tanpa, dengan, uji):
    h1(d, "4. Langkah Pengerjaan")
    par(d, "Pengujian dibagi menjadi lima langkah: menulis versi tanpa penjagaan, mengamati "
           "kegagalannya, menulis versi bermutex dan bersemafor, membandingkan hasil, lalu "
           "membuktikan bahwa race bukan efek dari jeda buatan.")

    h2(d, "4.1 Langkah 1: Menulis versi tanpa penjagaan")
    par(d, "Versi pertama sengaja ditulis naif. Produsen membaca indeks, menaikkannya, lalu "
           "menaruh data tanpa kunci apa pun. Jeda kecil disisipkan di antara langkah-langkah itu "
           "supaya celah waktunya cukup lebar untuk diamati. Jeda itu tidak menciptakan race; ia "
           "hanya membuat race lebih mudah tertangkap.")
    kode(d, baca_berkas("race_tanpa_mutex.py"))
    gambar(d, f"{BUKTI}/rapi-02-critical-section.png", 15.0,
           "Gambar 4.1 Bagian critical section pada versi tanpa penjagaan")

    h2(d, "4.2 Langkah 2: Membuktikan kegagalannya lewat eksekusi berulang")
    par(d, "Satu kali eksekusi tidak membuktikan apa pun, karena hasilnya bisa kebetulan benar. "
           "Program dijalankan sepuluh kali berturut-turut, dan setiap percobaan dicatat.")
    kode(d, "$ python3 race_tanpa_mutex.py --ulang 10\n"
            + "\n".join(
                f'{{"run": {h["run"]}, "ditulis": {h["ditulis"]}, "dibaca": {h["dibaca"]}, '
                f'"hilang": {h["hilang"]}, "duplikat": {h["duplikat"]}, '
                f'"unik": {h["unik"]}}}'
                for h in tanpa["hasil"][:5])
            + "\n...\n"
            f"run bermasalah: {sum(1 for h in tanpa['hasil'] if h['hilang'] or h['duplikat'])} "
            f"dari {len(tanpa['hasil'])}")
    gambar(d, f"{BUKTI}/rapi-03-tanpa-mutex.png", 15.0,
           "Gambar 4.2 Sepuluh percobaan versi tanpa mutex: seluruhnya kehilangan atau "
           "menduplikasi data")

    h2(d, "4.3 Langkah 3: Menulis versi bermutex dan bersemafor")
    par(d, "Versi perbaikan memakai tiga alat. Satu Lock menjaga indeks dan slot buffer. Satu "
           "semaphore menghitung slot kosong, sehingga produsen menunggu ketika buffer penuh. "
           "Satu semaphore lagi menghitung slot terisi, sehingga konsumen menunggu ketika buffer "
           "kosong. Kedua semafor itu menggantikan pemeriksaan berulang yang boros prosesor.")
    kode(d, baca_berkas("race_dengan_mutex.py"))
    gambar(d, f"{BUKTI}/rapi-06-mutex-semafor.png", 15.0,
           "Gambar 4.3 Pemakaian Lock dan dua Semaphore pada versi perbaikan")

    h2(d, "4.4 Langkah 4: Membandingkan hasil")
    par(d, "Versi perbaikan dijalankan dengan jumlah percobaan dan ukuran data yang sama persis, "
           "supaya perbandingannya adil.")
    kode(d, "$ python3 race_dengan_mutex.py --ulang 10\n"
            + "\n".join(
                f'{{"run": {h["run"]}, "ditulis": {h["ditulis"]}, "dibaca": {h["dibaca"]}, '
                f'"hilang": {h["hilang"]}, "duplikat": {h["duplikat"]}, '
                f'"unik": {h["unik"]}}}'
                for h in dengan["hasil"][:5])
            + "\n...\n"
            f"run bermasalah: {sum(1 for h in dengan['hasil'] if h['hilang'] or h['duplikat'])} "
            f"dari {len(dengan['hasil'])}")
    gambar(d, f"{BUKTI}/rapi-04-dengan-mutex.png", 15.0,
           "Gambar 4.4 Sepuluh percobaan versi bermutex: tidak ada data hilang maupun duplikat")

    h2(d, "4.5 Langkah 5: Membuktikan race bukan efek jeda buatan")
    par(d, "Keberatan yang wajar: bukankah race hanya muncul karena ada time.sleep di dalam "
           "critical section? Untuk menjawabnya, dibuat uji ketiga tanpa jeda sama sekali. Yang "
           "dilakukan justru mempersempit jatah giliran antar thread dengan "
           "sys.setswitchinterval(0.000001), sehingga perpindahan terjadi sesering mungkin. "
           "Jumlah rekaman dinaikkan menjadi 20000 supaya peluang race makin besar.")
    kode(d, baca_berkas("uji_tanpa_jeda.py"))
    kode(d, "$ python3 uji_tanpa_jeda.py 5\n"
            "=== tanpa_mutex ===\n"
            + "\n".join(
                f'{{"ditulis": {h["ditulis"]}, "dibaca": {h["dibaca"]}, "hilang": {h["hilang"]}, '
                f'"duplikat": {h["duplikat"]}, "unik": {h["unik"]}}}'
                for h in uji["hasil"]["tanpa_mutex"])
            + f"\nrata-rata unik terkirim: "
            f"{rata2(uji['hasil']['tanpa_mutex'], 'unik'):.1f} dari {uji['target']} "
            f"({rata2(uji['hasil']['tanpa_mutex'], 'unik') / uji['target'] * 100:.1f}%)\n"
            "=== dengan_mutex ===\n"
            + "\n".join(
                f'{{"ditulis": {h["ditulis"]}, "dibaca": {h["dibaca"]}, "hilang": {h["hilang"]}, '
                f'"duplikat": {h["duplikat"]}, "unik": {h["unik"]}}}'
                for h in uji["hasil"]["dengan_mutex"][:3])
            + f"\nrata-rata unik terkirim: "
            f"{rata2(uji['hasil']['dengan_mutex'], 'unik'):.1f} dari {uji['target']} "
            f"({rata2(uji['hasil']['dengan_mutex'], 'unik') / uji['target'] * 100:.1f}%)")
    gambar(d, f"{BUKTI}/rapi-05-tanpa-jeda.png", 15.0,
           "Gambar 4.5 Uji tanpa jeda: race tetap terjadi, bahkan lebih parah")


def hasil(d, k, tanpa, dengan, uji):
    h1(d, "5. Hasil dan Analisis")

    h2(d, "5.1 Hasil")
    par(d, "Tabel 5.1 membandingkan kedua versi. Rata-rata dihitung dari sepuluh percobaan "
           "masing-masing 2000 rekaman.")
    t_unik = rata2(tanpa["hasil"], "unik")
    d_unik = rata2(dengan["hasil"], "unik")
    tabel(d, ["Ukuran", "Tanpa mutex", "Dengan mutex"], [
        ("Jumlah percobaan", len(tanpa["hasil"]), len(dengan["hasil"])),
        ("Rekaman ditulis (target)", tanpa["target"], dengan["target"]),
        ("Rata-rata data unik terkirim", f"{t_unik:.0f}", f"{d_unik:.0f}"),
        ("Persentase data unik", f"{t_unik / tanpa['target'] * 100:.1f}%",
         f"{d_unik / dengan['target'] * 100:.1f}%"),
        ("Rata-rata rekaman duplikat", f"{rata2(tanpa['hasil'], 'duplikat'):.1f}",
         f"{rata2(dengan['hasil'], 'duplikat'):.1f}"),
        ("Rata-rata rekaman hilang", f"{rata2(tanpa['hasil'], 'hilang'):.1f}",
         f"{rata2(dengan['hasil'], 'hilang'):.1f}"),
        ("Percobaan bermasalah",
         sum(1 for h in tanpa["hasil"] if h["hilang"] or h["duplikat"]),
         sum(1 for h in dengan["hasil"] if h["hilang"] or h["duplikat"])),
    ], lebar=[6.4, 4.4, 4.4])
    caption(d, "Tabel 5.1 Perbandingan versi tanpa penjagaan dan versi bermutex")

    par(d, "Tabel 5.2 memuat hasil uji tanpa jeda buatan, yang membuktikan race bukan efek "
           "time.sleep semata.")
    tabel(d, ["Ukuran", "Tanpa mutex", "Dengan mutex"], [
        ("Rekaman per thread", uji["target"], uji["target"]),
        ("Jumlah percobaan", len(uji["hasil"]["tanpa_mutex"]),
         len(uji["hasil"]["dengan_mutex"])),
        ("Rata-rata data unik", f"{rata2(uji['hasil']['tanpa_mutex'], 'unik'):.1f}",
         f"{rata2(uji['hasil']['dengan_mutex'], 'unik'):.1f}"),
        ("Persentase data unik",
         f"{rata2(uji['hasil']['tanpa_mutex'], 'unik') / uji['target'] * 100:.1f}%",
         f"{rata2(uji['hasil']['dengan_mutex'], 'unik') / uji['target'] * 100:.1f}%"),
        ("Rata-rata duplikat", f"{rata2(uji['hasil']['tanpa_mutex'], 'duplikat'):.1f}",
         f"{rata2(uji['hasil']['dengan_mutex'], 'duplikat'):.1f}"),
    ], lebar=[6.4, 4.4, 4.4])
    caption(d, "Tabel 5.2 Uji tanpa jeda buatan dengan jatah giliran 1 mikrodetik")

    par(d, "Gambar 5.1 memperlihatkan persentase data unik pada masing-masing percobaan.")
    gambar(d, "results/gambar-perbandingan.png", 15.0,
           "Gambar 5.1 Data unik yang sampai ke konsumen, sebelum dan sesudah perbaikan")

    par(d, "Gambar 5.2 memperlihatkan bentuk kegagalannya: duplikat jauh lebih banyak daripada "
           "data hilang.")
    gambar(d, "results/gambar-kehilangan.png", 14.5,
           "Gambar 5.2 Rekaman duplikat dan hilang pada versi tanpa mutex")

    par(d, "Gambar 5.3 menampilkan hasil uji tanpa jeda buatan.")
    gambar(d, "results/gambar-tanpa-jeda.png", 12.5,
           "Gambar 5.3 Uji tanpa jeda: bukti race bukan akibat time.sleep")

    h2(d, "5.2 Analisis")
    t_dup = rata2(tanpa["hasil"], "duplikat")
    t_hil = rata2(tanpa["hasil"], "hilang")
    par(d, "Poin (1) deskripsi tugas — di mana race condition-nya. Penyebab utamanya bukan "
           "penulisan ke buffer, melainkan pemisahan antara perubahan indeks dan penempatan data. "
           "Produsen menjalankan tiga langkah berurutan: membaca posisi_tulis, menaikkan "
           "posisi_tulis, lalu menaruh data pada slot hasil bacaan tadi. Bila thread konsumen "
           "berjalan di antara langkah kedua dan ketiga, ia akan menaikkan posisi_baca lebih cepat "
           "daripada produsen menaruh data. Slot yang dibaca konsumen masih berisi nilai lama atau "
           "kosong.")
    par(d, f"Hasil pengujian cocok dengan penjelasan itu. Rata-rata {t_dup:.0f} rekaman duplikat "
           f"tetapi hanya {t_hil:.1f} rekaman hilang. Duplikat jauh lebih dominan karena konsumen "
           f"bergerak lebih cepat daripada produsen: setiap kali produsen tertinggal satu langkah, "
           f"konsumen sudah memutar indeks dan membaca slot yang sama lagi. Slot berukuran "
           f"{tanpa['besar_buffer']} membuat konsumen bisa berputar penuh sebelum produsen sempat "
           f"mengisi. Inilah sebabnya angka duplikat mencapai belasan persen sementara data hilang "
           f"hanya beberapa rekaman.")
    par(d, "Ada satu hal yang perlu dinyatakan jujur di sini. Pada Python, operasi tunggal seperti "
           "menaikkan variabel bilangan bulat tidak dapat disela di tengah jalan karena GIL. Race "
           "yang terjadi di sini bukan pada satu operasi, melainkan pada rangkaian tiga operasi "
           "yang membentuk satu kesatuan logis. Kalau program ini ditulis dalam C, kerusakannya "
           "akan lebih parah lagi: kenaikan variabel pun bisa terpotong.")
    par(d, "Poin (2) deskripsi tugas — perbaikannya. Critical section pada versi perbaikan mencakup "
           "pembacaan indeks, perubahan indeks, dan penulisan atau pengosongan slot — ketiganya di "
           "dalam satu blok with kunci. Yang berada di luar kunci adalah pelepasan semafor dan "
           "pemrosesan data yang sudah diambil, karena keduanya tidak menyentuh keadaan bersama. "
           "Pembagian ini disengaja: memasukkan pekerjaan yang tidak perlu ke dalam kunci hanya "
           "memperpanjang waktu tunggu thread lain tanpa manfaat.")
    par(d, "Mengapa perlu semafor juga, bukan mutex saja? Mutex menjaga kerapian indeks, tetapi "
           "tidak mencegah produsen menimpa data yang belum dibaca. Tanpa semafor slot kosong, "
           "produsen akan terus menulis meski buffer penuh. Sebaliknya, semafor tanpa mutex "
           "membuat jumlah slot terjaga tetapi isinya bisa tertukar. Pada uji di Tabel 5.1, "
           "kombinasi keduanya menghasilkan nol kehilangan dan nol duplikasi pada sepuluh "
           "percobaan, bukan sebagian.")
    par(d, "Poin (3) deskripsi tugas — perbandingan dan pembuktian. Uji tanpa jeda pada Tabel 5.2 "
           f"menjawab keberatan yang paling wajar: versi tanpa mutex hanya mengirim "
           f"{rata2(uji['hasil']['tanpa_mutex'], 'unik'):.0f} data unik dari {uji['target']} — "
           f"sekitar {rata2(uji['hasil']['tanpa_mutex'], 'unik') / uji['target'] * 100:.1f} "
           f"persen — padahal tidak ada time.sleep sama sekali di dalam critical section. Yang "
           f"membuatnya lebih parah justru jatah giliran yang dipersempit: dengan perpindahan "
           f"thread yang jauh lebih sering, peluang menyela rangkaian tiga operasi itu meningkat. "
           f"Ini membuktikan race adalah sifat dari kode yang tidak dijaga, bukan efek dari jeda "
           f"yang sengaja dipasang.")
    par(d, "Perlu dicatat pula bahwa perbaikan ini tidak gratis. Setiap acquire dan release "
           "menambah kerja, dan semafor yang membuat konsumen menunggu berarti produsen sesekali "
           "harus menunggu slot kosong. Pada uji ini biaya itu tidak sampai menurunkan jumlah data "
           "yang dipindahkan, karena buffer delapan slot cukup untuk menyerap selisih kecepatan. "
           "Pada buffer berukuran satu, biayanya akan terasa dan throughput turun. Pilihan ukuran "
           "buffer karena itu juga bagian dari desain, bukan angka sembarang.")

    h2(d, "5.3 Catatan keterbatasan")
    par(d, "Pengujian dilakukan pada Python, yang memiliki GIL. Pada bahasa yang tidak memiliki "
           "GIL, race bisa muncul bahkan pada operasi tunggal, sehingga hasil ini berlaku sebagai "
           "batas bawah, bukan gambaran terburuk. Selain itu, mesin uji memiliki "
           f"{k['jumlah_cpu']} CPU logis; pada mesin satu inti, pola penyelaan bisa berbeda. "
           "Jumlah percobaan sepuluh kali cukup untuk menunjukkan perbedaan yang mencolok, tetapi "
           "tidak cukup untuk menyimpulkan probabilitas kegagalan secara statistik.")


def kesimpulan(d, k, tanpa, dengan, uji):
    h1(d, "6. Kesimpulan")
    t_unik = rata2(tanpa["hasil"], "unik")
    d_unik = rata2(dengan["hasil"], "unik")
    par(d, f"Program producer-consumer tanpa penjagaan kehilangan data pada setiap percobaan: "
           f"hanya {t_unik:.0f} dari {tanpa['target']} rekaman yang sampai utuh, dengan duplikasi "
           f"sebagai bentuk kegagalan yang dominan. Critical section-nya bukan penulisan slot, "
           f"melainkan rangkaian indeks-dan-slot yang harus menjadi satu kesatuan. Perbaikan "
           f"dengan Lock dan dua Semaphore menaikkan angka itu menjadi {d_unik:.0f} dari "
           f"{dengan['target']} pada seluruh sepuluh percobaan, tanpa satu pun kegagalan. Uji "
           f"tanpa jeda buatan menegaskan bahwa race bukan akibat time.sleep: dengan jatah giliran "
           f"dipersempit, hanya {rata2(uji['hasil']['tanpa_mutex'], 'unik') / uji['target'] * 100:.1f} "
           f"persen data yang sampai. Dengan demikian mutex menjaga keutuhan keadaan bersama, "
           f"sedangkan semafor menjaga ketersediaan pekerjaan — keduanya diperlukan, dan masing-masing "
           f"menjawab persoalan yang berbeda.")


def kepingan(d):
    h1(d, "7. Kepingan Puzzle")
    tabel(d, ["Keterangan", "Isi"], [
        ("Nomor kepingan", "#6"),
        ("Isi kepingan", "Kode versi tanpa penjagaan dan versi bermutex/semafor, hasil sepuluh "
                         "percobaan masing-masing, uji tanpa jeda, serta analisis critical "
                         "section"),
        ("Lokasi di portofolio", REPO),
        ("Dipakai untuk", "Level 4 Puzzle UTS — puncak rantai kepingan #1 sampai #5. Buffer "
                          "bersama yang diperebutkan di sini adalah buffer logger dari kepingan "
                          "#4, dijalankan sebagai thread sesuai kepingan #3, dan dijadwalkan "
                          "oleh penjadwal yang dibahas pada kepingan #5"),
    ], lebar=[4.2, 11.0])


def pustaka(d):
    h1(d, "Daftar Pustaka")
    for teks in [
        "Kerrisk, M. (2010). The Linux programming interface. No Starch Press.",
        "Silberschatz, A., Galvin, P. B., & Gagne, G. (2018). Operating system concepts "
        "(10th ed.). Wiley.",
        "Tanenbaum, A. S., & Bos, H. (2015). Modern operating systems (4th ed.). Pearson.",
        "Python Software Foundation. (2024). threading — Thread-based parallelism. "
        "https://docs.python.org/3/library/threading.html",
    ]:
        p = d.add_paragraph(style="Normal")
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.first_line_indent = Cm(-1.0)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.add_run(teks)


def lampiran(d):
    d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    h1(d, "Lampiran A. Kode Program dan Log")
    par(d, "Empat berkas di bawah ini menghasilkan seluruh angka pada laporan dan dapat dijalankan "
           "ulang pada mesin yang sama.")
    for nama in ("race_tanpa_mutex.py", "race_dengan_mutex.py", "uji_tanpa_jeda.py",
                 "figures.py", "ambil-bukti.sh"):
        p = d.add_paragraph(style="Normal")
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(f"A.{nama}")
        r.bold = True
        r.font.size = Pt(9.5)
        kode(d, baca_berkas(nama), ukuran=7)

    h1(d, "Lampiran B. Pernyataan Penggunaan AI Generatif")
    par(d, "☐  Saya tidak menggunakan AI generatif dalam tugas ini.")
    par(d, "☒  Menggunakan AI generatif dengan rincian berikut:")
    tabel(d, ["Alat", "Tujuan penggunaan", "Bagian yang dibantu", "Cara memverifikasi"], [
        ("Claude (Anthropic)", "Menyusun skrip pengujian dan merapikan kalimat laporan",
         "Bagian 4 (kode), Bagian 5.2",
         "Seluruh angka berasal dari keluaran program pada tangkapan layar; kedua versi "
         "dijalankan ulang sepuluh kali dan hasilnya dicocokkan dengan Tabel 5.1"),
    ], lebar=[3.0, 4.4, 4.0, 4.4], ukuran=8.5)

    h1(d, "Lampiran C. Daftar Periksa Sebelum Mengumpulkan")
    for teks, sudah in [
        ("Semua teks petunjuk abu-abu dan kotak petunjuk sudah dihapus.", True),
        ("Identitas, kode tugas, dan nama host pada sampul sudah benar.", True),
        ("Setiap poin deskripsi tugas sudah dijawab di bagian Analisis.", True),
        ("Setiap tangkapan layar menampilkan prompt dan memiliki nomor serta keterangan.", True),
        ("Kepingan puzzle sudah disimpan di portofolio dan tautannya dicantumkan.", True),
        ("Pernyataan penggunaan AI generatif sudah diisi.", True),
        ("Berkas disimpan sebagai PDF dengan nama C_I-4_<NIM>_<Nama>.pdf.", True),
    ]:
        p = d.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(3)
        p.add_run(f"{'☒' if sudah else '☐'}  {teks}")

    par(d, "")
    h2(d, "Swa-nilai berdasarkan kriteria lembar tugas")
    tabel(d, ["Kriteria (dari lembar tugas)", "Bobot", "Sudah terpenuhi? Di bagian mana"],
          [("Ketepatan konsep", "35%",
            "Ya — critical section, mutex, dan semafor dijelaskan dengan perannya masing-masing"),
           ("Kedalaman analisis", "30%",
            "Ya — mengapa duplikat mendominasi, mengapa perlu dua alat, dan biaya perbaikan"),
           ("Bukti praktik/perhitungan", "25%",
            "Ya — 6 tangkapan layar asli, 10 percobaan per versi, uji tanpa jeda"),
           ("Orisinalitas dan kerapian", "10%",
            "Ya — grafik dari data uji, daftar pustaka gaya APA")],
          lebar=[5.2, 2.0, 8.0])


def main():
    d = docx.Document(TEMPLATE)
    bersihkan(d)

    k = fakta_sistem()
    tanpa = baca("tanpa-mutex")
    dengan = baca("dengan-mutex")
    uji = baca("uji-tanpa-jeda")

    sampul_i4(d)
    pendahuluan(d, k, tanpa, dengan)
    dasar_teori(d)
    lingkungan(d, k)
    langkah(d, k, tanpa, dengan, uji)
    hasil(d, k, tanpa, dengan, uji)
    kesimpulan(d, k, tanpa, dengan, uji)
    kepingan(d)
    pustaka(d)
    lampiran(d)

    header_dokumen(d, "Laporan Tugas Individu Sistem Operasi · ", f"{KELAS} · {KODE}")
    nomor_halaman(d)

    d.core_properties.title = "I-4 Analisis Race Condition dan Sinkronisasi"
    d.core_properties.author = NAMA
    d.core_properties.subject = "Sistem Operasi (USA-WP2260110), IF-3C"
    d.core_properties.last_modified_by = NAMA

    os.makedirs("results", exist_ok=True)
    d.save(OUT)
    print("tersimpan:", OUT)


if __name__ == "__main__":
    main()
