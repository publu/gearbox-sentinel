# gearbox-sentinel

Agent skill for monitoring Gearbox Finance lending pools, APY rates, reward programs, credit account positions, and protocol stats.

## Install as Agent Skill

```bash
curl -sL https://raw.githubusercontent.com/publu/gearbox-sentinel/master/gearbox-sentinel.md >> ~/.claude/skills/gearbox-sentinel.md
```

## Commands

| Command | Description |
|---------|------------|
| `position <address> [chain]` | Check credit account positions for a wallet |
| `pools [chain]` | List lending pools with TVL/APY, optionally filter by chain |
| `top [n]` | Show top N pools ranked by APY |
| `rewards` | Show active reward programs and points |
| `stats` | Protocol-level stats overview |

## Data Sources

- [DefiLlama Yields API](https://yields.llama.fi/pools) — pool TVL, APY
- [Gearbox State Cache](https://state-cache.gearbox.foundation/apy-server/latest.json) — rewards, points
- Ethereum RPC (public) — credit account on-chain data

## Requirements

- Python 3.7+
- No API keys needed
- No wallet needed (watch-only)
