"""Same-block, single-pool sandwich detection (rule in docs/research.md section 4).

Each transaction is merged into one leg per block (net of all its swaps on the pool) and given one role.
A sandwich is a front-run F and back-run B in the same block, F before B, in opposite directions, by the same
attacker, with at least one victim between them trading in F's direction from a different sender.

Attacker identity: same sending EOA, or the same target contract with the back-run selling back
within +/-1% of what the front-run bought (filters shared public routers).
Amount match: back-run input / front-run output in [0.9, 1.1] (Qin et al.); "strict" is [0.99, 1.01].
"""
import collections

QIN = (0.9, 1.1)
STRICT = (0.99, 1.01)


def legs(swaps):
    """Merge one block's swaps by tx. swaps: dicts with tx, log_index, amount0, amount1 (pool view)."""
    by = collections.OrderedDict()
    for s in sorted(swaps, key=lambda s: s["log_index"]):
        lg = by.setdefault(s["tx"], dict(tx=s["tx"], first=s["log_index"], last=s["log_index"],
                                         amount0=0, amount1=0, n=0))
        lg["amount0"] += s["amount0"]
        lg["amount1"] += s["amount1"]
        lg["last"] = s["log_index"]
        lg["n"] += 1
    out = []
    for lg in by.values():
        if lg["amount0"] > 0 and lg["amount1"] < 0:
            lg.update(z4o=True, amt_in=lg["amount0"], amt_out=-lg["amount1"])
        elif lg["amount1"] > 0 and lg["amount0"] < 0:
            lg.update(z4o=False, amt_in=lg["amount1"], amt_out=-lg["amount0"])
        else:
            continue  # net zero or both-in (a tx that trades both ways nets out ambiguously)
        out.append(lg)
    return out


def detect_block(block, swaps, meta, window=QIN):
    """meta: tx hash -> (from, to). Returns sandwich dicts."""
    L = legs(swaps)
    used = set()
    found = []
    for i, f in enumerate(L):
        if f["tx"] in used:
            continue
        ff, ft = meta[f["tx"]]
        best = None
        for j in range(i + 2, len(L)):
            b = L[j]
            if b["tx"] in used or b["z4o"] == f["z4o"]:
                continue
            bf, bt = meta[b["tx"]]
            ratio = b["amt_in"] / f["amt_out"]
            if not (ff == bf or (ft == bt and STRICT[0] <= ratio <= STRICT[1])):
                continue
            if not window[0] <= ratio <= window[1]:
                continue
            vic = [v for v in L[i + 1:j] if v["z4o"] == f["z4o"] and v["tx"] not in used
                   and meta[v["tx"]][0] not in (ff, bf) and meta[v["tx"]][1] != ft]
            if not vic:
                continue
            if best is None or abs(ratio - 1) < abs(best[2] - 1):
                best = (b, vic, ratio)
        if best:
            b, vic, ratio = best
            used.update([f["tx"], b["tx"]] + [v["tx"] for v in vic])
            found.append(dict(block=block, front=f["tx"], back=b["tx"], victims=[v["tx"] for v in vic],
                              attacker_eoa=ff, attacker_to=ft, back_eoa=meta[b["tx"]][0], z4o=f["z4o"],
                              ratio=ratio, strict=STRICT[0] <= ratio <= STRICT[1],
                              front_leg=f, back_leg=b, victim_legs=vic))
    return found


def detect(swaps, txs, window=QIN):
    by = collections.defaultdict(list)
    for s in swaps:
        by[s["block"]].append(s)
    meta = {h: (t["from"].lower(), (t["to"] or "").lower()) for h, t in txs.items()}
    out = []
    for bn in sorted(by):
        out += detect_block(bn, by[bn], meta, window)
    return out
