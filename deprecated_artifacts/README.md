# Deprecated / unverifiable artifacts

Artifacts kept for provenance only. None of these feed any number in the
manuscript; each is archived with the reason it cannot be used.

## student_proxy_experiment.json

Grouped the test partition by **submitter** rating and evaluated Gradient
Boosting per band: novice 96.01% / intermediate 95.21% / advanced 88.54%.
**Not citable:**

- The manuscript's generalization analysis (Section 5.5) segments by
  **problem** difficulty, not submitter skill. The user-skill grouping
  supported the backwards claim that novices are classified most accurately;
  the effect is composition (advanced problems carry a more diverse verdict
  mix), not classifier behaviour.
- The grouping depends on `user_ratings.json`, which is not part of the
  released dataset, so the split cannot be reproduced from the repository.
- The saved `n_users_with_rating` field counted rows with a rating (13,305),
  not users (4,005) — a labelling bug, fixed in the script's successor
  convention (`rows_with_rating`).

Replacement: `experiment_code/difficulty_tier_analysis.py`, which reproduces
the manuscript's 92.21 / 93.60 / 87.55% exactly from the authoritative rows
and persists `experiment_results/difficulty_tiers.json`.

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

## legacy_figures/ (archived 2026-10-18)

Figure files and plotting scripts from earlier manuscript versions. None is
referenced by `paper_acm.tex`; all were verified unreferenced before the move
(grep over the tex, the Chinese companion, and the README).

- `fig4_rf_confusion.pdf`, `fig5_gb_confusion.pdf`, `fig7_f1_comparison.pdf`,
  `fig_feature_importance.pdf` (2026-06-16): pre-v3 figures drawn from the
  retired feature set (seven fields, including `user_success_rate`).
- `fig11_lococv.pdf`, `fig12_contest_analysis.pdf`: LOCOCV cross-contest
  figures from the retired cross-contest experiment.
- `fig_ablation_chart.png` (2026-07-28): ablation chart superseded by Table 6
  plus `ablation_study.py`; its augmentation row carried the self-leakage
  artefact corrected in Round 14.
- `model_comparison.pdf`: model-comparison chart superseded by
  `fig_accuracy_chart.png`.
- `chart_figs/` (4 PNGs): duplicate charts from an intermediate iteration.
- `generate_figures.py` (2026-06-08): reads
  `02_预处理数据/preprocessed_data.csv`, a path that no longer exists; five
  features, RF confusion matrix. Non-runnable as archived.
- `regenerate_gb_figures.py`: draws GB figures from `final_results_v2.json`
  with hardcoded `/Users/mac/Desktop/SCI1/...` paths; the current authoritative
  source is `experiment_code/regenerate_figures_v3.py`, which is chained into
  the master gate (`verify_paper_numbers.py`, check 13, `--check` mode).
