# design-owner: rahil-design because these are Rahil's public X cards (the 3.x charcoal / off-white / yellow card family, Anton + IBM Plex Sans)
"""The two Wed Oct 28 X cards: wed28-am-mev (replay) and wed28-pm-mev-slippage (slippage tolerance).

usage: python scripts/x_cards.py [RESULTS]          # specs + alt text only, no browser
       python scripts/x_cards.py --render [RESULTS]  # also card.html, card.png (1080x1080) and brief.json

Every number comes from RESULTS/summary.json and RESULTS/victims.csv. Rendering needs Playwright with Firefox
(`uv run --with playwright==1.63.0 python scripts/x_cards.py --render`) and the rahil-design bundle for its tokens and
fonts (RAHIL_DESIGN, default: the hub's .agents/skills/rahil-design). Cards are 390px authored and exported at 1080px.
Text is fixed by the request, so each card draws its labels at the largest size at which everything fits; brief.json
records that size against the 22px label floor.
"""
import base64
import csv
import hashlib
import html
import json
import os
import struct
import sys

BUNDLE = os.environ.get("RAHIL_DESIGN", "/home/rahil/.t3/projects/main/.agents/skills/rahil-design")
FIREFOX = os.path.expanduser("~/.cache/ms-playwright/firefox-1555/firefox/firefox")
SIZE, EXPORT, TITLE_PX, LABEL_FLOOR, PAD = 390, 1080, 48, 22, 14
SCOPE = "busiest WETH/USDT pool, Oct 5–11, 2026"
REPLAY_AXIS = "Share of ${loss} sandwich loss recovered (counterfactual replay)"
SLIPPAGE_AXIS = "Slippage tolerance (no-attack output − victim's minimum), {n} of {victims} victims with decoded nonzero limits"


def num(x):
    return float(x) if x not in ("", None) else 0.0


def tolerance(results):
    """Victims with a decoded nonzero limit, their summed tolerance, and the dollars attackers took of it."""
    vic = [y for y in csv.DictReader(open(os.path.join(results, "victims.csv"))) if num(y["slippage_slack_c_usd"]) > 0]
    slack = sum(num(y["slippage_slack_c_usd"]) for y in vic)
    taken = sum(min(num(y["loss_a_usd"]), num(y["slippage_slack_c_usd"])) for y in vic)
    return len(vic), slack, taken


def replay_spec(s):
    pct = lambda k: 100 * s[k]
    arrival, mean = pct("prevented_share_static_arrival"), pct("prevented_share_static_random_mean")
    p5, p95 = pct("prevented_share_static_random_p5"), pct("prevented_share_static_random_p95")
    title = f"Replay recovered {mean:.0f}%. Arrival order: {arrival:.0f}%."
    axis = REPLAY_AXIS.format(loss=f"{s['loss_a_usd']:,.0f}")
    source = f"Source: mev-sandwich-batch-study replay · {SCOPE}"
    band = f"Random orders: {p5:.0f}–{p95:.0f}%, mean {mean:.0f}%"
    return {
        "id": "wed28-am-mev", "kind": "range", "title": title, "axis": axis, "source": source,
        "scale": [0, 100], "arrival": arrival, "mean": mean, "band": [p5, p95],
        "arrival_text": f"{arrival:.0f}%", "band_text": band,
        "alt": (f"{title} {axis}, on a 0–100% scale: arrival order {arrival:.0f}%; across {s['draws']} random "
                f"tie-break orders, the mean is {mean:.0f}% (marked on the random-orders bar) and the middle 90% "
                f"recovered {p5:.0f}–{p95:.0f}%. Same orders, one pool. {source}."),
    }


def slippage_spec(s, n, slack, taken):
    left, share = slack - taken, taken / slack
    title = f"{share:.0%} of the tolerance, taken."
    axis = SLIPPAGE_AXIS.format(n=n, victims=s["victims"])
    source = f"Source: mev-sandwich-batch-study methods.md · {SCOPE}"
    return {
        "id": "wed28-pm-mev-slippage", "kind": "fill", "title": title, "axis": axis, "source": source,
        "share": share, "taken_text": f"Taken ${taken:,.0f}", "left_text": f"Left ${left:,.0f}",
        "alt": (f"{title} {axis}: their slippage tolerance summed to ${slack:,.0f}; attackers took ${taken:,.0f} of it "
                f"and left ${left:,.0f}. A ratio of summed dollars over that subset, not a per-victim median or all "
                f"trades. {source}."),
    }


def specs(results="results"):
    s = json.load(open(os.path.join(results, "summary.json")))
    n, slack, taken = tolerance(results)
    assert n == s["victims_with_slack_c"] and abs(slack - s["slippage_slack_c_usd"]) < 0.01
    return [replay_spec(s), slippage_spec(s, n, slack, taken)]


def esc(x):
    return html.escape(x)


def figure_html(spec):
    if spec["kind"] == "fill":
        return (f'<div class="axis">{esc(spec["axis"])}</div><div class="gauge"><span class="used" '
                f'style="width:{100 * spec["share"]:.2f}%"></span></div>'
                f'<div class="ends"><span>{esc(spec["taken_text"])}</span><span>{esc(spec["left_text"])}</span></div>')
    pct = lambda v: f"{v:.2f}%"
    lo, hi = spec["band"]
    return (f'<div class="axis">{esc(spec["axis"])}</div>'
            f'<div class="strip"><span class="lab right">{esc(spec["band_text"])}</span>'
            f'<div class="plot"><span class="track"></span>'
            f'<span class="band" style="left:{pct(lo)};width:{pct(hi - lo)}"></span>'
            f'<span class="tick" style="left:{pct(spec["mean"])}"></span>'
            f'<span class="dot" style="left:{pct(spec["arrival"])}"></span></div>'
            f'<div class="scale"><span class="lab">0%</span>'
            f'<span class="lab mid" style="left:{pct(spec["arrival"])}">Arrival order '
            f'<span class="focus">{esc(spec["arrival_text"])}</span></span><span class="lab">100%</span></div></div>')


def card_html(spec, label_px):
    sys.path.insert(0, os.path.join(BUNDLE, "scripts"))
    from chart_theme import FONTS, T
    font = lambda n: base64.b64encode((FONTS / n).read_bytes()).decode()
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><style>
@font-face{{font-family:'Rahil Display';src:url(data:font/ttf;base64,{font('Anton-Regular.ttf')})}}
@font-face{{font-family:'Rahil Plex';src:url(data:font/ttf;base64,{font('IBMPlexSans-Regular.ttf')})}}
*{{box-sizing:border-box}}html,body{{margin:0}}
body{{width:{SIZE}px;height:{SIZE}px;background:{T['canvas']};color:{T['ink']};font-family:'Rahil Plex',sans-serif}}
article{{width:{SIZE}px;height:{SIZE}px;padding:{PAD}px;display:grid;grid-template-rows:auto minmax(0,1fr) auto;gap:6px}}
h1{{font:{TITLE_PX}px/1.0 'Rahil Display',sans-serif;margin:0;text-transform:uppercase;overflow-wrap:anywhere}}
.figure>*{{flex:none}}
.figure{{background:{T['figure-surface']};color:{T['figure-ink']};border-radius:12px;padding:10px;display:flex;
flex-direction:column;justify-content:center;gap:4px;font-size:{label_px}px;line-height:1.15;font-variant-numeric:tabular-nums}}
.axis{{color:{T['figure-secondary']}}}
.focus{{display:inline-block;background:{T['chart-highlight']};outline:2px solid {T['chart-series-1']};outline-offset:-2px;padding:0 4px}}
.source{{font-size:{label_px}px;line-height:1.15;color:{T['ink']};margin:0}}
.strip{{display:flex;flex-direction:column;gap:2px;margin-top:4px}}
.lab{{white-space:nowrap}}.right{{align-self:flex-end}}
.plot{{position:relative;height:26px}}.plot>span{{position:absolute;display:block}}
.track{{left:0;right:0;top:12px;height:2px;background:{T['chart-grid']}}}
.band{{top:4px;height:18px;background:{T['chart-series-3']}}}
.tick{{top:0;height:26px;width:3px;margin-left:-1.5px;background:{T['chart-series-1']}}}
.dot{{top:4px;height:18px;width:8px;margin-left:-4px;background:{T['chart-highlight']};outline:2px solid {T['chart-series-1']};outline-offset:-2px}}
.scale{{position:relative;display:flex;justify-content:space-between}}.mid{{position:absolute;transform:translateX(-50%)}}
.gauge{{display:flex;height:18px;border:2px solid {T['figure-ink']};background:{T['figure-surface']}}}
.used{{display:block;background:{T['chart-highlight']};border-right:2px solid {T['figure-ink']}}}
.ends{{display:flex;justify-content:space-between;gap:12px;white-space:nowrap}}</style></head><body><article>
<h1>{esc(spec['title'])}</h1><div class="figure">{figure_html(spec)}</div><p class="source">{esc(spec['source'])}</p></article></body></html>"""


MEASURE = """() => {
  const out = {overflow: []};
  const art = document.querySelector('article').getBoundingClientRect(), pad = %d;
  for (const el of document.querySelectorAll('body *')) {
    if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
    const r = el.getBoundingClientRect();
    if (r.right > art.right - pad + 0.5 || r.bottom > art.bottom - pad + 0.5 || r.left < art.left + pad - 0.5)
      out.overflow.push(el.textContent.slice(0, 30));
  }
  const fig = document.querySelector('.figure'), fr = fig.getBoundingClientRect(), fp = parseFloat(getComputedStyle(fig).paddingLeft);
  if (fig.scrollHeight > fig.clientHeight + 1) out.overflow.push('figure content taller than its box');
  for (const el of fig.querySelectorAll('*')) { const r = el.getBoundingClientRect();
    if (r.height && (r.top < fr.top - 0.5 || r.bottom > fr.bottom + 0.5 || r.right > fr.right - fp + 0.5 || r.left < fr.left + fp - 0.5))
      out.overflow.push('outside the figure: ' + el.textContent.slice(0, 30)); }
  const lines = el => Math.round(el.getBoundingClientRect().height / (parseFloat(getComputedStyle(el).fontSize) * (el.tagName === 'H1' ? 1 : 1.15)));
  out.title_lines = lines(document.querySelector('h1'));
  out.footer_lines = lines(document.querySelector('.source'));
  out.axis_lines = lines(document.querySelector('.axis'));
  out.fonts = ['Rahil Display', 'Rahil Plex'].map(f => [f, [...document.fonts].some(x => x.family.replace(/["']/g, '') === f && x.status === 'loaded')]);
  // Labels inside the strip and gauge rows must stay on one line; only the panel label and the footer may wrap.
  out.wrapped = [...document.querySelectorAll('.strip .lab, .ends span')].filter(el => lines(el) > 1).map(el => el.textContent);
  const row = [...document.querySelectorAll('.strip .lab')].map(e => { const r = document.createRange(); r.selectNodeContents(e); return r.getBoundingClientRect(); });
  for (let i = 0; i < row.length; i++) for (let j = i + 1; j < row.length; j++)
    if (row[i].top < row[j].bottom && row[j].top < row[i].bottom && row[i].left < row[j].right && row[j].left < row[i].right) out.overflow.push('labels overlap');
  const g = document.querySelector('.gauge');
  if (g && g.getBoundingClientRect().height < 18) out.overflow.push('gauge squeezed to ' + g.getBoundingClientRect().height);
  return out;
}""" % PAD


def png_size(data):
    return struct.unpack(">II", data[16:24])


def render(spec, out_dir, browser):
    """Draw the card at the largest label size (0.5px steps, at most the 22px floor) where nothing overflows."""
    page = browser.new_page(viewport={"width": SIZE, "height": SIZE}, device_scale_factor=EXPORT / SIZE)
    label_px = LABEL_FLOOR
    while True:
        page.set_content(card_html(spec, label_px))
        page.evaluate("document.fonts.ready")
        m = page.evaluate(MEASURE)
        if not m["overflow"] and not m["wrapped"] or label_px <= 12:
            break
        label_px -= 0.5
    os.makedirs(out_dir, exist_ok=True)
    html_text = page.content()
    png = page.screenshot(clip={"x": 0, "y": 0, "width": SIZE, "height": SIZE})
    page.close()
    assert png_size(png) == (EXPORT, EXPORT), png_size(png)
    for name, data in (("card.html", html_text.encode()), ("card.png", png), ("alt.txt", (spec["alt"] + "\n").encode())):
        with open(os.path.join(out_dir, name), "wb") as f:
            f.write(data)
    brief = {
        "id": spec["id"], "export_px": [EXPORT, EXPORT], "authored_px": SIZE, "title_px": TITLE_PX, "label_px": label_px,
        "min_label_px": label_px, "point_px": TITLE_PX, "measurement_basis": "canvas", "sizes_checked": ["1080x1080", "390x390"],
        "label_floor_px": LABEL_FLOOR, "label_px_at_326_feed": round(label_px * 326 / SIZE, 1),
        "title_px_at_326_feed": round(TITLE_PX * 326 / SIZE, 1), "title_lines": m["title_lines"],
        "axis_lines": m["axis_lines"], "footer_lines": m["footer_lines"], "fonts_loaded": m["fonts"],
        "overflow": m["overflow"], "wrapped": m["wrapped"], "text": {"title": spec["title"], "axis": spec["axis"], "footer": spec["source"]},
        "meets_label_floor": label_px >= LABEL_FLOOR, "design_status": "pending",
        "sha256": {n: hashlib.sha256(open(os.path.join(out_dir, n), "rb").read()).hexdigest() for n in ("card.html", "card.png")},
    }
    with open(os.path.join(out_dir, "brief.json"), "w") as f:
        json.dump(brief, f, indent=1, ensure_ascii=False)
        f.write("\n")
    return brief


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    results = args[0] if args else "results"
    out = os.path.join(results, "x-cards")
    cards = specs(results)
    for spec in cards:
        os.makedirs(os.path.join(out, spec["id"]), exist_ok=True)
        with open(os.path.join(out, spec["id"], "spec.json"), "w") as f:
            json.dump(spec, f, indent=1, ensure_ascii=False)
            f.write("\n")
        print("wrote", os.path.join(out, spec["id"], "spec.json"))
    if "--render" in sys.argv:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.firefox.launch(executable_path=FIREFOX) if os.path.exists(FIREFOX) else p.firefox.launch()
            for spec in cards:
                b = render(spec, os.path.join(out, spec["id"]), browser)
                print(spec["id"], "label_px", b["label_px"], "title_lines", b["title_lines"], "overflow", b["overflow"], "wrapped", b["wrapped"])
            browser.close()
