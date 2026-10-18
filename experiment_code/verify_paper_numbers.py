#!/usr/bin/env python3
"""Master gate: every number in the manuscript must trace to an artifact.

Runs each artifact check as a subprocess and aggregates the exit codes. Any
non-zero exit means at least one manuscript figure does not reproduce, and
submission must stop. This is the single command a pre-submission checklist
should point at.

Checks chained (each writes its own artifact and prints its own PASS/FAIL
lines):

  1. dataset_descriptives.py      Table 1, its footnote, Figure 2 caption
  2. difficulty_tier_analysis.py  Section 5.5 tiers (92.21 / 93.60 / 87.55)
  3. clustering_diagnostic.py     Section 5.1 ICC / design effect / n_eff
  4. fewshot_mechanism_analysis.py  Section 5 worked-example mechanism
  5. audit_llm_numbers.py         every LLM number, incl. Table 8 chi-squares
  6. verify_mcnemar_alignment.py  the pairing behind every McNemar row
  7. verify_references.py         bibliography against the registries
  8. equivalence_spectrum.py      Section 5.3 corpus-level claims (checked
                                   here against its JSON, since that script
                                   only writes the artifact)
  9. latency_benchmark.py         informational only: machine-dependent, so a
                                   mismatch with the printed value is not a
                                   failure; the artifact is the record.

Exit 0 = every check passed.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable

CHECKS = [
    ('Table 1 / footnote / Figure 2', 'dataset_descriptives.py', True),
    ('Difficulty tiers (§5.5)', 'difficulty_tier_analysis.py', True),
    ('Clustering diagnostic (§5.1)', 'clustering_diagnostic.py', True),
    ('Few-shot mechanism (§5)', 'fewshot_mechanism_analysis.py', True),
    ('LLM numbers audit', 'audit_llm_numbers.py', True),
    ('McNemar alignment gate', 'verify_mcnemar_alignment.py', True),
    ('Bibliography registry', 'verify_references.py', True),
    ('Latency benchmark (info only)', 'latency_benchmark.py', False),
]

# Section 5.3 corpus-level claims, checked against equivalence_spectrum.json
EQUIV_EXPECTED = [
    ('n_mixed_groups', 95, 0),
    ('rows_in_mixed_groups', 8653, 0),
    ('share_in_mixed_groups', 0.648, 0.001),
    ('high_entropy_groups/n', 70, 0),
    ('high_entropy_groups/rows', 1892, 0),
    ('low_entropy_groups/n', 25, 0),
    ('low_entropy_groups/rows', 6761, 0),
    ('modal_rule_signature_only/error_rate', 0.066, 0.001),
    ('collision/largest_group_signature/size', 1738, 0),
]


def dig(d, path):
    for k in path.split('/'):
        d = d[k]
    return d


def check_equivalence():
    with open(os.path.join(ROOT, 'experiment_results',
                           'equivalence_spectrum.json'), encoding='utf-8') as f:
        d = json.load(f)
    with open(os.path.join(ROOT, 'experiment_results',
                           'authoritative_results_v3.json'), encoding='utf-8') as f:
        auth = json.load(f)
    ok = True
    print('Section 5.3 corpus claims vs equivalence_spectrum.json:')
    for path, printed, tol in EQUIV_EXPECTED:
        if path.startswith('collision/'):
            actual = dig(auth['collision'], path[len('collision/'):])
        else:
            actual = dig(d, path)
        good = abs(actual - printed) <= tol
        ok &= good
        print(f"  [{'PASS' if good else 'FAIL'}] {path:42s} "
              f"manuscript {printed:>8}  artifact {actual:.6g}")
    return ok


def main():
    results = []
    for label, script, required in CHECKS:
        print('=' * 70)
        print(f'== {label}  ({script})')
        print('=' * 70)
        p = subprocess.run([PY, os.path.join(HERE, script)],
                           capture_output=True, text=True)
        tail = '\n'.join((p.stdout.strip().split('\n') or [''])[-6:])
        print(tail)
        if p.returncode != 0:
            print('  stderr tail:', (p.stderr.strip().split('\n') or [''])[-3:])
        results.append((label, p.returncode, required))

    print('=' * 70)
    print('== Section 5.3 corpus claims (equivalence_spectrum.py artifact)')
    print('=' * 70)
    subprocess.run([PY, os.path.join(HERE, 'equivalence_spectrum.py')],
                   capture_output=True, text=True)
    eq_ok = check_equivalence()
    results.append(('Section 5.3 corpus claims', 0 if eq_ok else 1, True))

    print('=' * 70)
    print('SUMMARY')
    print('=' * 70)
    all_ok = True
    for label, code, required in results:
        status = 'PASS' if code == 0 else ('INFO' if not required else 'FAIL')
        if required and code != 0:
            all_ok = False
        print(f'  [{status}] {label}')
    print('=' * 70)
    print('ALL PAPER NUMBERS ' + ('VERIFIED' if all_ok else 'NOT VERIFIED'))
    print('=' * 70)
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
