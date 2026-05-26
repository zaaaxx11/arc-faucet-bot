#!/usr/bin/env python3
"""
Arc Testnet - Full Automation: Faucet > GM > Swap > Bridge > LP > Send
Generates 10+ on-chain transactions per wallet for activity farming.

Usage:
  1. Copy .env.example to .env and fill in values
  2. Place wallets.json with your wallet keys (see wallets_example.json)
  3. pip install requests python-dotenv eth-account eth-abi
  4. python arc_automation.py
"""
import json
import os
import sys
import requests
import time
import random
from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_abi import encode

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Config
RPC_URL = os.getenv("RPC_URL", "https://rpc.testnet.arc.network")
CHAIN_ID = int(os.getenv("CHAIN_ID", "5042002"))
EXPLORER = "https://testnet.arcscan.app"
WALLETS_FILE = os.getenv("WALLETS_FILE", "wallets.json")

# Contracts
USDC_TOKEN = "0x3600000000000000000000000000000000000000"
EURC_TOKEN = "0x89B50855Aa3bE2F677cD6303Cec089B5F319D72a"
SWAP_ROUTER = "0x73742278c31a76dBb0D2587d03ef92E6E2141023"
GM_CONTRACT = "0x363cC75a89aE5673b427a1Fa98AFc48FfDE7Ba43"
GM_REFERRER = "0x6f479f2c97e9aa666323abd6a8f3a8821bccb289"
BRIDGE_CONTRACT = "0xC5567a5E3370d4DBfB0540025078e283e36A363d"
LP_POOL = "0x3DF3966F5138143dce7a9cFDdC2c0310ce083BB1"

# External addresses for random recipients (bridge/send targets)
EXTERNAL_ADDRESSES = [
    "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
    "0x5B38Da6a701c568545dCfcB03FcB875f56beddC4",
    "0xAb8483F64d9C6d1EcF9b849Ae677dD3315835cb2",
    "0x4B20993Bc481177ec7E8f571ceCaE8A9e22C02db",
    "0x78731D3Ca6b7E34aC0F824c42a7cC18A495cabaB",
    "0x617F2E2fD72FD9D5503197092aC168c91465E7f2",
    "0x17F6AD8Ef982297579C203069C1DbfFE4348c372",
    "0x5c6B0f7Bf3E7ce046039Bd8FABdfD3f9F5021678",
    "0x03C6FcED478cBbC9a4FAB34eF9f40767739D1Ff7",
    "0x1aE0EA34a72D944a8C7603FfB3eC30a6669E454C",
]


def load_wallets():
    """Load wallets from JSON file"""
    if not os.path.exists(WALLETS_FILE):
        print(f"ERROR: {WALLETS_FILE} not found!")
        print("Create wallets.json with format: [{\"address\": \"0x...\", \"pk\": \"abcdef...\"}, ...]")
        sys.exit(1)
    with open(WALLETS_FILE) as f:
        data = json.load(f)
    # Support both {"generated_wallets": [...]} and plain list
    wallets = data.get("generated_wallets", data) if isinstance(data, dict) else data
    return wallets


def rpc_call(method, params):
    try:
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        resp = requests.post(RPC_URL, json=payload, timeout=30)
        result = resp.json()
        if "error" in result:
            return None
        return result.get("result")
    except:
        return None


def get_nonce(address):
    result = rpc_call("eth_getTransactionCount", [address, "latest"])
    return int(result, 16) if result else 0


def get_gas_price():
    result = rpc_call("eth_gasPrice", [])
    return int(result, 16) if result else 1000000000


def send_tx(signed_tx):
    return rpc_call("eth_sendRawTransaction", [signed_tx])


def wait_receipt(tx_hash, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            receipt = rpc_call("eth_getTransactionReceipt", [tx_hash])
            if receipt:
                return int(receipt.get("status", "0x0"), 16) == 1
        except:
            pass
        time.sleep(3)
    return False


def approve_token(account, token, spender, amount):
    """Approve token for spending"""
    try:
        data = "0x095ea7b3" + spender[2:].lower().zfill(64) + hex(amount)[2:].zfill(64)
        nonce = get_nonce(account.address)
        gas_price = get_gas_price()
        tx = {
            "from": account.address,
            "to": token,
            "value": "0x0",
            "data": data,
            "nonce": hex(nonce),
            "gasPrice": hex(gas_price),
            "gas": hex(100000),
            "chainId": CHAIN_ID,
        }
        signed = account.sign_transaction(tx)
        tx_hash = send_tx(signed.raw_transaction.hex())
        if tx_hash:
            return wait_receipt(tx_hash)
    except:
        pass
    return False


def claim_faucet(address):
    """Claim faucet (cooldown 2 hours)"""
    try:
        resp = requests.post(
            "https://faucet.testnet.arc.network/api/claim",
            json={"address": address, "asset": "USDC", "network": "arc-testnet"},
            timeout=5
        )
        return resp.status_code == 200
    except:
        return False


def onchain_gm(account):
    """OnChain GM with referrer"""
    try:
        data = "0x84a3bb6b" + GM_REFERRER[2:].lower().zfill(64)
        nonce = get_nonce(account.address)
        gas_price = get_gas_price()
        tx = {
            "from": account.address,
            "to": GM_CONTRACT,
            "value": "0x0",
            "data": data,
            "nonce": hex(nonce),
            "gasPrice": hex(gas_price),
            "gas": hex(300000),
            "chainId": CHAIN_ID,
        }
        signed = account.sign_transaction(tx)
        tx_hash = send_tx(signed.raw_transaction.hex())
        if tx_hash:
            return wait_receipt(tx_hash)
    except:
        pass
    return False


def swap_tokens(account, token_in, token_out, amount):
    """Swap tokens via router"""
    try:
        deadline = int(time.time()) + 3600
        params_encoded = encode(
            ['address', 'address', 'uint256', 'uint256', 'address', 'uint256'],
            [token_in, token_out, amount, 0, account.address, deadline]
        )
        data = "0x56e87df9" + params_encoded.hex()
        nonce = get_nonce(account.address)
        gas_price = get_gas_price()
        tx = {
            "from": account.address,
            "to": SWAP_ROUTER,
            "value": "0x0",
            "data": data,
            "nonce": hex(nonce),
            "gasPrice": hex(gas_price),
            "gas": hex(500000),
            "chainId": CHAIN_ID,
        }
        signed = account.sign_transaction(tx)
        tx_hash = send_tx(signed.raw_transaction.hex())
        if tx_hash:
            return wait_receipt(tx_hash)
    except:
        pass
    return False


def bridge_tokens(account, amount):
    """Bridge USDC to random external address"""
    try:
        if not approve_token(account, USDC_TOKEN, BRIDGE_CONTRACT, amount * 2):
            return False
        time.sleep(2)

        recipient = random.choice(EXTERNAL_ADDRESSES)
        bridge_params = encode(
            ['uint256', 'uint256', 'uint256', 'bytes32', 'bytes32', 'address', 'address', 'uint32', 'uint32'],
            [amount, int(amount * 0.95), 0,
             bytes.fromhex(recipient[2:].zfill(64)),
             bytes(32),
             USDC_TOKEN, BRIDGE_CONTRACT, 0, 1000]
        )
        hook_data = bytes.fromhex("636374702d666f72776172640000000000000000000000000000000000000000")
        full_params = encode(
            ['(uint256,uint256,uint256,bytes32,bytes32,address,address,uint32,uint32)', 'bytes'],
            [tuple([amount, int(amount * 0.95), 0,
                    bytes.fromhex(recipient[2:].zfill(64)),
                    bytes(32),
                    USDC_TOKEN, BRIDGE_CONTRACT, 0, 1000]), hook_data]
        )
        data = "0x513e1175" + full_params.hex()
        nonce = get_nonce(account.address)
        gas_price = get_gas_price()
        tx = {
            "from": account.address,
            "to": BRIDGE_CONTRACT,
            "value": "0x0",
            "data": data,
            "nonce": hex(nonce),
            "gasPrice": hex(gas_price),
            "gas": hex(500000),
            "chainId": CHAIN_ID,
        }
        signed = account.sign_transaction(tx)
        tx_hash = send_tx(signed.raw_transaction.hex())
        if tx_hash:
            return wait_receipt(tx_hash)
    except:
        pass
    return False


def add_liquidity(account, amount_usdc, amount_eurc):
    """Add liquidity to USDC-EURC pool"""
    try:
        if not approve_token(account, USDC_TOKEN, LP_POOL, amount_usdc * 2):
            return False
        time.sleep(2)
        if not approve_token(account, EURC_TOKEN, LP_POOL, amount_eurc * 2):
            return False
        time.sleep(2)

        deadline = int(time.time()) + 3600
        recipient = random.choice(EXTERNAL_ADDRESSES)
        amounts_array = [amount_usdc, amount_eurc]
        params_encoded = encode(
            ['uint256[]', 'uint256', 'address', 'uint256'],
            [amounts_array, 0, recipient, deadline]
        )
        data = "0xcb9c7844" + params_encoded.hex()
        nonce = get_nonce(account.address)
        gas_price = get_gas_price()
        tx = {
            "from": account.address,
            "to": LP_POOL,
            "value": "0x0",
            "data": data,
            "nonce": hex(nonce),
            "gasPrice": hex(gas_price),
            "gas": hex(500000),
            "chainId": CHAIN_ID,
        }
        signed = account.sign_transaction(tx)
        tx_hash = send_tx(signed.raw_transaction.hex())
        if tx_hash:
            return wait_receipt(tx_hash)
    except:
        pass
    return False


def send_random_tx(account, recipient, amount):
    """Send USDC to random address"""
    try:
        data = "0xa9059cbb" + recipient[2:].lower().zfill(64) + hex(amount)[2:].zfill(64)
        nonce = get_nonce(account.address)
        gas_price = get_gas_price()
        tx = {
            "from": account.address,
            "to": USDC_TOKEN,
            "value": "0x0",
            "data": data,
            "nonce": hex(nonce),
            "gasPrice": hex(gas_price),
            "gas": hex(100000),
            "chainId": CHAIN_ID,
        }
        signed = account.sign_transaction(tx)
        tx_hash = send_tx(signed.raw_transaction.hex())
        if tx_hash:
            return wait_receipt(tx_hash)
    except:
        pass
    return False


def process_wallet(wallet_data, idx, total):
    """Process one wallet with random activities"""
    address = wallet_data["address"]
    pk = wallet_data["pk"]
    if not pk.startswith("0x"):
        pk = "0x" + pk

    stats = {"faucet": 0, "gm": 0, "swap": 0, "bridge": 0, "lp": 0, "send": 0}

    try:
        account: LocalAccount = Account.from_key(pk)

        # 1. Claim faucet
        if claim_faucet(address):
            stats["faucet"] = 1

        # 2. OnChain GM
        if onchain_gm(account):
            stats["gm"] = 1

        # 3. Random swaps (5-10)
        num_swaps = random.randint(5, 10)
        for i in range(num_swaps):
            amount = random.randint(100000, 2000000)
            if random.choice([True, False]):
                token_in, token_out = USDC_TOKEN, EURC_TOKEN
            else:
                token_in, token_out = EURC_TOKEN, USDC_TOKEN
            if swap_tokens(account, token_in, token_out, amount):
                stats["swap"] += 1
            time.sleep(2)

        # 4. Bridge (30% chance)
        if random.random() < 0.3:
            amount = random.randint(1000000, 5000000)
            if bridge_tokens(account, amount):
                stats["bridge"] += 1

        # 5. Add LP (30% chance)
        if random.random() < 0.3:
            amount = random.randint(500000, 1000000)
            if add_liquidity(account, amount, amount):
                stats["lp"] += 1

        # 6. Random sends (2-4)
        num_sends = random.randint(2, 4)
        for i in range(num_sends):
            if random.choice([True, False]):
                recipient = random.choice(EXTERNAL_ADDRESSES)
            else:
                recipient = random.choice(wallets_global)["address"]
            amount = random.randint(10000, 1000000)
            if send_random_tx(account, recipient, amount):
                stats["send"] += 1
            time.sleep(2)

        total_tx = sum(stats.values()) - stats["faucet"]
        print(f"[{idx}/{total}] {address[:10]}...{address[-8:]} → {total_tx} tx (gm:{stats['gm']} swap:{stats['swap']} bridge:{stats['bridge']} lp:{stats['lp']} send:{stats['send']})")
        return stats

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return stats


def main():
    global wallets_global
    wallets = load_wallets()
    wallets_global = wallets
    total = len(wallets)

    print("=" * 70)
    print("🚀 Arc Testnet - Full Automation v2")
    print("=" * 70)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print(f"Wallets: {total}")
    print("=" * 70)

    total_stats = {"faucet": 0, "gm": 0, "swap": 0, "bridge": 0, "lp": 0, "send": 0}

    for idx, wallet in enumerate(wallets, 1):
        stats = process_wallet(wallet, idx, total)
        for key in total_stats:
            total_stats[key] += stats[key]
        if idx < total:
            time.sleep(3)

    print("\n" + "=" * 70)
    print("📊 FINAL REPORT")
    print("=" * 70)
    print(f"Faucet claims: {total_stats['faucet']}/{total}")
    print(f"OnChain GM: {total_stats['gm']}/{total}")
    print(f"Swaps: {total_stats['swap']}")
    print(f"Bridges: {total_stats['bridge']}")
    print(f"LP adds: {total_stats['lp']}")
    print(f"Random sends: {total_stats['send']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
