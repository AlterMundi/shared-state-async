#!/usr/bin/env python3
"""Spec-suite runner: properties + scenario battery across strategies.

  python3 run_suite.py            # full run, writes report.md, exit != 0 on red
  python3 run_suite.py --quick    # fewer seeds/scenarios for iteration

Green means: every characterization check reproduces the field-observed
v1 pathology AND every correctness check holds for v2. That is the
"consistency engaged" criterion — the model, the spec, the field notes
and the proposed fix all telling the same story.
"""

import sys
import time

import properties
import scenarios
import wire
from model import STRATEGIES


def run(quick=False):
    t0 = time.time()
    lines = ["# Spec-suite report", ""]
    failures = 0

    # 0. wire codec selftest
    ok = wire.selftest()
    lines += ["## Wire codec", "", f"- selftest: {'PASS' if ok else 'FAIL'}", ""]
    failures += 0 if ok else 1

    # 1. properties
    if quick:
        properties.N_SEEDS = 40
    lines += ["## Properties (model-level)", "",
              "| property | strategy | expectation | result |",
              "|---|---|---|---|"]
    for r in properties.run_properties():
        expected = "holds" if r["expected"] else "defect reproduces"
        status = "PASS" if r["ok"] else f"FAIL {r['failures'][:2]}"
        if not r["ok"]:
            failures += 1
        lines.append(f"| {r['property']} | {r['strategy']} | {expected} | {status} |")
    lines.append("")

    # 2. scenarios
    seeds = [1] if quick else [1, 2, 3]
    lines += ["## Scenario battery (simulator)", ""]
    for name, fn in scenarios.SCENARIOS:
        lines += [f"### {name}", "",
                  "| strategy | seed | check | result | detail |",
                  "|---|---|---|---|---|"]
        stats_row = []
        for strategy in STRATEGIES:
            for seed in seeds:
                summary, checks = fn(strategy, seed=seed)
                for cname, passed, detail in checks:
                    if not passed:
                        failures += 1
                    lines.append(f"| {strategy} | {seed} | {cname} | "
                                 f"{'PASS' if passed else 'FAIL'} | {detail} |")
                stats_row.append(
                    f"| {strategy} | {seed} | ttl_div_p95={summary['ttl_div_p95']} "
                    f"lockouts={summary['lockout_rejects']} "
                    f"stale={summary['stale_regressions']} "
                    f"self={summary['self_regressions']} "
                    f"aoi_p95={None if summary['aoi_p95'] is None else round(summary['aoi_p95'], 1)} "
                    f"prop_p95={None if summary['prop_delay_p95'] is None else round(summary['prop_delay_p95'], 1)} "
                    f"conv={summary['converged']} |")
        lines += ["", "| strategy | seed | metrics |", "|---|---|---|"]
        lines += stats_row
        lines.append("")

    lines += ["## Verdict", "",
              f"- failures: **{failures}**",
              f"- wall time: {time.time() - t0:.1f}s",
              f"- consistency engaged: **{'YES' if failures == 0 else 'NO'}**", ""]
    report = "\n".join(lines)
    with open("report.md", "w") as f:
        f.write(report)
    print(report)
    return failures


if __name__ == "__main__":
    sys.exit(1 if run(quick="--quick" in sys.argv) else 0)
