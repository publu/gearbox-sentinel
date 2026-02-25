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

## Output Format

### position
```
Scanning 11 CreditManagers on ethereum for 0x8c2aec...78fee8

  Credit Account: 0xdefbb4c6bc382d3b2f367c7f491e84fccdf8048b
    CreditManager: 0xf5edc34204e67e592b...
    Underlying:    wstETH
    Debt:          0 wstETH
    Last debt update: block 22,000,000
    Collateral tokens enabled: 1
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
- Pools span multiple chains: Ethereum, Monad, Plasma, Etherlink, Lisk
- APY includes both base lending yield and reward token incentives
- Gearbox is a composable leverage protocol — pools supply liquidity that Credit Accounts borrow from
