#!/usr/bin/env python3
"""
Circle Faucet Auto-Claim with reCAPTCHA Solver
Claim USDC on Arc Testnet (chain ID 5042002) for multiple wallets.

Usage:
  1. Copy .env.example to .env and fill in your values
  2. Place wallet JSON file (see wallets_example.json for format)
  3. pip install requests python-dotenv
  4. python faucet_claim.py
"""
import os
import sys
import requests
import time
import json
from urllib.parse import urlencode

# Load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Config from env
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY", "")
CAPTCHA_BASE = os.getenv("CAPTCHA_BASE", "https://2captcha.com")
FAUCET_URL = "https://faucet.circle.com"
FAUCET_GRAPHQL = f"{FAUCET_URL}/api/graphql"
RECAPTCHA_SITEKEY = "6LcNs_0pAAAAAJuAAa-VQryi8XsocHubBk-YlUy2"

WALLETS_FILE = os.getenv("WALLETS_FILE", "wallets.json")
LOG_FILE = os.getenv("LOG_FILE", "faucet_claim_log.json")
CLAIM_DELAY = int(os.getenv("CLAIM_DELAY", "10"))  # seconds between wallets


def solve_recaptcha_v2(pageurl, sitekey):
    """Solve reCAPTCHA v2 using captcha solving service"""
    if not CAPTCHA_API_KEY:
        raise Exception("CAPTCHA_API_KEY not set. Check .env file.")

    print(f"→ Requesting reCAPTCHA solve for {pageurl}")

    params = {
        "key": CAPTCHA_API_KEY,
        "method": "userrecaptcha",
        "pageurl": pageurl,
        "sitekey": sitekey
    }

    url = f"{CAPTCHA_BASE}/in.php?" + urlencode(params)
    resp = requests.get(url, timeout=30)
    result = resp.text.strip()

    print(f"  Submit response: {result}")

    if "|" not in result:
        raise Exception(f"Failed to submit captcha task: {result}")

    status, task_id = result.split("|", 1)
    print(f"  Task ID: {task_id}")

    # Poll for result
    max_wait = 300
    poll_interval = 5
    start_time = time.time()

    while (time.time() - start_time) < max_wait:
        time.sleep(poll_interval)

        poll_params = {
            "key": CAPTCHA_API_KEY,
            "id": task_id,
            "action": "get"
        }
        poll_url = f"{CAPTCHA_BASE}/res.php?" + urlencode(poll_params)
        poll_resp = requests.get(poll_url, timeout=30)
        poll_result = poll_resp.text.strip()

        elapsed = time.time() - start_time
        print(f"  [{elapsed:.1f}s] {poll_result[:80]}")

        if "NOT_READY" not in poll_result and "PROCESSING" not in poll_result:
            if "|" in poll_result:
                _, token = poll_result.split("|", 1)
                print(f"✓ reCAPTCHA solved: {token[:60]}...")
                return token
            else:
                raise Exception(f"Unexpected result: {poll_result}")

    raise Exception("Timeout waiting for captcha solution")


def claim_faucet(address, blockchain="ARC", token="USDC"):
    """Claim faucet for one address"""
    print(f"\n→ Claiming for {address}")

    recaptcha_token = solve_recaptcha_v2(FAUCET_URL, RECAPTCHA_SITEKEY)

    query = """
    mutation RequestToken($input: RequestTokenInput!) {
        requestToken(input: $input) {
            amount
            blockchain
            contractAddress
            currency
            destinationAddress
            explorerLink
            hash
            status
        }
    }
    """

    payload = {
        "operationName": "RequestToken",
        "variables": {
            "input": {
                "destinationAddress": address,
                "blockchain": blockchain,
                "token": token
            }
        },
        "query": query
    }

    headers = {
        "user-agent": "Mozilla/5.0",
        "content-type": "application/json",
        "Apollo-Require-Preflight": "true",
        "origin": FAUCET_URL,
        "referer": f"{FAUCET_URL}/",
        "recaptcha-v2-token": recaptcha_token
    }

    resp = requests.post(FAUCET_GRAPHQL, json=payload, headers=headers, timeout=30)
    result = resp.json()

    print(f"  Response: {json.dumps(result, indent=2)}")

    if "errors" in result:
        return {"success": False, "error": result["errors"][0]["message"], "address": address}

    data = result.get("data", {}).get("requestToken", {})
    return {
        "success": True,
        "address": address,
        "amount": data.get("amount"),
        "hash": data.get("hash"),
        "explorerLink": data.get("explorerLink"),
        "status": data.get("status")
    }


def main():
    if not CAPTCHA_API_KEY:
        print("ERROR: CAPTCHA_API_KEY not set!")
        print("Copy .env.example to .env and fill in your captcha API key.")
        sys.exit(1)

    if not os.path.exists(WALLETS_FILE):
        print(f"ERROR: Wallets file not found: {WALLETS_FILE}")
        print("Create wallets.json with format: {\"generated_wallets\": [{\"address\": \"0x...\"}, ...]}")
        sys.exit(1)

    with open(WALLETS_FILE) as f:
        wallets_data = json.load(f)

    wallets = wallets_data.get("generated_wallets", wallets_data)[:20]
    results = []

    for i, wallet in enumerate(wallets, 1):
        address = wallet["address"] if isinstance(wallet, dict) else wallet
        print(f"\n{'='*60}")
        print(f"Wallet {i}/{len(wallets)}: {address}")
        print('='*60)

        try:
            result = claim_faucet(address)
            results.append(result)

            if result["success"]:
                print(f"✓ SUCCESS: {result['amount']} USDC")
                print(f"  Hash: {result['hash']}")
                print(f"  Explorer: {result['explorerLink']}")
            else:
                print(f"✗ FAILED: {result['error']}")

            with open(LOG_FILE, 'w') as f:
                json.dump(results, f, indent=2)

            if i < len(wallets):
                print(f"\n→ Waiting {CLAIM_DELAY}s before next wallet...")
                time.sleep(CLAIM_DELAY)

        except Exception as e:
            print(f"✗ ERROR: {e}")
            results.append({"success": False, "error": str(e), "address": address})
            with open(LOG_FILE, 'w') as f:
                json.dump(results, f, indent=2)
            continue

    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    success_count = sum(1 for r in results if r["success"])
    print(f"Success: {success_count}/{len(wallets)}")
    print(f"Failed: {len(wallets) - success_count}/{len(wallets)}")
    print(f"\nLog saved to: {LOG_FILE}")


if __name__ == "__main__":
    main()
