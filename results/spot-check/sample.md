# Sandwich spot-check sample

10 candidates drawn at random (seed 20261025) from 1607 detections. Labels are hidden: this file shows only what is on chain.

For each candidate, open the three links on Etherscan and decide:

- **S**: a sandwich. One address trades first in the block, a different user's swap on the same pool follows in the same direction, and the first address trades back the other way afterwards.
- **N**: not a sandwich (for example an arbitrage or a rebalance, or the middle swap is not a different user trading the same way).
- **U**: unsure.

On each transaction page, check the block position (`Position in block`) and the swap rows. Record the labels in `labels.csv`. Do not open `answer-key.csv` until you finish.

## Candidate 1

- Pool: WETH/USDT 0.01%
- Block: [26014839](https://etherscan.io/block/26014839)
- Possible front-run: [0x51414c0683a9531d9138080fd44a3da41a003626818847a20f905a2c29c03a11](https://etherscan.io/tx/0x51414c0683a9531d9138080fd44a3da41a003626818847a20f905a2c29c03a11)
- Possible victim 1: [0x66eeff1344acd598c7a9b521c5d2b4b71d80d85a95362b9b9afc76fb53d61b56](https://etherscan.io/tx/0x66eeff1344acd598c7a9b521c5d2b4b71d80d85a95362b9b9afc76fb53d61b56)
- Possible back-run: [0x5b7af118873a2e58763a69423468499a836015971498441e3f2656bc37a3ff7f](https://etherscan.io/tx/0x5b7af118873a2e58763a69423468499a836015971498441e3f2656bc37a3ff7f)

## Candidate 2

- Pool: WETH/USDT 0.01%
- Block: [26003336](https://etherscan.io/block/26003336)
- Possible front-run: [0x682c81120274be906e15ec33ce589b77f2030bfd1e3cafae274c2baa5e2ea8b1](https://etherscan.io/tx/0x682c81120274be906e15ec33ce589b77f2030bfd1e3cafae274c2baa5e2ea8b1)
- Possible victim 1: [0xc86c9e3af335b5e828e997232f465de1b8124cbe45f45f2adbf4d3ac84e36f35](https://etherscan.io/tx/0xc86c9e3af335b5e828e997232f465de1b8124cbe45f45f2adbf4d3ac84e36f35)
- Possible back-run: [0x83ee8587aea11f63d21274f3f02ecfdf94c06a73ee6d4a12541586876a5ad5d9](https://etherscan.io/tx/0x83ee8587aea11f63d21274f3f02ecfdf94c06a73ee6d4a12541586876a5ad5d9)

## Candidate 3

- Pool: USDC/WETH 0.05%
- Block: [26118100](https://etherscan.io/block/26118100)
- Possible front-run: [0xf0eedae363c6c51343e8f648e3dd2e87c80e497a6ccde12152b0bcf488436180](https://etherscan.io/tx/0xf0eedae363c6c51343e8f648e3dd2e87c80e497a6ccde12152b0bcf488436180)
- Possible victim 1: [0xe4390b995fc721af3959e9891d9f229474d3dd2781a5d70b5f3d7a3d63511cd2](https://etherscan.io/tx/0xe4390b995fc721af3959e9891d9f229474d3dd2781a5d70b5f3d7a3d63511cd2)
- Possible back-run: [0xf9706b9812183f4449ddcc74def0d1fe11434cc45a4a417e4596e50b22289880](https://etherscan.io/tx/0xf9706b9812183f4449ddcc74def0d1fe11434cc45a4a417e4596e50b22289880)

## Candidate 4

- Pool: USDC/WETH 0.01%
- Block: [26128031](https://etherscan.io/block/26128031)
- Possible front-run: [0x23524f3dd393b8747c281dd7b6f3d2242b3dcbab44c064990ed225015469a350](https://etherscan.io/tx/0x23524f3dd393b8747c281dd7b6f3d2242b3dcbab44c064990ed225015469a350)
- Possible victim 1: [0x34b65c493e6e60ac64fa2799a88000c476dc69d51b556fae21dc34bc51323684](https://etherscan.io/tx/0x34b65c493e6e60ac64fa2799a88000c476dc69d51b556fae21dc34bc51323684)
- Possible back-run: [0x2ca3677ebccca018b52b4e6a83f6ebf4cb7f3440a48cdd874d7c53ec8f639948](https://etherscan.io/tx/0x2ca3677ebccca018b52b4e6a83f6ebf4cb7f3440a48cdd874d7c53ec8f639948)

## Candidate 5

- Pool: USDC/WETH 0.01%
- Block: [26091295](https://etherscan.io/block/26091295)
- Possible front-run: [0xdf05acf8c904ee5d2130fb82b850f86563b61f180c88997f50cc7a68011d6bc2](https://etherscan.io/tx/0xdf05acf8c904ee5d2130fb82b850f86563b61f180c88997f50cc7a68011d6bc2)
- Possible victim 1: [0xc19afdf3fbcc427e8f17dc35e361e38e3a948c9b8846600d58ab12d6ae737c0e](https://etherscan.io/tx/0xc19afdf3fbcc427e8f17dc35e361e38e3a948c9b8846600d58ab12d6ae737c0e)
- Possible back-run: [0x0d75f77f0d570bb4965edfc48fbdde83ec8e86122bc9dc4a9c98e9a1fef966d3](https://etherscan.io/tx/0x0d75f77f0d570bb4965edfc48fbdde83ec8e86122bc9dc4a9c98e9a1fef966d3)

## Candidate 6

- Pool: WETH/USDT 0.01%
- Block: [26129864](https://etherscan.io/block/26129864)
- Possible front-run: [0xe85be7e80ceac03a9b227209450c1ea04a37a1a5b36cffeb143e48a8a08cbdb5](https://etherscan.io/tx/0xe85be7e80ceac03a9b227209450c1ea04a37a1a5b36cffeb143e48a8a08cbdb5)
- Possible victim 1: [0x8acd68e4fbefecd8d65cbcf009027e16b9a9387b03cbe28b9bcb486639cc853b](https://etherscan.io/tx/0x8acd68e4fbefecd8d65cbcf009027e16b9a9387b03cbe28b9bcb486639cc853b)
- Possible back-run: [0xfedc452d9be146dd840858a7d867f4b997f0c82702f829291bcaf2f8a59e3049](https://etherscan.io/tx/0xfedc452d9be146dd840858a7d867f4b997f0c82702f829291bcaf2f8a59e3049)

## Candidate 7

- Pool: WETH/USDT 0.01%
- Block: [26144436](https://etherscan.io/block/26144436)
- Possible front-run: [0xa3a00bf65186971876591baa5f5b4992926d7db0ff2c0526b92762e1cdbd6984](https://etherscan.io/tx/0xa3a00bf65186971876591baa5f5b4992926d7db0ff2c0526b92762e1cdbd6984)
- Possible victim 1: [0xb472d6dc5edd6b016838ea329a94ba2f64a1130e7606b8c6cdabe29ee4b73285](https://etherscan.io/tx/0xb472d6dc5edd6b016838ea329a94ba2f64a1130e7606b8c6cdabe29ee4b73285)
- Possible back-run: [0x0fd5d1c56236b4598cc63f3aaed2fb0a4cb631081a01e0e6c03f0c85cae9c1f2](https://etherscan.io/tx/0x0fd5d1c56236b4598cc63f3aaed2fb0a4cb631081a01e0e6c03f0c85cae9c1f2)

## Candidate 8

- Pool: WETH/USDT 0.01%
- Block: [26074090](https://etherscan.io/block/26074090)
- Possible front-run: [0x472feb04cd89c84c9934f67abd0e5a98485a4e8a901729c84cad2fd188993216](https://etherscan.io/tx/0x472feb04cd89c84c9934f67abd0e5a98485a4e8a901729c84cad2fd188993216)
- Possible victim 1: [0x54471497e9abad8eb5fe61bd989771d7676394d7cfd252ef3995b0feafc84fc5](https://etherscan.io/tx/0x54471497e9abad8eb5fe61bd989771d7676394d7cfd252ef3995b0feafc84fc5)
- Possible back-run: [0xb7d1cdcb8201a9fb092eda2fbf0834e3bc2ca882d893daf52d449b37ca33196a](https://etherscan.io/tx/0xb7d1cdcb8201a9fb092eda2fbf0834e3bc2ca882d893daf52d449b37ca33196a)

## Candidate 9

- Pool: WETH/USDT 0.01%
- Block: [26023128](https://etherscan.io/block/26023128)
- Possible front-run: [0xeab215f9aef7c67aae97432adb8dca5c61aeded80c62bd3dee74703b990c4f27](https://etherscan.io/tx/0xeab215f9aef7c67aae97432adb8dca5c61aeded80c62bd3dee74703b990c4f27)
- Possible victim 1: [0xadf99dd946c393d9cedcdb34c522d8ee3512943973e376cddb194aac771319fc](https://etherscan.io/tx/0xadf99dd946c393d9cedcdb34c522d8ee3512943973e376cddb194aac771319fc)
- Possible back-run: [0x9525772e22955350353946594fd81740702a21d2d8ddf48973c9048026ff50bf](https://etherscan.io/tx/0x9525772e22955350353946594fd81740702a21d2d8ddf48973c9048026ff50bf)

## Candidate 10

- Pool: USDC/WETH 0.01%
- Block: [26003222](https://etherscan.io/block/26003222)
- Possible front-run: [0xf64f05a8309c373c72510b24948f97667d3678eac9877f0cac33833e7d79667c](https://etherscan.io/tx/0xf64f05a8309c373c72510b24948f97667d3678eac9877f0cac33833e7d79667c)
- Possible victim 1: [0xc49a8aa0ed8d273fe21270cae78a7db2fe8b7ead0ad288fe25ac7498c441beeb](https://etherscan.io/tx/0xc49a8aa0ed8d273fe21270cae78a7db2fe8b7ead0ad288fe25ac7498c441beeb)
- Possible back-run: [0x1a23bd4d5a1e5850d744dabb57f92d96c469698cb670af979242ddaf38e95c58](https://etherscan.io/tx/0x1a23bd4d5a1e5850d744dabb57f92d96c469698cb670af979242ddaf38e95c58)
