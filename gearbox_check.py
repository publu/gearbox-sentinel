#!/usr/bin/env python3
"""Gearbox Finance sentinel — monitor lending pools, APY, credit accounts, and protocol stats."""

import json
import struct
import sys
import urllib.request

DEFILLAMA_YIELDS = "https://yields.llama.fi/pools"
GEARBOX_APY_CDN = "https://state-cache.gearbox.foundation/apy-server/latest.json"

# Public RPCs
RPCS = {
    "ethereum": "https://ethereum-rpc.publicnode.com",
    "arbitrum": "https://arbitrum-one-rpc.publicnode.com",
    "optimism": "https://optimism-rpc.publicnode.com",
}

# Function selectors (keccak256)
SEL_CREDIT_ACCOUNTS = "0x741f3e3c"         # creditAccounts()
SEL_CREDIT_ACCOUNT_INFO = "0x3c5bc3b2"     # creditAccountInfo(address)
SEL_POOL = "0x16f0115b"                     # pool()
SEL_ASSET = "0x38d52e0f"                    # asset()
SEL_UNDERLYING_TOKEN = "0x2495a599"         # underlyingToken()

# Known Gearbox v3 CreditManager contracts (Ethereum mainnet)
# From the Gearbox app frontend
CREDIT_MANAGERS = {
    "ethereum": [
        "0xf5edc34204e67e592bdcb84114571c9e4bd0bdf7",
        "0xb79d6544839d169869476589d2e54014a074317b",
        "0x79c6c1ce5b12abcc3e407ce8c160ee1160250921",
        "0xc307a074bd5aec2d6ad1d9b74465c24a59b490fd",
        "0x9a0fdf7cdab4604fc27ebeab4b3d57bd825e8ebe",
        "0x06c0df5ac1f24bc2097b59ed8ee1db86bf0b09df",
        "0x1128860755c6d452d9326e35d1672ca7c920b7c1",
        "0x35e154be3c856c37d539aae90178fe5ac6d37644",
        "0x11fd8801a051b296e337a3e1168839fb346d5940",
        "0x6252467C2FefB61cB55180282943139BAeEA36c5",
        "0x7a4EffD87C2f3C55CA251080b1343b605f327E3a",
    ],
}

# Well-known ERC20 tokens (for display)
KNOWN_TOKENS = {
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": ("WETH", 18),
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": ("USDC", 6),
    "0xdac17f958d2ee523a2206206994597c13d831ec7": ("USDT", 6),
    "0x6b175474e89094c44da98b954eedeac495271d0f": ("DAI", 18),
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": ("WBTC", 8),
    "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0": ("wstETH", 18),
    "0xae78736cd615f374d3085123a210448e74fc6393": ("rETH", 18),
    "0xf939e0a03fb07f59a73314e73794be0e57ac1b4e": ("crvUSD", 18),
    "0x83f20f44975d03b1b09e64809b757c47f942beea": ("sDAI", 18),
    "0x18084fba666a33d37592fa2633fd49a74dd93a88": ("tBTC", 18),
    "0x40d16fc0246ad3160ccc09b8d0d3a2cd28ae6c2f": ("GHO", 18),
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "gearbox-sentinel/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def eth_call(rpc, to, data):
    """Make an eth_call to a contract."""
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{"to": to, "data": data}, "latest"],
        "id": 1
    }).encode()
    req = urllib.request.Request(rpc, data=payload,
                                 headers={"Content-Type": "application/json",
                                           "User-Agent": "gearbox-sentinel/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read())
    if "error" in result:
        return None
    return result.get("result", "0x")


def decode_addresses(hex_data):
    """Decode an ABI-encoded dynamic array of addresses."""
    if not hex_data or hex_data == "0x" or len(hex_data) < 130:
        return []
    raw = bytes.fromhex(hex_data[2:])
    if len(raw) < 64:
        return []
    # offset at first 32 bytes, length at offset
    offset = int.from_bytes(raw[0:32], "big")
    length = int.from_bytes(raw[offset:offset + 32], "big")
    addrs = []
    for i in range(length):
        start = offset + 32 + i * 32
        addr_bytes = raw[start:start + 32]
        addr = "0x" + addr_bytes[-20:].hex()
        addrs.append(addr)
    return addrs


def decode_credit_account_info(hex_data):
    """Decode creditAccountInfo return: (debt, cumulativeIndexLastUpdate, cumulativeQuotaInterest, quotaFees, enabledTokensMask, flags, lastDebtUpdate, borrower)"""
    if not hex_data or hex_data == "0x" or len(hex_data) < 514:
        return None
    raw = bytes.fromhex(hex_data[2:])
    debt = int.from_bytes(raw[0:32], "big")
    cumulative_index = int.from_bytes(raw[32:64], "big")
    quota_interest = int.from_bytes(raw[64:96], "big")
    quota_fees = int.from_bytes(raw[96:128], "big")
    enabled_mask = int.from_bytes(raw[128:160], "big")
    flags = int.from_bytes(raw[160:192], "big")
    last_update = int.from_bytes(raw[192:224], "big")
    borrower = "0x" + raw[224:256][-20:].hex()
    return {
        "debt": debt,
        "cumulative_index": cumulative_index,
        "quota_interest": quota_interest,
        "quota_fees": quota_fees,
        "enabled_mask": enabled_mask,
        "flags": flags,
        "last_update": last_update,
        "borrower": borrower,
    }


def get_underlying(rpc, cm_addr):
    """Get the underlying token of a CreditManager (via pool -> underlying)."""
    pool_data = eth_call(rpc, cm_addr, SEL_POOL)
    if not pool_data or len(pool_data) < 66:
        return None, None
    pool_addr = "0x" + pool_data[-40:]

    # pool.asset() (ERC-4626) or pool.underlyingToken()
    underlying_data = eth_call(rpc, pool_addr, SEL_ASSET)
    if not underlying_data or len(underlying_data) < 66:
        underlying_data = eth_call(rpc, pool_addr, SEL_UNDERLYING_TOKEN)
    if not underlying_data or len(underlying_data) < 66:
        return pool_addr, None
    underlying = "0x" + underlying_data[-40:]
    return pool_addr, underlying


def get_token_name(addr):
    """Get human-readable token name."""
    key = addr.lower()
    if key in KNOWN_TOKENS:
        return KNOWN_TOKENS[key][0]
    return addr[:10] + "..."


def get_token_decimals(addr):
    """Get token decimals."""
    key = addr.lower()
    if key in KNOWN_TOKENS:
        return KNOWN_TOKENS[key][1]
    return 18


def fmt_token(amount_raw, decimals):
    """Format a raw token amount."""
    if amount_raw == 0:
        return "0"
    val = amount_raw / (10 ** decimals)
    if val >= 1_000_000:
        return f"{val:,.0f}"
    elif val >= 1:
        return f"{val:,.4f}"
    else:
        return f"{val:.6f}"


def cmd_position(args):
    """Check credit account positions for a wallet address."""
    if not args:
        print("Usage: gearbox_check.py position <wallet_address> [chain]")
        print("  chain: ethereum (default)")
        return

    wallet = args[0].lower()
    chain = args[1].lower() if len(args) > 1 else "ethereum"
    rpc = RPCS.get(chain)
    cms = CREDIT_MANAGERS.get(chain, [])

    if not rpc:
        print(f"Chain '{chain}' not supported. Available: {', '.join(RPCS.keys())}")
        return
    if not cms:
        print(f"No CreditManagers known for {chain}")
        return

    print(f"Scanning {len(cms)} CreditManagers on {chain} for {wallet[:8]}...{wallet[-6:]}")
    print()

    found_any = False
    scanned = 0
    for cm_addr in cms:
        try:
            # Get all credit accounts from this CreditManager
            result = eth_call(rpc, cm_addr, SEL_CREDIT_ACCOUNTS)
            accounts = decode_addresses(result)
            scanned += 1
        except Exception:
            continue

        if not accounts:
            continue

        # Get underlying token for this CM
        try:
            pool_addr, underlying = get_underlying(rpc, cm_addr)
        except Exception:
            underlying = None
        underlying_name = get_token_name(underlying) if underlying else "?"
        underlying_decimals = get_token_decimals(underlying) if underlying else 18

        # Check each account for our borrower
        for acct in accounts:
            try:
                padded = acct.lower().replace("0x", "").zfill(64)
                info_data = eth_call(rpc, cm_addr, SEL_CREDIT_ACCOUNT_INFO + padded)
                info = decode_credit_account_info(info_data)
            except Exception:
                continue

            if not info:
                continue

            if info["borrower"].lower() != wallet:
                continue

            found_any = True
            debt = info["debt"]
            debt_fmt = fmt_token(debt, underlying_decimals)

            print(f"  Credit Account: {acct}")
            print(f"    CreditManager: {cm_addr[:20]}...")
            print(f"    Underlying:    {underlying_name}")
            print(f"    Debt:          {debt_fmt} {underlying_name}")
            if info["last_update"] > 0:
                print(f"    Last debt update: block {info['last_update']:,}")

            # Count enabled tokens
            mask = info["enabled_mask"]
            enabled_count = bin(mask).count("1")
            print(f"    Collateral tokens enabled: {enabled_count}")
            print()

    print(f"  Scanned {scanned}/{len(cms)} CreditManagers")
    if not found_any:
        print("  No active credit accounts found for this address.")
        print("  Note: only Ethereum mainnet CreditManagers are currently indexed.")


def cmd_pools(args):
    """List all Gearbox lending pools with TVL and APY."""
    chain_filter = args[0].lower() if args else None
    data = fetch(DEFILLAMA_YIELDS)
    pools = [p for p in data["data"] if p.get("project") == "gearbox"]

    if chain_filter:
        pools = [p for p in pools if p["chain"].lower() == chain_filter]

    pools.sort(key=lambda p: p.get("tvlUsd", 0), reverse=True)

    if not pools:
        print(f"No Gearbox pools found" + (f" on {chain_filter}" if chain_filter else ""))
        return

    print(f"{'Symbol':<12} {'Chain':<12} {'TVL':>14} {'APY':>8} {'Base':>8} {'Reward':>8} {'Stable':>6}")
    print("-" * 80)
    total_tvl = 0
    for p in pools:
        tvl = p.get("tvlUsd", 0)
        total_tvl += tvl
        apy = p.get("apy", 0) or 0
        apy_base = p.get("apyBase", 0) or 0
        apy_reward = p.get("apyReward", 0) or 0
        stable = "yes" if p.get("stablecoin") else "no"
        print(f"{p['symbol']:<12} {p['chain']:<12} ${tvl:>12,.0f} {apy:>7.2f}% {apy_base:>7.2f}% {apy_reward:>7.2f}% {stable:>6}")

    print("-" * 80)
    print(f"{'Total':<12} {'':<12} ${total_tvl:>12,.0f}   {len(pools)} pools")


def cmd_rewards(args):
    """Show reward programs and points across Gearbox pools."""
    data = fetch(GEARBOX_APY_CDN)
    chains = data.get("chains", {})
    chain_names = {"1": "Ethereum", "10": "Optimism", "56": "BSC", "42161": "Arbitrum", "143": "Monad", "146": "Sonic"}

    found = False
    for chain_id, chain_data in chains.items():
        pools = chain_data.get("pools", {}).get("data", [])
        chain_name = chain_names.get(chain_id, f"Chain {chain_id}")

        for pool_info in pools:
            rewards = pool_info.get("rewards", {})
            points = rewards.get("points", [])
            ext_apy = rewards.get("externalAPY", [])
            extra_apy = rewards.get("extraAPY", [])

            if not points and not ext_apy and not extra_apy:
                continue

            found = True
            print(f"\n  Pool: {pool_info.get('pool', '?')[:20]}... ({chain_name})")

            if points:
                for pt in points:
                    print(f"    Points: {pt.get('name', '?')} ({pt.get('symbol', '?')}) — {pt.get('amount', '?')}/{pt.get('duration', '?')}")

            if ext_apy:
                for ea in ext_apy:
                    print(f"    External APY: {ea.get('name', '?')} — {ea.get('value', '?')}%")

            if extra_apy:
                for xa in extra_apy:
                    apy_val = xa.get("apy", 0)
                    sym = xa.get("rewardTokenSymbol", "?")
                    print(f"    Extra APY: {apy_val:.2f}% in {sym}")

    if not found:
        print("No active reward programs found.")


def cmd_stats(args):
    """Show Gearbox protocol-level stats."""
    data = fetch(DEFILLAMA_YIELDS)
    pools = [p for p in data["data"] if p.get("project") == "gearbox"]

    total_tvl = sum(p.get("tvlUsd", 0) for p in pools)
    chains = set(p["chain"] for p in pools)
    stables = [p for p in pools if p.get("stablecoin")]
    volatile = [p for p in pools if not p.get("stablecoin")]

    avg_apy = sum(p.get("apy", 0) or 0 for p in pools) / max(len(pools), 1)
    best = max(pools, key=lambda p: p.get("apy", 0) or 0) if pools else None
    biggest = max(pools, key=lambda p: p.get("tvlUsd", 0) or 0) if pools else None

    print("Gearbox Protocol Stats")
    print("=" * 50)
    print(f"  Total TVL:        ${total_tvl:>14,.0f}")
    print(f"  Pools:            {len(pools)}")
    print(f"  Chains:           {', '.join(sorted(chains))}")
    print(f"  Stablecoin pools: {len(stables)}")
    print(f"  Volatile pools:   {len(volatile)}")
    print(f"  Avg APY:          {avg_apy:.2f}%")
    if best:
        print(f"  Best APY:         {best.get('apy',0):.2f}% ({best['symbol']} on {best['chain']})")
    if biggest:
        print(f"  Largest pool:     ${biggest.get('tvlUsd',0):,.0f} ({biggest['symbol']} on {biggest['chain']})")


def cmd_top(args):
    """Show top Gearbox pools by APY."""
    n = int(args[0]) if args else 5
    data = fetch(DEFILLAMA_YIELDS)
    pools = [p for p in data["data"] if p.get("project") == "gearbox"]
    pools.sort(key=lambda p: p.get("apy", 0) or 0, reverse=True)
    pools = pools[:n]

    print(f"Top {n} Gearbox Pools by APY")
    print(f"{'#':<4} {'Symbol':<12} {'Chain':<12} {'APY':>8} {'TVL':>14}")
    print("-" * 55)
    for i, p in enumerate(pools, 1):
        print(f"{i:<4} {p['symbol']:<12} {p['chain']:<12} {(p.get('apy',0) or 0):>7.2f}% ${p.get('tvlUsd',0):>12,.0f}")


COMMANDS = {
    "position": (cmd_position, "Check credit accounts <address> [chain]"),
    "pools": (cmd_pools, "List lending pools [chain]"),
    "top": (cmd_top, "Top pools by APY [count]"),
    "rewards": (cmd_rewards, "Show reward programs"),
    "stats": (cmd_stats, "Protocol stats overview"),
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: gearbox_check.py <command> [args]")
        print("\nCommands:")
        for name, (_, desc) in COMMANDS.items():
            print(f"  {name:<12} {desc}")
        sys.exit(1)

    cmd = sys.argv[1]
    fn, _ = COMMANDS[cmd]
    fn(sys.argv[2:])


if __name__ == "__main__":
    main()
