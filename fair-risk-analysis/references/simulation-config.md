# Simulation Configuration Reference

Complete schema and examples for `scripts/fair_simulation.py --config params.json`.

## CLI Usage

```bash
# Run from a config file
python scripts/fair_simulation.py --config params.json --iterations 10000 --seed 42 --output-dir ./results

# Quick demo with built-in ransomware scenario
python scripts/fair_simulation.py --demo
```

**Outputs written to `--output-dir`:**
- `statistics.json` — EAL, VaR, LEF, conditional stats
- `loss_exceedance.png` — Loss exceedance curve
- `tornado.png` — Sensitivity tornado diagram
- `ale_distribution.png` — ALE histogram
- `simulation_results.csv` — Full 10,000-row simulation data

## JSON Config Schema

```json
{
  "name": "Scenario Name",
  "tef": {
    "minimum": <float, events/year>,
    "mode":    <float, events/year>,
    "maximum": <float, events/year>
  },
  "vulnerability": {
    "minimum": <float, 0–1>,
    "mode":    <float, 0–1>,
    "maximum": <float, 0–1>
  },
  "primary_losses": [
    {
      "name": "Loss Form Name",
      "params": { ... }       // PERT or lognormal — see below
    }
  ],
  "secondary_losses": [
    {
      "name": "Loss Form Name",
      "params": { ... },
      "probability": <float, 0–1>   // Default: 1.0 (always occurs if event fires)
    }
  ],
  "loss_correlation":     <float, 0–1, default 0.0>,
  "conditional_secondary": <bool, default false>
}
```

### Distribution Params

**PERT** — use when you think in min/mode/max three-point estimates:
```json
"params": { "minimum": 500000, "mode": 2000000, "maximum": 10000000 }
```

**Lognormal** — use for heavy-tailed losses where extreme outliers are plausible (e.g., regulatory fines, class action settlements). Specified by 10th and 90th percentile:
```json
"params": { "p10": 1000000, "p90": 50000000 }
```
The engine back-solves the underlying normal distribution from `p10`/`p90` automatically.

### Optional Fields

| Field | Default | Description |
|-------|---------|-------------|
| `loss_correlation` | `0.0` | Shared severity factor across loss forms within one event. `0` = independent, `1` = perfectly correlated. Values of `0.3`–`0.7` are typical for correlated incidents. |
| `conditional_secondary` | `false` | When `true`, the probability of secondary losses scales with primary loss severity — larger primary events increase the chance of regulatory/reputation impacts. |

## Complete Example: Ransomware on Core Banking

```json
{
  "name": "Ransomware on Core Banking System",
  "tef": { "minimum": 5, "mode": 15, "maximum": 30 },
  "vulnerability": { "minimum": 0.03, "mode": 0.08, "maximum": 0.15 },
  "primary_losses": [
    {
      "name": "Productivity",
      "params": { "minimum": 2000000, "mode": 10000000, "maximum": 50000000 }
    },
    {
      "name": "Response",
      "params": { "minimum": 500000, "mode": 2000000, "maximum": 10000000 }
    },
    {
      "name": "Restoration",
      "params": { "minimum": 1000000, "mode": 5000000, "maximum": 20000000 }
    }
  ],
  "secondary_losses": [
    {
      "name": "Regulatory Fines",
      "params": { "p10": 1000000, "p90": 50000000 },
      "probability": 0.6
    },
    {
      "name": "Reputation",
      "params": { "minimum": 500000, "mode": 5000000, "maximum": 25000000 },
      "probability": 0.7
    }
  ],
  "loss_correlation": 0.7,
  "conditional_secondary": true
}
```

## Minimal Example: BEC Wire Fraud

```json
{
  "name": "Business Email Compromise",
  "tef": { "minimum": 50, "mode": 100, "maximum": 150 },
  "vulnerability": { "minimum": 0.005, "mode": 0.02, "maximum": 0.05 },
  "primary_losses": [
    {
      "name": "Direct Fraud Loss",
      "params": { "minimum": 50000, "mode": 250000, "maximum": 5000000 }
    }
  ],
  "secondary_losses": [
    {
      "name": "Regulatory",
      "params": { "minimum": 100000, "mode": 500000, "maximum": 5000000 },
      "probability": 0.15
    }
  ]
}
```

## Reading the Outputs

**`statistics.json` key fields:**
```
annual_loss_exposure.mean        → Expected Annual Loss (EAL)
annual_loss_exposure.var_95      → 95th percentile (VaR)
annual_loss_exposure.p_zero_events → Probability of a zero-loss year
annual_loss_exposure.mean_event_count → Average events per year
annual_loss_exposure.conditional_ale.mean → Mean loss for years that had at least one event
lef.mean                         → Mean Loss Event Frequency
```
