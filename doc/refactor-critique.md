# Refactor Red-Team — Challenging the Port Plan and the Protocol

Status: adversarial review of both the codebase (fresh pass, new findings
below) and of our own `rust-port-plan.md` / `cpp-code-audit.md`. Written
to be argued with. Where this document and the plan disagree, this
document is the challenge and the plan is the incumbent — resolve each
point explicitly rather than letting the plan win by default.

## 0. The premise is wrong: there is nothing here to "port"

Of 4,967 LOC: ~2,700 is the hand-rolled reactor (discarded by design),
~500 is the stats subsystem (dead weight, see §1.2), serialization glue
goes to serde, and the actual replicated-map + gossip + hooks logic is a
few hundred lines — **which contain the worst bugs in the codebase**
(dead merge guard, TTL-as-freshness, expiry-without-hooks, config wipe
race). A file-by-file "port" faithfully reproduces the ambiguity of code
that even its authors couldn't keep consistent.

The protocol exists nowhere except in this code and in the field. No
document says what merge is *supposed* to do — commit `db58e3d` proves
even the author's intent and the author's code diverged, unnoticed, for
over a year.

**Deliverable zero is therefore not `main.rs`; it is a 2–3 page protocol
spec** (wire format, handshake, merge semantics including the version
counter, expiry, hook contract) plus golden fixtures and property tests
extracted from the C++ binary. The Rust code then implements the spec,
not the C++ source. This inverts the plan's §3 mapping tables from
"porting guide" to "coverage checklist."

## 1. The protocol is a bigger liability than the implementation

The audit (B1–B3) blamed the implementation for slowness. Fresh eyes:
even a flawless implementation of this protocol degrades the mesh.

### 1.1 Full-state exchange, both directions, every interval

Every sync sends the client's **entire** state slice and receives the
server's **entire** merged state back — up to 1 MB each way, per peer,
per data type, per update interval, forever. No digests, no deltas, no
"nothing changed" fast path. On a wireless mesh, airtime is the scarcest
resource there is, and steady-state gossip of unchanged data competes
with user traffic on every link, scaling O(state × peers × types ×
frequency). This — not coroutine bugs — is the long-term scalability
wall. A wire-compatible Rust port changes none of it.

### 1.2 The stats subsystem doesn't earn its cost

The handshake is 3 messages instead of 1 (1.5 RTT extra per sync)
*specifically to estimate RTT*; the byte-count ACK exists to estimate
bandwidth. What that buys:

- Records timestamped with `steady_clock::time_since_epoch()` — i.e.
  **boot-relative ticks** — persisted to JSON. Meaningless across
  reboots, incomparable between nodes; the 30-minute age pruning
  compares fresh boot-relative times against stale ones.
- Read-modify-write of `network_statistics.json` on every sync, with
  file locking **OFF by default** (`SS_STAT_FILE_LOCKING`, CMake) —
  daemon and concurrent CLI syncs interleave and tear the file
  (matching the in-code "Discarding corrupted or empty statistics file"
  warning path).
- Bandwidth math that divides by a duration that floors to zero
  (audit C4).

**Open question that decides real scope: does anything in lime-packages
actually consume this file today?** If not, the honest move for v2 is
deleting the subsystem — and with it the extra handshake messages, the
ACK, `collectStat`, and the flock question. (Wire compat forces keeping
the *messages*; it does not force keeping the estimator or the file.)

### 1.3 Zero authentication, root-executed consequences

Any host that can reach TCP 3490 can inject arbitrary entries into any
data type — `bat-hosts`, DNS host lists, node metadata — mesh-wide
(gossip does the distribution for free), and hook scripts run as root
consuming that data. There is also no rate limiting and no per-entry
size cap below the global 1 MB, so a hostile or broken peer can push
1 MB per connection into RAM of every 64 MB router. Open community
networks may *choose* to trust the L2 domain — but that must be a
documented decision in the spec, not an omission. A port that silently
inherits it makes the omission permanent.

### 1.4 Expired entries never notify hooks

`bleachDataLoop` discards `bleach()`'s return value; `notifyHooks` fires
only on merge changes. When entries expire, downstream artifacts
(hosts files, bat-hosts, DNS) keep serving the dead data until the next
*positive* merge change for that type — indefinitely on a quiet type.
Expiry is a semantic change and must fire hooks; the spec must say so.

## 2. New implementation findings (this pass)

- **F1 — State-wipe race, fires every second.** `registerDataType`
  rewrites the config file in place with truncate (no temp+rename).
  The daemon calls `loadRegisteredTypes()` **every second, twice**
  (bleach loop + peer loop); on each parse it *erases the in-memory
  state of every type absent from the file*. A reader that catches the
  file mid-truncate wipes entire data types; they refill only via later
  gossip — or if the parse *fails*, config stays but the two parses per
  second continue. Fix (both languages): write-temp + `rename(2)`, parse
  only on mtime change, and never destroy state on a failed parse.
- **F2 — Handshake enforcement is real** (good news): version mismatch
  cleanly refuses the connection on both sides. This is the ready-made
  upgrade lever for any v2: bump `WIRE_PROTO_VERSION`, negotiate.
- **F3 — Discovery is all-or-nothing.** One malformed line from
  `shared-state-async-discover` (blank line, log noise on stdout) makes
  `getCandidatesNeighbours` abort the *entire* peer list — one bad line
  and the node syncs with nobody this round. Combined with ignoring the
  helper's exit status (audit C5), discovery reliability rests entirely
  on a shell script always producing perfect output.
- **F4 — Idle churn.** Two JSON config parses per second at idle
  (see F1), plus stats-file read-parse-rewrite per sync — on routers
  where `/tmp` is RAM-backed tmpfs, this is pure CPU/allocator churn.

## 3. Red-teaming our own plan

### 3.1 Gate 0 is missing and may be disqualifying: MIPS

The plan's §5 "verify feed maturity" is far too soft. Rust demoted all
`mips*-unknown-linux-*` targets to **Tier 3** in 2023 (Rust 1.72): no
prebuilt std, no CI, known codegen-bug exposure, nightly `-Z build-std`
or custom toolchains required. LibreMesh's dominant deployed hardware is
MIPS: ath79 (LibreRouter v1, TL-WDR3600 — big-endian MIPS 74Kc/24Kc) and
ramips/MT76xx (mipsel). If the fleet inventory is MIPS-heavy, the Rust
port as planned is high-risk **precisely for the devices that matter**.

This must become an explicit *Gate 0 — before any Rust code*:
inventory actual deployed boards (AlterMundi networks + LibreRouter v2
SoC), check current Rust tier status, and produce a working
`opkg`-installable hello-world on the *oldest* fielded board. If Gate 0
fails, the fallback is not "try harder": it is Track 1 below (C++
stabilization) as the deliverable, with Rust deferred to ARM-era
hardware.

### 3.2 The validation plan validates nothing

The plan leans on `tests/python-testclient/` as its regression suite.
Those tests **pass today** against a binary containing every bug in the
audit — serial daemon, UB, dead merge guard, state-wipe race. They are
happy-path smoke tests; a port that reproduced every bug would sail
through them. Actually required, and each is more work than the plan's
corresponding port milestone:

- Property tests on merge: convergence (all nodes reach identical state),
  idempotence, order-independence, version monotonicity — these would
  have caught C1 and C6 on day one.
- Multi-node simulation: N in-process nodes, injected packet loss,
  reordering, slow nodes, reboots (version-counter loss!), clock skew.
  The C6 corruption class is *only* visible here — it was found in the
  field because no such harness exists.
- Chaos/soak: hung peers mid-protocol, hooks that block/fail/daemonize,
  malformed discovery output, torn config writes.

### 3.3 "Drop-in wire compat" is a value trap

Strict compat locks in full-state exchange, the RTT-theater handshake,
no-auth, and JSON-with-C++-member-names — effectively forever, because
"protocol v2 later" becomes a migration nobody schedules. Meanwhile the
fleet already tolerates long mixed-version windows badly (#1105: x86
release builds were months stale). Since version enforcement already
exists and works (F2), the defensible scope is: **speak v1 for interop,
and structure the Rust internals so v2 (digest/delta sync, versioned
merge, size limits, optional transport auth) is a protocol module behind
the negotiated version — designed now, shipped when ready.** Plan §9's
"no protocol v2" non-goal should be reworded from "never" to "not in
v1-parity milestones."

### 3.4 Concurrency without backpressure trades one DoS for another

The plan's fix for B1 ("spawn per connection + timeouts") is necessary
but incomplete: unbounded accept-spawn × 1 MB buffers on a 64 MB router
converts the serial-availability failure into a memory-exhaustion
failure. The port needs: a max-concurrent-syncs semaphore, per-peer
connection limits, a global in-flight byte budget, and hard per-message
limits enforced *before* allocation.

### 3.5 Operational scope absent from the plan

- procd service file + respawn policy (the current daemon *exits* on
  many errors; supervision strategy is part of availability).
- Logging design: #1150 was a log-flood bug; the plan never mentions
  log levels/rate-limiting as a requirement.
- Canary rollout: package both implementations, per-node switch, revert
  path — mixed-fleet behavior asymmetry (Rust nodes faster) needs a
  documented observation period.
- Config atomicity fix (F1) must ship in the **C++ fleet too**, not
  wait for the port.

### 3.6 Sequencing: the port is not the urgent deliverable

The mesh is degraded *now*; Rust-to-parity is months. The honest
sequencing is two coordinated tracks:

- **Track 1 (days–weeks, on javierbrk's fork):** C++ stabilization —
  I/O timeouts, accept-error handling, version-counter merge
  (`merge_with_version`), config temp+rename, CLOEXEC, hostname cache,
  `max(1, µs)`. No reactor surgery (the UB fix — symmetric transfer —
  is small and contained in `task.hh`; worth attempting, but everything
  else on this list is safe without it). This de-risks the fleet
  immediately and makes the *target behavior observable in production*
  before Rust ships.
- **Track 2 (Rust):** Gate 0 → protocol spec + fixtures + simulation
  harness (new M-1) → then the plan's M0–M5, validated against the
  simulation, not just the Python scripts.

Track 1 is not wasted work for Track 2 — it is how the golden fixtures
and the merge semantics get field-validated before being spec-frozen.

## 4. Disposition table

| # | Challenge | Action required |
|---|---|---|
| 0 | Port the spec, not the code | Write protocol spec + fixtures as deliverable zero |
| 1.1 | Full-state gossip is the scalability wall | Design v2 delta/digest sync as a module; not in v1 scope |
| 1.2 | Stats subsystem dead weight | Verify consumers in lime-packages; if none, drop in v2 |
| 1.3 | No auth, root hooks | Document threat-model decision in spec |
| 1.4 | Expiry never fires hooks | Spec decision + fix in both tracks |
| F1 | Config wipe race (every second) | Fix in C++ now (temp+rename); same in Rust |
| F3 | Discovery all-or-nothing | Skip bad lines + check exit status, both tracks |
| 3.1 | MIPS Tier 3 may disqualify Rust | Gate 0: board inventory + toolchain proof on oldest board |
| 3.2 | Python tests validate nothing | Property tests + multi-node simulation harness (M-1) |
| 3.3 | Wire-compat value trap | v1 interop + v2-ready internals; reword §9 non-goal |
| 3.4 | Unbounded spawn = memory DoS | Backpressure limits in port design |
| 3.5 | No ops scope | procd, logging, canary, revert path into plan |
| 3.6 | Port is not the urgent fix | Two-track: C++ stabilization first, in coordination with javierbrk |
