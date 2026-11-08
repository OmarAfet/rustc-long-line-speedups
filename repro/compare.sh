#!/usr/bin/env bash
# Compares two rustc toolchains on the test crates: wall time (3 runs each) and byte-identical
# output. Usage: ./compare.sh <toolchain A> <toolchain B> [crate dir]
# Example: rustup toolchain link before <path to stage1>; rustup toolchain link after <path>; ./compare.sh before after
set -euo pipefail
A="$1"; B="$2"; D="${3:-repro-out}"
[ -d "$D" ] || python3 "$(dirname "$0")/make_repro.py" "$D"
cd "$D"
for f in short_lines_rel long_line_rel long_line_abs panics_short panics_long; do
  for t in "$A" "$B"; do
    mkdir -p "out-$t"
    for k in 1 2 3; do
      s=$(python3 -c 'import time;print(time.time())')
      rustc "+$t" --edition 2024 --crate-type lib --emit=obj -C opt-level=0 -C codegen-units=1 -o "out-$t/$f.o" "$f.rs"
      e=$(python3 -c 'import time;print(time.time())')
      echo "$f $t run$k $(python3 -c "print(round($e-$s,2))") s"
    done
  done
  if cmp -s "out-$A/$f.o" "out-$B/$f.o"; then echo "$f output: identical"; else echo "$f output: DIFFERENT"; fi
done
