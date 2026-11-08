#!/usr/bin/env python3
"""Generates the test crates used to measure the long-line cost in rustc.

Usage: python3 make_repro.py <out dir>

All data is synthetic (random bytes); no third-party files are needed.
Files written:
  data/fNNNN.bin            1,511 binary files, 4.2 MB in total
  short_lines_rel.rs        1,511 relative include_bytes! calls, one per line
  long_line_rel.rs          the same calls, all on one 2.4 MB line
  long_line_abs.rs          the same, absolute paths (the slow path is not taken)
  panics_short.rs           10,000 panic locations (index + unwrap), one function per line
  panics_long.rs            the same, all on one long line
Each .rs file starts with about 2.4 MB of other code, so the calls sit far into the line.
"""
import os
import random
import sys

N = 1511
out = os.path.abspath(sys.argv[1])
os.makedirs(os.path.join(out, "data"), exist_ok=True)
rng = random.Random(0)
for i in range(N):
    size = 200 + rng.randrange(5400)          # about 4.2 MB in total
    with open(os.path.join(out, "data", f"f{i:04d}.bin"), "wb") as f:
        f.write(rng.randbytes(size))

pad = "pub const PAD: &[u32] = &[" + ",".join(str(i % 1000) for i in range(600_000)) + "];"
data = os.path.join(out, "data")


def arms(absolute):
    path = (lambda i: f"{data}/f{i:04d}.bin") if absolute else (lambda i: f"data/f{i:04d}.bin")
    return [f'"k{i}" => Some(include_bytes!("{path(i)}")),' for i in range(N)]


def get_fn(arm_list, sep):
    return sep.join(["pub fn get(k: &str) -> Option<&'static [u8]> { match k {", *arm_list, "_ => None, } }"])


def write(name, text):
    with open(os.path.join(out, name), "w") as f:
        f.write(text)


write("short_lines_rel.rs", pad + "\n" + get_fn(arms(False), "\n") + "\n")
write("long_line_rel.rs", pad + " " + get_fn(arms(False), " ") + "\n")
write("long_line_abs.rs", pad + " " + get_fn(arms(True), " ") + "\n")
fns = [f"pub fn f{i}(v: &[u8], o: Option<u8>) -> u8 {{ v[{i % 7}] + o.unwrap() }}" for i in range(5000)]
write("panics_short.rs", pad + "\n" + "\n".join(fns) + "\n")
write("panics_long.rs", pad + " " + " ".join(fns) + "\n")
print(f"wrote test crates to {out}")
