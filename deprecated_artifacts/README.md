# Deprecated / unverifiable artifacts

Artifacts kept for provenance only. None of these feed any number in the
manuscript; each is archived with the reason it cannot be used.

## fewshot_full_results_v4.json

DeepSeek-V3 "3-shot per class, 15 examples" full-partition run, accuracy
64.55%, macro F1 0.6266 (2026-07-27). **Not citable**:

- No script in the repository produces it (`grep -rn fewshot_full_results_v4`
  matches only the git index).
- Its test-set class distribution (WA 1864, RE 294, TLE 235, MLE 101,
  CE 178) cannot arise from the authoritative stratified split
  (WA 2047, RE 131, TLE 258, MLE 40, CE 196): RE and MLE are ~2.2-2.5x
  their expected counts, ~14 standard deviations out under the null.
- Two simulated reviews quote its 64.55% as if it were comparable to the
  reported 76.65%; the two numbers come from different test sets, so the
  comparison is invalid.

The mechanistic reading the reviews ask for (few-shot examples spread
predictions more evenly: WA recall 0.637, RE recall 0.257 vs 0.016 for the
three-shot run) is directionally consistent with the manuscript's argument,
but it needs a re-run on the authoritative split before it can be cited.
Re-run requires a DeepSeek API key (`DEEPSEEK_API_KEY`).

**Superseded 2026-10-18.** The mechanism the reviews asked for is now
established from artifact-verified runs instead, by
`experiment_code/fewshot_mechanism_analysis.py` (output:
`experiment_results/fewshot_mechanism.json`). On the shared authoritative
2,672-item partition, the no-example run answers WA for 95.0% of submissions
(entropy 0.35 bits; CE recall 0.179) while the three-shot run spreads to 62.6%
WA (entropy 1.45 bits; CE recall 1.000 at precision 0.321): the examples decide
whether the platform encoding is applied at all. The two arms differ in call
format as well as example count, so a controlled 15-example dose-response
remains open; that arm still needs an API key.

## ds_v4_predictions.json (top level, not moved)

Produced by `run_ds_v4_fair.py` / `run_ds_v4_final.py` against
`deepseek-v4-flash`, single-item zero-shot. Its `load_data` splits the data
with `random.Random(42).shuffle()` rather than sklearn's stratified split, so
its partition is not the manuscript's test partition. Not citable; retained
only because the cost estimate reads its per-call token counts.
