# Textbook plan: what Rahil needs to learn to own this study

## Reader, goal, test

- **Reader:** Rahil, before discussing the study with Ke Wu (mechanism design for AMMs) and Michael Wellman (market design, empirical game theory).
- **Goal:** explain every number in `docs/methods.md` in your own words, and answer the obvious follow-up questions without reading from notes.
- **Test of done:** for each chapter, you can answer its self-check questions with the answers hidden, and you can say the results paragraph (chapter 11) from memory.

## Skills used

- `rahil-design` 3.x owns identity: charcoal canvas, Anton display, IBM Plex Sans body, light figure panels with charcoal ink and one yellow emphasis, and the "student trynna learn" voice. It takes precedence over the explainer skill's light/dark theme default.
- `explainer` sets the format: one self-contained HTML page (ladder step 3), with hand-written inline SVG diagrams (step 2) and 80% STE prose, followed by its reader test.
- `present-data` and `tufte-graphics` cover the data figure and tables: a point sentence, zero baselines, direct labels, one accent, a figure brief, and the check script.

## Structure

Each chapter has the same parts:
- why you need it for this study
- the ideas
- one diagram or toy example
- "say it in one breath"
- self-check questions with hidden answers

Toy numbers are computed by `build.py`, never typed by hand, and every figure that uses them is labelled "Illustration". Real numbers are read from `results/`.

| # | Chapter | Diagram |
|---|---|---|
| 0 | How to use this book; the study in one page | Reading map |
| 1 | Ethereum blocks, ordering, builders and private order flow | Path of a transaction from wallet to block |
| 2 | AMMs: x·y = k, price, slippage, fees | Constant-product curve with one trade (toy) |
| 3 | Uniswap v3: concentrated liquidity, ticks, sqrtPriceX96 | Liquidity by tick range and a tick crossing |
| 4 | Sandwich attacks, minimum output and JIT liquidity | Price path: front-run, victim, back-run (toy) |
| 5 | Detecting sandwiches from logs | One block's transactions with the detection rules |
| 6 | Measuring loss: counterfactuals (a), (b), (c) and the exact-replay gate | Actual against no-attack timelines |
| 7 | Mechanism-design vocabulary: IC, arbitrage resilience, sequencing models | Plain model against weak fair-sequencing model |
| 8 | The Chan–Wu–Shi two-phase mechanism | Interactive: the same toy block under continuous execution and the mechanism |
| 9 | The Trilemma: IC, wLE, UP | Three properties, three mechanisms |
| 10 | Wellman's lens: call markets, latency arbitrage, EGTA | Continuous against batch clearing timeline |
| 11 | What the study found and how to say it | Cumulative-loss figure (real data) and results table |
| 12 | Meeting prep: likely questions, honest answers | none |
| – | Glossary and reading list | none |

## Build and checks

- `textbook/build.py` reads `results/*.csv` and `results/summary.json`, computes the toy examples, embeds the design system's fonts and tokens, and writes `textbook/index.html`. The page is self-contained and works offline.
- Toy-number unit checks run inside `build.py`, for example that the attacker's profit equals the pool's net flows.
- Render checks: `inspect_render.py` on the page at 1440 and 390 px wide.
- Figure checks: `check_figure.py` with a brief for the real-data figure.
- A manual read at desktop and phone width, then the explainer reader test (five-second, scan, jargon, biggest number, slant, uncertainty).
- Out of scope: publishing, posting, and sending anything.
