"""Discrete-event multi-node simulator for shared-state gossip.

Models N nodes running the shared-state protocol over a topology graph,
with per-link latency, message loss, per-node bleach phase, node reboots
and publisher schedules. Every merge is instrumented so the metrics that
matter (spec §10, critique §3.2) fall out:

  ttl_divergence      max-min TTL per key across nodes (the MonteNet table)
  author_deficit      (max TTL anywhere) - (author's own TTL) for own key
  stale_regressions   an entry replaced by an OLDER generation payload
  self_regressions    ...at the author's own node (worst-case corruption)
  lockout_rejects     author's strictly-newer payload rejected by a peer
  propagation         publish -> full-mesh delay per generation
  aoi                 Age of Information of held payloads, sampled 1 Hz
  converged           value convergence after publishers stop

Payloads are (generation:int, blob:str); generation orders freshness
ground-truth, which the *protocol under test does not see* — that is the
whole point: we measure how well each merge strategy tracks a ground
truth it can only infer from TTL or version.
"""

import heapq
import random
from dataclasses import dataclass, field

import model
from model import Entry


@dataclass
class LinkSpec:
    latency_min: float = 0.05
    latency_max: float = 0.5
    loss: float = 0.0


@dataclass
class SimConfig:
    topology: dict = None            # node -> list of neighbors
    link: LinkSpec = field(default_factory=LinkSpec)
    strategy: str = "v1"
    bleach_ttl: int = 300
    update_interval: int = 30       # type config: publish + sync cadence
    sync_interval: float = 30.0
    publish_interval: float = 30.0
    duration: float = 600.0
    quiesce: float = 120.0           # extra sync-only time after publishers stop
    reboots: list = field(default_factory=list)   # [(time, node), ...]
    seed: int = 1


class Node:
    def __init__(self, name: str, cfg: SimConfig, rng: random.Random):
        self.name = name
        self.cfg = cfg
        self.state = {}                       # key -> Entry
        self.bleach_phase = rng.uniform(0.0, 1.0)
        self.last_bleach = None
        self.gen = 0                          # publisher generation counter
        self.first_seen = {}                  # (key, gen) -> time

    def publish(self, now: float):
        self.gen += 1
        model.author_insert(
            self.state, hostname=self.name, key=self.name,
            data=(self.gen, f"{self.name}/g{self.gen}"),
            strategy=self.cfg.strategy, bleach_ttl=self.cfg.bleach_ttl,
            update_interval=self.cfg.update_interval)

    def reboot(self):
        # /tmp state and version counters lost; measurements (gen) continue
        self.state = {}

    def snapshot(self) -> dict:
        return {k: e.clone() for k, e in self.state.items()}


class Simulation:
    def __init__(self, cfg: SimConfig):
        self.cfg = cfg
        self.rng = random.Random(cfg.seed)
        self.nodes = {n: Node(n, cfg, self.rng) for n in cfg.topology}
        self.now = 0.0
        self._q = []
        self._seq = 0
        self.publish_time = {}                # (author, gen) -> time
        self.metrics = {
            "stale_regressions": 0, "self_regressions": 0,
            "lockout_rejects": 0, "recoveries": 0, "ill_discards": 0,
            "regression_events": [],
            "ttl_divergence_samples": [], "author_deficit_samples": [],
            "aoi_samples": [], "propagation_delays": [],
            "gens_superseded_before_full": 0,
            "converged": None, "diverged_keys": [],
        }

    # -- event machinery ---------------------------------------------------
    def _push(self, t, fn, *args):
        self._seq += 1
        heapq.heappush(self._q, (t, self._seq, fn, args))

    # -- instrumentation ---------------------------------------------------
    def _held_gen(self, node: Node, key: str):
        e = node.state.get(key)
        return e.data[0] if e is not None and isinstance(e.data, tuple) else None

    def _note_first_seen(self, node: Node):
        for k, e in node.state.items():
            if isinstance(e.data, tuple):
                fk = (k, e.data[0])
                if fk not in node.first_seen:
                    node.first_seen[fk] = self.now

    def _instrumented_merge(self, dst: Node, slice_, src_name: str):
        before = {k: self._held_gen(dst, k) for k in slice_}
        res = model.merge(dst.state, slice_, remote=True,
                          hostname=dst.name, strategy=self.cfg.strategy)
        for kind, k in res.events:
            if kind == "recover":
                self.metrics["recoveries"] += 1
            if kind == "discard_ill":
                self.metrics["ill_discards"] += 1
            if kind in ("replace", "replace_tiebreak", "insert"):
                old_g, new_g = before.get(k), self._held_gen(dst, k)
                if old_g is not None and new_g is not None and new_g < old_g:
                    self.metrics["stale_regressions"] += 1
                    if len(self.metrics["regression_events"]) < 50:
                        self.metrics["regression_events"].append(
                            (round(self.now, 1), dst.name, k, old_g, new_g, kind))
                    if k == dst.name:
                        self.metrics["self_regressions"] += 1
            if kind in ("keep", "discard_ill") and k == src_name:
                # source is the author of key k: did it offer something newer?
                offered, held = slice_[k].data[0], self._held_gen(dst, k)
                if held is not None and offered > held:
                    self.metrics["lockout_rejects"] += 1
        self._note_first_seen(dst)
        return res

    # -- protocol events ---------------------------------------------------
    def _sync_session(self, client: Node, server: Node):
        """Spec §5: client slice -> server merge -> full response -> client merge."""
        lat = self.rng.uniform(self.cfg.link.latency_min, self.cfg.link.latency_max)
        slice_ = client.snapshot()
        if self.rng.random() < self.cfg.link.loss:
            return  # request leg lost: nothing happens anywhere
        self._push(self.now + lat, self._server_side, client.name, server.name,
                   slice_, lat)

    def _server_side(self, client_name, server_name, slice_, lat):
        server, client = self.nodes[server_name], self.nodes[client_name]
        self._instrumented_merge(server, slice_, client_name)
        response = server.snapshot()
        if self.rng.random() < self.cfg.link.loss:
            return  # response leg lost: server merged, client didn't (asymmetry)
        self._push(self.now + lat, self._client_side, client_name, server_name,
                   response)

    def _client_side(self, client_name, server_name, response):
        client = self.nodes[client_name]
        self._instrumented_merge(client, response, server_name)

    # -- periodic events ----------------------------------------------------
    def _bleach_tick(self, name):
        node = self.nodes[name]
        if node.last_bleach is None:
            node.last_bleach = self.now
        else:
            elapsed = int(self.now - node.last_bleach)
            if elapsed >= 1:
                model.bleach(node.state, elapsed)
                node.last_bleach += elapsed
        self._push(self.now + 1.0, self._bleach_tick, name)

    def _publish_tick(self, name, stop_at):
        if self.now >= stop_at:
            return
        node = self.nodes[name]
        node.publish(self.now)
        self.publish_time[(name, node.gen)] = self.now
        node.first_seen[(name, node.gen)] = self.now
        self._push(self.now + self.cfg.publish_interval, self._publish_tick,
                   name, stop_at)

    def _sync_tick(self, name, stop_at):
        if self.now >= stop_at:
            return
        node = self.nodes[name]
        for nb in self.cfg.topology[name]:
            self._sync_session(node, self.nodes[nb])
        self._push(self.now + self.cfg.sync_interval, self._sync_tick,
                   name, stop_at)

    def _sample_tick(self, stop_at):
        keys = set()
        for n in self.nodes.values():
            keys |= set(n.state.keys())
        for k in keys:
            holders = [n for n in self.nodes.values() if k in n.state]
            if len(holders) >= 2:
                ttls = [n.state[k].ttl for n in holders]
                self.metrics["ttl_divergence_samples"].append(max(ttls) - min(ttls))
                if k in self.nodes and k in self.nodes[k].state:
                    self.metrics["author_deficit_samples"].append(
                        max(ttls) - self.nodes[k].state[k].ttl)
            for n in holders:
                e = n.state[k]
                if isinstance(e.data, tuple):
                    pt = self.publish_time.get((e.author, e.data[0]))
                    if pt is not None:
                        self.metrics["aoi_samples"].append(self.now - pt)
        if self.now < stop_at:
            self._push(self.now + 1.0, self._sample_tick, stop_at)

    # -- run ----------------------------------------------------------------
    def run(self):
        cfg = self.cfg
        publish_stop = cfg.duration
        total = cfg.duration + cfg.quiesce
        for i, name in enumerate(self.nodes):
            node = self.nodes[name]
            self._push(node.bleach_phase, self._bleach_tick, name)
            self._push(0.1 + i * 0.01, self._publish_tick, name, publish_stop)
            jitter = self.rng.uniform(0, cfg.sync_interval)
            self._push(jitter, self._sync_tick, name, total)
        self._push(1.0, self._sample_tick, total)
        for t, name in cfg.reboots:
            self._push(t, lambda n=name: self.nodes[n].reboot())

        while self._q:
            t, _, fn, args = heapq.heappop(self._q)
            if t > total:
                break
            self.now = t
            fn(*args)

        self._finish(publish_stop)
        return self.metrics

    def _finish(self, publish_stop):
        # propagation delays for generations published while all nodes were up
        for (author, gen), t0 in self.publish_time.items():
            seen = [n.first_seen.get((author, gen)) for n in self.nodes.values()]
            if all(s is not None for s in seen):
                self.metrics["propagation_delays"].append(max(seen) - t0)
            else:
                nxt = self.publish_time.get((author, gen + 1))
                if nxt is not None:
                    self.metrics["gens_superseded_before_full"] += 1
        # value convergence after quiescence (compare payloads, not TTLs)
        diverged = []
        keys = set()
        for n in self.nodes.values():
            keys |= set(n.state.keys())
        for k in keys:
            vals = {repr(n.state[k].data) for n in self.nodes.values() if k in n.state}
            missing = [n.name for n in self.nodes.values() if k not in n.state]
            if len(vals) > 1 or missing:
                diverged.append((k, sorted(vals), missing))
        self.metrics["converged"] = not diverged
        self.metrics["diverged_keys"] = diverged


def summarize(m: dict) -> dict:
    def pct(xs, p):
        if not xs:
            return None
        xs = sorted(xs)
        return xs[min(len(xs) - 1, int(p * len(xs)))]
    return {
        "stale_regressions": m["stale_regressions"],
        "self_regressions": m["self_regressions"],
        "lockout_rejects": m["lockout_rejects"],
        "recoveries": m["recoveries"],
        "ill_discards": m["ill_discards"],
        "ttl_div_p95": pct(m["ttl_divergence_samples"], 0.95),
        "ttl_div_max": max(m["ttl_divergence_samples"], default=None),
        "author_deficit_p95": pct(m["author_deficit_samples"], 0.95),
        "aoi_p95": pct(m["aoi_samples"], 0.95),
        "prop_delay_p95": pct(m["propagation_delays"], 0.95),
        "gens_superseded_before_full": m["gens_superseded_before_full"],
        "converged": m["converged"],
        "n_diverged_keys": len(m["diverged_keys"]),
    }
