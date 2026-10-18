"""Detect sandwiches in the ingested week, measure victim losses and replay each sandwich block through the
Chan-Wu-Shi mechanism.

usage: python scripts/analyze.py [DATADIR] [OUTDIR]     (defaults data/week, results)
Needs DATADIR/{swaps,liquidity,txs}.parquet, init_state.json and replay.parquet (scripts/replay.py).
Writes OUTDIR/sandwiches.csv, OUTDIR/victims.csv, OUTDIR/summary.json.
"""
import csv
import json
import os
import random
import statistics
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pyarrow.parquet as pq

from mev import calldata, data, detect, mechanism, rpc, v3
from mev.pool import FEE_PIPS, POOL, T_SWAP, WEEK

V2_SWAP = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
T_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
WETH_ADDR = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
USDT_ADDR = "0xdac17f958d2ee523a2206206994597c13d831ec7"
V4_SWAP = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"

ARGS = [x for x in sys.argv[1:] if not x.startswith("--")]
D = ARGS[0] if ARGS else "data/week"
OUT = ARGS[1] if len(ARGS) > 1 else "results"
DRAWS = 200
SEED = 20261017
F = Fraction(FEE_PIPS, 1_000_000)


# -- order specs ----------------------------------------------------------------------------------
def actual(s):
    z4o = s["amount0"] > 0
    paid, got = (s["amount0"], -s["amount1"]) if z4o else (s["amount1"], -s["amount0"])
    return z4o, paid, got


def pool_price_limit(z4o, rate_out_per_in):
    """Marginal pool price (raw token1/token0) at which the after-fee rate equals rate_out_per_in."""
    if z4o:      # receives token1 per token0 = P * (1 - f)
        return rate_out_per_in / (1 - F)
    return (1 - F) / rate_out_per_in  # pays P / (1 - f) token1 per token0


def specs_for_block(swaps, txs, modes, single_route=frozenset()):
    """One order per swap. Mode and limit from calldata where it decodes and agrees with the log;
    otherwise mode from the replay and limit = executed average price (a limit the trader accepted)."""
    by_tx = {}
    for s in swaps:
        by_tx.setdefault(s["tx"], []).append(s)
    out = []
    for tx, ss in by_tx.items():
        dec = [d for d in calldata.decode(txs[tx]["input"]) if not d["multihop"]]
        if not dec:
            dec = [d for d in calldata.decode_embedded(txs[tx]["input"]) if not d["multihop"]]
        use_dec = len(dec) == len(ss)
        if not use_dec and tx in single_route and len(ss) == 1:
            # aggregator or wallet whose whole route is this pool: its minimum output is this swap's bound
            z4o, paid, got = actual(ss[0])
            m = calldata.route_bound(txs[tx]["input"], paid, got, z4o)
            if m is not None and "exact_in" in modes[(ss[0]["block"], ss[0]["log_index"])].split(","):
                dec, use_dec = [dict(exact_in=True, amount=paid, bound=m, sqrt_limit=0, multihop=False,
                                     route=True)], True
        for k, s in enumerate(ss):
            z4o, paid, got = actual(s)
            m = modes[(s["block"], s["log_index"])]
            spec = dict(id=(s["block"], s["log_index"]), tx=tx, z4o=z4o, paid=paid, got=got, log_index=s["log_index"])
            d = dec[k] if use_dec else None
            if d is not None:
                amt = d["amount"] if d["amount"] is not None else (paid if d["exact_in"] else got)
                limited = "limit_in" in m.split(",")  # stopped early by a price limit
                if amt <= 0 or d["exact_in"] and amt != paid and not limited or not d["exact_in"] and amt != got:
                    d = None  # calldata does not describe this log; fall back
            if d is not None:
                # the order's amount is what was specified; a price-limited exact-in used only `paid`
                spec.update(exact_in=d["exact_in"], amount=paid if d["exact_in"] else got,
                            limit_src="calldata_route" if d.get("route") else "calldata")
                lim = None
                if d["bound"]:
                    spec["bound"] = d["bound"]
                    rate = Fraction(d["bound"], amt) if d["exact_in"] else Fraction(amt, d["bound"])
                    lim = pool_price_limit(z4o, rate)
                if d["sqrt_limit"]:
                    p = Fraction(d["sqrt_limit"] ** 2, 1 << 192)
                    lim = p if lim is None else (max(lim, p) if z4o else min(lim, p))
                if lim is None:
                    spec["limit_src"] = "calldata_none"
                spec["limit"] = lim
            else:
                ms = m.split(",")
                exact_in = "exact_in" in ms or "limit_in" in ms
                spec.update(exact_in=exact_in, amount=paid if exact_in else got,
                            limit=pool_price_limit(z4o, Fraction(got, paid)), limit_src="executed")
            out.append(spec)
    return out


def run_cf(snapshot, block_events, attacker_txs, specs_by_id):
    """Counterfactual (a): the block's events in order without the attacker legs, swaps re-run by amount."""
    p = snapshot.copy()
    res = {}
    for e in block_events:
        if e["kind"] != "swap":
            if e["tx"] in attacker_txs:
                continue  # no attack also means no attacker just-in-time liquidity
            p.modify(e["tick_lower"], e["tick_upper"], (1 if e["kind"] == "mint" else -1) * e["liq_amount"])
            continue
        sid = (e["block"], e["log_index"])
        if e["tx"] in attacker_txs or sid not in specs_by_id:
            continue
        sp = specs_by_id[sid]
        a0, a1 = p.swap(sp["z4o"], sp["amount"] if sp["exact_in"] else -sp["amount"])
        res[sid] = (a0, -a1) if sp["z4o"] else (a1, -a0)
    return res


def run_mech(snapshot, block_events, specs, order, unlimited=False, fee_phase1=False, unlimited_txs=(),
             drop_liquidity_txs=()):
    p = snapshot.copy()
    for e in block_events:
        if e["kind"] != "swap" and e["tx"] not in drop_liquidity_txs:
            p.modify(e["tick_lower"], e["tick_upper"], (1 if e["kind"] == "mint" else -1) * e["liq_amount"])
    orders = [dict(id=s["id"], z4o=s["z4o"], exact_in=s["exact_in"], amount=s["amount"],
                   limit=None if unlimited or s["tx"] in unlimited_txs else s["limit"])
              for s in (specs[i] for i in order)]
    return mechanism.clear(p, orders, fee_phase1=fee_phase1)


def gain(sp, r, base_paid, base_got):
    """Order's improvement over a baseline execution, on its filled fraction, in the calculated token.
    exact in: extra output; exact out: input saved. Returns (amount, token_is0)."""
    phi = Fraction(r["filled"])
    if sp["exact_in"]:
        return Fraction(r["got"]) - phi * base_got, not sp["z4o"]
    return phi * base_paid - Fraction(r["paid"]), sp["z4o"]


def usd(x, is0, r0):
    return float(Fraction(x) * (r0 if is0 else 1)) / 1e6


# -- chain metadata for attacker gas and builders ---------------------------------------------------
def cached(path, fn):
    if os.path.exists(path):
        return json.load(open(path))
    v = fn()
    json.dump(v, open(path, "w"))
    return v


def main():
    os.makedirs(OUT, exist_ok=True)
    events, txs, st = data.load(D)
    swaps = [e for e in events if e["kind"] == "swap" and (e["amount0"] or e["amount1"])]
    missing = {s["tx"] for s in swaps} - txs.keys()
    if "--partial" in sys.argv:  # debugging only: drop blocks with any missing tx
        bad = {s["block"] for s in swaps if s["tx"] in missing}
        swaps = [s for s in swaps if s["block"] not in bad]
        events = [e for e in events if e["block"] not in bad or e["kind"] != "swap"]
        missing = set()
    assert not missing, f"{len(missing)} swap txs missing from txs.parquet"
    modes = {(r["block"], r["log_index"]): r["modes"] for r in pq.read_table(os.path.join(D, "replay.parquet")).to_pylist()}
    assert all(modes.values()), "replay gate failed: run scripts/replay.py first"

    sws = detect.detect(swaps, txs, detect.QIN)
    strict_n = sum(1 for x in sws if x["strict"])
    blocks = sorted({x["block"] for x in sws})
    bset = set(blocks)
    print(f"sandwiches={len(sws)} strict={strict_n} victims={sum(len(x['victims']) for x in sws)} blocks={len(blocks)}")

    # receipts (gas) for attacker legs, headers for builders
    atk = sorted({x["front"] for x in sws} | {x["back"] for x in sws})
    rc = cached(os.path.join(D, "receipts.json"), lambda: dict(zip(atk, rpc.batch(
        [("eth_getTransactionReceipt", [h]) for h in atk], size=20))))
    hd = cached(os.path.join(D, "headers.json"), lambda: dict(zip(map(str, blocks), rpc.batch(
        [("eth_getBlockByNumber", [hex(b), False]) for b in blocks], size=20))))

    vtx = sorted({v for x in sws for v in x["victims"]})
    vrc = cached(os.path.join(D, "victim_receipts.json"), lambda: dict(zip(vtx, rpc.batch(
        [("eth_getTransactionReceipt", [h]) for h in vtx], size=20))))
    swap_topics = {T_SWAP, V2_SWAP, V4_SWAP}
    single_route = frozenset(h for h, r in vrc.items()
                             if {lg["address"].lower() for lg in r["logs"]
                                 if lg["topics"] and lg["topics"][0] in swap_topics} == {POOL})

    # walk the week; snapshot the pool at the start of each sandwich block
    pool = data.initial_pool(st)
    snaps, bev = {}, {}
    for e in events:
        b = e["block"]
        if b in bset and b not in snaps:
            snaps[b] = pool.copy()
        if b in bset:
            bev.setdefault(b, []).append(e)
        if e["kind"] == "swap":
            if e["amount0"] or e["amount1"]:
                pool.set_state((e["sqrtPriceX96"], e["tick"], e["liquidity"]))
        else:
            pool.modify(e["tick_lower"], e["tick_upper"], (1 if e["kind"] == "mint" else -1) * e["liq_amount"])

    rng = random.Random(SEED)
    vic_rows, sw_rows = [], []
    agg = {"static": [0.0] * DRAWS, "attacker_unlimited": [0.0] * DRAWS}  # recovered loss per draw, all victims
    for b in blocks:
        snap, be = snaps[b], bev[b]
        r0 = mechanism.r0_of(snap)
        bswaps = [e for e in be if e["kind"] == "swap" and (e["amount0"] or e["amount1"])]
        specs = specs_for_block(bswaps, txs, modes, single_route)
        sid = {s["id"]: s for s in specs}
        mine = [x for x in sws if x["block"] == b]
        atk_txs = {x["front"] for x in mine} | {x["back"] for x in mine}
        cf = run_cf(snap, be, atk_txs, sid)
        n = len(specs)
        arrival = list(range(n))
        draws = [rng.sample(range(n), n) for _ in range(DRAWS)]
        no_atk = [i for i in arrival if specs[i]["tx"] not in atk_txs]
        main = run_mech(snap, be, specs, arrival)
        runs = [run_mech(snap, be, specs, o) for o in draws]
        unl = run_mech(snap, be, specs, arrival, unlimited=True)
        fee1 = run_mech(snap, be, specs, arrival, fee_phase1=True)
        rm = run_mech(snap, be, specs, no_atk, drop_liquidity_txs=atk_txs)
        au = run_mech(snap, be, specs, arrival, unlimited_txs=atk_txs)
        au_runs = [run_mech(snap, be, specs, o, unlimited_txs=atk_txs) for o in draws]

        def atk_net(res, x):
            """Attacker's net over its legs in this pool at r0, in USD (positive = profit)."""
            tot = 0
            for s in specs:
                if s["tx"] in (x["front"], x["back"]):
                    rr = res[s["id"]]
                    tot += usd(rr["got"], not s["z4o"], r0) - usd(rr["paid"], s["z4o"], r0)
            return tot

        for x in mine:
            # (b) attacker's net token flow with the pool in both legs: swaps plus any just-in-time
            # liquidity added, removed and fees collected, from the receipts' ERC-20 Transfer logs
            act = 0
            for hh in (x["front"], x["back"]):
                for lg in rc[hh]["logs"]:
                    if not lg["topics"] or lg["topics"][0] != T_TRANSFER or len(lg["topics"]) < 3:
                        continue
                    tok = lg["address"].lower()
                    if tok not in (WETH_ADDR, USDT_ADDR):
                        continue
                    amt = int(lg["data"], 16)
                    src, dst = "0x" + lg["topics"][1][-40:], "0x" + lg["topics"][2][-40:]
                    sign = 1 if src == POOL else -1 if dst == POOL else 0
                    act += sign * usd(amt, tok == WETH_ADDR, r0)
            jit = any(e["kind"] != "swap" and e["tx"] in (x["front"], x["back"]) for e in be)
            gas = sum(int(rc[h]["gasUsed"], 16) * int(rc[h]["effectiveGasPrice"], 16) for h in (x["front"], x["back"]))
            gas_usd = gas * float(r0) / 1e6   # wei of ETH valued at the WETH price
            h = hd[str(b)]
            mech_runs = [atk_net(r, x) for r in runs + au_runs + [unl, fee1, au]]
            vloss = vprev = vdet = 0.0
            for vt in x["victims"]:
                vs = [s for s in specs if s["tx"] == vt]
                la = ga = gu = gf = gr = gau = 0.0
                gd = [0.0] * DRAWS
                gaud = [0.0] * DRAWS
                slack = 0.0
                fill = []
                for s in vs:
                    cp, cg = cf[s["id"]]
                    if s["exact_in"]:
                        la += usd(cg - s["got"], not s["z4o"], r0)
                    else:
                        la += usd(s["paid"] - cp, s["z4o"], r0)
                    g, is0 = gain(s, main[s["id"]], s["paid"], s["got"])
                    ga += usd(g, is0, r0)
                    fill.append(float(main[s["id"]]["filled"]))
                    for k, rr in enumerate(runs):
                        g2, _ = gain(s, rr[s["id"]], s["paid"], s["got"])
                        gd[k] += usd(g2, is0, r0)
                    gu += usd(gain(s, unl[s["id"]], s["paid"], s["got"])[0], is0, r0)
                    gf += usd(gain(s, fee1[s["id"]], s["paid"], s["got"])[0], is0, r0)
                    gr += usd(gain(s, rm[s["id"]], s["paid"], s["got"])[0], is0, r0)
                    gau += usd(gain(s, au[s["id"]], s["paid"], s["got"])[0], is0, r0)
                    for k, rr in enumerate(au_runs):
                        gaud[k] += usd(gain(s, rr[s["id"]], s["paid"], s["got"])[0], is0, r0)
                    if s.get("bound"):
                        # (c) slippage tolerance available to the attacker: no-attack result minus the bound
                        if s["exact_in"]:
                            slack += usd(cg - s["bound"], not s["z4o"], r0)
                        else:
                            slack += usd(s["bound"] - cp, s["z4o"], r0)
                srcs = sorted({s["limit_src"] for s in vs})
                for k in range(DRAWS):
                    agg["static"][k] += min(max(gd[k], 0), la) if la > 0 else 0
                    agg["attacker_unlimited"][k] += min(max(gaud[k], 0), la) if la > 0 else 0
                gd.sort()
                vloss += la
                vprev += min(max(ga, 0), la) if la > 0 else 0
                vdet += min(max(gr, 0), la) if la > 0 else 0
                vic_rows.append(dict(
                    block=b, victim_tx=vt, front=x["front"], back=x["back"], direction="sell WETH" if vs[0]["z4o"] else "buy WETH",
                    exact_in=all(s["exact_in"] for s in vs), limit_src="+".join(srcs),
                    victim_volume_usd=round(sum(usd(s["paid"], s["z4o"], r0) for s in vs), 2),
                    loss_a_usd=round(la, 4), slippage_slack_c_usd=round(slack, 4) if slack else "",
                    mech_gain_usd=round(ga, 4), mech_gain_p5=round(gd[int(0.05 * DRAWS)], 4),
                    mech_gain_p95=round(gd[int(0.95 * DRAWS) - 1], 4), mech_gain_mean=round(statistics.mean(gd), 4),
                    mech_gain_unlimited_usd=round(gu, 4), mech_gain_fee_phase1_usd=round(gf, 4),
                    mech_gain_attacker_removed_usd=round(gr, 4),
                    mech_gain_attacker_unlimited_usd=round(gau, 4),
                    mech_gain_attacker_unlimited_mean=round(statistics.mean(gaud), 4),
                    prevented_deterred_usd=round(min(max(gr, 0), la), 4) if la > 0 else 0.0,
                    prevented_static_arrival_usd=round(min(max(ga, 0), la), 4) if la > 0 else 0.0,
                    filled=round(min(fill), 4),
                    to=(txs[vt]["to"] or "").lower()))
            sw_rows.append(dict(
                block=b, front=x["front"], back=x["back"], n_victims=len(x["victims"]), attacker_eoa=x["attacker_eoa"],
                attacker_to=x["attacker_to"], ratio=round(x["ratio"], 5), strict=x["strict"],
                attacker_gross_b_usd=round(act, 4), jit_liquidity=jit, attacker_gas_usd=round(gas_usd, 4),
                attacker_net_of_gas_usd=round(act - gas_usd, 4), victim_loss_a_usd=round(vloss, 4),
                prevented_deterred_usd=round(vdet, 4), prevented_static_arrival_usd=round(vprev, 4),
                mech_attacker_net_usd=round(atk_net(main, x), 6),
                mech_attacker_net_max_all_runs=round(max(mech_runs), 6),
                mech_attacker_net_unlimited=round(atk_net(unl, x), 6),
                builder=h["miner"].lower(), extra_data=bytes.fromhex(h["extraData"][2:]).decode("utf8", "replace")[:32],
                base_fee_gwei=round(int(h["baseFeePerGas"], 16) / 1e9, 3)))

    for name, rows in (("sandwiches.csv", sw_rows), ("victims.csv", vic_rows)):
        with open(os.path.join(OUT, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    tot = lambda rows, k: sum(r[k] for r in rows if r[k] != "")
    loss = tot(vic_rows, "loss_a_usd")
    pos = [r for r in vic_rows if r["loss_a_usd"] > 0]
    def share(col):
        """Share of loss (a) recovered, each victim's recovery capped at its own loss."""
        return round(sum(min(max(r[col], 0), r["loss_a_usd"]) for r in pos) / loss, 4) if loss > 0 else None

    summary = dict(
        block_range=list(WEEK), rpc=rpc.ENDPOINTS[0], swaps=len(swaps), swap_txs=len({s["tx"] for s in swaps}),
        sandwiches=len(sw_rows), sandwiches_strict=strict_n, victims=len(vic_rows), victims_with_positive_loss=len(pos),
        victim_volume_usd=round(tot(vic_rows, "victim_volume_usd"), 2),
        loss_a_usd=round(loss, 2),
        attacker_gross_b_usd=round(tot(sw_rows, "attacker_gross_b_usd"), 2),
        attacker_gas_usd=round(tot(sw_rows, "attacker_gas_usd"), 2),
        slippage_slack_c_usd=round(tot(vic_rows, "slippage_slack_c_usd"), 2),
        victims_with_slack_c=sum(1 for r in vic_rows if r["slippage_slack_c_usd"] != ""),
        # mechanism: the attack itself
        mech_attacker_net_usd_arrival=round(tot(sw_rows, "mech_attacker_net_usd"), 2),
        mech_attacker_net_max_any_sandwich_any_run=max(r["mech_attacker_net_max_all_runs"] for r in sw_rows),
        # mechanism: victims
        prevented_share_deterred=share("mech_gain_attacker_removed_usd"),
        prevented_share_static_arrival=share("mech_gain_usd"),
        prevented_share_static_random_mean=share("mech_gain_mean"),
        prevented_share_static_random_p5=round(sorted(agg["static"])[int(0.05 * DRAWS)] / loss, 4),
        prevented_share_static_random_p95=round(sorted(agg["static"])[int(0.95 * DRAWS) - 1] / loss, 4),
        prevented_share_static_attacker_unlimited_arrival=share("mech_gain_attacker_unlimited_usd"),
        prevented_share_static_attacker_unlimited_random_mean=share("mech_gain_attacker_unlimited_mean"),
        prevented_share_static_attacker_unlimited_random_p5=round(
            sorted(agg["attacker_unlimited"])[int(0.05 * DRAWS)] / loss, 4),
        prevented_share_static_attacker_unlimited_random_p95=round(
            sorted(agg["attacker_unlimited"])[int(0.95 * DRAWS) - 1] / loss, 4),
        prevented_share_static_all_unlimited=share("mech_gain_unlimited_usd"),
        prevented_share_static_fee_phase1=share("mech_gain_fee_phase1_usd"),
        sandwiches_with_jit_liquidity=sum(1 for r in sw_rows if r["jit_liquidity"]),
        excess_deterred_usd=round(sum(max(r["mech_gain_attacker_removed_usd"] - max(r["loss_a_usd"], 0), 0)
                                      for r in vic_rows), 2),
        victims_limit_from_calldata=sum(1 for r in vic_rows if r["limit_src"].startswith("calldata")),
        victims_single_pool_route=len(single_route),
        victims_limit_attributable_decoded=sum(1 for r in vic_rows if r["limit_src"].startswith("calldata")),
        victims_min_fill_static_arrival=min(r["filled"] for r in vic_rows),
        draws=DRAWS, seed=SEED,
    )
    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
