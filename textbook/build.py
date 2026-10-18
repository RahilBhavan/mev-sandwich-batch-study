"""Build the study textbook as one self-contained HTML page in the rahil-design system.

usage: python textbook/build.py
reads results/*.csv, results/summary.json and textbook/toy.py; writes textbook/index.html
"""
import base64
import csv
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, ROOT]
import toy  # noqa: E402

DESIGN = os.path.expanduser("~/.t3/projects/main/.agents/skills/rahil-design")
E, U = toy.E, toy.U

S = json.load(open(os.path.join(ROOT, "results", "summary.json")))
SW = list(csv.DictReader(open(os.path.join(ROOT, "results", "sandwiches.csv"))))
VI = list(csv.DictReader(open(os.path.join(ROOT, "results", "victims.csv"))))
EX = toy.all_examples()


def usd(x, d=0):
    return f"${x:,.{d}f}"


def pct(x, d=0):
    return f"{100 * x:.{d}f}%"


def eth(x, d=4):
    return f"{float(x) / E:.{d}f}"


def usdc(x, d=2):
    return f"{float(x) / U:,.{d}f}"


# ---------------------------------------------------------------------------------------------- numbers
NA = EX["no_attack"]
SA = EX["sandwich"]
MF, MV, ML, AM = EX["mech_front_first"], EX["mech_victim_first"], EX["mech_executed_limits"], EX["avg_as_marginal"]
toy_loss_eth = NA["victim_eth"] - SA["victim_eth"]
toy_recovered_exec = (float(ML["victim_eth"]) - SA["victim_eth"]) / toy_loss_eth
per = {}
for y in VI:
    p = per.setdefault(y["front"], [0.0, 0.0])
    la = float(y["loss_a_usd"])
    p[0] += la
    p[1] += la - min(max(float(y["mech_gain_mean"]), 0), la)
ranked = sorted(per.values(), key=lambda p: -p[0])
cum_sq, cum_m = [0.0], [0.0]
for a, b in ranked:
    cum_sq.append(cum_sq[-1] + a)
    cum_m.append(cum_m[-1] + b)
top20 = cum_sq[20] / cum_sq[-1]
gas_share = S["attacker_gas_usd"] / S["attacker_gross_b_usd"]
jared = sum(1 for x in SW if x["attacker_eoa"] == "0xae2fc483527b8ef99eb5d9b44875f005ba1fae13")


# ---------------------------------------------------------------------------------------------- diagrams
def svg(w, h, label, body):
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(label)}">'
            '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="ink-fill"/></marker></defs>'
            f"{body}</svg>")


def fig(fid, label, body_svg, caption, illustration=False, title=None):
    tag = '<span class="illus">Illustration</span>' if illustration else ""
    if title:
        tag += f'<p class="figtitle">{title}</p>'
    return (f'<figure class="fig" id="{fid}">{tag}<div class="scroll" tabindex="0" role="group" '
            f'aria-label="{html.escape(label)} figure, scrolls sideways on small screens">{body_svg}</div>'
            '<p class="scroll-hint">Scroll sideways to see the whole figure.</p>'
            f"<figcaption>{caption}</figcaption></figure>")


def box(x, y, w, h, text, cls="box", sub=None):
    t = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" class="{cls}"/>'
    if sub:
        t += f'<text x="{x + w / 2}" y="{y + h / 2 - 4}" text-anchor="middle" class="lbl strong">{text}</text>'
        t += f'<text x="{x + w / 2}" y="{y + h / 2 + 15}" text-anchor="middle" class="lbl muted">{sub}</text>'
    else:
        t += f'<text x="{x + w / 2}" y="{y + h / 2 + 5}" text-anchor="middle" class="lbl strong">{text}</text>'
    return t


def arrow(x1, y1, x2, y2, label=None, lx=None, ly=None, anchor="middle"):
    t = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="edge" marker-end="url(#arr)"/>'
    if label:
        lx = (x1 + x2) / 2 if lx is None else lx
        ly = (y1 + y2) / 2 - 8 if ly is None else ly
        t += f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" class="lbl small muted">{label}</text>'
    return t


def d_tx_path():
    b = ""
    b += box(20, 120, 130, 56, "Wallet", sub="signs a swap")
    b += box(220, 40, 160, 56, "Public mempool", sub="anyone can see")
    b += box(220, 200, 160, 56, "Private RPC", sub="hidden until mined")
    b += box(450, 40, 150, 56, "Searcher bot", sub="sandwich, arbitrage")
    b += box(450, 200, 150, 56, "Builder", sub="orders the block")
    b += box(670, 200, 120, 56, "Proposer", sub="publishes")
    b += arrow(150, 140, 218, 72, "broadcast", 170, 92, "end")
    b += arrow(150, 156, 218, 226, "send privately", 200, 176, "start")
    b += arrow(380, 68, 448, 68, "sees tx")
    b += arrow(525, 96, 525, 198, "bundle + tip", 535, 152, "start")
    b += arrow(380, 228, 448, 228, "tx")
    b += arrow(600, 228, 668, 228, "best block")
    # block slots
    b += '<text x="450" y="300" class="lbl small muted">Block order (one bundle)</text>'
    for i, (t, c) in enumerate((("front-run", "hl"), ("victim", "box"), ("back-run", "hl"))):
        b += box(450 + i * 116, 310, 108, 36, t, cls=c)
    return svg(820, 360, "A swap goes from a wallet through the public mempool or a private RPC to a builder, "
               "who can place a searcher's front-run and back-run around it", b)


def scale(v, a, b, c, d):
    return c + (v - a) * (d - c) / (b - a)


def d_curve():
    k = 100 * 200_000
    x0, x1 = 60, 140
    W, H, L, R, T, B = 820, 380, 80, 760, 30, 320
    pts = []
    for i in range(81):
        x = x0 + (x1 - x0) * i / 80
        pts.append((scale(x, x0, x1, L, R), scale(k / x, k / x1, k / x0, B, T)))
    path = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    xa, ya = 100, 200_000
    xb = NA["victim_eth"] / E
    xb = 100 - xb
    yb = 220_000
    pa = (scale(xa, x0, x1, L, R), scale(ya, k / x1, k / x0, B, T))
    pb = (scale(xb, x0, x1, L, R), scale(yb, k / x1, k / x0, B, T))
    b = f'<line x1="{L}" y1="{B}" x2="{R}" y2="{B}" class="axis"/><line x1="{L}" y1="{B}" x2="{L}" y2="{T}" class="axis"/>'
    b += f'<path d="{path}" class="curve"/>'
    b += f'<line x1="{pa[0]}" y1="{pa[1]}" x2="{pb[0]}" y2="{pb[1]}" class="edge" marker-end="url(#arr)"/>'
    b += f'<circle cx="{pa[0]}" cy="{pa[1]}" r="7" class="dot"/><circle cx="{pb[0]}" cy="{pb[1]}" r="8" class="dot hl"/>'
    b += f'<text x="{pa[0] + 4}" y="{pa[1] + 34}" text-anchor="end" class="lbl">Before: 100 ETH, 200,000 USDC</text>'
    b += f'<text x="{pa[0] + 4}" y="{pa[1] + 54}" text-anchor="end" class="lbl muted">price 2,000 USDC per ETH</text>'
    b += f'<text x="{pb[0] + 16}" y="{pb[1] - 24}" class="lbl">After: {xb:.2f} ETH, 220,000 USDC</text>'
    b += f'<text x="{pb[0] + 16}" y="{pb[1] - 4}" class="lbl muted">price {NA["price_after"]:,.0f}; buyer got {eth(NA["victim_eth"], 2)} ETH</text>'
    b += f'<text x="{(L + R) / 2}" y="{B + 40}" text-anchor="middle" class="lbl muted">ETH in the pool (60 to 140)</text>'
    b += f'<text x="{L - 12}" y="{T + 4}" text-anchor="end" class="lbl small muted">USDC</text>'
    b += f'<text x="{L + 70}" y="{T + 10}" class="lbl small muted">x × y = 20,000,000</text>'
    return svg(W, H, "A buy of 20,000 USDC moves the pool along the curve x times y equals k, from 100 ETH to about 90.9 ETH, "
               "and raises the price from 2,000 to 2,420", b)


def d_ticks():
    W, H = 820, 330
    ranges = [(80, 200, 60), (200, 330, 150), (330, 470, 230), (470, 560, 150), (560, 700, 70), (700, 760, 30)]
    b = f'<line x1="70" y1="250" x2="770" y2="250" class="axis"/>'
    for x1, x2, h in ranges:
        b += f'<rect x="{x1}" y="{250 - h}" width="{x2 - x1}" height="{h}" class="liq"/>'
    b += '<rect x="330" y="20" width="140" height="230" class="liq hlrect"/>'
    b += '<line x1="400" y1="10" x2="400" y2="262" class="edge"/>'
    b += '<text x="400" y="282" text-anchor="middle" class="lbl strong">current price</text>'
    b += arrow(410, 70, 545, 70, "a buy pushes price right", 552, 75, "start")
    b += '<text x="476" y="302" text-anchor="start" class="lbl small muted">tick boundary: liquidity drops, price moves faster</text>'
    b += '<line x1="470" y1="250" x2="470" y2="284" class="thin"/>'
    b += '<text x="72" y="320" class="lbl small muted">lower price  ←  price, in ticks of 0.01% each  →  higher price</text>'
    b += '<text x="80" y="40" class="lbl small muted">active liquidity</text>'
    return svg(W, H, "Uniswap v3 liquidity sits in price ranges. A buy moves the price right; when it crosses a range "
               "boundary the active liquidity changes", b)


def d_price_path():
    W, H, L, R, T, B = 820, 360, 90, 700, 30, 290
    lo, hi = 1950, 2550
    steps = SA["path"]
    xs = [L + i * (R - L) / 3 for i in range(4)]
    ys = [scale(p, lo, hi, B, T) for _, p in steps]
    b = f'<line x1="{L}" y1="{B}" x2="{R}" y2="{B}" class="axis"/>'
    for v in (2000, 2200, 2400):
        y = scale(v, lo, hi, B, T)
        b += f'<text x="{L - 10}" y="{y + 5}" text-anchor="end" class="lbl small muted">{v:,}</text>'
        b += f'<line x1="{L - 4}" y1="{y}" x2="{L}" y2="{y}" class="thin"/>'
    path = f"M{xs[0]},{ys[0]}"
    for i in range(1, 4):
        path += f" H{xs[i]} V{ys[i]}"
    b += f'<path d="{path}" class="curve thick"/>'
    na_y = scale(NA["price_after"], lo, hi, B, T)
    b += f'<path d="M{xs[0]},{ys[0]} H{xs[2]} V{na_y}" class="curve dash"/>'
    b += f'<text x="{xs[2] - 8}" y="{na_y + 22}" text-anchor="end" class="lbl small muted">no attack: victim alone ends at {NA["price_after"]:,.0f}</text>'
    labels = ["start", f"front-run buys {eth(SA['front_eth'], 2)} ETH", "victim buys", f"back-run sells {eth(SA['front_eth'], 2)} ETH"]
    for i, ((_, p), lab) in enumerate(zip(steps, labels)):
        cls = "dot hl" if i in (1, 3) else "dot"
        b += f'<circle cx="{xs[i]}" cy="{ys[i]}" r="7" class="{cls}"/>'
        b += f'<text x="{xs[i]}" y="{B + 26}" text-anchor="middle" class="lbl small">{lab}</text>'
        b += f'<text x="{xs[i] + 10}" y="{ys[i] - 10}" class="lbl small strong">{p:,.0f}</text>'
    b += f'<text x="{L - 10}" y="{T - 8}" text-anchor="end" class="lbl small muted">USDC/ETH</text>'
    return svg(W, H, f"Price path in the toy sandwich: 2,000 at start, {steps[1][1]:,.0f} after the front-run, "
               f"{steps[2][1]:,.0f} after the victim, {steps[3][1]:,.0f} after the back-run", b)


def d_detect():
    W, H = 820, 300
    rows = [("0", "arbitrage bot", "sells ETH", "box"), ("1", "bot 0x1f2f…", "buys ETH", "hl"),
            ("2", "Universal Router", "buys ETH", "box"), ("3", "bot 0x1f2f…", "sells ETH", "hl"),
            ("4", "1inch router", "sells ETH", "box")]
    b = ""
    for i, (pos, who, what, c) in enumerate(rows):
        y = 20 + i * 52
        b += box(20, y, 360, 42, f"position {pos}: {who}, {what}", cls=c)
    b += '<path d="M390,61 C460,61 460,165 390,165" class="edge" marker-end="url(#arr)"/>'
    b += '<text x="470" y="100" class="lbl small">same sender, opposite directions</text>'
    b += '<text x="470" y="120" class="lbl small">back-run sells 90–110% of what the front-run bought</text>'
    b += '<path d="M390,113 L450,113" class="edge"/>'
    b += '<text x="470" y="150" class="lbl small">victim between them, same direction as the front-run,</text>'
    b += '<text x="470" y="170" class="lbl small">different sender and contract</text>'
    b += '<text x="470" y="220" class="lbl small muted">positions 0 and 4 play no role</text>'
    return svg(W, H, "Detection reads one block's swaps on the pool in order and looks for a front-run and back-run "
               "by the same attacker around a victim trading in the front-run's direction", b)


def d_counterfactual():
    W, H = 820, 300
    b = '<text x="20" y="30" class="lbl strong">Actual block</text>'
    b += box(20, 44, 130, 40, "front-run", cls="hl") + box(160, 44, 130, 40, "victim") + box(300, 44, 130, 40, "back-run", cls="hl")
    b += f'<text x="450" y="70" class="lbl">victim gets {eth(SA["victim_eth"], 4)} ETH</text>'
    b += '<text x="20" y="130" class="lbl strong">Replay without the attacker</text>'
    b += box(160, 144, 130, 40, "victim")
    b += f'<text x="450" y="170" class="lbl">victim gets {eth(NA["victim_eth"], 4)} ETH</text>'
    b += f'<line x1="440" y1="196" x2="800" y2="196" class="thin"/>'
    b += f'<text x="450" y="222" class="lbl strong">loss (a) = {eth(toy_loss_eth, 4)} ETH</text>'
    b += (f'<text x="450" y="248" class="lbl small muted">(c) tolerance = {eth(NA["victim_eth"], 2)} − minimum '
          f'{eth(toy.VICTIM_MIN, 1)} = {eth(NA["victim_eth"] - toy.VICTIM_MIN, 4)} ETH; the attack used all of it</text>')
    return svg(W, H, "Loss (a) is the difference between what the victim got in the real block and what an exact replay "
               "without the attacker gives", b)


def d_models():
    W, H = 820, 260
    b = '<text x="20" y="28" class="lbl strong">Plain model (Ethereum today)</text>'
    b += '<text x="430" y="28" class="lbl strong">Weak fair-sequencing model</text>'
    for i, t in enumerate(("block producer picks the order", "can insert its own orders", "can drop others' orders",
                           "sees every order first")):
        b += f'<text x="20" y="{70 + i * 34}" class="lbl">• {t}</text>'
    for i, t in enumerate(("order fixed by arrival time", "can insert orders, but only later", "cannot drop others' orders",
                           "can still see orders and race them")):
        b += f'<text x="430" y="{70 + i * 34}" class="lbl">• {t}</text>'
    b += '<line x1="410" y1="10" x2="410" y2="200" class="thin"/>'
    b += '<rect x="20" y="214" width="380" height="34" rx="6" class="box"/>'
    b += '<text x="210" y="236" text-anchor="middle" class="lbl small">mechanism gives: arbitrage resilience</text>'
    b += '<rect x="430" y="214" width="370" height="34" rx="6" class="hl"/>'
    b += '<text x="615" y="236" text-anchor="middle" class="lbl small strong">mechanism gives: full incentive compatibility</text>'
    return svg(W, H, "In the plain model the mechanism guarantees arbitrage resilience; with weak fair sequencing it is "
               "also incentive compatible", b)


def d_mechanism():
    """Two-phase clearing of the toy block, front-run first. Sizes in ETH at r0 = 2,000."""
    W, H = 820, 340
    r0 = 2000
    f_sz = SA["front_in"] / U / r0
    v_sz = toy.VICTIM_IN / U / r0
    b_sz = SA["front_eth"] / E
    L, sc = 150, 54  # px per ETH
    xb = L + b_sz * sc
    xf = L + f_sz * sc
    xe = L + (f_sz + v_sz) * sc
    b = '<text x="20" y="62" class="lbl strong">Buy ETH</text><text x="20" y="80" class="lbl small muted">dominant side</text>'
    b += '<text x="20" y="182" class="lbl strong">Sell ETH</text><text x="20" y="200" class="lbl small muted">minority side</text>'
    b += f'<rect x="{L}" y="44" width="{f_sz * sc:.1f}" height="44" class="hl step s3"/>'
    b += f'<rect x="{xf:.1f}" y="44" width="{v_sz * sc:.1f}" height="44" class="box step s4"/>'
    b += f'<text x="{L + 6}" y="30" class="lbl small">front-run {f_sz:.2f}</text>'
    b += f'<text x="{xf + 10:.1f}" y="72" class="lbl small">victim {v_sz:.2f}</text>'
    b += f'<rect x="{L}" y="164" width="{b_sz * sc:.1f}" height="44" class="hl step s3"/>'
    b += f'<text x="{L + 6}" y="232" class="lbl small">back-run {b_sz:.2f}</text>'
    b += f'<line x1="{xb:.1f}" y1="36" x2="{xb:.1f}" y2="216" class="edge dashline"/>'
    # brackets under the buy side
    b += f'<path d="M{L},100 v8 H{xb:.1f} v-8" class="edge"/>'
    b += f'<path d="M{xb + 4:.1f},100 v8 H{xe:.1f} v-8" class="edge"/>'
    b += f'<text x="{L}" y="130" class="lbl small strong">phase 1</text>'
    b += f'<text x="{L}" y="148" class="lbl small muted">at r0</text>'
    b += f'<text x="{(xb + xe) / 2:.1f}" y="130" text-anchor="middle" class="lbl small strong">phase 2: {f_sz - b_sz + v_sz:.2f} ETH on the curve, one order at a time</text>'
    b += f'<text x="{xb + 12:.1f}" y="192" class="lbl small">all {b_sz:.2f} ETH sold at r0 = 2,000; the pool does not move</text>'
    b += (f'<text x="20" y="290" class="lbl small muted">Sizes in ETH at the start-of-block price r0. '
          f'Orders whose limit is worse than r0 are dropped before this step.</text>')
    b += f'<text x="20" y="314" class="lbl small muted">Front-run first in tie-break order; attacker legs have no limit.</text>'
    return svg(W, H, "The back-run's sell is matched against the front-run at the starting price, so the front-run "
               "barely moves the pool and the victim trades near the no-attack price", b)


def d_scenarios():
    rows = [("No attack", NA["victim_eth"], None, False),
            ("Continuous: sandwiched", SA["victim_eth"], SA["attacker_profit_usdc"], True),
            ("Mechanism, front-run first", MF["victim_eth"], MF["attacker_net_usdc"], False),
            ("Mechanism, victim first", MV["victim_eth"], MV["attacker_net_usdc"], False),
            ("Mechanism, attacker legs limited", ML["victim_eth"], ML["attacker_net_usdc"], False)]
    W, H, L, R = 820, 310, 280, 590
    lo, hi = 8.6, 9.5
    b = ""
    for v in (8.6, 8.8, 9.0, 9.2, 9.4):
        x = scale(v, lo, hi, L, R)
        b += f'<line x1="{x}" y1="40" x2="{x}" y2="260" class="grid"/>'
        b += f'<text x="{x}" y="280" text-anchor="middle" class="lbl small muted">{v:.1f}</text>'
    b += f'<text x="{(L + R) / 2}" y="302" text-anchor="middle" class="lbl small muted">ETH the victim receives (axis starts at 8.6)</text>'
    b += '<text x="670" y="24" text-anchor="end" class="lbl small muted">victim, ETH</text>'
    b += '<text x="800" y="24" text-anchor="end" class="lbl small muted">attacker, USDC</text>'
    for i, (name, ve, an, hl) in enumerate(rows):
        y = 60 + i * 44
        x = scale(float(ve) / E, lo, hi, L, R)
        b += f'<text x="{L - 16}" y="{y + 5}" text-anchor="end" class="lbl small{" strong" if hl else ""}">{name}</text>'
        b += f'<circle cx="{x:.1f}" cy="{y}" r="8" class="dot{" hl" if hl else ""}"/>'
        b += f'<text x="670" y="{y + 5}" text-anchor="end" class="lbl small">{float(ve) / E:.2f}</text>'
        if an is not None:
            b += f'<text x="800" y="{y + 5}" text-anchor="end" class="lbl small">{float(an) / U:+,.2f}</text>'
    return svg(W, H, "Victim's ETH and attacker's net in five versions of the same toy block", b)


def d_trilemma():
    W, H = 820, 330
    A, B_, C = (410, 40), (130, 270), (690, 270)
    b = f'<path d="M{A[0]},{A[1]} L{B_[0]},{B_[1]} L{C[0]},{C[1]} Z" class="tri"/>'
    for (x, y), t in ((A, "IC"), (B_, "wLE"), (C, "UP")):
        b += f'<circle cx="{x}" cy="{y}" r="30" class="hl"/><text x="{x}" y="{y + 7}" text-anchor="middle" class="lbl strong">{t}</text>'
    b += '<text x="230" y="140" text-anchor="end" class="lbl small strong">Chan–Wu–Shi</text>'
    b += '<text x="230" y="160" text-anchor="end" class="lbl small muted">(fair sequencing)</text>'
    b += '<text x="590" y="140" class="lbl small strong">Li–Shi–Zhang Mechanism 1</text>'
    b += '<text x="590" y="160" class="lbl small muted">(very inefficient)</text>'
    b += '<text x="410" y="300" text-anchor="middle" class="lbl small strong">uniform-price batch clearing</text>'
    b += '<text x="410" y="320" text-anchor="middle" class="lbl small muted">(not incentive compatible)</text>'
    return svg(W, H, "Any two of incentive compatibility, weak local efficiency and uniform pricing are possible; "
               "all three are not", b)


def d_call_market():
    W, H = 820, 280
    arrivals = [60, 130, 150, 160, 290, 330, 470, 520, 540]
    b = '<text x="20" y="28" class="lbl strong">Continuous: each order trades on arrival</text>'
    b += '<line x1="40" y1="70" x2="780" y2="70" class="axis"/>'
    for t in arrivals:
        b += f'<line x1="{40 + t * 1.3}" y1="56" x2="{40 + t * 1.3}" y2="84" class="tickline"/>'
    b += '<text x="40" y="110" class="lbl small muted">who arrives a microsecond earlier trades first; ordering is worth money</text>'
    b += '<text x="20" y="160" class="lbl strong">Batch (call market, or one block): collect, then clear together</text>'
    b += '<line x1="40" y1="200" x2="780" y2="200" class="axis"/>'
    for i, (a, z) in enumerate(((0, 200), (200, 400), (400, 570))):
        b += f'<rect x="{40 + a * 1.3}" y="182" width="{(z - a) * 1.3 - 6}" height="36" rx="6" class="box"/>'
    for t in arrivals:
        b += f'<line x1="{40 + t * 1.3}" y1="188" x2="{40 + t * 1.3}" y2="212" class="tickline"/>'
    b += '<text x="40" y="250" class="lbl small muted">inside one batch, arriving earlier does not get a better price</text>'
    return svg(W, H, "Continuous markets reward speed; a batch clears everything in an interval together", b)


def d_results():
    n = len(ranked)
    W, H, L, R, T, B = 820, 390, 90, 560, 30, 320
    top = cum_sq[-1] * 1.04

    def pts(c):
        s = f"M{L},{B}"
        for i, v in enumerate(c[1:], 1):
            s += f" H{scale(i, 0, n, L, R):.1f} V{scale(v, 0, top, B, T):.1f}"
        return s
    b = f'<line x1="{L}" y1="{B}" x2="{R}" y2="{B}" class="axis"/><line x1="{L}" y1="{B}" x2="{L}" y2="{T}" class="axis"/>'
    for v in (0, 4000, 8000, 12000):
        y = scale(v, 0, top, B, T)
        b += f'<text x="{L - 10}" y="{y + 5}" text-anchor="end" class="lbl mid muted">{"$0" if v == 0 else f"${v // 1000}k"}</text>'
    for v in (0, 50, 100, 150, 200):
        b += f'<text x="{scale(v, 0, n, L, R)}" y="{B + 22}" text-anchor="middle" class="lbl mid muted">{v}</text>'
    b += f'<text x="{(L + R) / 2}" y="{B + 50}" text-anchor="middle" class="lbl mid muted">sandwiches, ranked by victim loss (n = {n})</text>'
    b += f'<path d="{pts(cum_sq)}" class="curve gray"/>'
    b += f'<path d="{pts(cum_m)}" class="curve thick"/>'
    b += f'<line x1="{L}" y1="{B - 1}" x2="{R}" y2="{B - 1}" class="curve dash"/>'
    ys, ym = scale(cum_sq[-1], 0, top, B, T), scale(cum_m[-1], 0, top, B, T)
    b += f'<circle cx="{R}" cy="{ym}" r="7" class="dot hl"/>'
    b += f'<text x="{R + 14}" y="{ys + 5}" class="lbl big">Status quo {usd(cum_sq[-1])}</text>'
    b += f'<text x="{R + 14}" y="{ym - 6}" class="lbl big strong">Same orders,</text>'
    b += f'<text x="{R + 14}" y="{ym + 14}" class="lbl big strong">per-block clearing {usd(cum_m[-1])}</text>'
    b += f'<text x="{R + 14}" y="{B + 5}" class="lbl mid muted">Attackers stop ≈ $0</text>'
    return svg(W, H, f"Cumulative victim loss over {n} sandwiches: {usd(cum_sq[-1])} in the status quo and "
               f"{usd(cum_m[-1])} with the same orders under per-block clearing", b)


# ---------------------------------------------------------------------------------------------- content
def check(*qa):
    items = "".join(f"<li><details><summary>{q}</summary><p>{a}</p></details></li>" for q, a in qa)
    return f'<section class="check"><h3>Check yourself</h3><ol>{items}</ol></section>'


def breath(text):
    return f'<p class="breath"><span>Say it in one breath</span>{text}</p>'


def why(text):
    return f'<p class="why"><span>Why you need this</span>{text}</p>'


CH = []


def chapter(cid, num, title, body):
    CH.append((cid, num, title, body))


chapter("start", "0", "The study on one page", f"""
{why("Everything else in this book supports the five sentences below. Read them first, then use the chapters to make each one yours.")}
<ol class="claims">
<li>In one week (5–11 October 2026) Uniswap v3's WETH/USDT 0.01% pool had {S['swaps']:,} swaps and <strong>{S['sandwiches']} sandwich attacks</strong> on {S['victims']} traders.</li>
<li>The victims lost <strong>{usd(S['loss_a_usd'])}</strong> compared with an exact replay of the same block without the attacker.</li>
<li>Where the victim's minimum output could be read, attackers took <strong>98%</strong> of the slippage the victim allowed.</li>
<li>Under Ke Wu's per-block two-phase mechanism (Chan, Wu &amp; Shi, AFT 2025), <strong>no attack makes money</strong> in any run.</li>
<li>With the same orders replayed, victims keep <strong>{pct(S['prevented_share_static_random_mean'])}</strong> of their loss on average ({pct(S['prevented_share_static_arrival'])}–{pct(S['prevented_share_static_attacker_unlimited_random_p95'])} across variants), and about 100% if attackers stop because the attack no longer pays.</li>
</ol>
<h3>Reading map</h3>
<p>Chapters 1–4 are the market: blocks, AMMs, Uniswap v3 and the attack itself. Chapters 5–6 are the measurement: how a sandwich is found and how a loss is defined. Chapters 7–9 are the theory you will discuss with Ke Wu. Chapter 10 is the lens for Michael Wellman. Chapter 11 puts the results together and chapter 12 prepares the conversation.</p>
<p>Every toy number in this book comes from the study's own tested code (<code>textbook/toy.py</code> runs <code>mev/v3.py</code> and <code>mev/mechanism.py</code>). Every real number comes from <code>results/</code>. Toy figures carry an Illustration label.</p>
""")

chapter("ethereum", "1", "Blocks, ordering and who sees your trade", f"""
{why("A sandwich only works because someone controls the order of transactions inside a block. You need to explain who that is.")}
<p>A transaction is a signed instruction, for example "swap 20,000 USDC for ETH, and revert if I get less than 8.8 ETH". Ethereum groups transactions into a <strong>block</strong> every 12 seconds. Inside a block the transactions run one after another, so their <strong>order</strong> decides what price each swap gets.</p>
<p>Today the order is chosen by a <strong>builder</strong>. Builders compete to give the block <strong>proposer</strong> (a validator) the most valuable block. <strong>Searchers</strong> are bots that watch pending transactions and send the builder a <strong>bundle</strong>: their own transactions in a fixed order, plus a tip. The tip can be a priority fee or a direct ETH transfer to the builder. Profit that comes from choosing, inserting or reordering transactions is called <strong>MEV</strong> (maximal extractable value). A sandwich is one kind of MEV.</p>
<p>A transaction sent to the <strong>public mempool</strong> is visible to every searcher before it is mined. A transaction sent through a <strong>private RPC</strong> goes only to selected builders. That is one reason why the biggest pools now see few sandwiches: much of their flow is private.</p>
{fig("f-path", "transaction path", d_tx_path(), "A swap from the public mempool can be seen by a searcher. The searcher pays the builder to put its front-run and back-run on each side of the swap in the same block.")}
<p><strong>In this study:</strong> {S['sandwiches']} sandwiches, mostly built by Titan, BuilderNet, Quasar and Eureka. The top attacker, <em>jaredfromsubway.eth</em>, ran {jared} of them. Attackers paid at least {usd(S['attacker_gas_usd'])} in fees, {pct(gas_share)} of what they took from the pool. Etherscan also shows direct ETH tips to builders, which receipts do not show.</p>
{breath("Ethereum runs a block's transactions in order, and builders choose that order, so whoever pays the builder can put trades on both sides of yours.")}
{check(("Why can the attacker be sure its back-run comes right after the victim?", "It sends the front-run, the victim's transaction and the back-run to the builder as one bundle with a fixed order. The builder includes the bundle as a unit or not at all."),
       ("Why might a big pool show almost no sandwiches?", "Most of its order flow goes through private RPCs or aggregators that protect it, so searchers never see the swap before it is mined. In this study the main USDC/WETH pool had 13 in the same week."),
       ("What does an attacker's gas figure miss?", "Direct ETH transfers to the builder inside the transaction (for example 0.251 ETH to Titan Builder in block 26,164,108). Those need traces, so the study's gas number is a lower bound on what attackers paid."))}
""")

chapter("amm", "2", "Automated market makers", f"""
{why("The price impact of a trade is what the attacker exploits. You need to compute it in your head for a simple pool.")}
<p>An <strong>automated market maker</strong> (AMM) is a contract that holds two tokens and trades against anyone. The simplest rule is <strong>constant product</strong>: if the pool holds x ETH and y USDC, every trade must keep x × y = k.</p>
<p>The <strong>price</strong> is the slope of the curve, y ÷ x USDC per ETH. A buy of ETH adds USDC and removes ETH, so the price rises during the trade. The buyer pays an <strong>average price</strong> above the starting price. The gap is the <strong>price impact</strong>, or slippage. A <strong>fee</strong> (0.01% on the study pool) is charged on the input.</p>
{fig("f-curve", "constant product", d_curve(), f"The toy pool: 100 ETH and 200,000 USDC, no fee. Paying 20,000 USDC returns {eth(NA['victim_eth'], 4)} ETH, an average of {20000 / (NA['victim_eth'] / E):,.0f} USDC per ETH. The price after the trade is {NA['price_after']:,.0f}.", illustration=True)}
<p>Two prices matter in this study. The <strong>average price</strong> is what one trade paid overall. The <strong>marginal price</strong> is the price of the next tiny unit, the slope at the end of the trade. Uniswap users protect themselves with an average price (a minimum output). Ke Wu's mechanism uses a marginal price. Chapter 8 shows why that difference matters.</p>
{breath("In a constant-product pool your own trade moves the price against you, so anyone who trades in front of you in the same direction makes your price worse.")}
{check(("In the toy pool, what does 20,000 USDC buy, and why not 10 ETH?", f"{eth(NA['victim_eth'], 4)} ETH. Each ETH removed makes the next one more expensive: the price climbs from 2,000 to {NA['price_after']:,.0f} during the trade."),
       ("What is the difference between average and marginal price?", "Average: total paid divided by total received for one trade. Marginal: the price of the next unit at a given pool state, the slope of the curve."),
       ("Why is the price impact larger in a smaller pool?", "The same trade is a bigger fraction of the reserves, so the product rule forces a larger price move."))}
""")

chapter("v3", "3", "Uniswap v3: concentrated liquidity", f"""
{why("The study replays every swap with Uniswap v3's exact integer math. You need to say what that math tracks and why exact replay is the gate.")}
<p>In Uniswap v3, liquidity providers put money in a chosen <strong>price range</strong>. Inside a range the pool behaves like a constant-product pool with that much <strong>liquidity</strong>. Ranges are built from <strong>ticks</strong>: each tick is a 0.01% price step. When a swap moves the price across a range boundary, the <strong>active liquidity</strong> changes and the price can move faster or slower.</p>
<p>The contract stores the price as <strong>sqrtPriceX96</strong>: the square root of the price, times 2<sup>96</sup>, as an integer. Every Swap event records the price, active liquidity and tick after the swap. That is why the study can rebuild the pool state from logs alone.</p>
{fig("f-ticks", "ticks", d_ticks(), "Liquidity is stacked in price ranges. A buy pushes the price right; at a range boundary the active liquidity drops and the price moves faster.", illustration=True)}
<p><strong>The replay gate.</strong> The study ported Uniswap's integer math to Python and replayed all {S['swaps']:,} swaps of the week. Every one matched exactly: the amounts and the price, liquidity and tick afterwards. Three broken inputs make it fail, which shows the check can catch errors: a wrong fee breaks 70,645 swaps, dropping 20 ticks breaks 1,284, and ignoring the 129 liquidity changes breaks 334.</p>
<p><strong>Just-in-time (JIT) liquidity.</strong> A bot can add liquidity in a narrow range right before a big swap and remove it right after, collecting the fee. In 37 of the 236 sandwiches the attacker did this inside the attack. Chapter 4 shows how.</p>
{breath("Uniswap v3 is a stack of constant-product pools over price ranges; the study reproduces every swap of the week to the last unit before it trusts any what-if.")}
{check(("Why replay every real swap before computing any counterfactual?", "If the simulator matches reality exactly on 70,669 swaps, a difference in the counterfactual comes from the change you made (removing the attacker), not from a simulator error."),
       ("What does a tick crossing change?", "The active liquidity. Liquidity providers whose range starts or ends at that tick join or leave."),
       ("Why do negative controls matter?", "A gate that never fails proves nothing. Breaking the fee, the tick data or the liquidity events makes it fail, so it really checks the inputs."))}
""")

chapter("sandwich", "4", "The sandwich attack", f"""
{why("This is the problem the paper solves. You need the mechanics, and the reason the minimum output is the attacker's budget.")}
<p>The victim sends "buy ETH with 20,000 USDC, at least 8.8 ETH". An attacker sees it and puts three transactions in order:</p>
<ol>
<li><strong>Front-run:</strong> buy ETH first, pushing the price up.</li>
<li><strong>Victim:</strong> buys at the higher price and gets less ETH.</li>
<li><strong>Back-run:</strong> sell the ETH from step 1 at the even higher price.</li>
</ol>
{fig("f-sandwich", "sandwich price path", d_price_path(), f"The toy sandwich. The front-run spends {usdc(SA['front_in'])} USDC. The victim gets exactly its minimum, {eth(SA['victim_eth'], 2)} ETH instead of {eth(NA['victim_eth'], 2)}. The back-run returns {usdc(SA['back_usdc'])} USDC, a profit of {usdc(SA['attacker_profit_usdc'])} USDC.", illustration=True)}
<p><strong>The minimum output is the budget.</strong> The attacker makes the front-run as large as possible while the victim's swap still succeeds. In the toy, a larger front-run would push the victim below 8.8 ETH and the victim's transaction would revert, ending the attack. So the attacker uses all of the victim's tolerance. The real data shows the same: attackers took 98% of the tolerance victims allowed. Victims with no minimum at all (29 decoded cases) can lose almost everything. One wallet put 0.447 WETH into the pool and got 3.89 USDT back.</p>
<p><strong>The JIT variant.</strong> jaredfromsubway's front-run sometimes also adds liquidity in the single tick where the victim will trade, and the back-run removes it. The victim then trades at the pushed price against the attacker's own liquidity.</p>
{breath("The attacker buys in front of you, lets you buy at the higher price, then sells back, and it sizes the front-run to push you exactly to your minimum.")}
{check(("Why doesn't the attacker use an even bigger front-run?", "The victim's transaction would fall below its minimum output and revert. The back-run would then sell into a market the victim never pushed up."),
       ("Why does setting a tight slippage limit protect you?", "It shrinks the attacker's budget. A 0.1% tolerance leaves almost nothing to take after fees and gas."),
       ("What is the attacker's profit made of?", "The price difference between the front-run's buy and the back-run's sell, which the victim's trade created."))}
""")

chapter("detect", "5", "Finding sandwiches in the data", f"""
{why("A professor's first question will be how you know these are sandwiches. You need the rule, its tiers and how it was checked.")}
<p>The detector reads each block's swaps on the pool in log order. It merges each transaction into one leg and looks for this pattern:</p>
<ul>
<li>a front-run and a back-run in the same block, front-run first, in opposite directions;</li>
<li>the same attacker: the same sending address, or the same bot contract with amounts within ±1%;</li>
<li>the back-run sells 90–110% of what the front-run bought (the rule from Qin, Zhou &amp; Gervais, S&amp;P 2022);</li>
<li>at least one victim between them, trading in the front-run's direction, from a different sender and contract.</li>
</ul>
{fig("f-detect", "detection", d_detect(), "One block's swaps on the pool, in order. Positions 1 and 3 are the attacker's legs; position 2 is the victim.", illustration=True)}
<table class="t"><thead><tr><th>Detection tier</th><th>Sandwiches</th><th>Victim loss</th></tr></thead><tbody>
<tr><td>All detected (90–110% amount match)</td><td>236</td><td>$12,387</td></tr>
<tr><td>Strict amount match (±1%)</td><td>193</td><td>$10,428</td></tr>
<tr><td>Strict, single-pool front-run, same sender</td><td>178</td><td>$10,043</td></tr></tbody></table>
<p><strong>How it was checked.</strong> The evidence for 30 random hits was read row by row: each leg's full receipt, how many senders use each contract, and ENS names resolved on chain. 25 were textbook sandwiches, 3 were losing attempts, and 2 had front-runs that also traded in other pools. Then 15 Etherscan pages were read for 5 hits. All 5 are sandwiches, and the attacker contracts carry Etherscan's "MEV Bot" tags. The check also found the JIT pattern.</p>
<p><strong>What it misses:</strong> sandwiches that span two blocks or several pools, and attacks on private flow whose cause cannot be seen. A Dune cross-check was skipped by choice.</p>
{breath("A sandwich is the same attacker trading both ways in one block around a victim, with the back-run undoing the front-run, and the result holds in its strictest tier.")}
{check(("Why require the back-run to sell 90–110% of what the front-run bought?", "It separates an attacker closing its position from two unrelated trades by a bot that trades both ways all day."),
       ("Why report three tiers?", "So the headline doesn't depend on one threshold. The strictest tier still has 178 sandwiches and $10,043 of loss."),
       ("Name one kind of attack the detector cannot see.", "A sandwich whose legs are in different blocks, or one that front-runs through another pool."))}
""")

chapter("loss", "6", "Measuring loss: the counterfactual", f"""
{why("“Loss” needs a definition someone can check. You need to say what is compared with what.")}
<p><strong>(a) Counterfactual loss, the headline.</strong> Take the pool state at the start of the block. Replay the block exactly, with every attacker swap and attacker liquidity change removed. The victim's loss is what it would have received in that replay minus what it actually received.</p>
{fig("f-cf", "counterfactual", d_counterfactual(), f"Loss (a) in the toy: {eth(toy_loss_eth, 4)} ETH. Loss (c), the tolerance, equals the loss here because the attacker pushed the victim exactly to its minimum.", illustration=True)}
<p><strong>(b) Attacker gross.</strong> Every WETH and USDT transfer between the pool and the attacker's two transactions: {usd(S['attacker_gross_b_usd'])} for the week, before {usd(S['attacker_gas_usd'])} of gas.</p>
<p><strong>(c) Tolerance available.</strong> The no-attack output minus the victim's own minimum output, read from the router call. Defined for 115 victims: $1,582 of tolerance, of which attackers took $1,544 (98%).</p>
<p>Values are in USD at the price at the start of the block, with USDT taken as $1. The median victim lost {usd(float(sorted(float(y['loss_a_usd']) for y in VI)[len(VI) // 2]), 2)}; the 20 largest sandwiches carry {pct(top20)} of the week's loss.</p>
{breath("Loss is the difference between the victim's real output and an exact replay of the same block without the attacker.")}
{check(("Why is (b) not equal to (a)?", "The attacker's gain and the victim's loss are measured against different baselines, and some value goes to fees and liquidity providers. Here (b) was $8,713 and (a) was $12,387."),
       ("Why remove the attacker's liquidity changes too?", "A world without the attack has no JIT liquidity either. Keeping it would cushion the victim and understate the loss."),
       ("What does 98% of tolerance tell you?", "Attackers size the front-run to the victim's limit. The limit, not the trade size, sets how much a victim can lose."))}
""")

chapter("theory", "7", "Mechanism-design vocabulary", f"""
{why("Ke Wu's paper is written in this language. You need these four terms to read it and discuss it.")}
<ul>
<li><strong>Order:</strong> (type, amount v, limit rate r). For example, buy up to v ETH, paying at most r USDC per ETH.</li>
<li><strong>Arbitrage resilience:</strong> no group of orders can end with a gain in one token and no loss in the other. That is, no risk-free profit, even for a block producer who inserts, drops or reorders orders (Definition 2, Theorem 3.1).</li>
<li><strong>Incentive compatibility (IC):</strong> reporting your true order is your best strategy; no lie, split, delay or fake order makes you better off (Definition 3). IC implies arbitrage resilience.</li>
<li><strong>Plain model and weak fair-sequencing model:</strong> what a strategic player can do to the order of transactions.</li>
</ul>
{fig("f-models", "sequencing models", d_models(), "The two models differ in who controls ordering. The mechanism is arbitrage-resilient in both, and fully incentive compatible only with fair sequencing.")}
<p>The paper compares outcomes with a <strong>partial ordering</strong>, not a single utility number: an outcome is better if you get more of what you wanted at a price within your limit. Some outcomes are not comparable, for example getting more ETH than you asked for.</p>
{breath("Arbitrage resilience means nobody can make risk-free profit from the batch; incentive compatibility is the stronger claim that honesty is your best strategy, and it needs fair sequencing.")}
{check(("Is a sandwich an arbitrage in the paper's sense?", "Yes. The attacker ends with no net ETH and more USDC, a risk-free gain, which arbitrage resilience forbids."),
       ("Why does IC need the fair-sequencing model?", "In the plain model, ties are broken by arrival time, and a block producer can fake an early arrival to get a better place. Fair sequencing removes that move."),
       ("Which property did the study test numerically?", "Arbitrage resilience: in every run the attacker's two legs net to zero or less."))}
""")

chapter("mechanism", "8", "The Chan–Wu–Shi two-phase mechanism", f"""
{why("This is the design the email is about. You need to run it by hand on a small block.")}
<p>The mechanism clears all of one block's orders for one pool together (Figure 1 of the paper):</p>
<ol class="steps" id="mech-steps">
<li data-step="1"><strong>Fix r0</strong>, the pool's marginal price at the start of the block. Drop any order whose limit is worse than r0.</li>
<li data-step="2"><strong>Measure</strong> each order's size in ETH at r0. The side with more volume is <em>dominant</em>; the other is the <em>minority</em>.</li>
<li data-step="3"><strong>Phase 1:</strong> fill the whole minority side at r0 against the dominant side, in tie-break order. The pool does not move.</li>
<li data-step="4"><strong>Phase 2:</strong> the rest of the dominant side trades on the curve one order at a time, each until it is filled or the marginal price reaches its limit.</li>
</ol>
<div class="stepper" hidden><button type="button" id="prev">Previous step</button><button type="button" id="next" class="primary">Next step</button><span id="step-label" aria-live="polite"></span></div>
{fig("f-mech", "mechanism", d_mechanism(), "The toy block, front-run first. Phase 1 matches the back-run's sell against the front-run at r0, so the front-run hardly moves the pool before the victim trades.", illustration=True)}
<p><strong>Why the sandwich fails.</strong> In phase 1 everything trades at r0. In phase 2 only the dominant side trades, and each order pays r0 or worse. So the attacker's buy pays at least r0 and its sell gets at most r0. It cannot end with a risk-free gain. That is Theorem 3.1, and the study's code checks it in every run.</p>
{fig("f-scen", "scenarios", d_scenarios(), f"Five versions of the toy block. The sandwich leaves the victim {eth(SA['victim_eth'], 2)} ETH and the attacker +{usdc(SA['attacker_profit_usdc'])} USDC. Under the mechanism the attacker never gains. With the victim first, the victim gets more than with no attack, because phase 1 hands it the back-run's ETH at r0.", illustration=True)}
<h3>Why the real result is 52–99%, not 100%</h3>
<p>The mechanism removes the profit. It does not stop a trade placed ahead of the victim from moving the price in phase 2. The study gave each attacker leg its own executed price as a limit, a price the attacker is known to accept. Then:</p>
<ul>
<li>The back-run's limit is worse than r0, so step 1 drops it.</li>
<li>The front-run trades on the curve until the marginal price reaches its own average price, about half its size.</li>
<li>The victim, behind it, still pays for that half.</li>
</ul>
<p>In the toy this recovers {pct(toy_recovered_exec)} of the victim's loss; in the real week, {pct(S['prevented_share_static_arrival'])}. Random tie-breaking puts the victim first about half the time, giving {pct(S['prevented_share_static_random_mean'])} on average. If the attack stops because it no longer pays, the victim keeps about 100%.</p>
<h3>Average limits against marginal limits</h3>
<p>Uniswap users state an <em>average</em> limit (a minimum output). The paper's limit is <em>marginal</em>. Reading the toy victim's minimum (8.8 ETH for 20,000 USDC) as a marginal limit fills only {pct(float(AM['victim_filled']))} of its order, because its own trade pushes the marginal price past 2,273 USDC per ETH. That is the question the email to Ke Wu asks.</p>
{breath("Match buys against sells at the start-of-block price, then run the leftover one-sided flow along the curve; the attacker's two legs can only trade at r0 or worse, so the sandwich has no profit left.")}
{check(("In phase 1, does the pool's price change?", "No. Buyers and sellers trade with each other at r0, and the pool's reserves are untouched."),
       ("Why can't the back-run sell above r0?", "The sell side is the minority, so it trades only in phase 1, at exactly r0. Only the dominant side trades along the curve."),
       ("Why does the study report a range, not one prevented share?", "The result depends on how the attacker's orders would look under the mechanism (limits, ordering) and whether the attacker attacks at all. The range shows that dependence."),
       ("Is this a uniform-price batch auction?", "No. Phase 2 orders pay different prices. The paper says uniform pricing alone does not give incentive compatibility, and the Trilemma paper proves you cannot have both with weak local efficiency."))}
""")

chapter("trilemma", "9", "The Trilemma", f"""
{why("The follow-up paper (Li, Shi &amp; Zhang, 2026) tells you what the mechanism had to give up. It is the natural next question in a meeting.")}
<ul>
<li><strong>IC:</strong> incentive compatibility (chapter 7).</li>
<li><strong>wLE, weak local efficiency:</strong> no "reasonable" order (limit at least as good as r0) is left unfilled when the pool's ending price would still have suited it.</li>
<li><strong>UP, uniform pricing:</strong> every executed order trades at the same price.</li>
</ul>
{fig("f-tri", "trilemma", d_trilemma(), "Theorem 2 of Li, Shi &amp; Zhang: any two properties are possible, all three are not. Chan–Wu–Shi gives up uniform pricing.")}
<p>A uniform-price batch auction (CoW-style) gets wLE and UP, but the paper shows a user with real demand can gain by misreporting. So it is not IC. Uniform pricing removes the pure sandwich, but not every strategic gain.</p>
<p>The trilemma paper also notes the cost of the drop rule in step 1: an order to buy below r0 is ignored even if the pool's ending price would have suited it. In the study, the smallest victim fill in the arrival-order run was {pct(S['victims_min_fill_static_arrival'])}.</p>
{breath("You can have any two of honesty-is-optimal, no wasted reasonable demand, and one price for everyone, but not all three; Ke Wu's mechanism keeps the first two.")}
{check(("Which property does Chan–Wu–Shi give up?", "Uniform pricing."),
       ("Why isn't a uniform-price batch auction enough?", "It stops zero-demand arbitrage like sandwiches, but a trader with real demand can still gain by misreporting, so it is not incentive compatible."),
       ("What is the main open question both papers leave?", "Achieving IC with weak local efficiency in the plain model, without assuming fair sequencing."))}
""")

chapter("wellman", "10", "Wellman's lens: batch against continuous", f"""
{why("Wellman has no blockchain papers. The connection is his work on how market rules change strategic behavior.")}
<p>In a <strong>continuous</strong> market each order trades on arrival, so being first is worth money. Wah &amp; Wellman (2016) simulate fragmented stock markets and find that <strong>frequent call markets</strong>, which collect orders and clear them together at intervals, eliminate latency arbitrage. A block is a natural batch interval.</p>
{fig("f-call", "call market", d_call_market(), "The same arrivals under continuous trading and under batches. Inside a batch, arriving first no longer buys a better price.")}
<p><strong>Empirical game-theoretic analysis (EGTA)</strong> is Wellman's main method. Simulate a market with many strategies, estimate the payoff of each combination, and find the equilibrium among them. The study's biggest limit is exactly an EGTA question: it replays the same orders and cannot say how bots, builders and traders would change their behavior under the new rule.</p>
{breath("Continuous trading pays whoever is first; batching removes that prize, and how traders re-optimize under the new rule is an empirical game.")}
{check(("What does a frequent call market remove, according to Wah & Wellman?", "Latency arbitrage: profit from reacting to information or orders faster than others."),
       ("Why is the 52–100% range an EGTA question?", "The range depends on what attackers do once the attack stops paying. Working that out means finding the equilibrium of the new game, which is what EGTA does."))}
""")

chapter("results", "11", "What the study found, and how to say it", f"""
{why("This is the paragraph you will say most often. Learn it with its limits attached.")}
{fig("f-results", "results", d_results(), title=f"Per-block clearing cuts the week's {usd(cum_sq[-1])} sandwich loss to {usd(cum_m[-1])} with the same orders", caption=f"Real data, 5–11 Oct 2026. Same orders under per-block clearing: mean of 200 random tie-breaks. The 20 largest sandwiches carry {pct(top20)} of the loss.")}
<table class="t"><thead><tr><th>Measure</th><th>Value</th></tr></thead><tbody>
<tr><td>Swaps / sandwiches / victims</td><td>{S['swaps']:,} / {S['sandwiches']} / {S['victims']}</td></tr>
<tr><td>Victim loss (a)</td><td>{usd(S['loss_a_usd'])}</td></tr>
<tr><td>Attacker gross (b) / gas</td><td>{usd(S['attacker_gross_b_usd'])} / {usd(S['attacker_gas_usd'])}</td></tr>
<tr><td>Tolerance taken (c), 115 victims</td><td>98%</td></tr>
<tr><td>Attacker net under the mechanism, best run</td><td>$0.00</td></tr>
<tr><td>Loss kept by victims: deterred</td><td>{pct(S['prevented_share_deterred'])}</td></tr>
<tr><td>Same orders, random tie-break (5th–95th percentile)</td><td>{pct(S['prevented_share_static_random_mean'])} ({pct(S['prevented_share_static_random_p5'])}–{pct(S['prevented_share_static_random_p95'])})</td></tr>
<tr><td>Same orders, arrival order (lowest variant)</td><td>{pct(S['prevented_share_static_arrival'])}</td></tr>
<tr><td>Control pool USDC/WETH 0.05%, same week</td><td>13 sandwiches</td></tr></tbody></table>
<h3>The paragraph</h3>
<p class="quote">"One week of Uniswap v3's busiest WETH/USDT pool, 70,669 swaps, replayed with exact integer math: 236 sandwiches cost 244 traders $12.4k, and attackers took 98% of the slippage those traders allowed. Under your two-phase mechanism none of those attacks makes money. With the same orders, victims keep 75% of their loss on average, and all of it if attackers stop."</p>
<p class="meta">Describe your own role accurately when you say this, including the AI assistance in building the study.</p>
<h3>Limits to say with it</h3>
<ul>
<li>One pool and one week: a sample, not a yearly rate.</li>
<li>Same order flow: behavior under the new rule is not modeled.</li>
<li>Same-block, single-pool detection only; builder tips by direct transfer are not counted.</li>
<li>Average limits read as marginal limits, which sets the lower bound.</li>
<li>The paper's model has no fee and no liquidity changes inside a block; the study applies them at the block start.</li>
</ul>
{breath("236 sandwiches, $12.4k lost, 98% of tolerance taken; under the mechanism no attack pays, and victims keep 75% with the same orders and all of it if attacks stop.")}
""")

QA = [
    ("Why this pool?", "It was the busiest of nine popular pools scanned and the only one with regular sandwiches. The main USDC/WETH pool had 13 that week."),
    ("How do you know they are sandwiches?", "A published rule, three robustness tiers, evidence for 30 random hits, and 5 hits checked on Etherscan. All held up; the strictest tier still has 178 sandwiches."),
    ("Isn't “attacker net ≤ 0” just your Theorem 3.1?", "Yes, and it checks the implementation rather than adding a new result. The new parts are the victim numbers, the 98% tolerance finding and the range of protection on real order flow."),
    ("Why not 100% with the same orders?", "Phase 2 still lets an order ahead of the victim move the price. With the attacker's executed prices as limits the back-run is dropped and half the front-run still trades. Random tie-breaking raises the share to 75%."),
    ("How did you treat Uniswap's average-price limits?", "As marginal limits. That under-fills orders and sets the lower bound. A version of the mechanism for average-price limits is the open question I'd like to ask about."),
    ("What about fees?", "Phase 2 keeps the 0.01% pool fee. Phase 1 was run with and without it; the result is the same to the reported precision."),
    ("Concentrated liquidity?", "v3 is constant-product within each range, and the price still rises with each unit bought (increasing marginal cost), which the proofs need. JIT liquidity inside a block is outside the paper's model."),
    ("What would you do next?", "More weeks and pools; multi-pool and cross-block sandwiches; an empirical game of attacker and builder responses; and mechanisms for average-price limits."),
]

chapter("prep", "12", "Meeting prep", f"""
{why("Practise these out loud. Each answer is short and true to the data.")}
<div class="qa">{''.join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q, a in QA)}</div>
<p>Before you send anything: read the figure at full size, check both email addresses, and keep the claims to what the tables show.</p>
""")

GLOSSARY = [
    ("AMM", "Automated market maker: a contract that holds two tokens and trades against anyone by a fixed rule."),
    ("Arbitrage resilience", "No group of orders can make a risk-free profit from the mechanism."),
    ("Average price", "Total paid ÷ total received for one trade."),
    ("Back-run", "The attacker's trade right after the victim, closing its position."),
    ("Builder", "The party that orders transactions into a block to sell to the proposer."),
    ("Counterfactual", "An exact replay of the block with something changed, here the attacker removed."),
    ("EGTA", "Empirical game-theoretic analysis: estimate a game's payoffs by simulation and solve it."),
    ("Front-run", "The attacker's trade right before the victim, in the same direction."),
    ("IC", "Incentive compatibility: truthful reporting is the best strategy."),
    ("JIT liquidity", "Liquidity added just before a swap and removed just after."),
    ("Marginal price", "The price of the next tiny unit; the slope of the curve."),
    ("MEV", "Maximal extractable value: profit from choosing, inserting or reordering transactions in a block."),
    ("Minimum output", "The least a swap accepts; below it the transaction reverts."),
    ("r0", "The pool's marginal price at the start of the block."),
    ("sqrtPriceX96", "Uniswap v3's stored price: √price × 2⁹⁶, an integer."),
    ("Tick", "A 0.01% price step; liquidity ranges start and end on ticks."),
    ("UP", "Uniform pricing: every executed order trades at one price."),
    ("wLE", "Weak local efficiency: no reasonable order is left unfilled when the ending price still suits it."),
]
READING = [
    ("Chan, Wu & Shi, Mechanism Design for Automated Market Makers (AFT 2025)", "https://arxiv.org/abs/2402.09357", "Read §1–3 and Figure 1 first."),
    ("Li, Shi & Zhang, A Trilemma in AMM Mechanism Design (2026)", "https://arxiv.org/abs/2605.27602", "Theorems 1–2 and §4."),
    ("Qin, Zhou & Gervais, Quantifying Blockchain Extractable Value (S&P 2022)", "https://arxiv.org/abs/2101.05511", "The detection rule."),
    ("Daian et al., Flash Boys 2.0 (S&P 2020)", "https://arxiv.org/abs/1904.05234", "Where the MEV idea started."),
    ("Uniswap v3 whitepaper", "https://uniswap.org/whitepaper-v3.pdf", "§6: ticks and sqrtPriceX96."),
    ("Wah & Wellman, Latency arbitrage in fragmented markets (2016)", "https://content.iospress.com/doi/10.3233/AF-160060", "The call-market result."),
    ("Heimbach et al., sandwich measurement (2026)", "https://arxiv.org/abs/2609.28115", "Exact re-simulation of victim loss."),
]

chapter("glossary", "–", "Glossary and reading list",
        "<dl class='gloss'>" + "".join(f"<dt>{t}</dt><dd>{d}</dd>" for t, d in GLOSSARY) + "</dl>"
        + "<h3>Read next</h3><ul class='reading'>" + "".join(
            f'<li><a href="{u}">{html.escape(t)}</a> — {n}</li>' for t, u, n in READING) + "</ul>")


# ---------------------------------------------------------------------------------------------- page
def font_face(name, file, weight):
    data = base64.b64encode(open(os.path.join(DESIGN, "assets", "fonts", file), "rb").read()).decode()
    return f"@font-face{{font-family:'{name}';src:url(data:font/ttf;base64,{data}) format('truetype');font-weight:{weight};font-display:swap}}"


def tokens_css():
    t = json.load(open(os.path.join(DESIGN, "assets", "tokens.json")))
    out = [f"--color-{k}:{v['$value']}" for k, v in t["color"].items()]
    out += [f"--space-{k}:{v['$value']['value']}px" for k, v in t["space"].items()]
    out += [f"--radius-panel:{t['radius']['panel']['$value']['value']}px"]
    return ":root{" + ";".join(out) + "}"


BOOK_CSS = """
body{font-size:18px}
.layout{display:grid;grid-template-columns:260px minmax(0,1fr);gap:56px;max-width:1240px;margin:auto;padding:0 48px 64px}
.toc{position:sticky;top:0;align-self:start;max-height:100vh;overflow:auto;padding:32px 0}
.toc ol{list-style:none;padding:0;margin:16px 0 0}
.toc li{margin:0}
.toc a{display:flex;gap:12px;min-height:40px;align-items:center;color:var(--color-secondary);text-decoration:none;font-size:15px}
.toc a:hover,.toc a:focus-visible{color:var(--color-ink)}
.toc .n{font-family:'Rahil Display';color:var(--color-accent);min-width:22px}
.cover{padding:72px 0 40px;border-bottom:1px solid var(--color-border)}
.cover .kicker{color:var(--color-accent);font-weight:600;letter-spacing:.04em}
.cover h1{margin-top:28px}
.cover p{font-size:21px;margin-top:20px;max-width:56ch}
.chapter{padding:56px 0;border-bottom:1px solid var(--color-border);scroll-margin-top:16px}
.chnum{color:var(--color-accent);font-weight:600;letter-spacing:.06em;text-transform:uppercase;font-size:14px;margin-bottom:10px}
.chapter p,.chapter li{max-width:68ch}
.chapter ul,.chapter ol{padding-left:22px}
.chapter li{margin:8px 0}
.why,.breath{border-left:4px solid var(--color-accent);padding:4px 0 4px 18px;margin:20px 0}
.why span,.breath span{display:block;font-size:14px;letter-spacing:.06em;text-transform:uppercase;color:var(--color-accent);font-weight:600;margin-bottom:4px}
.breath{font-size:20px}
.claims li{font-size:20px;margin:12px 0}
code{font:15px/1.4 monospace;background:var(--color-surface);padding:2px 6px;border-radius:4px}
.fig{margin:28px 0;background:var(--color-figure-surface);color:var(--color-figure-ink);border-radius:var(--radius-panel);padding:28px;position:relative}
.fig svg{display:block;width:100%;height:auto;font-variant-numeric:tabular-nums}
.figtitle{font-family:'Rahil Plex';font-weight:600;font-size:20px;color:var(--color-figure-ink);margin:0 0 16px;max-width:52ch}
.fig figcaption{color:var(--color-figure-secondary);font-size:16px;margin-top:16px;max-width:none}
.fig .illus{position:absolute;top:12px;right:16px;font-size:14px;font-weight:600;color:var(--color-figure-secondary);letter-spacing:.04em;text-transform:uppercase}
.fig text{font-family:'Rahil Plex',sans-serif;fill:var(--color-figure-ink)}
.fig .lbl{font-size:15px}.fig .small{font-size:14px}.fig .mid{font-size:17px}.fig .big{font-size:18px}.fig .strong{font-weight:600}
.fig .muted{fill:var(--color-figure-secondary)}
.fig .box{fill:var(--color-figure-canvas);stroke:var(--color-figure-border);stroke-width:1.5}
.fig .hl{fill:var(--color-accent);stroke:var(--color-figure-ink);stroke-width:2}
.fig .edge{stroke:var(--color-figure-ink);stroke-width:1.8;fill:none}
.fig .dashline{stroke-dasharray:5 4}
.fig .ink-fill{fill:var(--color-figure-ink)}
.fig .axis,.fig .thin{stroke:var(--color-figure-secondary);stroke-width:1}
.fig .grid{stroke:var(--color-figure-border);stroke-width:1}
.fig .tickline{stroke:var(--color-figure-ink);stroke-width:2}
.fig .curve{stroke:var(--color-figure-ink);stroke-width:2.5;fill:none}
.fig .curve.thick{stroke-width:4}
.fig .curve.gray{stroke:var(--color-figure-secondary);stroke-width:2.5}
.fig .curve.dash{stroke:var(--color-figure-secondary);stroke-dasharray:6 5;stroke-width:2}
.fig .dot{fill:var(--color-figure-surface);stroke:var(--color-figure-ink);stroke-width:2}
.fig .dot.hl{fill:var(--color-accent)}
.fig .liq{fill:var(--color-figure-canvas);stroke:var(--color-figure-border)}
.fig .hlrect{fill:none;stroke:var(--color-figure-ink);stroke-width:2;stroke-dasharray:5 4}
.fig .tri{fill:none;stroke:var(--color-figure-ink);stroke-width:2}
.fig .step{transition:opacity .3s}
.fig.stepping .step{opacity:.25}.fig.stepping .step.on{opacity:1}
.t{border-collapse:collapse;margin:24px 0;width:100%;max-width:720px;font-variant-numeric:tabular-nums}
.t th,.t td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--color-border);vertical-align:top}
.t td:last-child,.t th:last-child{text-align:right}
.t th{color:var(--color-secondary);font-weight:600;font-size:15px}
.check{margin-top:32px;background:var(--color-surface);border-radius:var(--radius-panel);padding:24px 28px}
.check h3{margin:0 0 8px;font-size:26px}
.check ol{padding-left:22px;margin:0}
.check details{margin:0}
.check summary,.qa summary{font-weight:600}
.check details p,.qa details p{color:var(--color-secondary);margin:4px 0 12px}
.qa details{border-top:1px solid var(--color-border);padding:6px 0}
.steps li{border-radius:8px;padding:4px 8px;margin:4px 0}
.steps li.on{background:var(--color-surface);outline:2px solid var(--color-accent)}
.stepper{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:16px 0}
.quote{font-size:20px;border-left:4px solid var(--color-accent);padding-left:18px}
.gloss{display:grid;grid-template-columns:200px 1fr;gap:10px 24px;max-width:860px}
.gloss dt{font-weight:600}.gloss dd{margin:0;color:var(--color-secondary)}
.reading li{margin:10px 0}
.foot{padding:32px 0;color:var(--color-secondary);font-size:14px}
@media(max-width:900px){.layout{grid-template-columns:minmax(0,1fr);gap:0;padding:0 24px 40px}.toc{position:static;max-height:none;padding:24px 0;border-bottom:1px solid var(--color-border)}.toc ol{columns:2}}
.scroll-hint{display:none}
@media(max-width:700px){.fig .scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}.fig svg{min-width:780px}.scroll-hint{display:block;font-size:14px;color:var(--color-figure-secondary);margin-top:8px}}
@media(max-width:600px){.fig{padding:16px 12px;margin:20px -8px}.toc ol{columns:1}.gloss{grid-template-columns:1fr}.cover{padding:40px 0 28px}.claims li,.breath{font-size:18px}}
@media(prefers-reduced-motion:reduce){.fig .step{transition:none}}
@media print{.toc,.stepper{display:none}.layout{display:block}.chapter{break-inside:auto}.check details{display:block}}
"""

JS = """
(function(){
  var steps=[].slice.call(document.querySelectorAll('#mech-steps li'));
  var fig=document.getElementById('f-mech'); var ui=document.querySelector('.stepper');
  if(!steps.length||!fig||!ui)return;
  ui.hidden=false; var i=0; var label=document.getElementById('step-label');
  var marks=[[],[],['s3'],['s3','s4']];
  function show(){
    steps.forEach(function(li,k){li.classList.toggle('on',k===i);});
    fig.classList.add('stepping');
    fig.querySelectorAll('.step').forEach(function(el){
      var on=marks[i].some(function(c){return el.classList.contains(c);}) || i<2;
      el.classList.toggle('on',on);});
    label.textContent='Step '+(i+1)+' of '+steps.length;
    document.getElementById('prev').disabled=i===0; document.getElementById('next').disabled=i===steps.length-1;
  }
  document.getElementById('prev').addEventListener('click',function(){if(i>0){i--;show();}});
  document.getElementById('next').addEventListener('click',function(){if(i<steps.length-1){i++;show();}});
  show();
})();
"""


def page():
    css = (font_face("Rahil Display", "Anton-Regular.ttf", 400) + font_face("Rahil Plex", "IBMPlexSans-Regular.ttf", 400)
           + font_face("Rahil Plex", "IBMPlexSans-SemiBold.ttf", 600) + tokens_css()
           + open(os.path.join(DESIGN, "assets", "components.css")).read() + BOOK_CSS)
    toc = "".join(f'<li><a href="#{cid}"><span class="n">{n}</span>{html.escape(t)}</a></li>' for cid, n, t, _ in CH)
    chapters = "".join(
        f'<section class="chapter" id="{cid}" aria-labelledby="{cid}-h"><p class="chnum">{"Chapter " + n if n != "–" else "Reference"}</p><h2 id="{cid}-h">{html.escape(t)}</h2>{b}</section>'
        for cid, n, t, b in CH)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sandwiches and per-block clearing: a study guide</title>
<style>{css}</style></head>
<body><a class="skip" href="#main">Skip to the chapters</a>
<div class="layout">
<nav class="toc" aria-label="Chapters"><a class="brand" href="#top">Study guide</a><ol>{toc}</ol></nav>
<main id="main">
<header class="cover" id="top"><p class="kicker">A student trynna learn · study guide</p>
<h1>Sandwiches and per-block clearing</h1>
<p>Everything you need to explain, and defend, one week of Uniswap sandwich attacks replayed through Chan, Wu &amp; Shi's two-phase mechanism.</p>
<p class="meta">Built {os.environ.get('BOOK_DATE', '2026-10-18')} from the study's results and tested code. Toy examples are labelled Illustration. rahil-design 3.x.</p></header>
{chapters}
<p class="foot">Sources: the study repository (<code>docs/methods.md</code>, <code>results/</code>), and the papers in the reading list. Toy numbers: <code>textbook/toy.py</code>. Nothing here has been published.</p>
</main></div>
<script>{JS}</script></body></html>"""


if __name__ == "__main__":
    out = os.path.join(HERE, "index.html")
    open(out, "w").write(page())
    print(f"wrote {out} ({os.path.getsize(out) / 1024:.0f} KB), {len(CH)} chapters")
