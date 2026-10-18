#!/usr/bin/env python3
"""Inference-latency benchmark -- provenance for the cost figures in Table 7
and Section 4.6 ("RF 15.2 ms, GB 5.9 ms, LR 0.1 ms per 1,000 submissions,
single CPU core, about $0.0002 per 1,000 at $0.04/vCPU-hour").

Why this script exists
----------------------
The manuscript prices supervised inference from a measurement. Round 9
rebuilt those figures after the earlier unsupported claims ("2 ms latency",
"$0.10/1k") were removed, but the measurement itself was never persisted: a
reader could not reproduce "15.2 ms" from the repository. This script fits
the three Table 3 models on the authoritative training split, then times
batch prediction of the 2,672-row test partition (scaled to per-1,000) with
all thread pools pinned to one core, and writes the result with the host
machine's CPU model so the number can be interpreted.

Latency is machine-dependent by nature; the artifact records the machine, and
the manuscript should be read as "measured on the authors' machine" (as it
already states). Exit 0 = benchmark written.
"""
import json
import os
import platform
import sys
import time

import numpy as np
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import pipeline_authoritative as pa  # noqa: E402

OUT = os.path.join(ROOT, 'experiment_results', 'latency_benchmark.json')
N_REPEAT = 5
PRICE_PER_VCPU_HOUR = 0.04


def cpu_name():
    try:
        import subprocess
        out = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'],
                             capture_output=True, text=True, timeout=5)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return platform.processor() or platform.machine()


def main():
    rows, _ = pa.load_rows()
    X, y = pa.matrix(rows, pa.FEATURES)
    idx = np.arange(len(rows))
    tr, te = train_test_split(idx, test_size=0.2, random_state=pa.SEED, stratify=y)
    X_te = X[te]

    report = {
        'machine': cpu_name(),
        'os': platform.platform(),
        'threads_pinned': 1,
        'n_predictions': len(te),
        'repeats': N_REPEAT,
        'price_per_vcpu_hour_usd': PRICE_PER_VCPU_HOUR,
        'models': {},
    }

    print(f'Inference latency on {report["machine"]} (single core)')
    for name in ('Random Forest', 'Gradient Boosting', 'Logistic Regression'):
        m = pa.models()[name]
        m.fit(X[tr], y[tr])
        # warm up (JIT-free, but caches matter)
        m.predict(X_te[:64])
        times = []
        for _ in range(N_REPEAT):
            t0 = time.perf_counter()
            m.predict(X_te)
            times.append(time.perf_counter() - t0)
        med_ms_per_1k = float(np.median(times)) / len(te) * 1000 * 1000
        cost = PRICE_PER_VCPU_HOUR / 3600 * (float(np.median(times)) / len(te) * 1000)
        report['models'][name] = {
            'median_ms_per_1000': round(med_ms_per_1k, 1),
            'best_ms_per_1000': round(min(times) / len(te) * 1000 * 1000, 1),
            'usd_per_1000': round(cost, 9),
        }
        print(f"  {name:22s} {med_ms_per_1k:7.1f} ms / 1,000 (median)   "
              f"${cost:.2e} / 1,000")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f'\nwrote {OUT}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
