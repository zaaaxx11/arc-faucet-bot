# ARC Testnet Automation Bot

On-chain activity automation for Arc Testnet (chain ID 5042002).

## Activities

Faucet · OnChain GM · Swap · Bridge · LP · Send

## Setup

```bash
pip install requests python-dotenv eth-account eth-abi
cp .env.example .env
# Edit .env
# Add wallets.json (see wallets_example.json)
python arc_automation.py
```

## Faucet Only (reCAPTCHA)

```bash
python faucet_claim.py
```

## Wallet Format

```json
[
  {"address": "0x...", "pk": "abcdef..."},
  {"address": "0x...", "pk": "abcdef..."}
]
```
