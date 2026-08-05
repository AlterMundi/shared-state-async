# spec-suite — executable spec, property tests & multi-node simulator

Companion of [`doc/protocol-spec-DRAFT.md`](../../doc/protocol-spec-DRAFT.md).
Pure Python 3 stdlib, no dependencies, deterministic (seeded).

```
python3 run_suite.py            # full battery, writes report.md, exit!=0 on red
python3 run_suite.py --quick    # fast iteration mode
python3 wire.py selftest        # wire codec self-test
python3 wire.py sync <ip> <type>  # run a real sync session vs a live daemon
```

## What it is

| file | role |
|---|---|
| `model.py` | executable merge/bleach semantics: `v1` (deployed), `v1i` (intended db58e3d guard), `v2` (javierbrk `merge_with_version`), `v2r` (v2 + suite-proposed recovery refinement) |
| `simulator.py` | discrete-event N-node gossip sim: latency, loss, bleach phase, reboots; instruments every merge |
| `properties.py` | model-level properties incl. characterization tests (defects EXPECTED to reproduce) |
| `scenarios.py` | field-scenario battery: office bench, MonteNet chain, echo corruption, reboot, lossy mesh |
| `wire.py` | byte-exact framing/handshake codec + fixture-capture client (spec §10) |
| `run_suite.py` | runner; "consistency engaged: YES" == every check green |

Green means the model, the spec, the field notes and the proposed fix
all tell the same story: every v1 pathology observed in the field
reproduces in simulation, and every v2/v2r correctness claim holds.

## Findings this suite produced (beyond confirming the field notes)

1. **TTL inflation**: with the `>=` accept rule, same-data echoes between
   nodes with desynchronized bleach clocks refresh each other's TTL —
   circulating copies decay *slower than real time*, bounded by the
   publish interval. This, not transit delay alone, drives the large
   author-deficit divergences (author's own copy decays honestly and
   ends up lowest — exactly the MonteNet table).
2. **v1 author-island, both polarities** (echo_corruption seeds 2/3):
   (a) the author's newer generation cannot beat TTL-inflated stale
   copies; (b) the author gets corrupted by a stale echo and the
   "is remote peer ill?" guard then **locks the corruption in** by
   rejecting the mesh's correction.
3. **v1i (the intended db58e3d guard) is not a fix**: it freezes
   own-authored entries against all remote input, trading corruption
   for author lockout (`self=0` but `lockouts≈180`) and producing
   permanently divergent author-islands.
4. **v2 echo resurrection**: a rebooted node that hears an *outdated*
   echo of its own key before a newer one "recovers" the outdated
   payload to the highest version, resurrecting stale data mesh-wide
   until its next publish. `v2r` fixes it by requiring the recovery
   leapfrog to apply only to entries locally (re-)inserted since boot
   (`prop_echo_resurrection`). **Recommend to javierbrk.**
5. **Own-echo merges are order-dependent in every strategy** (v1 via
   fresh-boot insert bypassing the guards, v2 via recovery version
   bookkeeping) — merge is not a CRDT join; harmless because the next
   authored publish re-anchors, but the spec must not claim confluence.

## Iterating

The loop this suite is built for: change a rule in `model.py` (or add a
scenario), `python3 run_suite.py --quick`, read which characterization
or correctness check moved. Anything that changes a check is a
spec-relevant behavioral difference and belongs in
`doc/protocol-spec-DRAFT.md`. Metrics rows (TTL divergence, AoI p95,
propagation p95, lockouts, regressions) are reported for every scenario
× strategy × seed even where not gated — trend them when tuning.

## Not yet done (needs a built C++ binary)

Golden-fixture capture (spec §10): run `wire.py sync` against a real
`shared-state-async peer` on loopback and store the raw bytes under
`fixtures/captured/`. Until then the payload JSON layout in `wire.py`
is the spec's ⚠️UNVERIFIED best guess; the model semantics are unaffected.
