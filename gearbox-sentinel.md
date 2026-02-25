# Gearbox Sentinel — Agent Skill

Monitor Gearbox Finance lending pools, APY rates, reward programs, and protocol stats.

## Setup

```bash
# Save the checker script
curl -sL https://raw.githubusercontent.com/publu/gearbox-sentinel/master/gearbox_check.py -o /tmp/gearbox_check.py
```

## Commands

### List all lending pools
```bash
python3 /tmp/gearbox_check.py pools
```

### Filter pools by chain
```bash
python3 /tmp/gearbox_check.py pools ethereum
python3 /tmp/gearbox_check.py pools monad
python3 /tmp/gearbox_check.py pools plasma
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

## Output Format

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

### rewards
```
  Pool: 0xda00010eda646913f2... (Ethereum)
    Points: Lombard LUX (LBTC) — 20000000/day

  Pool: 0x6b343f7b797f1488aa... (Monad)
    Extra APY: 5.41% in WMON
```

## Notes

- No wallet or API key required — all data is public
- Pools span multiple chains: Ethereum, Monad, Plasma, Etherlink, Lisk
- APY includes both base lending yield and reward token incentives
- Gearbox is a composable leverage protocol — pools supply liquidity that Credit Accounts borrow from
