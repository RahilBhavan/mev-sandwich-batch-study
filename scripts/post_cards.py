"""The Oct 28 post cards (MEV 9:30 AM ET, slippage 6 PM ET) in Rahil Design: charcoal, off-white, yellow, Anton and IBM Plex Sans.

usage: uv run --with playwright==1.63.0 --with pillow --with numpy python scripts/post_cards.py [RESULTS]

Every number is computed from RESULTS/victims.csv and RESULTS/summary.json, so the cards cannot drift from the study.
Writes to RESULTS/post-cards/: the two 1080x1080 PNGs, the HTML each is drawn from, one alt-text file per card,
360px and 390px feed screenshots, measurements.json, palette-check.txt and SHA256SUMS. Exits 1 if any check fails.

Each card is authored on a 390px canvas (22px labels, 48px title) and exported at 1080px, so a 326px feed image
shows labels of 18.4px and a title of 40.1px, the floors in rahil-design's feed tokens.
"""
import base64
import csv
import hashlib
import html
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = HERE / "post-card-fonts"
CANVAS, SURFACE, INK, ACCENT = "#111214", "#F5F5EF", "#111214", "#FFE500"
CARD_RGB = {"#111214": (17, 18, 20), "#F5F5EF": (245, 245, 239), "#FFE500": (255, 229, 0)}
FEED_BG, FEED_MUTED, FEED_LINE = "#202124", "#B7B8B1", "#424348"  # surface, secondary and border tokens, for the review mockup only
BASE, EXPORT = 390, 1080
LABEL_PX, TITLE_PX = 22, 48
FEED_BOX = {360: 328, 390: 358}  # image width inside a feed of that width (16px gutters)
FEED_FLOOR = {"content": 326, "label": 18, "point": 40}
AS_OF = "Oct 17, 2026"
SOURCE = "mev-sandwich-batch-study"
FIREFOX = Path.home() / ".cache/ms-playwright/firefox-1555/firefox/firefox"


def num(x):
    return float(x) if x not in ("", None) else 0.0


def pct(share):
    return f"{share * 100:.1f}%"


def numbers(results):
    """Everything the two cards print, computed from the study's own files."""
    victims = list(csv.DictReader(open(Path(results) / "victims.csv")))
    summary = json.load(open(Path(results) / "summary.json"))
    loss = sum(num(v["loss_a_usd"]) for v in victims)
    recovered = lambda col: sum(min(max(num(v[col]), 0), num(v["loss_a_usd"])) for v in victims) / loss
    with_limit = [v for v in victims if v["slippage_slack_c_usd"] != ""]
    tolerance = sum(num(v["slippage_slack_c_usd"]) for v in with_limit)
    taken = sum(num(v["loss_a_usd"]) for v in with_limit)
    return dict(loss=loss, arrival=recovered("mech_gain_usd"), mean=recovered("mech_gain_mean"),
                p5=summary["prevented_share_static_random_p5"], p95=summary["prevented_share_static_random_p95"],
                draws=summary["draws"], victims=len(victims), with_limit=len(with_limit),
                tolerance=tolerance, taken=taken)


def cards(n):
    """The two cards as data. A '|' in a label is a deliberate line break."""
    assert n["draws"] == 200 and n["victims"] == 244 and n["with_limit"] == 115
    mev_rows = [("Arrival order", pct(n["arrival"]), False),
                ("Random tie-breaks,|mean of 200", pct(n["mean"]), True)]
    mev_range = f"5th–95th percentile: {n['p5']:.0%}–{n['p95']:.0%}"
    slip_rows = [("Tolerance set", f"${n['tolerance']:,.0f}", False), ("Taken by attackers", f"${n['taken']:,.0f}", False),
                 ("Share taken", f"{n['taken'] / n['tolerance']:.0%}", True)]
    return [
        dict(id="wed28-am-mev", slot="2026-10-28 09:30 ET",
             title=f"{n['arrival']:.0%} or {n['mean']:.0%}:|order matters.",
             context=f"Share of ${n['loss']:,.0f} loss recovered", rows=mev_rows, note=mev_range,
             foot=["Same orders, one WETH/USDT pool,", "Oct 5–11, 2026. Replay, not live.", f"Source: {SOURCE},",
                   f"data as of {AS_OF}."],
             alt=(f"{n['arrival']:.0%} or {n['mean']:.0%}: order matters. Share of the ${n['loss']:,.0f} sandwich loss recovered "
                  f"under per-block batch clearing, replaying the same orders in one WETH/USDT pool, Oct 5–11, 2026. "
                  f"Arrival order: {pct(n['arrival'])}. Random tie-breaks, mean of {n['draws']}: {pct(n['mean'])}, "
                  f"5th–95th percentile {n['p5']:.0%}–{n['p95']:.0%}. Counterfactual replay, not observed protocol behavior. "
                  f"Source: {SOURCE}, data as of {AS_OF}.")),
        dict(id="wed28-pm-mev-slippage", slot="2026-10-28 18:00 ET",
             title=f"{n['taken'] / n['tolerance']:.0%} of slippage|tolerance taken.",
             context=f"Dollars, {n['with_limit']} of {n['victims']} victims", rows=slip_rows,
             note="Summed dollars, not a median.",
             foot=["WETH/USDT, Oct 5–11, 2026.", "Nonzero decoded limits only.", f"Source: {SOURCE},",
                   f"data as of {AS_OF}."],
             alt=(f"{n['taken'] / n['tolerance']:.0%} of slippage tolerance taken. Dollar totals for {n['with_limit']} of "
                  f"{n['victims']} victims, the ones whose decoded minimum was not zero. Tolerance set: ${n['tolerance']:,.0f}. "
                  f"Taken by attackers: ${n['taken']:,.0f}. Share taken: {n['taken'] / n['tolerance']:.0%}, summed dollars rather "
                  f"than a median. WETH/USDT, Oct 5–11, 2026. Source: {SOURCE}, data as of {AS_OF}.")),
    ]


def b64(name):
    return base64.b64encode((FONTS / name).read_bytes()).decode()


def lines(text):
    return "<br>".join(html.escape(p) for p in text.split("|"))


def card_html(c):
    rows = "".join(
        f'<tr><th scope="row">{lines(label)}</th><td><span{" class=hi" if hi else ""}>{html.escape(value)}</span></td></tr>'
        for label, value, hi in c["rows"])
    css = f"""
@font-face{{font-family:'Rahil Display';src:url(data:font/ttf;base64,{b64('Anton-Regular.ttf')})}}
@font-face{{font-family:'Rahil Plex';font-weight:400;src:url(data:font/ttf;base64,{b64('IBMPlexSans-Regular.ttf')})}}
@font-face{{font-family:'Rahil Plex';font-weight:600;src:url(data:font/ttf;base64,{b64('IBMPlexSans-SemiBold.ttf')})}}
*{{box-sizing:border-box}}html,body{{margin:0}}
body{{width:{BASE}px;height:{BASE}px;background:{CANVAS};color:{SURFACE};font-family:'Rahil Plex';font-size:{LABEL_PX}px;line-height:1.08}}
article{{width:{BASE}px;height:{BASE}px;padding:16px 16px 14px;display:flex;flex-direction:column;gap:8px}}
h1{{font:{TITLE_PX}px/1.0 'Rahil Display';margin:0;text-transform:uppercase}}
.figure{{background:{SURFACE};color:{INK};border-radius:12px;padding:8px 12px;display:flex;flex-direction:column;gap:2px}}
.figure p{{margin:0}}.context{{font-weight:600}}
table{{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}}
th,td{{padding:1px 0;vertical-align:middle;font-weight:400}}
th{{text-align:left;padding-right:8px}}td{{text-align:right;white-space:nowrap;font-weight:600}}
.hi{{display:inline-block;background:{ACCENT};color:{INK};outline:2px solid {INK};padding:0 5px;margin:2px 2px 2px 0}}
.foot{{margin:0}}
"""
    body = (f'<article><h1>{lines(c["title"])}</h1><section class="figure" aria-label="{html.escape(c["context"], quote=True)}">'
            f'<p class="context">{html.escape(c["context"])}</p><table>{rows}</table><p class="note">{html.escape(c["note"])}</p></section>'
            f'<p class="foot">{lines("|".join(c["foot"]))}</p></article>')
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>'


MEASURE = r"""() => {
  const out = {sizes: [], problems: [], blocks: [], fonts: []};
  const art = document.querySelector('article').getBoundingClientRect();
  const hasText = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el);
    if (cs.transform !== 'none' || (cs.zoom && cs.zoom !== '1') || parseFloat(cs.opacity) < 1 || cs.filter !== 'none')
      out.problems.push('transform, zoom, opacity or filter on ' + el.tagName);
    if (!hasText(el)) continue;
    const rg = document.createRange(); rg.selectNodeContents(el); const r = rg.getBoundingClientRect();
    out.sizes.push([el.tagName.toLowerCase() + (el.className ? '.' + el.className : ''), parseFloat(cs.fontSize)]);
    out.fonts.push(cs.fontFamily.split(',')[0].replace(/["']/g, '').trim());
    if (r.right > art.right - 15.5 || r.left < art.left + 15.5 || r.bottom > art.bottom - 13.5)
      out.problems.push('outside its box: ' + el.textContent.trim().slice(0, 40));
  }
  const fig = document.querySelector('.figure'), fr = fig.getBoundingClientRect();
  for (const el of fig.querySelectorAll('*')) { const r = el.getBoundingClientRect();
    if (r.height && (r.top < fr.top - 0.5 || r.bottom > fr.bottom + 0.5 || r.right > fr.right + 0.5)) out.problems.push('figure child outside the figure: ' + el.textContent.trim().slice(0, 30)); }
  // Lines as drawn: group each text block's words by their top edge. A block that wraps may not leave a one-word line.
  for (const el of document.querySelectorAll('h1, th, p, td')) {
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT), tops = [];
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const re = /\S+/g; let m;
      while ((m = re.exec(n.textContent))) { const rg = document.createRange(); rg.setStart(n, m.index); rg.setEnd(n, m.index + m[0].length);
        const t = Math.round(rg.getClientRects()[0].top); tops.push(t); } }
    const uniq = [...new Set(tops)], counts = uniq.map(t => tops.filter(x => x === t).length);
    out.blocks.push({text: el.textContent.trim(), lines: uniq.length, words_per_line: counts});
    if (uniq.length > 1 && counts.includes(1)) out.problems.push('one-word line in: ' + el.textContent.trim());
  }
  const ctx = document.createElement('canvas').getContext('2d'), sample = 'Hamburgefonstiv 0123456789';
  const width = f => { ctx.font = f; return ctx.measureText(sample).width; };
  for (const fam of ['Rahil Display', 'Rahil Plex']) {
    const loaded = [...document.fonts].some(f => f.family.replace(/["']/g, '') === fam && f.status === 'loaded');
    const w = width(`40px "${fam}", serif`);
    if (!loaded || [width('40px serif'), width('40px sans-serif'), width('40px monospace')].some(a => Math.abs(a - w) < 0.5))
      out.problems.push(fam + ' not loaded; a fallback is drawn');
  }
  return out;
}"""


def feed_html(png, width):
    """A review mockup of the image inside a feed of this width. It uses the surface, ink and secondary tokens."""
    box = FEED_BOX[width]
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>*{{box-sizing:border-box}}body{{margin:0;background:{FEED_BG};color:{SURFACE};'
            f'font:16px/1.3 sans-serif;width:{width}px;padding:16px}}.user{{font-weight:bold;margin-bottom:12px}}.user small{{font-weight:normal;color:{FEED_MUTED}}}'
            f'img{{width:{box}px;display:block;border:1px solid {FEED_LINE};border-radius:12px}}.label{{color:{FEED_MUTED};font-size:14px;margin:12px 0}}</style></head>'
            f'<body><div class="user">Rahil Bhavan <small>@Bhavanzim</small></div><img src="../{Path(png).name}">'
            f'<div class="label">Review mockup at {width}px · design review pending</div></body></html>')


def palette_report(png):
    """Every pixel must be one of the three colours or an anti-aliased blend of two of them."""
    import itertools
    import numpy as np
    from PIL import Image
    px = np.asarray(Image.open(png).convert("RGB")).astype(float)
    flat = px.reshape(-1, 3)
    cols = list(CARD_RGB.values())
    exact = {name: int((np.abs(flat - np.array(rgb)).max(axis=1) <= 1).sum()) for name, rgb in CARD_RGB.items()}
    near = np.zeros(len(flat), bool)
    for a, b in itertools.combinations_with_replacement(cols, 2):
        a, b = np.array(a, float), np.array(b, float)
        ab = b - a
        t = np.clip(((flat - a) @ ab) / max(ab @ ab, 1), 0, 1)
        near |= np.linalg.norm(flat - (a + t[:, None] * ab), axis=1) <= 6
    off = int((~near).sum())
    return dict(size=Image.open(png).size, pixels=len(flat), exact=exact, blended=int(near.sum()) - sum(exact.values()), off_palette=off)


def main(results="results"):
    from playwright.sync_api import sync_playwright
    out = Path(results) / "post-cards"
    (out / "feed").mkdir(parents=True, exist_ok=True)
    n = numbers(results)
    report, failed, hashes = {}, False, []
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True, executable_path=str(FIREFOX) if FIREFOX.exists() else None)
        for c in cards(n):
            html_path, png = out / f"{c['id']}.html", out / f"{c['id']}-square.png"
            html_path.write_text(card_html(c))
            page = browser.new_page(viewport={"width": BASE, "height": BASE}, device_scale_factor=EXPORT / BASE)
            page.goto(html_path.resolve().as_uri())
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(300)
            m = page.evaluate(MEASURE)
            page.screenshot(path=str(png))
            page.close()
            for width in FEED_BOX:
                feed = browser.new_page(viewport={"width": width, "height": 520}, device_scale_factor=2)
                (out / "feed" / f"{c['id']}-{width}.html").write_text(feed_html(png, width))
                feed.goto((out / "feed" / f"{c['id']}-{width}.html").resolve().as_uri())
                feed.wait_for_timeout(200)
                feed.screenshot(path=str(out / "feed" / f"{c['id']}-{width}.png"), full_page=True)
                feed.close()
            (out / f"{c['id']}.alt.txt").write_text(c["alt"] + "\n")
            sizes = [s for _, s in m["sizes"]]
            pal = palette_report(png)
            problems = list(m["problems"])
            if pal["size"] != (EXPORT, EXPORT):
                problems.append(f"PNG is {pal['size']}, not {EXPORT}x{EXPORT}")
            if pal["off_palette"]:
                problems.append(f"{pal['off_palette']} off-palette pixels")
            if min(sizes) < LABEL_PX or max(sizes) < TITLE_PX:
                problems.append("text below the canvas floors")
            if set(m["fonts"]) - {"Rahil Display", "Rahil Plex"}:
                problems.append("non-token font in use")
            if "\n" in c["alt"] or "  " in c["alt"]:
                problems.append("alt text has a stray line break or double space")
            shown = {w: dict(label_px=round(min(sizes) * (box / BASE), 1), title_px=round(max(sizes) * (box / BASE), 1)) for w, box in FEED_BOX.items()}
            shown["326 (floor box)"] = dict(label_px=round(min(sizes) * FEED_FLOOR["content"] / BASE, 1), title_px=round(max(sizes) * FEED_FLOOR["content"] / BASE, 1))
            if shown["326 (floor box)"]["label_px"] < FEED_FLOOR["label"] or shown["326 (floor box)"]["title_px"] < FEED_FLOOR["point"]:
                problems.append("below the feed floors at 326px")
            sha = hashlib.sha256(png.read_bytes()).hexdigest()
            hashes.append(f"{sha}  {png.name}")
            report[c["id"]] = dict(slot=c["slot"], png=png.name, sha256=sha, canvas_px=BASE, min_label_px=min(sizes), title_px=max(sizes),
                                   displayed_px=shown, blocks=m["blocks"], palette=pal, problems=problems)
            failed |= bool(problems)
            brief = dict(id=c["id"], title=c["title"].replace("|", " "), sizes_checked=[f"{BASE}x{BASE}"],
                         measurement_basis="canvas", measured_by="post_cards.py/firefox", min_label_px=min(sizes),
                         point_px=max(sizes), alt=c["alt"], artifacts={png.name: sha})
            (out / f"{c['id']}.brief.json").write_text(json.dumps(brief, indent=2, ensure_ascii=False) + "\n")
        browser.close()
    (out / "measurements.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    (out / "SHA256SUMS").write_text("\n".join(hashes) + "\n")
    lines_ = ["Palette check: every pixel must be #111214, #F5F5EF, #FFE500 or an anti-aliased blend of two of them (RGB distance <= 6)."]
    for k, r in report.items():
        pal = r["palette"]
        lines_.append(f"{r['png']}: {pal['size'][0]}x{pal['size'][1]}, {pal['pixels']} px; exact "
                      + ", ".join(f"{name} {count}" for name, count in pal["exact"].items())
                      + f"; anti-aliased blends {pal['blended']}; off-palette {pal['off_palette']}; "
                      + ("PASS" if not pal["off_palette"] else "FAIL"))
    (out / "palette-check.txt").write_text("\n".join(lines_) + "\n")
    for k, r in report.items():
        print(k, r["sha256"], "min label", r["min_label_px"], "title", r["title_px"], "problems:", r["problems"] or "none")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
