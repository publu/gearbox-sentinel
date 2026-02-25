# Gearbox Sentinel — Agent Skill

Monitor Gearbox Finance: check wallet positions, browse lending pools, compare APYs, and view protocol stats.

## Setup

```bash
curl -sL https://raw.githubusercontent.com/publu/gearbox-sentinel/master/gearbox_check.py -o /tmp/gearbox_check.py
```

## Quick Reference

| Command | What it does |
|---------|-------------|
| `position <address>` | Show all credit accounts for a wallet — debt, collateral, USD values, liquidation thresholds, health |
| `pools` | List all lending pools with TVL and APY |
| `pools <chain>` | Filter pools by chain (ethereum, monad, plasma, etherlink, lisk) |
| `top [n]` | Rank pools by APY (default top 5) |
| `rewards` | Active reward programs and point incentives |
| `stats` | Protocol overview: total TVL, pool count, chains, best APY |

## Usage

### Check a wallet's leveraged positions
```bash
python3 /tmp/gearbox_check.py position 0xd25b400836fc3376029bef3831c364e16c780de8
```
This scans all 11 CreditManagers on Ethereum and returns:
- Each credit account's borrowed (debt) amount in USD
- Full collateral breakdown: token, balance, USD value, liquidation threshold
- Overall collateral ratio (health indicator — below 1.0x means liquidatable)

### Browse pools
```bash
python3 /tmp/gearbox_check.py pools           # all pools
python3 /tmp/gearbox_check.py pools monad     # monad only
python3 /tmp/gearbox_check.py top 10          # best 10 by APY
```

### Check rewards and protocol stats
```bash
python3 /tmp/gearbox_check.py rewards
python3 /tmp/gearbox_check.py stats
```

## Example Output

### position
```
Scanning 11 CreditManagers on ethereum for 0xd25b40...780de8

  Credit Account: 0xc5f40bfdd6a94f20a61fd6f2692ba861ccd9ad79
    CreditManager:  0x9a0fdf7cdab4604fc2...
    Underlying:     WETH

    Debt:
      240.0000 WETH  ($460,605.02)
    Collateral:
      0 WETH  ($0.00)  LT: 96%
      243.0000 weETH  ($507,208.42)  LT: 93%

    Total collateral: $507,208.42
    Total debt:       $460,605.02
    Collateral ratio: 1.10x
```

### pools
```
Symbol       Chain               TVL      APY     Base   Reward Stable
------------------------------------------------------------------------
WSTETH       Ethereum   $  5,500,054    0.41%    0.06%    0.36%     no
USDC         Monad      $  3,361,634    7.60%    2.21%    5.39%    yes
```

### stats
```
Gearbox Protocol Stats
==================================================
  Total TVL:        $    15,187,695
  Pools:            18
  Chains:           Ethereum, Etherlink, Lisk, Monad, Plasma
  Best APY:         7.80% (AUSD on Monad)
```

## Data Sources

- **Pools/TVL/APY:** DefiLlama Yields API
- **Rewards/points:** Gearbox state cache CDN
- **Credit accounts:** On-chain CreditManager contracts via public Ethereum RPC
- **Token prices:** DefiLlama price API

## Notes

- No API keys or wallet needed — fully read-only
- Position lookups read directly from Ethereum mainnet (11 CreditManagers)
- Collateral ratio < 1.0x = undercollateralized / liquidatable
- Gearbox is a composable leverage protocol — users borrow from lending pools into Credit Accounts
