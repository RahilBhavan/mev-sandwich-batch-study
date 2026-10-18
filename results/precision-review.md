# Detection precision check (plan day 5)

Reviewed 2026-10-17 by the agent, one row at a time, from on-chain evidence: full receipts of each leg and victim, the weekly sender count of each target contract, and ENS reverse names resolved on chain. Sample: 30 of 236 hits drawn with `random.Random(30)` in `scripts/inspect_hits.py` output order. Etherscan pages were not opened; the same facts come from the receipts. A human spot-check of five of these on Etherscan is still worth doing before sending.

Verdict key: **S** = sandwich (private bot contract, same EOA on both legs, victim trades in the front-run's direction through a public router or its own wallet, back-run sells back what the front-run bought). **S-loss** = same structure, but the attacker's legs lost money on this pool. **S-arb** = sandwich whose front-run also routes through other pools.

| Block | Attacker | Ratio | Front pools | Victim target senders | Victim loss | Attacker gross | Verdict |
|---:|---|---:|---:|---|---:|---:|---|
| 26148949 | mevrevolutionx.eth | 1.000 | 1 | 234 | $13.45 | $10.72 | S |
| 26165600 | jaredfromsubway.eth | 0.925 | 1 | 234 | $8.21 | $-4.48 | S-loss |
| 26136920 | mevrevolutionx.eth | 1.000 | 1 | 234 | $5.14 | $0.74 | S |
| 26152729 | 0xdee2f2b8… | 1.000 | 1 | 234 | $0.43 | $0.15 | S |
| 26125685 | jaredfromsubway.eth | 1.000 | 1 | 468 | $57.03 | $6.21 | S |
| 26153313 | jaredfromsubway.eth | 0.933 | 1 | 234 | $7.85 | $-4.54 | S-loss |
| 26155796 | jaredfromsubway.eth | 1.000 | 1 | 2963 | $7.74 | $5.48 | S |
| 26167942 | 0x654fae4a… | 1.000 | 1 | 234 | $16.43 | $8.24 | S |
| 26133455 | 0xe3d5e8d7… | 1.000 | 1 | 234 | $8.11 | $3.64 | S |
| 26134934 | mevrevolutionx.eth | 1.000 | 1 | 2963 | $91.60 | $69.90 | S |
| 26127208 | jaredfromsubway.eth | 1.000 | 1 | 2963 | $5.75 | $1.43 | S |
| 26141797 | jaredfromsubway.eth | 1.000 | 3 | 2963 | $22.10 | $17.99 | S-arb |
| 26141326 | 0x654fae4a… | 1.000 | 1 | 328 | $4.12 | $1.33 | S |
| 26155521 | mevrevolutionx.eth | 1.000 | 1 | 1144 | $124.87 | $69.34 | S |
| 26132340 | mevrevolutionx.eth | 1.000 | 1 | 234 | $13.62 | $9.12 | S |
| 26128523 | mevrevolutionx.eth | 1.000 | 1 | 234 | $18.20 | $13.71 | S |
| 26145085 | jaredfromsubway.eth | 0.927 | 1 | 234 409 | $16.30 | $-4.61 | S-loss |
| 26122729 | mevrevolutionx.eth | 1.000 | 1 | 234 | $9.14 | $4.61 | S |
| 26148550 | 0x595caa1c… | 1.000 | 1 | 234 | $28.39 | $24.58 | S |
| 26134300 | jaredfromsubway.eth | 1.000 | 1 | 1144 | $47.89 | $21.00 | S |
| 26125091 | 0xdee2f2b8… | 1.000 | 1 | 234 | $2.63 | $0.31 | S |
| 26128469 | mevrevolutionx.eth | 1.000 | 1 | 234 | $15.20 | $10.98 | S |
| 26133074 | 0xe3d5e8d7… | 1.000 | 1 | 2963 | $13.41 | $2.74 | S |
| 26166744 | 0xef126872… | 1.000 | 1 | 1144 | $13.45 | $1.00 | S |
| 26150201 | mevrevolutionx.eth | 1.000 | 1 | 1 | $17.56 | $13.98 | S |
| 26148807 | mevrevolutionx.eth | 1.000 | 1 | 1 | $44.56 | $25.51 | S |
| 26142246 | mevrevolutionx.eth | 1.000 | 1 | 1 | $47.75 | $30.51 | S |
| 26170917 | 0x595caa1c… | 1.000 | 2 | 2963 | $4.65 | $0.51 | S-arb |
| 26140042 | mevrevolutionx.eth | 1.000 | 1 | 1 | $5.25 | $1.85 | S |
| 26148912 | mevrevolutionx.eth | 1.000 | 1 | 2963 | $332.35 | $298.71 | S |

Result: 30 of 30 have the sandwich structure ({'S': 25, 'S-loss': 3, 'S-arb': 2}). None is a false positive in the sense of a victim that was not traded against. The S-loss rows are jaredfromsubway attempts whose back-run sold back about 92–93% of the front-run; their victims still lost the amounts shown.

A victim target with 1 sender is usually the user's own smart account (ERC-7579 `execute` or EIP-7702 batch selectors), not a bot. Full evidence for all 236 hits: `results/precision-evidence.csv`.