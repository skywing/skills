#!/usr/bin/env python3
"""
FAIR Risk Analysis Monte Carlo Simulation

Executes probabilistic risk quantification using the FAIR methodology.
Generates loss distributions, exceedance curves, and sensitivity analysis.

Usage:
    python fair_simulation.py --config params.json
    python fair_simulation.py --demo
    python fair_simulation.py --config baseline.json --compare treated.json
    python fair_simulation.py --portfolio s1.json s2.json s3.json

Output:
    - Loss distribution statistics (JSON), including TVaR (expected shortfall)
      and Monte Carlo standard errors
    - Loss exceedance curve (PNG)
    - Tornado diagram for sensitivity analysis (PNG)
    - ALE distribution histogram (PNG)
    - Full simulation results (CSV)
    - Machine-readable risk-register row (JSON)
"""

import json
import argparse
import warnings
import math
import numpy as np

# Force a non-interactive backend: this script only writes image files and must
# run on headless servers (CI, examination environments) without a display.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from dataclasses import dataclass, field  # noqa: E402
from typing import Optional, Union  # noqa: E402
from scipy import stats as sp_stats  # noqa: E402


# ---------------------------------------------------------------------------
# Distribution parameter types
# ---------------------------------------------------------------------------

@dataclass
class PERTParams:
    """PERT distribution parameters (min, mode, max)"""
    minimum: float
    mode: float
    maximum: float
    lamb: float = 4.0

    def __post_init__(self):
        if not (math.isfinite(self.minimum) and math.isfinite(self.mode) and math.isfinite(self.maximum)):
            raise ValueError(f"PERTParams values must be finite: min={self.minimum}, mode={self.mode}, max={self.maximum}")
        if not (self.minimum <= self.mode <= self.maximum):
            raise ValueError(
                f"PERTParams must satisfy minimum <= mode <= maximum: "
                f"got min={self.minimum}, mode={self.mode}, max={self.maximum}"
            )

    def to_beta_params(self):
        """Convert PERT to Beta distribution parameters using simplified formula"""
        a, b = self.minimum, self.maximum

        if b == a:
            return None, None, a, b

        mu = (a + self.lamb * self.mode + b) / (self.lamb + 2)
        mu_s = (mu - a) / (b - a)

        alpha = mu_s * (self.lamb + 2)
        beta = (1 - mu_s) * (self.lamb + 2)

        return alpha, beta, a, b

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """Generate n samples from PERT distribution"""
        alpha, beta, low, high = self.to_beta_params()

        if alpha is None:
            return np.full(n, low)

        samples = rng.beta(alpha, beta, n)
        return low + samples * (high - low)

    def sample_at_quantiles(self, quantiles: np.ndarray) -> np.ndarray:
        """Inverse CDF sampling at given quantile values (0-1)"""
        quantiles = np.asarray(quantiles, dtype=float)
        alpha, beta_param, low, high = self.to_beta_params()

        if alpha is None:
            return np.full(len(quantiles), low)

        raw = sp_stats.beta.ppf(quantiles, alpha, beta_param)
        return low + raw * (high - low)

    @property
    def analytic_mean(self) -> float:
        """Analytic PERT mean — used by tests and quick sanity checks."""
        return (self.minimum + self.lamb * self.mode + self.maximum) / (self.lamb + 2)


@dataclass
class LognormalParams:
    """Lognormal distribution specified by 10th and 90th percentiles"""
    p10: float
    p90: float

    def __post_init__(self):
        if self.p10 <= 0:
            raise ValueError(f"LognormalParams p10 must be > 0, got {self.p10}")
        if self.p90 <= self.p10:
            raise ValueError(f"LognormalParams p90 must be > p10: p10={self.p10}, p90={self.p90}")

    @property
    def _params(self):
        z = sp_stats.norm.ppf(0.90)
        sigma = (math.log(self.p90) - math.log(self.p10)) / (2 * z)
        mu = (math.log(self.p10) + math.log(self.p90)) / 2
        return mu, sigma

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        mu, sigma = self._params
        return rng.lognormal(mu, sigma, n)

    def sample_at_quantiles(self, quantiles: np.ndarray) -> np.ndarray:
        quantiles = np.asarray(quantiles, dtype=float)
        mu, sigma = self._params
        return sp_stats.lognorm.ppf(quantiles, s=sigma, scale=math.exp(mu))


def parse_params(params_dict: dict) -> Union[PERTParams, LognormalParams]:
    """Build a distribution from a config dict (PERT or lognormal)."""
    if 'p10' in params_dict and 'p90' in params_dict:
        return LognormalParams(p10=params_dict['p10'], p90=params_dict['p90'])
    return PERTParams(**params_dict)


@dataclass
class LossForm:
    """A single loss form with its distribution parameters"""
    name: str
    params: Union[PERTParams, LognormalParams]
    probability: float = 1.0

    def __post_init__(self):
        if not (0.0 <= self.probability <= 1.0):
            raise ValueError(f"LossForm probability must be in [0, 1], got {self.probability}")

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """Sample loss amounts, accounting for probability (kept for tests/compat)."""
        base_samples = self.params.sample(n, rng)
        if self.probability < 1.0:
            occurs = rng.random(n) < self.probability
            return base_samples * occurs
        return base_samples


@dataclass
class InsuranceTerms:
    """
    Risk-transfer (insurance) terms applied to the gross loss distribution.

    Recovery is computed per loss event:
        covered  = clip(event_loss - per_occurrence_deductible, 0, per_occurrence_limit)
        recovery = covered * (1 - coinsurance)
    then summed across the year's events and capped at aggregate_limit.
    Net ALE = gross ALE - annual recovery.
    """
    per_occurrence_deductible: float = 0.0
    per_occurrence_limit: float = math.inf
    coinsurance: float = 0.0          # fraction of covered loss retained by the insured
    aggregate_limit: float = math.inf

    def __post_init__(self):
        if self.per_occurrence_deductible < 0:
            raise ValueError("insurance per_occurrence_deductible must be >= 0")
        if self.per_occurrence_limit <= 0:
            raise ValueError("insurance per_occurrence_limit must be > 0")
        if not (0.0 <= self.coinsurance <= 1.0):
            raise ValueError("insurance coinsurance must be in [0, 1]")
        if self.aggregate_limit <= 0:
            raise ValueError("insurance aggregate_limit must be > 0")

    @classmethod
    def from_dict(cls, data: dict) -> 'InsuranceTerms':
        return cls(
            per_occurrence_deductible=float(data.get('per_occurrence_deductible', 0.0)),
            per_occurrence_limit=float(data.get('per_occurrence_limit', math.inf)),
            coinsurance=float(data.get('coinsurance', 0.0)),
            aggregate_limit=float(data.get('aggregate_limit', math.inf)),
        )


@dataclass
class FAIRScenario:
    """Complete FAIR scenario definition"""
    name: str
    primary_losses: list
    secondary_losses: list = field(default_factory=list)
    # Loss Event Frequency: either decompose as TEF x Vulnerability, or provide LEF directly.
    tef: Optional[PERTParams] = None          # Threat Event Frequency
    vulnerability: Optional[PERTParams] = None  # As decimal (0-1)
    lef: Optional[PERTParams] = None          # Direct Loss Event Frequency (Open FAIR)
    loss_correlation: float = 0.0
    conditional_secondary: bool = False
    insurance: Optional[InsuranceTerms] = None

    @property
    def uses_direct_lef(self) -> bool:
        return self.lef is not None

    def validate(self):
        """Validate scenario parameters and warn on unusual inputs"""
        # Frequency: direct LEF, or TEF x Vulnerability
        if self.lef is not None:
            if self.lef.minimum < 0:
                raise ValueError("LEF minimum must be >= 0")
            if self.tef is not None or self.vulnerability is not None:
                warnings.warn("Both direct 'lef' and 'tef'/'vulnerability' supplied; using direct 'lef'.")
        else:
            if self.tef is None or self.vulnerability is None:
                raise ValueError("Provide either 'lef' directly, or both 'tef' and 'vulnerability'.")
            if self.tef.minimum < 0:
                raise ValueError("TEF minimum must be >= 0")
            if self.vulnerability.minimum < 0 or self.vulnerability.maximum > 1:
                raise ValueError("Vulnerability must be in [0, 1]")

        # Correlation must be a valid blend weight
        if not (0.0 <= self.loss_correlation <= 1.0):
            raise ValueError(f"loss_correlation must be in [0, 1], got {self.loss_correlation}")

        # Must have at least one primary loss
        if not self.primary_losses:
            raise ValueError("At least one primary loss form is required")

        # Non-negative loss magnitudes for PERT params
        for lf in self.primary_losses + self.secondary_losses:
            if isinstance(lf.params, PERTParams) and lf.params.minimum < 0:
                raise ValueError(f"Loss form '{lf.name}' has negative minimum loss magnitude")

        # Warnings for unusual inputs
        if self.vulnerability is not None and self.vulnerability.mode > 0.50:
            warnings.warn(f"Vulnerability mode {self.vulnerability.mode:.0%} is unusually high (>50%)")

        freq = self.lef if self.lef is not None else self.tef
        if freq is not None and freq.mode > 1000:
            warnings.warn(f"Frequency mode {freq.mode} is very high (>1000 events/year)")

    @classmethod
    def from_dict(cls, data: dict) -> 'FAIRScenario':
        """Create scenario from dictionary (e.g., loaded from JSON)"""

        def _loss_forms(key):
            return [
                LossForm(
                    name=lf['name'],
                    params=parse_params(lf['params']),
                    probability=lf.get('probability', 1.0)
                )
                for lf in data.get(key, [])
            ]

        scenario = cls(
            name=data['name'],
            tef=PERTParams(**data['tef']) if 'tef' in data else None,
            vulnerability=PERTParams(**data['vulnerability']) if 'vulnerability' in data else None,
            lef=PERTParams(**data['lef']) if 'lef' in data else None,
            primary_losses=_loss_forms('primary_losses'),
            secondary_losses=_loss_forms('secondary_losses'),
            loss_correlation=data.get('loss_correlation', 0.0),
            conditional_secondary=data.get('conditional_secondary', False),
            insurance=InsuranceTerms.from_dict(data['insurance']) if 'insurance' in data else None,
        )
        scenario.validate()
        return scenario


# ---------------------------------------------------------------------------
# Simulation engine
# ---------------------------------------------------------------------------

def _tvar(x: np.ndarray, q: float) -> float:
    """Tail Value at Risk (expected shortfall): mean of losses at/above the qth percentile."""
    if x.size == 0:
        return 0.0
    thr = np.percentile(x, q)
    tail = x[x >= thr]
    return float(tail.mean()) if tail.size else float(thr)


class FAIRSimulation:
    """Monte Carlo simulation engine for FAIR analysis (vectorized compound Poisson)."""

    def __init__(self, scenario: FAIRScenario, iterations: int = 10000,
                 seed: Optional[int] = None, bootstrap: int = 200):
        self.scenario = scenario
        self.iterations = iterations
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.bootstrap = bootstrap
        self.results = None

    def run(self) -> dict:
        """Execute Monte Carlo simulation using a vectorized compound Poisson process."""
        n = self.iterations
        rng = self.rng
        sc = self.scenario
        corr = sc.loss_correlation

        # --- Loss Event Frequency ---
        if sc.uses_direct_lef:
            lef_samples = np.clip(sc.lef.sample(n, rng), 0, None)
            tef_samples = None
            vuln_samples = None
        else:
            tef_samples = sc.tef.sample(n, rng)
            vuln_samples = sc.vulnerability.sample(n, rng)
            lef_samples = np.clip(tef_samples * vuln_samples, 0, None)

        # --- Event counts (one Poisson draw per simulated year) ---
        event_counts = rng.poisson(lef_samples)
        total = int(event_counts.sum())
        # Map each event to its simulated year
        year_idx = np.repeat(np.arange(n), event_counts)

        def agg(per_event_vals: np.ndarray) -> np.ndarray:
            """Sum per-event values into per-year totals."""
            if total == 0:
                return np.zeros(n)
            return np.bincount(year_idx, weights=per_event_vals, minlength=n)

        # Shared severity factor: one draw per event, blended with each loss
        # form's independent draw. corr=0 -> fully independent; corr=1 -> lockstep.
        shared_u = rng.random(total) if total else np.zeros(0)

        def blended_quantiles() -> np.ndarray:
            indep = rng.random(total) if total else np.zeros(0)
            return np.clip(corr * shared_u + (1 - corr) * indep, 0.0, 1.0)

        # --- Primary losses (per event) ---
        primary_event = np.zeros(total)
        primary_breakdown_event = {}
        for lf in sc.primary_losses:
            eff_u = blended_quantiles()
            vals = lf.params.sample_at_quantiles(eff_u) if total else np.zeros(0)
            if lf.probability < 1.0 and total:
                vals = vals * (rng.random(total) < lf.probability)
            primary_breakdown_event[lf.name] = vals
            primary_event = primary_event + vals

        # Severity percentile of each event's primary loss — drives conditional secondary.
        if total:
            sev_percentile = sp_stats.rankdata(primary_event, method='average') / total
        else:
            sev_percentile = np.zeros(0)

        # --- Secondary losses (per event) ---
        secondary_event = np.zeros(total)
        secondary_breakdown_event = {}
        for lf in sc.secondary_losses:
            if total:
                if sc.conditional_secondary:
                    # Scale probability by primary severity. Mean of (0.5 + percentile)
                    # is 1.0, so expected secondary frequency is preserved while larger
                    # primary events become more likely to trigger secondary losses.
                    prob = np.clip(lf.probability * (0.5 + sev_percentile), 0.0, 1.0)
                else:
                    prob = np.full(total, lf.probability)
                occurs = rng.random(total) < prob
                eff_u = blended_quantiles()
                vals = lf.params.sample_at_quantiles(eff_u) * occurs
            else:
                vals = np.zeros(0)
            secondary_breakdown_event[lf.name] = vals
            secondary_event = secondary_event + vals

        event_loss = primary_event + secondary_event

        # --- Aggregate to per-year totals ---
        primary_totals = agg(primary_event)
        secondary_totals = agg(secondary_event)
        primary_breakdown = {k: agg(v) for k, v in primary_breakdown_event.items()}
        secondary_breakdown = {k: agg(v) for k, v in secondary_breakdown_event.items()}
        gross_ale = primary_totals + secondary_totals

        # --- Insurance / risk transfer ---
        net_ale = None
        annual_recovery = None
        if sc.insurance is not None:
            ins = sc.insurance
            if total:
                covered = np.clip(event_loss - ins.per_occurrence_deductible, 0.0, ins.per_occurrence_limit)
                recovery_event = covered * (1.0 - ins.coinsurance)
            else:
                recovery_event = np.zeros(0)
            annual_recovery = np.minimum(agg(recovery_event), ins.aggregate_limit)
            net_ale = gross_ale - annual_recovery

        self.results = {
            'tef': tef_samples,
            'vulnerability': vuln_samples,
            'lef': lef_samples,
            'event_counts': event_counts,
            'primary_loss': primary_totals,
            'secondary_loss': secondary_totals,
            'total_lm': gross_ale,
            'ale': gross_ale,
            'net_ale': net_ale,
            'annual_recovery': annual_recovery,
            'primary_breakdown': primary_breakdown,
            'secondary_breakdown': secondary_breakdown,
        }

        return self.get_statistics()

    def _bootstrap_se(self, ale: np.ndarray) -> dict:
        """Bootstrap standard errors for the headline statistics (mean, VaR)."""
        if self.bootstrap <= 0 or ale.size == 0:
            return {}
        boot_rng = np.random.default_rng(0 if self.seed is None else self.seed + 1)
        n = ale.size
        means = np.empty(self.bootstrap)
        var95 = np.empty(self.bootstrap)
        var99 = np.empty(self.bootstrap)
        for b in range(self.bootstrap):
            sample = ale[boot_rng.integers(0, n, n)]
            means[b] = sample.mean()
            var95[b] = np.percentile(sample, 95)
            var99[b] = np.percentile(sample, 99)
        mean_val = float(np.mean(ale))
        return {
            'resamples': self.bootstrap,
            'mean_se': float(means.std(ddof=1)),
            'mean_rel_error': float(means.std(ddof=1) / mean_val) if mean_val else 0.0,
            'var_95_se': float(var95.std(ddof=1)),
            'var_99_se': float(var99.std(ddof=1)),
        }

    def get_statistics(self) -> dict:
        """Calculate summary statistics from simulation results"""
        if self.results is None:
            raise ValueError("Run simulation first")

        ale = self.results['ale']
        lef = self.results['lef']
        lm = self.results['total_lm']
        event_counts = self.results['event_counts']

        percentiles = [10, 25, 50, 75, 90, 95, 99]

        has_events = event_counts > 0
        p_zero_events = float(1 - np.mean(has_events))
        mean_event_count = float(np.mean(event_counts))

        conditional_ale = {}
        if np.any(has_events):
            ale_with_events = ale[has_events]
            conditional_ale = {
                'mean': float(np.mean(ale_with_events)),
                'median': float(np.median(ale_with_events)),
                'var_95': float(np.percentile(ale_with_events, 95)),
                'var_99': float(np.percentile(ale_with_events, 99)),
                'tvar_95': _tvar(ale_with_events, 95),
            }

        def _dist_block(x):
            return {
                'mean': float(np.mean(x)),
                'median': float(np.median(x)),
                'std': float(np.std(x)),
                'var_95': float(np.percentile(x, 95)),
                'var_99': float(np.percentile(x, 99)),
                'tvar_95': _tvar(x, 95),
                'tvar_99': _tvar(x, 99),
                'percentiles': {p: float(np.percentile(x, p)) for p in percentiles},
            }

        ale_block = _dist_block(ale)
        ale_block.update({
            'p_zero_events': p_zero_events,
            'mean_event_count': mean_event_count,
            'conditional_ale': conditional_ale,
            'mc_standard_error': self._bootstrap_se(ale),
        })

        stats = {
            'scenario_name': self.scenario.name,
            'iterations': self.iterations,
            'seed': self.seed,
            'frequency_model': 'direct_lef' if self.scenario.uses_direct_lef else 'tef_x_vulnerability',
            'lef': {
                'mean': float(np.mean(lef)),
                'median': float(np.median(lef)),
                'std': float(np.std(lef)),
                'percentiles': {p: float(np.percentile(lef, p)) for p in percentiles}
            },
            'loss_magnitude': {
                'mean': float(np.mean(lm)),
                'median': float(np.median(lm)),
                'std': float(np.std(lm)),
                'percentiles': {p: float(np.percentile(lm, p)) for p in percentiles}
            },
            'annual_loss_exposure': ale_block,
        }

        # Net-of-insurance block
        if self.results['net_ale'] is not None:
            net = self.results['net_ale']
            recovery = self.results['annual_recovery']
            net_block = _dist_block(net)
            net_block['expected_annual_recovery'] = float(np.mean(recovery))
            net_block['gross_minus_net_mean'] = float(np.mean(ale) - np.mean(net))
            stats['net_annual_loss_exposure'] = net_block

        stats['risk_register_row'] = self.risk_register_row(stats)
        return stats

    def risk_register_row(self, stats: Optional[dict] = None) -> dict:
        """Compact, machine-readable summary suitable for a risk register."""
        if stats is None:
            stats = self.get_statistics()
        ale = stats['annual_loss_exposure']
        drivers = self.sensitivity_analysis()
        top_driver = next(iter(drivers), None)
        row = {
            'scenario': self.scenario.name,
            'frequency_model': stats['frequency_model'],
            'lef_mean': stats['lef']['mean'],
            'eal': ale['mean'],
            'median_ale': ale['median'],
            'var_95': ale['var_95'],
            'var_99': ale['var_99'],
            'tvar_95': ale['tvar_95'],
            'tvar_99': ale['tvar_99'],
            'p_zero_loss_year': ale['p_zero_events'],
            'top_driver': top_driver,
            'top_driver_correlation': drivers.get(top_driver) if top_driver else None,
        }
        if 'net_annual_loss_exposure' in stats:
            row['net_eal'] = stats['net_annual_loss_exposure']['mean']
            row['net_var_95'] = stats['net_annual_loss_exposure']['var_95']
            row['expected_annual_recovery'] = stats['net_annual_loss_exposure']['expected_annual_recovery']
        return row

    def sensitivity_analysis(self) -> dict:
        """
        Identify key risk drivers via Spearman rank correlation with ALE.
        Robust to the non-linear relationships in the FAIR model.
        """
        if self.results is None:
            raise ValueError("Run simulation first")

        ale = self.results['ale']
        correlations = {}

        def _add(label, samples):
            if samples is None:
                return
            # Spearman is undefined when an input is constant (e.g., a fixed
            # loss form); skip rather than emit a warning.
            if np.ptp(samples) == 0 or np.ptp(ale) == 0:
                return
            corr, _ = sp_stats.spearmanr(samples, ale)
            if not np.isnan(corr):
                correlations[label] = float(corr)

        if self.scenario.uses_direct_lef:
            _add('LEF', self.results['lef'])
        else:
            _add('TEF', self.results['tef'])
            _add('Vulnerability', self.results['vulnerability'])

        for name, samples in self.results['primary_breakdown'].items():
            _add(f'Primary: {name}', samples)
        for name, samples in self.results['secondary_breakdown'].items():
            _add(f'Secondary: {name}', samples)

        return dict(sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True))

    def plot_loss_exceedance_curve(self, output_path: str = 'loss_exceedance.png'):
        """Generate loss exceedance curve visualization"""
        if self.results is None:
            raise ValueError("Run simulation first")

        ale = np.sort(self.results['ale'])
        exceedance_prob = 1 - np.arange(1, len(ale) + 1) / len(ale)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(ale / 1e6, exceedance_prob * 100, 'b-', linewidth=2, label='Gross')

        var_95 = np.percentile(self.results['ale'], 95)
        var_99 = np.percentile(self.results['ale'], 99)
        mean_ale = np.mean(self.results['ale'])

        ax.axvline(var_95 / 1e6, color='orange', linestyle='--', label=f'95th %ile: ${var_95/1e6:.1f}M')
        ax.axvline(var_99 / 1e6, color='red', linestyle='--', label=f'99th %ile: ${var_99/1e6:.1f}M')
        ax.axvline(mean_ale / 1e6, color='green', linestyle='--', label=f'Mean: ${mean_ale/1e6:.1f}M')

        # Overlay net-of-insurance curve when present
        if self.results['net_ale'] is not None:
            net = np.sort(self.results['net_ale'])
            net_exc = 1 - np.arange(1, len(net) + 1) / len(net)
            ax.plot(net / 1e6, net_exc * 100, color='purple', linewidth=2, linestyle='-', label='Net of insurance')

        ax.set_xlabel('Annual Loss ($M)', fontsize=12)
        ax.set_ylabel('Probability of Exceedance (%)', fontsize=12)
        ax.set_title(f'Loss Exceedance Curve: {self.scenario.name}', fontsize=14)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(left=0)
        ax.set_ylim(0, 100)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return output_path

    def plot_tornado_diagram(self, output_path: str = 'tornado.png'):
        """Generate tornado diagram for sensitivity analysis"""
        if self.results is None:
            raise ValueError("Run simulation first")

        sensitivities = self.sensitivity_analysis()
        top_drivers = list(sensitivities.items())[:10]
        if not top_drivers:
            return None
        names = [x[0] for x in top_drivers]
        values = [x[1] for x in top_drivers]

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#d73027' if v > 0 else '#4575b4' for v in values]
        y_pos = np.arange(len(names))

        ax.barh(y_pos, values, color=colors, height=0.6)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names)
        ax.invert_yaxis()
        ax.set_xlabel('Rank Correlation (Spearman) with Annual Loss Exposure', fontsize=12)
        ax.set_title(f'Risk Driver Sensitivity: {self.scenario.name}', fontsize=14)
        ax.axvline(0, color='black', linewidth=0.5)
        ax.set_xlim(-1, 1)
        ax.grid(True, alpha=0.3, axis='x')

        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return output_path

    def plot_ale_distribution(self, output_path: str = 'ale_distribution.png'):
        """Generate ALE distribution histogram"""
        if self.results is None:
            raise ValueError("Run simulation first")

        ale = self.results['ale'] / 1e6  # millions

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(ale, bins=50, density=True, alpha=0.7, color='steelblue', edgecolor='white')

        mean_ale = np.mean(ale)
        var_95 = np.percentile(ale, 95)

        ax.axvline(mean_ale, color='green', linestyle='--', linewidth=2, label=f'Mean: ${mean_ale:.1f}M')
        ax.axvline(var_95, color='red', linestyle='--', linewidth=2, label=f'95th %ile: ${var_95:.1f}M')

        ax.set_xlabel('Annual Loss Exposure ($M)', fontsize=12)
        ax.set_ylabel('Density', fontsize=12)
        ax.set_title(f'Annual Loss Exposure Distribution: {self.scenario.name}', fontsize=14)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return output_path

    def export_results(self, output_path: str = 'simulation_results.csv'):
        """Export full simulation results to CSV"""
        if self.results is None:
            raise ValueError("Run simulation first")
        import csv

        headers = ['iteration', 'tef', 'vulnerability', 'lef', 'event_count',
                   'primary_loss', 'secondary_loss', 'total_lm', 'ale']
        has_net = self.results['net_ale'] is not None
        if has_net:
            headers += ['annual_recovery', 'net_ale']
        for name in self.results['primary_breakdown']:
            headers.append(f'primary_{name}')
        for name in self.results['secondary_breakdown']:
            headers.append(f'secondary_{name}')

        tef = self.results['tef']
        vuln = self.results['vulnerability']

        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for i in range(self.iterations):
                row = [
                    i + 1,
                    '' if tef is None else tef[i],
                    '' if vuln is None else vuln[i],
                    self.results['lef'][i],
                    self.results['event_counts'][i],
                    self.results['primary_loss'][i],
                    self.results['secondary_loss'][i],
                    self.results['total_lm'][i],
                    self.results['ale'][i],
                ]
                if has_net:
                    row += [self.results['annual_recovery'][i], self.results['net_ale'][i]]
                for name in self.results['primary_breakdown']:
                    row.append(self.results['primary_breakdown'][name][i])
                for name in self.results['secondary_breakdown']:
                    row.append(self.results['secondary_breakdown'][name][i])
                writer.writerow(row)
        return output_path


# ---------------------------------------------------------------------------
# Scenario comparison & portfolio aggregation
# ---------------------------------------------------------------------------

def compare_scenarios(base: FAIRScenario, alt: FAIRScenario,
                      iterations: int = 10000, seed: Optional[int] = None,
                      bootstrap: int = 200) -> dict:
    """Run two scenarios under identical settings and return a delta table.

    Useful for control-improvement ('treated' vs baseline) and risk-transfer
    (insurance on/off) what-if analysis.
    """
    sim_a = FAIRSimulation(base, iterations, seed, bootstrap)
    sim_b = FAIRSimulation(alt, iterations, None if seed is None else seed + 1000, bootstrap)
    stats_a = sim_a.run()
    stats_b = sim_b.run()

    def headline(s):
        a = s['annual_loss_exposure']
        return {'eal': a['mean'], 'var_95': a['var_95'], 'var_99': a['var_99'], 'tvar_95': a['tvar_95']}

    h_a, h_b = headline(stats_a), headline(stats_b)
    delta = {k: h_b[k] - h_a[k] for k in h_a}
    pct = {k: (delta[k] / h_a[k] if h_a[k] else 0.0) for k in h_a}
    return {
        'baseline': {'name': base.name, **h_a},
        'alternative': {'name': alt.name, **h_b},
        'delta': delta,
        'pct_change': pct,
        '_sims': (sim_a, sim_b),
    }


def run_portfolio(scenarios: list, iterations: int = 10000,
                  seed: Optional[int] = None, bootstrap: int = 200) -> dict:
    """Aggregate independent scenarios into a combined annual loss distribution.

    Assumes scenarios are independent: per-iteration ALE samples are summed
    across scenarios. Each scenario uses a distinct RNG stream.
    """
    sims = []
    combined = np.zeros(iterations)
    rows = []
    for i, sc in enumerate(scenarios):
        s_seed = None if seed is None else seed + i
        sim = FAIRSimulation(sc, iterations, s_seed, bootstrap)
        sim.run()
        combined = combined + sim.results['ale']
        rows.append(sim.risk_register_row())
        sims.append(sim)

    percentiles = [10, 25, 50, 75, 90, 95, 99]
    portfolio = {
        'mean': float(np.mean(combined)),
        'median': float(np.median(combined)),
        'std': float(np.std(combined)),
        'var_95': float(np.percentile(combined, 95)),
        'var_99': float(np.percentile(combined, 99)),
        'tvar_95': _tvar(combined, 95),
        'tvar_99': _tvar(combined, 99),
        'percentiles': {p: float(np.percentile(combined, p)) for p in percentiles},
    }
    # Diversification benefit vs. naive sum of standalone VaRs
    sum_var95 = sum(r['var_95'] for r in rows)
    portfolio['sum_standalone_var_95'] = sum_var95
    portfolio['diversification_benefit_var_95'] = sum_var95 - portfolio['var_95']

    return {
        'portfolio': portfolio,
        'scenarios': rows,
        'assumption': 'Scenarios modeled as independent; ALE samples summed per iteration.',
        '_combined': combined,
        '_sims': sims,
    }


def plot_portfolio_exceedance(combined: np.ndarray, output_path: str, sims: list):
    """Loss exceedance curve for the aggregated portfolio with per-scenario overlay."""
    fig, ax = plt.subplots(figsize=(10, 6))
    s = np.sort(combined)
    exc = 1 - np.arange(1, len(s) + 1) / len(s)
    ax.plot(s / 1e6, exc * 100, 'k-', linewidth=2.5, label='Portfolio (combined)')
    for sim in sims:
        ss = np.sort(sim.results['ale'])
        ee = 1 - np.arange(1, len(ss) + 1) / len(ss)
        ax.plot(ss / 1e6, ee * 100, linewidth=1, alpha=0.6, label=sim.scenario.name)
    ax.set_xlabel('Annual Loss ($M)', fontsize=12)
    ax.set_ylabel('Probability of Exceedance (%)', fontsize=12)
    ax.set_title('Portfolio Loss Exceedance Curve', fontsize=14)
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(0, 100)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path


def write_register_csv(rows: list, output_path: str, portfolio: Optional[dict] = None):
    """Write risk-register rows (and optional portfolio total) to CSV."""
    import csv
    fields = ['scenario', 'frequency_model', 'lef_mean', 'eal', 'median_ale',
              'var_95', 'var_99', 'tvar_95', 'tvar_99', 'p_zero_loss_year',
              'top_driver', 'top_driver_correlation', 'net_eal', 'net_var_95',
              'expected_annual_recovery']
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
        if portfolio is not None:
            writer.writerow({
                'scenario': 'PORTFOLIO (combined)',
                'eal': portfolio['mean'], 'median_ale': portfolio['median'],
                'var_95': portfolio['var_95'], 'var_99': portfolio['var_99'],
                'tvar_95': portfolio['tvar_95'], 'tvar_99': portfolio['tvar_99'],
            })
    return output_path


# ---------------------------------------------------------------------------
# Demo scenario & CLI
# ---------------------------------------------------------------------------

def create_sample_scenario() -> FAIRScenario:
    """Create a sample ransomware scenario for demonstration"""
    return FAIRScenario(
        name="Ransomware on Core Banking System",
        tef=PERTParams(minimum=5, mode=15, maximum=30),
        vulnerability=PERTParams(minimum=0.03, mode=0.08, maximum=0.15),
        primary_losses=[
            LossForm("Productivity", PERTParams(2_000_000, 10_000_000, 50_000_000)),
            LossForm("Response", PERTParams(500_000, 2_000_000, 10_000_000)),
            LossForm("Restoration", PERTParams(1_000_000, 5_000_000, 20_000_000)),
        ],
        secondary_losses=[
            LossForm("Regulatory Fines", LognormalParams(p10=1_000_000, p90=50_000_000), probability=0.6),
            LossForm("Reputation", PERTParams(500_000, 5_000_000, 25_000_000), probability=0.7),
        ],
        loss_correlation=0.7,
        conditional_secondary=True,
    )


def _print_summary(scenario, stats):
    ale = stats['annual_loss_exposure']
    print("\n" + "=" * 60)
    print(f"FAIR Analysis Summary: {scenario.name}")
    print("=" * 60)
    print(f"Expected Annual Loss (Mean): ${ale['mean']/1e6:.2f}M")
    print(f"Median Annual Loss: ${ale['median']/1e6:.2f}M")
    print(f"95th Percentile (VaR): ${ale['var_95']/1e6:.2f}M")
    print(f"99th Percentile: ${ale['var_99']/1e6:.2f}M")
    print(f"TVaR 95 (expected shortfall): ${ale['tvar_95']/1e6:.2f}M")
    if ale.get('mc_standard_error'):
        se = ale['mc_standard_error']
        print(f"MC standard error (mean): ${se['mean_se']/1e6:.3f}M ({se['mean_rel_error']:.1%} rel.)")
    print(f"Loss Event Frequency (Mean): {stats['lef']['mean']:.2f} events/year")
    print(f"P(Zero Loss Year): {ale['p_zero_events']:.1%}")
    print(f"Mean Event Count: {ale['mean_event_count']:.2f}")
    if ale['conditional_ale']:
        print(f"Conditional Mean (given event): ${ale['conditional_ale']['mean']/1e6:.2f}M")
    if 'net_annual_loss_exposure' in stats:
        net = stats['net_annual_loss_exposure']
        print("-" * 60)
        print(f"Net of insurance — EAL: ${net['mean']/1e6:.2f}M | VaR95: ${net['var_95']/1e6:.2f}M")
        print(f"Expected annual recovery: ${net['expected_annual_recovery']/1e6:.2f}M")
    print("=" * 60)


def _load(path) -> FAIRScenario:
    with open(path) as f:
        return FAIRScenario.from_dict(json.load(f))


def main():
    parser = argparse.ArgumentParser(description='FAIR Risk Analysis Monte Carlo Simulation')
    parser.add_argument('--config', type=str, help='Path to scenario configuration JSON')
    parser.add_argument('--compare', type=str, help='Second config to compare against --config (what-if)')
    parser.add_argument('--portfolio', type=str, nargs='+', help='Multiple configs to aggregate into a portfolio')
    parser.add_argument('--iterations', type=int, default=10000, help='Number of simulation iterations')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    parser.add_argument('--bootstrap', type=int, default=200, help='Bootstrap resamples for MC error (0 to disable)')
    parser.add_argument('--output-dir', type=str, default='.', help='Output directory for results')
    parser.add_argument('--demo', action='store_true', help='Run with sample scenario')
    args = parser.parse_args()

    out = args.output_dir

    # --- Portfolio mode ---
    if args.portfolio:
        scenarios = [_load(p) for p in args.portfolio]
        result = run_portfolio(scenarios, args.iterations, args.seed, args.bootstrap)
        with open(f"{out}/portfolio_statistics.json", 'w') as f:
            json.dump({k: v for k, v in result.items() if not k.startswith('_')}, f, indent=2)
        plot_portfolio_exceedance(result['_combined'], f"{out}/portfolio_exceedance.png", result['_sims'])
        write_register_csv(result['scenarios'], f"{out}/risk_register.csv", result['portfolio'])
        p = result['portfolio']
        print("\n" + "=" * 60)
        print("FAIR Portfolio Summary")
        print("=" * 60)
        print(f"Combined EAL: ${p['mean']/1e6:.2f}M | VaR95: ${p['var_95']/1e6:.2f}M | TVaR95: ${p['tvar_95']/1e6:.2f}M")
        print(f"Diversification benefit (VaR95): ${p['diversification_benefit_var_95']/1e6:.2f}M")
        print(f"Outputs written to: {out}/")
        print("=" * 60)
        return

    # --- Single / compare mode ---
    if args.demo:
        scenario = create_sample_scenario()
    elif args.config:
        scenario = _load(args.config)
    else:
        print("Please provide --config, --demo, or --portfolio")
        return

    sim = FAIRSimulation(scenario, args.iterations, args.seed, args.bootstrap)
    stats = sim.run()

    with open(f"{out}/statistics.json", 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Statistics saved to: {out}/statistics.json")
    with open(f"{out}/risk_register_row.json", 'w') as f:
        json.dump(stats['risk_register_row'], f, indent=2)

    print(f"Loss exceedance curve saved to: {sim.plot_loss_exceedance_curve(f'{out}/loss_exceedance.png')}")
    print(f"Tornado diagram saved to: {sim.plot_tornado_diagram(f'{out}/tornado.png')}")
    print(f"ALE distribution saved to: {sim.plot_ale_distribution(f'{out}/ale_distribution.png')}")
    print(f"Full results saved to: {sim.export_results(f'{out}/simulation_results.csv')}")

    _print_summary(scenario, stats)

    # --- Comparison ---
    if args.compare:
        alt = _load(args.compare)
        cmp = compare_scenarios(scenario, alt, args.iterations, args.seed, args.bootstrap)
        with open(f"{out}/comparison.json", 'w') as f:
            json.dump({k: v for k, v in cmp.items() if not k.startswith('_')}, f, indent=2)
        print("\n" + "=" * 60)
        print(f"Comparison: {cmp['baseline']['name']}  vs  {cmp['alternative']['name']}")
        print("=" * 60)
        for metric in ['eal', 'var_95', 'var_99', 'tvar_95']:
            b = cmp['baseline'][metric] / 1e6
            a = cmp['alternative'][metric] / 1e6
            print(f"{metric.upper():>8}: ${b:8.2f}M -> ${a:8.2f}M  ({cmp['pct_change'][metric]:+.1%})")
        print("=" * 60)


if __name__ == '__main__':
    main()
