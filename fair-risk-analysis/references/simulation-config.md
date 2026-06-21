# Simulation Configuration Reference

Complete schema and examples for `scripts/fair_simulation.py --config params.json`.

## CLI Usage

```bash
# Run from a config file
python scripts/fair_simulation.py --config params.json --iterations 10000 --seed 42 --output-dir ./results

# Quick demo with built-in ransomware scenario
python scripts/fair_simulation.py --demo

# What-if: compare a baseline config against a treated/insured one
python scripts/fair_simulation.py --config baseline.json --compare treated.json --output-dir ./results

# Portfolio: aggregate several scenarios (assumed independent)
python scripts/fair_simulation.py --portfolio s1.json s2.json s3.json --output-dir ./results
```

**Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--iterations` | 10000 | Monte Carlo iterations (simulated years) |
| `--seed` | none | Random seed for reproducibility (set it for any reportable run) |
| `--bootstrap` | 200 | Bootstrap resamples for MC standard error (`0` disables) |
| `--compare` | — | Second config; emits a delta table vs `--config` |
| `--portfolio` | — | Two or more configs; aggregates into a combined distribution |

**Outputs written to `--output-dir`:**
- `statistics.json` — EAL, VaR, **TVaR**, LEF, conditional stats, **MC standard error**, net-of-insurance block (if `insurance` set)
- `risk_register_row.json` — compact, machine-readable summary for a risk register
- `loss_exceedance.png` — Loss exceedance curve (with net-of-insurance overlay if applicable)
- `tornado.png` — Sensitivity tornado diagram
- `ale_distribution.png` — ALE histogram
- `simulation_results.csv` — Full per-iteration simulation data
- `comparison.json` — (with `--compare`) baseline vs alternative delta table
- `portfolio_statistics.json`, `portfolio_exceedance.png`, `risk_register.csv` — (with `--portfolio`)

## JSON Config Schema

```json
{
  "name": "Scenario Name",

  // FREQUENCY — choose ONE of (A) TEF x Vulnerability, or (B) direct LEF:
  // (A) decomposed:
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
  // (B) direct LEF (Open FAIR; use when you have internal loss-event data):
  "lef": { "minimum": <float>, "mode": <float>, "maximum": <float> },

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
  "conditional_secondary": <bool, default false>,

  // RISK TRANSFER (optional) — adds a net-of-insurance distribution:
  "insurance": {
    "per_occurrence_deductible": <float, default 0>,
    "per_occurrence_limit":      <float, default unlimited>,
    "coinsurance":               <float, 0–1, default 0>,
    "aggregate_limit":           <float, default unlimited>
  }
}
```

Provide **either** `tef`+`vulnerability` **or** `lef` — not both. If both are
present, `lef` wins and a warning is emitted.

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
| `loss_correlation` | `0.0` | Shared severity factor across loss forms within one event. `0` = independent, `1` = perfectly correlated. Values of `0.3`–`0.7` are typical for correlated incidents. Validated to `[0, 1]`. |
| `conditional_secondary` | `false` | When `true`, the probability of each secondary loss scales with that event's primary-loss severity percentile: `p × (0.5 + percentile)`, clipped to `[0,1]`. Larger primary events become more likely to trigger regulatory/reputation impacts, while the *expected* secondary frequency is preserved (the mean multiplier is 1.0). Works independently of `loss_correlation`. |
| `insurance` | none | Risk-transfer terms. Recovery per event = `clip(event_loss − deductible, 0, limit) × (1 − coinsurance)`, summed per year and capped at `aggregate_limit`. Output gains a `net_annual_loss_exposure` block. |

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
annual_loss_exposure.mean             → Expected Annual Loss (EAL)
annual_loss_exposure.var_95 / var_99  → 95th / 99th percentile (VaR)
annual_loss_exposure.tvar_95 / tvar_99 → Tail VaR / Expected Shortfall (mean loss beyond VaR)
annual_loss_exposure.mc_standard_error → Bootstrap SE for mean & VaR (gauge of MC noise)
annual_loss_exposure.p_zero_events    → Probability of a zero-loss year
annual_loss_exposure.mean_event_count → Average events per year
annual_loss_exposure.conditional_ale.mean → Mean loss for years that had at least one event
net_annual_loss_exposure.mean         → EAL net of insurance (only if "insurance" set)
net_annual_loss_exposure.expected_annual_recovery → Mean insurance recovery per year
lef.mean                              → Mean Loss Event Frequency
risk_register_row                     → Compact summary (also written to risk_register_row.json)
```

**`comparison.json`** (with `--compare`): `baseline`, `alternative`, `delta`, and
`pct_change` for EAL / VaR / VaR99 / TVaR95.

**`portfolio_statistics.json`** (with `--portfolio`): combined `portfolio` block,
per-scenario `scenarios` rows, and `diversification_benefit_var_95`.
