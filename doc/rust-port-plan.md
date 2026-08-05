# Rust Port: Architecture Mapping & Refactor Plan

Status: research / planning — no Rust code written yet.
Scope: full rewrite (not FFI bridging) of the `shared-state-async` daemon,
preserving the existing wire protocol so it stays interoperable with any
C++ instances still deployed on the mesh during rollout.

## 1. Why a clean rewrite, not incremental FFI

The current design's core (`task.hh`, `io_context.*`, `awaitable_syscall.hh`)
is a hand-rolled stackless-coroutine epoll reactor. There is no clean seam to
bridge piecemeal into Rust futures — the reactor and the coroutine machinery
are the same ~800 lines and would have to be reimplemented as a unit either
way. At ~5k LOC total or ~1.6k LOC "actual" (`sharedstate.hh/.cc` +
`shared_state_cli.*`) once the reactor is a swapped-in async runtime,
a full rewrite is cheaper than maintaining a C++/Rust FFI boundary across an
epoll loop.

## 2. Target Rust dependency choices

| Concern | Current (C++) | Rust choice | Why |
|---|---|---|---|
| Async runtime / reactor | hand-rolled epoll + `task<T>` | `async-io` + `async-executor` (smol stack), single-threaded | Closest architectural match to a single-reactor daemon; far smaller binary/RAM than tokio, which this workload doesn't need (see below) |
| Subprocess + waitpid | `AsyncCommand` / `waitpid_operation.cc` | `async-process` (smol-family) — or raw `nix::sys::wait::waitpid` for 1:1 control | Async stdin/stdout + child reaping without pulling in tokio |
| JSON | rapidjson + `RsJson` wrapper | `serde_json` | Deletes the `RsJson`/`RsTypeSerializer` glue entirely; DOM-parse perf difference is irrelevant at this message size |
| sockaddr / socket utils | libretroshare `rsnet`/`rsnet_ss` | `socket2` (native `SockAddrStorage`) | Same low-level control, no vendored dependency |
| Stacktrace | vendored cpptrace | `std::backtrace` (stable) | Built into std, no extra dependency |
| Serialization framework | `RsSerializable` / `RsTypeSerializer` | `serde::{Serialize, Deserialize}` derives | Replaces hand-written `serial_process()` methods with derive macros |
| CLI arg parsing | hand-rolled in `shared_state_cli.cc` | `clap` (derive API) | — |
| Test harness | doctest + Python/shell test clients | `cargo test` + **keep** the existing Python/shell clients as black-box protocol tests | Wire protocol is unchanged, so these are free regression coverage |

**Runtime choice rationale**: this daemon runs one epoll loop with a handful
of sockets, subprocess pipes, and timers on routers with tens of MB of RAM.
Full tokio brings a scheduler and feature surface this doesn't use; the smol
stack (`async-io`/`async-executor`/`async-process`) mirrors the current
single-threaded reactor almost 1:1 at a much smaller footprint. io_uring
runtimes (monoio) are irrelevant — the I/O pattern (a handful of FDs) doesn't
benefit from it. Note the current code already requires kernel ≥ 5.3
(`pidfd_open` in `async_command.cc`), so kernel age is not the constraint;
binary size and RAM are.

**Subprocess semantics to preserve** (`src/async_command.cc`): command
strings are whitespace-tokenized and `execvp`'d directly — **no shell**.
`command.rs` must do split + `Command::args`, not `sh -c`, or hook and
discover invocation behavior changes. Child termination is awaited via
`pidfd_open` registered in epoll; if strict single-threadedness matters,
verify `async-process`'s reaping strategy on the pinned version (some
configurations spawn a helper thread) — the 1:1 alternative is `nix` +
pidfd wrapped in `Async<OwnedFd>`.

**Net effect of dependency swap**: dropping the vendored `libretroshare`
FetchContent (currently the biggest build-time/cross-compile cost in
`CMakeLists.txt`) plus `rapidjson`, replacing both with `serde_json` +
`socket2` + `base64`, removes essentially the entire external-dependency
surface.

## 3. File-by-file mapping

### Reactor core → replaced by runtime crate, not hand-ported

| Current file | LOC | Rust replacement |
|---|---|---|
| `include/task.hh` | 195 | `async fn` / `Future` (language + `async-executor`) — no custom coroutine type needed |
| `include/io_context.hh` + `src/io_context.cc` | 202+279 | `async-io`'s `Async<T>` reactor registration |
| `include/awaitable_syscall.hh` | 192 | absorbed into `async-io`'s poll/wake machinery |
| `include/accept_operation.hh` + `src/accept_operation.cc` | 43+51 | `Async<TcpListener>::accept()` |
| `include/connect_operation.hh` + `src/connect_operation.cc` | 45+105 | `Async<TcpStream>::connect()` |
| `include/read_operation.hh`/`.cc`, `recv_operation.*`, `send_operation.*`, `write_operation.*` | ~50 each | `AsyncRead`/`AsyncWrite` trait methods on `Async<T>` |
| `include/close_operation.hh` + `.cc` | 35+73 | `Drop` impl (RAII close, no explicit close-coroutine needed) |
| `include/waitpid_operation.hh` + `src/waitpid_operation.cc` | 46+73 | `async-process::Child::status()` |
| `include/epoll_events_to_string.hh` + `.cc` | 26+53 | debug-only; `bitflags`-derived `Debug` impl or drop entirely |

### File-descriptor / socket / command wrappers → thin adapter module

| Current file | LOC | Rust replacement |
|---|---|---|
| `include/async_file_descriptor.hh` + `src/async_file_descriptor.cc` | 144+29 | mostly unneeded — `async-io::Async<T>` owns readiness tracking; keep only if custom pending-op semantics are still needed for the socket protocol's request/response ordering |
| `include/async_socket.hh` + `src/async_socket.cc` | 95+217 | `net.rs`: thin wrapper over `async_io::Async<TcpStream>` / `Async<TcpListener>`, `socket2::SockAddr` for peer address handling |
| `include/async_command.hh` + `src/async_command.cc` | 132+285 | `command.rs`: wrapper over `async_process::Command` |
| `include/async_timer.hh` + `src/async_timer.cc` | 68+92 | `async_io::Timer` — no wrapper needed, used directly |

### Protocol / domain logic → ported logic, not architecture

| Current file | LOC | Rust replacement | Notes |
|---|---|---|---|
| `include/sharedstate.hh` + `src/sharedstate.cc` | 282+1106 | `sharedstate.rs` (or split: `protocol.rs`, `state.rs`, `stats.rs`) | Core of the actual port effort — merge/bleach/handshake/hooks logic, `serde`-derived `StateEntry`/`DataTypeConf`/`NetworkMessage`/`NetworkStats` |
| `include/shared_state_errors.hh` + `src/shared_state_errors.cc` | 68+24 | `error.rs` using `thiserror` | Replace `std::error_condition` bubbling with `Result<T, SharedStateError>` |
| `app/shared_state_cli.hh` + `app/shared_state_cli.cc` | 72+337 | `cli.rs` + `bin/shared-state-async.rs` | `clap`-derived subcommands matching the existing verbs exactly: `discover`, `dump`, `get`, `insert`, `peer`, `register`, `sync` (see `app/shared-state-async.cc`) |
| `app/shared-state-async.cc` | 153 | `main.rs` | Entry point, arg dispatch, executor setup |

### Build / packaging

| Current file | Rust replacement |
|---|---|
| `CMakeLists.txt` | `Cargo.toml` (workspace or single crate) |
| `doc/openwrtMakefile` | new OpenWrt package Makefile targeting a prebuilt static-musl binary (see §5) |
| `tests/CMakeLists.txt`, `tests/*.cc` (doctest) | `cargo test` unit tests for merge/bleach logic |
| `tests/python-testclient/*` | **kept as-is** — black-box protocol/regression tests against the new binary |

## 4. Target Rust crate layout

```
shared-state-async/
├── Cargo.toml
├── src/
│   ├── main.rs            # entry point, executor setup, arg dispatch
│   ├── cli.rs              # clap subcommands (discover/dump/get/insert/peer/register/sync)
│   ├── net.rs              # AsyncSocket/ListeningSocket/ConnectingSocket equivalents
│   ├── command.rs          # async subprocess exec + waitpid wrapper
│   ├── protocol.rs          # wire format: NetworkMessage encode/decode
│   ├── state.rs            # StateEntry, DataTypeConf, in-memory state map, merge, bleach
│   ├── stats.rs             # NetworkStats (RTT/bandwidth estimation)
│   ├── hooks.rs             # notifyHooks equivalent
│   └── error.rs             # SharedStateError (thiserror)
└── tests/
    └── protocol_interop.rs  # optional: rust-native protocol round-trip tests
                              # (kept alongside tests/python-testclient/ black-box tests)
```

## 5. OpenWrt cross-compilation approach

- `lang/rust` exists in the official `openwrt/packages` feed (merged 2023),
  confirmed working on x86_64/aarch64/armv7. MIPS/MIPSEL (some older
  LibreMesh hardware) had reported build issues in that feed's history —
  **verify current feed status against the actual target boards before
  committing to in-tree builds.**
- Preferred path (matches practice from comparable mesh-routing Rust
  projects): build a static **musl** binary outside the OpenWrt SDK
  (`rustup target add <target>-unknown-linux-musl` or the `cross` tool),
  then package just the resulting binary via a thin OpenWrt Makefile
  (replacing `doc/openwrtMakefile`'s CMake invocation with a "copy prebuilt
  binary" package). This avoids roughly doubling buildbot time by dragging
  the full `lang/rust` toolchain into the OpenWrt build.
- Decision needed before Phase 4 (below): confirm the actual deployed board
  architectures (ath79/MIPS vs newer ARM targets) to settle whether MIPS musl
  support is a blocking risk or a non-issue.

## 6. Phased refactor plan

**M0 — Scaffolding** (no protocol logic yet)
Cargo workspace, `error.rs`, pick and pin runtime crates (`async-io`,
`async-executor`, `async-process`, `socket2`, `serde`/`serde_json`), a
minimal `main.rs` that starts the executor and does nothing else. Exit
criteria: `cargo build` succeeds cross-compiled to at least one target arch.

**M1 — Reactor/net/command layer**
Implement `net.rs` (listening/connecting/accepting sockets) and `command.rs`
(subprocess exec + waitpid) on top of `async-io`/`async-process`. Exit
criteria: a toy echo-server binary using these modules passes a manual smoke
test.

**M2 — Wire protocol**
Port `NetworkMessage` framing (`protocol.rs`) and `serde`-derived
`StateEntry`/`DataTypeConf`/`NetworkStats`.

⚠️ **Interop-critical**: the payload JSON is produced by libretroshare's
`RsTypeSerializer` with keys equal to the C++ member names — `"mAuthor"`,
`"mTtl"`, `"mData"` — and the state slice is wrapped in an object whose outer
key is literally `"stateSlice"` (see the `fromStateSlice`/`toStateSlice`
comments in `src/sharedstate.cc` warning to keep the parameter name stable).
Plain serde derives produce different keys and no wrapper: the handshake
would succeed and merge would silently exchange nothing against C++ peers.
The Rust types need explicit `#[serde(rename = "...")]` attributes plus a
wrapper struct, driven by **golden payload fixtures captured from the C++
binary before any Rust encoder is written**.

Exit criteria: round-trip encode/decode tests pass against the captured C++
golden fixtures (not just Rust-to-Rust), and the new binary can complete a
handshake with itself.

**M3 — Domain logic**
Port `merge`, `bleach`, `notifyHooks`, `syncWithPeer`,
`handleReqSyncConnection`, `getCandidatesNeighbours`, stats collection
(`state.rs`, `stats.rs`, `hooks.rs`). Exit criteria: the existing
`tests/python-testclient/pythonTcpClient.py` and
`tests/samplestate.txt`/`runclientlocal.sh` scripts succeed unmodified
against the new binary.

**M4 — CLI parity**
Port `shared_state_cli.cc`'s subcommands via `clap`. Exit criteria: CLI
output byte-for-byte (or intentionally-noted-different) compared against the
C++ binary for `discover`, `dump`, `get`, `insert`, `peer`, `register`,
`sync`.

**M5 — Cross-compile & packaging**
Static musl builds per target architecture, OpenWrt package Makefile, deploy
to a test router (or the QEMU dev setup referenced in `doc/openwrt.txt`) and
verify interop with a live C++ instance on the same mesh segment during a
mixed-version window.

## 7. Validation strategy

The wire protocol is not changing, so the existing black-box test clients
under `tests/python-testclient/` are reusable as regression tests with zero
modification — run them against the Rust binary the same way they're run
against the C++ one today. This also gives a natural mixed-fleet interop
check: a Rust node and a C++ node on the same segment should sync
transparently, which matters for any staged rollout across a live mesh.

## 8. Open risks / decisions

- **MIPS/musl feed maturity** — needs a direct check against real target
  boards before Phase 5, not just the packages-feed PR history.
- **`AsyncFileDescriptor`'s pending-op queue** (`include/async_file_descriptor.hh:143`
  comment) encodes an assumption specific to this protocol ("read and write
  never happen at same time on the same socket"). Confirm this invariant
  still holds before relying on `async-io`'s default readiness handling to
  replace it outright — if it doesn't, `net.rs` needs to preserve equivalent
  ordering guarantees explicitly.
- **`SS_STAT_FILE_LOCKING` / `SHARED_STATE_STAT_FILE_LOCKING`** build option
  in `CMakeLists.txt` — confirm whether file-locking semantics for
  `network_statistics.json` need an explicit Rust equivalent (e.g. `fs2` /
  advisory locks) or whether the access pattern makes it unnecessary.
- **Hooks directory / config file paths** (`/usr/share/shared-state/hooks/`,
  `/tmp/shared-state/shared-state-async.conf`) are hardcoded `constexpr`
  paths — carry over as-is for interop, don't "improve" them mid-port.
- **`shared-state-async-discover` external helper** —
  `getCandidatesNeighbours()` execs this command (a separate LibreMesh
  script expected on `PATH` on the router) and parses one peer address per
  line from its stdout. This runtime dependency survives the port unchanged,
  and the M3 python-client exit criteria do **not** exercise it on a dev
  machine — it needs its own smoke test in M5 on-target.

## 9. Non-goals

- No protocol/wire-format changes in this port — goal is a drop-in
  replacement binary, not a protocol v2.
- No changes to hook script contract, config file format, or CLI subcommand
  names/semantics.
- No changes to the on-disk `/tmp/shared-state/network_statistics.json`
  format: it is written with wrapper key `"stats"` and the same
  member-name key convention as the wire payload, and is consumed by other
  LibreMesh tooling for bandwidth-aware routing decisions — it is an
  external contract, and gets a golden-fixture test like the wire format.
- No introduction of tokio or a multi-threaded scheduler unless a concrete
  performance need is identified post-port.
