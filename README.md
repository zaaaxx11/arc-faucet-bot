# ARC Testnet Automation Bot

Full on-chain activity automation for Arc Testnet (chain ID 5042002). Generates 10+ transactions per wallet.

## Features

- **Faucet** — Auto-claim USDC
- **OnChain GM** — Daily GM with referrer
- **Swap** — USDC↔EURC random swaps (5-10x per wallet)
- **Bridge** — Cross-chain USDC bridge (30% chance)
- **LP** — Add liquidity to USDC-EURC pool (30% chance)
- **Send** — Random USDC transfers to external/internal addresses (2-4x)

## Setup

```bash
pip install requests python-dotenv eth-account eth-abi
cp .env.example .env
# Edit .env with your config
# Add wallets.json with your wallet keys (see wallets_example.json)
python arc_automation.py
```

## Faucet Only (with reCAPTCHA solver)

```bash
python faucet_claim.py
```

## Config (.env)

| Variable | Description |
|---|---|
| `RPC_URL` | Arc Testnet RPC (default: rpc.testnet.arc.network) |
| `CHAIN_ID` | Chain ID (default: 5042002) |
| `WALLETS_FILE` | Path to wallets JSON (default: wallets.json) |
| `CAPTCHA_API_KEY` | 2captcha/sctg API key (faucet_claim.py only) |
| `CAPTCHA_BASE` | Captcha service URL |

## Wallet Format

```json
[
  {"address": "0x...", "pk": "abcdef1234..."},
  {"address": "0x...", "pk": "abcdef4567..."}
]
```

## Chain Info

- Network: Arc Testnet
- Chain ID: 5042002
- Explorer: https://testnet.arcscan.app
- Rate limit (faucet): 20 USDC per address per 2 hours

## Contracts

| Contract | Address |
|---|---|
| USDC | `0x3600...0000` |
| EURC | `0x89B5...D72a` |
| Swap Router | `0x7374...1023` |
| GM | `0x363c...a43` |
| Bridge | `0xC556...363d` |
| LP Pool | `0x3DF3...bB1` |
