"""Grafik untuk laporan I-4: kehilangan data dan duplikasi sebelum vs sesudah."""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

FONT = "DejaVu Sans"
OUT = "results"
BIRU, ORANYE, HIJAU, MERAH = "#3B5B8C", "#B7791F", "#2F6B3C", "#A03B2C"


def baca(nama):
    with open(f"results/{nama}.json", encoding="utf-8") as f:
        return json.load(f)


def grafik_unik(tanpa, dengan, uji, path):
    """Persentase data unik yang benar-benar sampai ke pengirim."""
    target = tanpa["target"]

    def persen(daftar):
        return [h["unik"] / target * 100 for h in daftar]

    fig, ax = plt.subplots(figsize=(7.4, 3.3))
    kiri = persen(tanpa["hasil"])
    kanan = persen(dengan["hasil"])
    x1 = list(range(len(kiri)))
    x2 = list(range(len(kanan), len(kiri) + len(kanan)))
    ax.set_xticks(x1 + x2)
    ax.set_xticklabels([str(i + 1) for i in range(len(kiri) + len(kanan))])

    ax.bar(x1, kiri, color=MERAH, edgecolor="white", width=0.7,
           label="tanpa mutex")
    ax.bar(x2, kanan, color=HIJAU, edgecolor="white", width=0.7,
           label="dengan mutex")
    ax.axhline(100, color="#888888", linewidth=0.8, linestyle="--")
    ax.text(len(kiri) / 2, 101, "target 100%", ha="center", fontsize=7,
            fontfamily=FONT, color="#666666")

    ax.set_ylim(0, 112)
    ax.set_ylabel("Data unik terkirim (%)", fontfamily=FONT, fontsize=8.5)
    ax.set_xlabel("Percobaan ke-", fontfamily=FONT, fontsize=8.5)
    ax.tick_params(labelsize=7.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("Data unik yang sampai ke konsumen, sebelum dan sesudah perbaikan",
                 fontsize=9.6, fontfamily=FONT, fontweight="bold", pad=8)
    fig.tight_layout()
    fig.savefig(path, dpi=220, facecolor="white")
    plt.close(fig)


def grafik_galat(tanpa, path):
    """Jumlah data hilang dan duplikat per percobaan."""
    fig, ax = plt.subplots(figsize=(7.4, 3.1))
    x = range(len(tanpa["hasil"]))
    hilang = [h["hilang"] for h in tanpa["hasil"]]
    duplikat = [h["duplikat"] for h in tanpa["hasil"]]

    ax.bar([i - 0.19 for i in x], duplikat, width=0.36, color=ORANYE,
           edgecolor="white", label="duplikat")
    ax.bar([i + 0.19 for i in x], hilang, width=0.36, color=BIRU,
           edgecolor="white", label="hilang")
    for i, (d, h) in enumerate(zip(duplikat, hilang)):
        ax.annotate(str(d), (i - 0.19, d), textcoords="offset points",
                    xytext=(0, 2), ha="center", fontsize=6.6, fontfamily=FONT)
        ax.annotate(str(h), (i + 0.19, h), textcoords="offset points",
                    xytext=(0, 2), ha="center", fontsize=6.6, fontfamily=FONT)

    ax.set_xticks(list(x))
    ax.set_xticklabels([str(h["run"]) for h in tanpa["hasil"]])
    ax.set_xlabel("Percobaan ke-", fontfamily=FONT, fontsize=8.5)
    ax.set_ylabel("Jumlah rekaman", fontfamily=FONT, fontsize=8.5)
    ax.tick_params(labelsize=7.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(duplikat) * 1.22)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Rekaman duplikat dan hilang pada versi tanpa mutex",
                 fontsize=9.6, fontfamily=FONT, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=220, facecolor="white")
    plt.close(fig)


def grafik_skala(uji, path):
    """Uji tanpa jeda: memperlihatkan race bukan efek sleep."""
    target = uji["target"]
    tanpa = [h["unik"] / target * 100 for h in uji["hasil"]["tanpa_mutex"]]
    dengan = [h["unik"] / target * 100 for h in uji["hasil"]["dengan_mutex"]]

    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    posisi = [0, 1]
    nilai = [sum(tanpa) / len(tanpa), sum(dengan) / len(dengan)]
    batang = ax.bar(posisi, nilai, color=[MERAH, HIJAU], width=0.5,
                    edgecolor="white")
    for b, v in zip(batang, nilai):
        ax.annotate(f"{v:.1f}%", (b.get_x() + b.get_width() / 2, v),
                    textcoords="offset points", xytext=(0, 4), ha="center",
                    fontsize=9, fontfamily=FONT, fontweight="bold")

    ax.set_xticks(posisi)
    ax.set_xticklabels(["tanpa mutex", "dengan mutex"], fontfamily=FONT,
                       fontsize=9)
    ax.set_ylim(0, 115)
    ax.set_ylabel("Data unik terkirim (%)", fontfamily=FONT, fontsize=8.5)
    ax.tick_params(labelsize=7.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_title(f"Uji tanpa jeda buatan ({uji['target']} rekaman per thread)",
                 fontsize=9.6, fontfamily=FONT, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=220, facecolor="white")
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    tanpa = baca("tanpa-mutex")
    dengan = baca("dengan-mutex")
    uji = baca("uji-tanpa-jeda")
    grafik_unik(tanpa, dengan, uji, f"{OUT}/gambar-perbandingan.png")
    grafik_galat(tanpa, f"{OUT}/gambar-kehilangan.png")
    grafik_skala(uji, f"{OUT}/gambar-tanpa-jeda.png")
    print("gambar:", [f for f in sorted(os.listdir(OUT)) if f.endswith(".png")])


if __name__ == "__main__":
    main()
