# Deprecated results — do not use

These files record an earlier analysis whose numbers are **not** the ones reported
in the paper. They are kept only so that the revision history is auditable.

| File | Reported | Why it is superseded |
|---|---|---|
| `final_results_v2.json` | GB 95.02%, RF 94.24%, LR 73.91% | Built on seven features including `hour` (a constant 12 — the public submission record carries no timestamp) and `user_success_rate`, which was computed over the whole corpus and therefore let each row's own label enter its own predictor. Removing that leak costs 2.1 pp rather than gaining 3.6 pp. LR was fitted on unstandardised inputs and had not converged. |
| `experiment_results_v2.json` | figure data derived from the above | Same pipeline, same defects. |
| `gb_predictions_test.json` | GB 91.99% on the test split | Per-row predictions from the superseded pipeline. The manuscript reports 91.77%. Anyone recomputing a McNemar test from this file gets 376.30 for GB vs.\ DeepSeek-V3; the correct figure, recomputed from the authoritative pipeline, is 364.23. |
| `ml_predictions_test_5feat.json` | GB 91.99%, RF 91.54%, LR 87.61% | Same defect in the five-field variant used for the like-for-like ML--LLM comparison. |

The authoritative results are in `../authoritative_results_v3.json`, produced by
`../../experiment_code/pipeline_authoritative.py`. That script regenerates every
number, table and figure in the manuscript in a single run. The per-class structure,
the equivalence-cell analysis and the submitter-disjoint replication are all reported
from it.

To check the LLM numbers that the JSON does not store — per-class recall and
precision, the prediction distributions, and every McNemar row that involves an LLM —
run `../../experiment_code/audit_llm_numbers.py`. It recomputes them from the raw
prediction dumps in `../../llm_experiments/` and prints a PASS/FAIL verdict against
the manuscript. It deliberately recomputes the ML predictions from the pipeline
instead of reading the two dumps archived here.

If you are replicating this work, run that script and compare against
`authoritative_results_v3.json`. Do not compare against the files in this folder.
Note that `../../llm_experiments/recompute_gb.py` still reads
`gb_predictions_test.json`; it belongs to the superseded pipeline and is kept only
for history.
