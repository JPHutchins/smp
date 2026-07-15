"""Measure the cold import time of ``from smp import image_management``.

Each sample is a fresh interpreter so nothing is cached in ``sys.modules``.
This is the headline metric for https://github.com/JPHutchins/smp/issues/26.
"""

from __future__ import annotations

import statistics
import subprocess
import sys
import time


def _one(cmd: list[str]) -> float:
    start = time.perf_counter()
    subprocess.run(cmd, capture_output=True, check=True)
    return (time.perf_counter() - start) * 1000.0


def sample(runs: int) -> list[float]:
    cmd = [sys.executable, "-c", "from smp import image_management"]
    subprocess.run(cmd, capture_output=True, check=True)  # warm bytecode cache
    return [_one(cmd) for _ in range(runs)]


def main() -> None:
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    ms = sample(runs)
    print(
        f"cold `from smp import image_management` over {runs} runs: "
        f"mean={statistics.mean(ms):.1f}ms  min={min(ms):.1f}ms  "
        f"median={statistics.median(ms):.1f}ms  stdev={statistics.pstdev(ms):.1f}ms"
    )


if __name__ == "__main__":
    main()
