"""Scenario battery: named multi-node simulations with per-strategy
expectations. Each scenario returns (summary, checks) where checks is a
list of (check_name, passed, detail).

The v1 expectations are CHARACTERIZATION: they pass when the
field-observed pathology reproduces (TTL divergence, author lockout,
stale-echo corruption). The v2 expectations are CORRECTNESS: they pass
when the pathology is gone. "Consistency engaged" = every check green.
"""

from simulator import SimConfig, LinkSpec, Simulation, summarize


def full_mesh(nodes):
    return {n: [m for m in nodes if m != n] for n in nodes}


def office_bench(strategy, seed=1):
    """4 LibreRouters on a bench with radio distance forced to 1000 —
    G10h4ck's TTL-divergence note. Slow links, everyone hears everyone.
    Field observation to reproduce (v1): TTL error ~ seconds, author
    holds the LOWEST TTL for its own key."""
    cfg = SimConfig(
        topology=full_mesh(["A", "B", "C", "D"]),
        link=LinkSpec(latency_min=1.0, latency_max=4.0, loss=0.05),
        strategy=strategy, bleach_ttl=2000, update_interval=30,
        sync_interval=30.0, publish_interval=30.0,
        duration=600.0, quiesce=180.0, seed=seed)
    s = summarize(Simulation(cfg).run())
    checks = []
    if strategy in ("v1", "v1i"):
        checks.append(("ttl_divergence_reproduced", (s["ttl_div_p95"] or 0) >= 2,
                       f"p95={s['ttl_div_p95']}"))
        checks.append(("author_holds_lowest_ttl", (s["author_deficit_p95"] or 0) >= 2,
                       f"p95 deficit={s['author_deficit_p95']}"))
    checks.append(("value_converged_after_quiesce", s["converged"] is True,
                   f"diverged={s['n_diverged_keys']}"))
    return s, checks


def montenet_chain(strategy, seed=1):
    """MonteNet-like topology: jime - balcon - tronco - {ebob, suri}.
    Nodes behind tronco see jime only through tronco's (higher-TTL)
    copies. Field observation to reproduce (v1): author lockout —
    jime's fresher generations rejected upstream."""
    topo = {"jime": ["balcon"],
            "balcon": ["jime", "tronco"],
            "tronco": ["balcon", "ebob", "suri"],
            "ebob": ["tronco"], "suri": ["tronco"]}
    cfg = SimConfig(
        topology=topo,
        link=LinkSpec(latency_min=0.5, latency_max=3.0, loss=0.10),
        strategy=strategy, bleach_ttl=1200, update_interval=30,
        sync_interval=30.0, publish_interval=90.0,
        duration=900.0, quiesce=240.0, seed=seed)
    s = summarize(Simulation(cfg).run())
    checks = []
    if strategy == "v1":
        # the exact field symptom: "Discarding received known entry ...
        # authored by this node with higher TTL ... is remote peer ill?"
        checks.append(("ill_warnings_reproduced", s["ill_discards"] > 0,
                       f"ill_discards={s['ill_discards']}"))
    if strategy in ("v2", "v2r"):
        checks.append(("no_author_lockout", s["lockout_rejects"] == 0,
                       f"rejects={s['lockout_rejects']}"))
        checks.append(("no_stale_regressions", s["stale_regressions"] == 0,
                       f"regressions={s['stale_regressions']}"))
    checks.append(("value_converged_after_quiesce", s["converged"] is True,
                   f"diverged={s['n_diverged_keys']}"))
    return s, checks


def echo_corruption(strategy, seed=1):
    """Fast republish against slow echo: author updates its entry while
    same-TTL echoes of the previous generation still circulate.
    Field/analysis observation to reproduce (v1): stale echoes overwrite
    newer data, including at the author itself (audit C1/C6)."""
    cfg = SimConfig(
        topology=full_mesh(["A", "B", "C"]),
        link=LinkSpec(latency_min=0.5, latency_max=2.5, loss=0.0),
        strategy=strategy, bleach_ttl=600, update_interval=5,
        sync_interval=4.0, publish_interval=6.0,
        duration=400.0, quiesce=120.0, seed=seed)
    s = summarize(Simulation(cfg).run())
    checks = []
    if strategy == "v1":
        checks.append(("stale_echo_corruption_reproduced",
                       s["stale_regressions"] > 0,
                       f"regressions={s['stale_regressions']}"))
        # No convergence gate for v1 here: seeds show BOTH island
        # polarities — (a) author's newer gen can't beat TTL-inflated
        # copies, (b) author corrupted to an old gen and the
        # "is remote peer ill?" guard locks the corruption in by
        # rejecting the mesh's correction. Convergence is reported in
        # the metrics row instead of asserted.
    if strategy == "v1i":
        # SUITE FINDING: the *intended* db58e3d guard does not cure the
        # scenario — it trades corruption for author lockout (and can
        # leave the author on a permanently divergent island). PASS =
        # trade reproduces.
        checks.append(("v1i_trades_corruption_for_lockout",
                       s["self_regressions"] == 0 and s["lockout_rejects"] > 0,
                       f"self={s['self_regressions']} rejects={s['lockout_rejects']}"))
    if strategy in ("v2", "v2r"):
        checks.append(("no_stale_echo_corruption", s["stale_regressions"] == 0,
                       f"regressions={s['stale_regressions']}"))
        checks.append(("value_converged_after_quiesce", s["converged"] is True,
                       f"diverged={s['n_diverged_keys']}"))
    return s, checks


def reboot_recovery(strategy, seed=1):
    """Author reboots mid-run, losing state (and v2 version counters).
    v2 correctness: recovery leapfrog works under gossip, zero
    regressions at the author after reboot, still converges."""
    cfg = SimConfig(
        topology=full_mesh(["A", "B", "C", "D"]),
        link=LinkSpec(latency_min=0.2, latency_max=1.5, loss=0.05),
        strategy=strategy, bleach_ttl=900, update_interval=15,
        sync_interval=15.0, publish_interval=20.0,
        duration=500.0, quiesce=150.0,
        reboots=[(230.0, "A")], seed=seed)
    s = summarize(Simulation(cfg).run())
    checks = [("value_converged_after_quiesce", s["converged"] is True,
               f"diverged={s['n_diverged_keys']}")]
    if strategy == "v2":
        # SUITE FINDING (echo resurrection): plain v2 may transiently
        # resurrect pre-reboot data mesh-wide; bounded by one publish
        # interval, so we only require eventual convergence above.
        checks.append(("no_self_regression_post_reboot",
                       s["self_regressions"] == 0,
                       f"self={s['self_regressions']}"))
    if strategy == "v2r":
        checks.append(("no_stale_regressions_even_across_reboot",
                       s["stale_regressions"] == 0,
                       f"regressions={s['stale_regressions']}"))
        checks.append(("no_self_regression_post_reboot",
                       s["self_regressions"] == 0,
                       f"self={s['self_regressions']}"))
    return s, checks


def lossy_mesh(strategy, seed=1):
    """General stress: 6 nodes, ring+chords, 20% loss, moderate latency.
    Both strategies must still value-converge after quiescence; v2 must
    additionally show zero regressions/lockouts."""
    topo = {"n1": ["n2", "n6", "n3"], "n2": ["n1", "n3"],
            "n3": ["n2", "n4", "n1"], "n4": ["n3", "n5"],
            "n5": ["n4", "n6"], "n6": ["n5", "n1"]}
    cfg = SimConfig(
        topology=topo,
        link=LinkSpec(latency_min=0.1, latency_max=2.0, loss=0.20),
        strategy=strategy, bleach_ttl=1200, update_interval=20,
        sync_interval=20.0, publish_interval=40.0,
        duration=800.0, quiesce=300.0, seed=seed)
    s = summarize(Simulation(cfg).run())
    checks = [("value_converged_after_quiesce", s["converged"] is True,
               f"diverged={s['n_diverged_keys']}")]
    if strategy in ("v2", "v2r"):
        checks.append(("no_stale_regressions", s["stale_regressions"] == 0,
                       f"regressions={s['stale_regressions']}"))
        checks.append(("no_author_lockout", s["lockout_rejects"] == 0,
                       f"rejects={s['lockout_rejects']}"))
    return s, checks


SCENARIOS = [
    ("office_bench", office_bench),
    ("montenet_chain", montenet_chain),
    ("echo_corruption", echo_corruption),
    ("reboot_recovery", reboot_recovery),
    ("lossy_mesh", lossy_mesh),
]
