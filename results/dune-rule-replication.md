# Dune spellbook rule, re-implemented locally (2026-10-18)

No Dune account was used. `scripts/dune_rule.py` re-implements the public spellbook macros `dex_sandwiches.sql` and `dex_sandwiched.sql`. They were read from the spellbook `main` branch on 2026-10-18. The script runs them on the same week of logs, and `scripts/compare_dune.py` compares the output with this study's detector. This tests the detector against an independently written rule; it is not a query run on Dune's data.

**Dune's rule:** same block and pool; front-run and back-run from the same sender, in opposite directions; at least one trade between them in the front-run's direction from another sender. There is no amount check. Victims are every same-direction trade between the legs.

| | This study | Dune rule | Both | Dune rule confirms ours | We find of Dune's |
|---|---:|---:|---:|---:|---:|
| Sandwich blocks | 236 | 255 | 235 | 99.6% | 92.2% |
| Attacker legs | 472 | 511 | 470 | 99.6% | 92.0% |
| Victims | 244 | 264 | 242 | 99.2% | 91.7% |

**Differences:**
- **The one block only we flag** (26,149,803): the two legs come from different sending addresses through the same bot contract, so Dune's same-sender rule misses it. Etherscan shows it as a probable sandwich by an arbitrage bot.
- **The 20 blocks only Dune's rule flags** all fail this study's amount check. Their back-run sold 0.00–2.00 times what the front-run bought: 12 below 0.9 and 8 above 1.1. 15 are by jaredfromsubway or 0x654f…, the same attackers as in the main set. So the study's count is conservative: these are probably sandwiches whose back-run also does something else, such as JIT liquidity or another position, which pushes the amount outside the 90–110% window.
