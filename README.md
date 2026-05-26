# ARC Testnet Automation Bot

Automated on-chain activity bot for [Arc Testnet](https://testnet.arcscan.app) (Chain ID: 5042002). Runs multiple DeFi interactions across your wallets to build consistent on-chain presence.

## What It Does

For each wallet, the bot automatically:

- **Faucet** — Claims testnet USDC from the faucet
- **OnChain GM** — Sends daily GM greetings on-chain
- **Swap** — Trades between USDC and EURC via the swap router
- **Bridge** — Bridges USDC cross-chain to external addresses
- **Liquidity** — Adds liquidity to the USDC/EURC pool
- **Transfers** — Sends USDC to random addresses (internal & external)

All activities are randomized per wallet — different amounts, tokens, and timing.

## Setup

```bash
pip install requests python-dotenv eth-account eth-abi
cp .env.example .env
# Configure your .env
# Add wallets.json (see wallets_example.json)
python arc_automation.py
```

## Faucet Only

Standalone faucet claimer with reCAPTCHA solver support:

```bash
pip install requests python-dotenv
python faucet_claim.py
```

## Wallet Format

```json
[
  {"address": "0x...", "pk": "abcdef1234..."},
  {"address": "0x...", "pk": "abcdef5678..."}
]
```

## Environment Variables

See `.env.example` for all available configuration options.

## Disclaimer

This is a testnet automation tool. Use at your own risk. Always review the code before running.
