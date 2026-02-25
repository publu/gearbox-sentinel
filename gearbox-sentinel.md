# Gearbox Sentinel — Agent Skill

Monitor Gearbox Finance lending pools, APY rates, reward programs, credit account positions, and protocol stats.

## Setup

```bash
# Save the checker script
curl -sL https://raw.githubusercontent.com/publu/gearbox-sentinel/master/gearbox_check.py -o /tmp/gearbox_check.py
```

## Commands

### Check credit account positions by wallet address
```bash
python3 /tmp/gearbox_check.py position <wallet_address>
python3 /tmp/gearbox_check.py position 0x1234...abcd ethereum
```

### List all lending pools
```bash
python3 /tmp/gearbox_check.py pools
```

### Filter pools by chain
```bash
python3 /tmp/gearbox_check.py pools ethereum
python3 /tmp/gearbox_check.py pools monad
```

### Show top pools by APY
```bash
python3 /tmp/gearbox_check.py top        # default top 5
python3 /tmp/gearbox_check.py top 10     # top 10
```

### Show reward programs and points
```bash
python3 /tmp/gearbox_check.py rewards
```

### Protocol stats overview
```bash
python3 /tmp/gearbox_check.py stats
```

## Data Sources

- **Pool data (TVL, APY):** DefiLlama Yields API (`yields.llama.fi/pools`)
- **Rewards/points:** Gearbox state cache CDN (`state-cache.gearbox.foundation/apy-server/latest.json`)
- **Credit accounts:** On-chain via Ethereum RPC (reads CreditManager contracts directly)
- **Token prices:** DefiLlama price API (`coins.llama.fi`)

## Output Format

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

## Notes

- No wallet or API key required — all data is public
- Position lookups query 11 CreditManagers on Ethereum mainnet via public RPC
- Shows per-token collateral balances, USD values, liquidation thresholds, and overall collateral ratio
- Pools span multiple chains: Ethereum, Monad, Plasma, Etherlink, Lisk
- APY includes both base lending yield and reward token incentives
- Gearbox is a composable leverage protocol — pools supply liquidity that Credit Accounts borrow from
