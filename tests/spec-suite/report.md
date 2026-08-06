# Spec-suite report

## Wire codec

- selftest: PASS

## Properties (model-level)

| property | strategy | expectation | result |
|---|---|---|---|
| idempotent | v1 | holds | PASS |
| idempotent | v1i | holds | PASS |
| idempotent | v2 | holds | PASS |
| idempotent | v2r | holds | PASS |
| commutative_third_party | v1 | holds | PASS |
| commutative_third_party | v1i | holds | PASS |
| commutative_third_party | v2 | holds | PASS |
| commutative_third_party | v2r | holds | PASS |
| own_echo_order_dependent | v1 | holds | PASS |
| own_echo_order_dependent | v1i | holds | PASS |
| own_echo_order_dependent | v2 | holds | PASS |
| own_echo_order_dependent | v2r | holds | PASS |
| version_monotone | v2 | holds | PASS |
| version_monotone | v2r | holds | PASS |
| stale_echo_rejected | v1 | defect reproduces | PASS |
| stale_echo_rejected | v1i | holds | PASS |
| stale_echo_rejected | v2 | holds | PASS |
| stale_echo_rejected | v2r | holds | PASS |
| echo_resurrection_resisted | v2 | defect reproduces | PASS |
| echo_resurrection_resisted | v2r | holds | PASS |
| reboot_recovery | v2 | holds | PASS |
| reboot_recovery | v2r | holds | PASS |
| tie_gap_documented | v2 | holds | PASS |
| tie_gap_documented | v2r | holds | PASS |

## Scenario battery (simulator)

### office_bench

| strategy | seed | check | result | detail |
|---|---|---|---|---|
| v1 | 1 | ttl_divergence_reproduced | PASS | p95=46 |
| v1 | 1 | author_holds_lowest_ttl | PASS | p95 deficit=45 |
| v1 | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v1 | 2 | ttl_divergence_reproduced | PASS | p95=42 |
| v1 | 2 | author_holds_lowest_ttl | PASS | p95 deficit=42 |
| v1 | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v1 | 3 | ttl_divergence_reproduced | PASS | p95=43 |
| v1 | 3 | author_holds_lowest_ttl | PASS | p95 deficit=43 |
| v1 | 3 | value_converged_after_quiesce | PASS | diverged=0 |
| v1i | 1 | ttl_divergence_reproduced | PASS | p95=46 |
| v1i | 1 | author_holds_lowest_ttl | PASS | p95 deficit=45 |
| v1i | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v1i | 2 | ttl_divergence_reproduced | PASS | p95=42 |
| v1i | 2 | author_holds_lowest_ttl | PASS | p95 deficit=42 |
| v1i | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v1i | 3 | ttl_divergence_reproduced | PASS | p95=43 |
| v1i | 3 | author_holds_lowest_ttl | PASS | p95 deficit=43 |
| v1i | 3 | value_converged_after_quiesce | PASS | diverged=0 |
| v2 | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v2 | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v2 | 3 | value_converged_after_quiesce | PASS | diverged=0 |
| v2r | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v2r | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v2r | 3 | value_converged_after_quiesce | PASS | diverged=0 |

| strategy | seed | metrics |
|---|---|---|
| v1 | 1 | ttl_div_p95=46 lockouts=0 stale=0 self=0 aoi_p95=171.9 prop_p95=26.9 conv=True |
| v1 | 2 | ttl_div_p95=42 lockouts=0 stale=0 self=0 aoi_p95=171.9 prop_p95=27.2 conv=True |
| v1 | 3 | ttl_div_p95=43 lockouts=0 stale=0 self=0 aoi_p95=171.9 prop_p95=27.5 conv=True |
| v1i | 1 | ttl_div_p95=46 lockouts=0 stale=0 self=0 aoi_p95=171.9 prop_p95=26.9 conv=True |
| v1i | 2 | ttl_div_p95=42 lockouts=0 stale=0 self=0 aoi_p95=171.9 prop_p95=27.2 conv=True |
| v1i | 3 | ttl_div_p95=43 lockouts=0 stale=0 self=0 aoi_p95=171.9 prop_p95=27.5 conv=True |
| v2 | 1 | ttl_div_p95=28 lockouts=0 stale=0 self=0 aoi_p95=171.9 prop_p95=26.9 conv=True |
| v2 | 2 | ttl_div_p95=28 lockouts=0 stale=0 self=0 aoi_p95=171.9 prop_p95=27.2 conv=True |
| v2 | 3 | ttl_div_p95=27 lockouts=0 stale=0 self=0 aoi_p95=171.9 prop_p95=27.5 conv=True |
| v2r | 1 | ttl_div_p95=28 lockouts=0 stale=0 self=0 aoi_p95=171.9 prop_p95=26.9 conv=True |
| v2r | 2 | ttl_div_p95=28 lockouts=0 stale=0 self=0 aoi_p95=171.9 prop_p95=27.2 conv=True |
| v2r | 3 | ttl_div_p95=27 lockouts=0 stale=0 self=0 aoi_p95=171.9 prop_p95=27.5 conv=True |

### montenet_chain

| strategy | seed | check | result | detail |
|---|---|---|---|---|
| v1 | 1 | ill_warnings_reproduced | PASS | ill_discards=486 |
| v1 | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v1 | 2 | ill_warnings_reproduced | PASS | ill_discards=484 |
| v1 | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v1 | 3 | ill_warnings_reproduced | PASS | ill_discards=463 |
| v1 | 3 | value_converged_after_quiesce | PASS | diverged=0 |
| v1i | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v1i | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v1i | 3 | value_converged_after_quiesce | PASS | diverged=0 |
| v2 | 1 | no_author_lockout | PASS | rejects=0 |
| v2 | 1 | no_stale_regressions | PASS | regressions=0 |
| v2 | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v2 | 2 | no_author_lockout | PASS | rejects=0 |
| v2 | 2 | no_stale_regressions | PASS | regressions=0 |
| v2 | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v2 | 3 | no_author_lockout | PASS | rejects=0 |
| v2 | 3 | no_stale_regressions | PASS | regressions=0 |
| v2 | 3 | value_converged_after_quiesce | PASS | diverged=0 |
| v2r | 1 | no_author_lockout | PASS | rejects=0 |
| v2r | 1 | no_stale_regressions | PASS | regressions=0 |
| v2r | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v2r | 2 | no_author_lockout | PASS | rejects=0 |
| v2r | 2 | no_stale_regressions | PASS | regressions=0 |
| v2r | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v2r | 3 | no_author_lockout | PASS | rejects=0 |
| v2r | 3 | no_stale_regressions | PASS | regressions=0 |
| v2r | 3 | value_converged_after_quiesce | PASS | diverged=0 |

| strategy | seed | metrics |
|---|---|---|
| v1 | 1 | ttl_div_p95=86 lockouts=0 stale=0 self=0 aoi_p95=274.9 prop_p95=76.0 conv=True |
| v1 | 2 | ttl_div_p95=87 lockouts=0 stale=0 self=0 aoi_p95=274.9 prop_p95=71.7 conv=True |
| v1 | 3 | ttl_div_p95=83 lockouts=0 stale=0 self=0 aoi_p95=273.9 prop_p95=61.7 conv=True |
| v1i | 1 | ttl_div_p95=86 lockouts=0 stale=0 self=0 aoi_p95=274.9 prop_p95=76.0 conv=True |
| v1i | 2 | ttl_div_p95=87 lockouts=0 stale=0 self=0 aoi_p95=274.9 prop_p95=71.7 conv=True |
| v1i | 3 | ttl_div_p95=83 lockouts=0 stale=0 self=0 aoi_p95=273.9 prop_p95=61.7 conv=True |
| v2 | 1 | ttl_div_p95=83 lockouts=0 stale=0 self=0 aoi_p95=274.9 prop_p95=76.0 conv=True |
| v2 | 2 | ttl_div_p95=83 lockouts=0 stale=0 self=0 aoi_p95=274.9 prop_p95=71.7 conv=True |
| v2 | 3 | ttl_div_p95=82 lockouts=0 stale=0 self=0 aoi_p95=273.9 prop_p95=61.7 conv=True |
| v2r | 1 | ttl_div_p95=83 lockouts=0 stale=0 self=0 aoi_p95=274.9 prop_p95=76.0 conv=True |
| v2r | 2 | ttl_div_p95=83 lockouts=0 stale=0 self=0 aoi_p95=274.9 prop_p95=71.7 conv=True |
| v2r | 3 | ttl_div_p95=82 lockouts=0 stale=0 self=0 aoi_p95=273.9 prop_p95=61.7 conv=True |

### echo_corruption

| strategy | seed | check | result | detail |
|---|---|---|---|---|
| v1 | 1 | stale_echo_corruption_reproduced | PASS | regressions=214 |
| v1 | 2 | stale_echo_corruption_reproduced | PASS | regressions=256 |
| v1 | 3 | stale_echo_corruption_reproduced | PASS | regressions=269 |
| v1i | 1 | v1i_trades_corruption_for_lockout | PASS | self=0 rejects=179 |
| v1i | 2 | v1i_trades_corruption_for_lockout | PASS | self=0 rejects=203 |
| v1i | 3 | v1i_trades_corruption_for_lockout | PASS | self=0 rejects=134 |
| v2 | 1 | no_stale_echo_corruption | PASS | regressions=0 |
| v2 | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v2 | 2 | no_stale_echo_corruption | PASS | regressions=0 |
| v2 | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v2 | 3 | no_stale_echo_corruption | PASS | regressions=0 |
| v2 | 3 | value_converged_after_quiesce | PASS | diverged=0 |
| v2r | 1 | no_stale_echo_corruption | PASS | regressions=0 |
| v2r | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v2r | 2 | no_stale_echo_corruption | PASS | regressions=0 |
| v2r | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v2r | 3 | no_stale_echo_corruption | PASS | regressions=0 |
| v2r | 3 | value_converged_after_quiesce | PASS | diverged=0 |

| strategy | seed | metrics |
|---|---|---|
| v1 | 1 | ttl_div_p95=63 lockouts=29 stale=214 self=77 aoi_p95=100.9 prop_p95=5.1 conv=True |
| v1 | 2 | ttl_div_p95=70 lockouts=144 stale=256 self=94 aoi_p95=105.9 prop_p95=5.0 conv=False |
| v1 | 3 | ttl_div_p95=75 lockouts=44 stale=269 self=100 aoi_p95=103.9 prop_p95=4.5 conv=False |
| v1i | 1 | ttl_div_p95=63 lockouts=179 stale=136 self=0 aoi_p95=99.9 prop_p95=4.6 conv=False |
| v1i | 2 | ttl_div_p95=70 lockouts=203 stale=182 self=0 aoi_p95=99.9 prop_p95=4.8 conv=False |
| v1i | 3 | ttl_div_p95=75 lockouts=134 stale=202 self=0 aoi_p95=98.9 prop_p95=4.5 conv=True |
| v2 | 1 | ttl_div_p95=4 lockouts=0 stale=0 self=0 aoi_p95=98.9 prop_p95=4.5 conv=True |
| v2 | 2 | ttl_div_p95=4 lockouts=0 stale=0 self=0 aoi_p95=98.9 prop_p95=4.6 conv=True |
| v2 | 3 | ttl_div_p95=3 lockouts=0 stale=0 self=0 aoi_p95=98.9 prop_p95=4.4 conv=True |
| v2r | 1 | ttl_div_p95=4 lockouts=0 stale=0 self=0 aoi_p95=98.9 prop_p95=4.5 conv=True |
| v2r | 2 | ttl_div_p95=4 lockouts=0 stale=0 self=0 aoi_p95=98.9 prop_p95=4.6 conv=True |
| v2r | 3 | ttl_div_p95=3 lockouts=0 stale=0 self=0 aoi_p95=98.9 prop_p95=4.4 conv=True |

### reboot_recovery

| strategy | seed | check | result | detail |
|---|---|---|---|---|
| v1 | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v1 | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v1 | 3 | value_converged_after_quiesce | PASS | diverged=0 |
| v1i | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v1i | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v1i | 3 | value_converged_after_quiesce | PASS | diverged=0 |
| v2 | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v2 | 1 | no_self_regression_post_reboot | PASS | self=0 |
| v2 | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v2 | 2 | no_self_regression_post_reboot | PASS | self=0 |
| v2 | 3 | value_converged_after_quiesce | PASS | diverged=0 |
| v2 | 3 | no_self_regression_post_reboot | PASS | self=0 |
| v2r | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v2r | 1 | no_stale_regressions_even_across_reboot | PASS | regressions=0 |
| v2r | 1 | no_self_regression_post_reboot | PASS | self=0 |
| v2r | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v2r | 2 | no_stale_regressions_even_across_reboot | PASS | regressions=0 |
| v2r | 2 | no_self_regression_post_reboot | PASS | self=0 |
| v2r | 3 | value_converged_after_quiesce | PASS | diverged=0 |
| v2r | 3 | no_stale_regressions_even_across_reboot | PASS | regressions=0 |
| v2r | 3 | no_self_regression_post_reboot | PASS | self=0 |

| strategy | seed | metrics |
|---|---|---|
| v1 | 1 | ttl_div_p95=26 lockouts=0 stale=0 self=0 aoi_p95=137.9 prop_p95=14.2 conv=True |
| v1 | 2 | ttl_div_p95=28 lockouts=0 stale=0 self=0 aoi_p95=137.9 prop_p95=13.6 conv=True |
| v1 | 3 | ttl_div_p95=28 lockouts=0 stale=0 self=0 aoi_p95=137.9 prop_p95=12.4 conv=True |
| v1i | 1 | ttl_div_p95=26 lockouts=0 stale=0 self=0 aoi_p95=137.9 prop_p95=14.2 conv=True |
| v1i | 2 | ttl_div_p95=28 lockouts=0 stale=0 self=0 aoi_p95=137.9 prop_p95=13.6 conv=True |
| v1i | 3 | ttl_div_p95=28 lockouts=0 stale=0 self=0 aoi_p95=137.9 prop_p95=12.4 conv=True |
| v2 | 1 | ttl_div_p95=18 lockouts=0 stale=3 self=0 aoi_p95=137.9 prop_p95=14.2 conv=True |
| v2 | 2 | ttl_div_p95=18 lockouts=0 stale=0 self=0 aoi_p95=137.9 prop_p95=13.6 conv=True |
| v2 | 3 | ttl_div_p95=18 lockouts=0 stale=0 self=0 aoi_p95=137.9 prop_p95=12.4 conv=True |
| v2r | 1 | ttl_div_p95=18 lockouts=0 stale=0 self=0 aoi_p95=137.9 prop_p95=14.2 conv=True |
| v2r | 2 | ttl_div_p95=18 lockouts=0 stale=0 self=0 aoi_p95=137.9 prop_p95=13.6 conv=True |
| v2r | 3 | ttl_div_p95=18 lockouts=0 stale=0 self=0 aoi_p95=137.9 prop_p95=12.4 conv=True |

### lossy_mesh

| strategy | seed | check | result | detail |
|---|---|---|---|---|
| v1 | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v1 | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v1 | 3 | value_converged_after_quiesce | PASS | diverged=0 |
| v1i | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v1i | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v1i | 3 | value_converged_after_quiesce | PASS | diverged=0 |
| v2 | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v2 | 1 | no_stale_regressions | PASS | regressions=0 |
| v2 | 1 | no_author_lockout | PASS | rejects=0 |
| v2 | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v2 | 2 | no_stale_regressions | PASS | regressions=0 |
| v2 | 2 | no_author_lockout | PASS | rejects=0 |
| v2 | 3 | value_converged_after_quiesce | PASS | diverged=0 |
| v2 | 3 | no_stale_regressions | PASS | regressions=0 |
| v2 | 3 | no_author_lockout | PASS | rejects=0 |
| v2r | 1 | value_converged_after_quiesce | PASS | diverged=0 |
| v2r | 1 | no_stale_regressions | PASS | regressions=0 |
| v2r | 1 | no_author_lockout | PASS | rejects=0 |
| v2r | 2 | value_converged_after_quiesce | PASS | diverged=0 |
| v2r | 2 | no_stale_regressions | PASS | regressions=0 |
| v2r | 2 | no_author_lockout | PASS | rejects=0 |
| v2r | 3 | value_converged_after_quiesce | PASS | diverged=0 |
| v2r | 3 | no_stale_regressions | PASS | regressions=0 |
| v2r | 3 | no_author_lockout | PASS | rejects=0 |

| strategy | seed | metrics |
|---|---|---|
| v1 | 1 | ttl_div_p95=48 lockouts=0 stale=0 self=0 aoi_p95=285.9 prop_p95=39.9 conv=True |
| v1 | 2 | ttl_div_p95=50 lockouts=0 stale=0 self=0 aoi_p95=285.9 prop_p95=45.6 conv=True |
| v1 | 3 | ttl_div_p95=51 lockouts=0 stale=0 self=0 aoi_p95=285.9 prop_p95=49.9 conv=True |
| v1i | 1 | ttl_div_p95=48 lockouts=0 stale=0 self=0 aoi_p95=285.9 prop_p95=39.9 conv=True |
| v1i | 2 | ttl_div_p95=50 lockouts=0 stale=0 self=0 aoi_p95=285.9 prop_p95=45.6 conv=True |
| v1i | 3 | ttl_div_p95=51 lockouts=0 stale=0 self=0 aoi_p95=285.9 prop_p95=49.9 conv=True |
| v2 | 1 | ttl_div_p95=38 lockouts=0 stale=0 self=0 aoi_p95=285.9 prop_p95=39.9 conv=True |
| v2 | 2 | ttl_div_p95=39 lockouts=0 stale=0 self=0 aoi_p95=285.9 prop_p95=45.6 conv=True |
| v2 | 3 | ttl_div_p95=40 lockouts=0 stale=0 self=0 aoi_p95=285.9 prop_p95=49.9 conv=True |
| v2r | 1 | ttl_div_p95=38 lockouts=0 stale=0 self=0 aoi_p95=285.9 prop_p95=39.9 conv=True |
| v2r | 2 | ttl_div_p95=39 lockouts=0 stale=0 self=0 aoi_p95=285.9 prop_p95=45.6 conv=True |
| v2r | 3 | ttl_div_p95=40 lockouts=0 stale=0 self=0 aoi_p95=285.9 prop_p95=49.9 conv=True |

## Verdict

- failures: **0**
- wall time: 1.8s
- consistency engaged: **YES**
