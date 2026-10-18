-- Cross-check for the detector (plan day 5). Run once in a Dune trial session and export as CSV.
-- Spellbook tables dex.sandwiches (attacker legs) and dex.sandwiched (victims); column names follow the
-- spellbook macro dex_sandwiches.sql and were not verified against the live schema. Fix them in the editor if needed.
SELECT 'leg' AS role, block_number, tx_hash, tx_from, tx_to
FROM dex.sandwiches
WHERE blockchain = 'ethereum'
  AND project_contract_address = 0xc7bbec68d12a0d1830360f8ec58fa599ba1b0e9b
  AND block_number BETWEEN 26122440 AND 26172657
UNION ALL
SELECT 'victim' AS role, block_number, tx_hash, tx_from, tx_to
FROM dex.sandwiched
WHERE blockchain = 'ethereum'
  AND project_contract_address = 0xc7bbec68d12a0d1830360f8ec58fa599ba1b0e9b
  AND block_number BETWEEN 26122440 AND 26172657
ORDER BY block_number
