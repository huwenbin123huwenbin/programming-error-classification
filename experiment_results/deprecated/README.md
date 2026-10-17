# Deprecated results — do not use

These two files record an earlier analysis whose numbers are **not** the ones reported
in the paper. They are kept only so that the revision history is auditable.

| File | Reported | Why it is superseded |
|---|---|---|
| `final_results_v2.json` | GB 95.02%, RF 94.24%, LR 73.91% | Built on seven features including `hour` (a constant 12 — the public submission record carries no timestamp) and `user_success_rate`, which was computed over the whole corpus and therefore let each row's own label enter its own predictor. Removing that leak costs 2.1 pp rather than gaining 3.6 pp. LR was fitted on unstandardised inputs and had not converged. |
| `experiment_results_v2.json` | figure data derived from the above | Same pipeline, same defects. |

The authoritative results are in `../authoritative_results_v3.json`, produced by
`../../experiment_code/pipeline_authoritative.py`. That script regenerates every
number, table and figure in the manuscript in a single run. The per-class structure,
the equivalence-cell analysis and the submitter-disjoint replication are all reported
from it.

If you are replicating this work, run that script and compare against
`authoritative_results_v3.json`. Do not compare against the files in this folder.
