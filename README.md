# ARC Faucet Auto-Claim Bot

Automated Circle USDC faucet claimer for Arc Testnet (chain ID 5042002) with reCAPTCHA solver integration.

## Features

- Auto-solve reCAPTCHA v2 via captcha solving service
- Multi-wallet batch claiming
- Configurable delay between claims
- JSON log output

## Setup

```bash
pip install requests python-dotenv
cp .env.example .env
# Edit .env with your API keys
# Add wallets.json with your wallet addresses
python faucet_claim.py
```

## Config (.env)

| Variable | Description |
|---|---|
| `CAPTCHA_API_KEY` | 2captcha/sctg API key |
| `CAPTCHA_BASE` | Captcha service URL (default: 2captcha) |
| `WALLETS_FILE` | Path to wallets JSON (default: wallets.json) |
| `CLAIM_DELAY` | Seconds between claims (default: 10) |

## Wallet Format

See `wallets_example.json` for the expected format.

## Chain Info

- Network: Arc Testnet
- Chain ID: 5042002
- Token: USDC
- Rate limit: 20 USDC per address per 2 hours
