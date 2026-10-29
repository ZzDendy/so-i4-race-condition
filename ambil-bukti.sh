#!/usr/bin/env bash
# Bukti terminal asli untuk laporan I-4: race condition dan perbaikannya.
set -u

DIR=${1:?butuh folder kerja}
OUT=${2:?butuh folder keluaran}
FIFO=/tmp/shotest/i4.fifo
mkdir -p "$OUT"
rm -f "$FIFO"; mkfifo "$FIFO"

cd "$DIR" || exit 1

io.elementary.terminal -n -w "$DIR" -x "bash --noprofile --rcfile $HOME/.bashrc -i < $FIFO" \
  > /dev/null 2>&1 &
TERM_PID=$!
sleep 4

exec 3>"$FIFO"

tangkap() {
  sleep 1.0
  gdbus call --session --dest org.gnome.Shell.Screenshot \
    --object-path /org/gnome/Shell/Screenshot \
    --method org.gnome.Shell.Screenshot.ScreenshotWindow \
    true false false "$OUT/ss-$1.png" > /dev/null 2>&1
  echo "  -> ss-$1.png"
}

ketik() { printf '%s\n' "$1" >&3; }

ketik 'clear'
sleep 1
tangkap "01-prompt"

ketik 'grep -n "critical section" -A3 -B3 race_tanpa_mutex.py | head -14'
tangkap "02-critical-section"

ketik 'python3 race_tanpa_mutex.py --ulang 5'
sleep 4
tangkap "03-tanpa-mutex"

ketik 'python3 race_dengan_mutex.py --ulang 5'
sleep 4
tangkap "04-dengan-mutex"

ketik 'python3 uji_tanpa_jeda.py 3'
sleep 6
tangkap "05-tanpa-jeda"

ketik 'grep -n "kunci\|slot_kosong\|slot_terisi" race_dengan_mutex.py | head -8'
tangkap "06-mutex-semafor"

exec 3>&-
sleep 1
kill "$TERM_PID" 2>/dev/null
rm -f "$FIFO"
echo "selesai: $(ls -1 "$OUT"/ss-*.png | wc -l) tangkapan layar"
