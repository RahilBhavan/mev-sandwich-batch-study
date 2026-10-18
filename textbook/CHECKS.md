# Textbook checks (2026-10-18)

Output: `textbook/index.html`, one self-contained file of about 844 KB. Fonts are embedded and it works offline. Rebuild it with `.venv/bin/python textbook/build.py`.

## What was exercised

- **Numbers.**
  - Every toy number comes from `textbook/toy.py`, which runs the study's tested `mev/v3.py` and `mev/mechanism.py` on a full-range v3 position (exactly x·y = k).
  - Assertions in `toy.py`: the sandwiched victim gets at least its minimum, the attacker profits in the continuous market, the attacker's net is ≤ 0 in every mechanism scenario, and the victim-first outcome is at least the no-attack outcome.
  - Real numbers are read from `results/summary.json` and `results/*.csv` at build time.
- **Render.**
  - Headless Chromium screenshots of every chapter at 1440 px and 390 px. No console errors.
  - The page width equals the viewport at both sizes (no sideways page scroll).
  - On narrow screens, figures scroll sideways inside their own box, with a visible hint.
- **`present-data` inspector** (`inspect_render.py`), run with all answer boxes expanded:
  - no text overlaps;
  - lowest contrast 5.93:1;
  - smallest text 13 px at both widths.
  - Two kinds of finding don't apply and were not fixed:
    - "Clipped" below the first screen: the inspector is built for fixed-size cards, not long pages.
    - "Text on rect": labels deliberately placed inside diagram boxes.
- **`present-data` brief check** for the one real-data figure (chapter 11, `figure-brief-results.json`): PASS. Its labels render at 16 px on desktop and phone.
- **Interaction.**
  - The chapter 8 step-through moves through 4 steps and highlights the matching bars.
  - Previous and Next disable at the ends.
  - With JavaScript off, the buttons are hidden and all steps stay readable.
- **Explainer reader test.**
  - *Five-second test:* the cover and chapter 0 give the topic and the five headline claims.
  - *Scan test:* the chapter titles, "say it in one breath" lines and figure captions carry the argument.
  - *Jargon pass:* each term is defined at first use. MEV was the one gap, and it is now defined in chapter 1.
  - *Biggest number:* $12,387 and 236 appear in chapter 0 and chapter 11.
  - *Slant:* the static range (52–99%) is shown next to the "deterred ≈ 100%" figure, never alone.
  - *Uncertainty:* given as ranges and percentiles.

## Decisions and limits

- `rahil-design` sets the look: charcoal page, Anton display type, IBM Plex body type, light figure panels, and one yellow accent with a charcoal outline. The explainer skill's light/dark theme default was not used, because the design system fixes the identity.
- The page uses agent-authored neutral wording, not invented first-person experience. The suggested results paragraph is neutral, with a reminder to describe your own role accurately, including AI assistance.
- The only reader test so far is the agent's. Rahil reading it is the real one.
- Nothing has been published or posted.
