#!/usr/bin/env python3
"""
FAIR Risk Analysis Monte Carlo Simulation

Executes probabilistic risk quantification using the FAIR methodology.
Generates loss distributions, exceedance curves, and sensitivity analysis.

Usage:
    python fair_simulation.py --config params.json
    python fair_simulation.py --interactive

Output:
    - Loss distribution statistics (JSON)
    - Loss exceedance curve (PNG)
    - Tornado diagram for sensitivity analysis (PNG)
    - Full simulation results (CSV)
"""

import json
import argparse
import warnings
import math
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Union
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy import stats as sp_stats


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
        alpha, beta_param, low, high = self.to_beta_params()

        if alpha is None:
            return np.full(len(quantiles), low)

        raw = sp_stats.beta.ppf(quantiles, alpha, beta_param)
        return low + raw * (high - low)


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
        mu, sigma = self._params
        return sp_stats.lognorm.ppf(quantiles, s=sigma, scale=math.exp(mu))


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
        """Sample loss amounts, accounting for probability"""
        base_samples = self.params.sample(n, rng)

        if self.probability < 1.0:
            occurs = rng.random(n) < self.probability
            return base_samples * occurs

        return base_samples


@dataclass
class FAIRScenario:
    """Complete FAIR scenario definition"""
    name: str
    tef: PERTParams  # Threat Event Frequency
    vulnerability: PERTParams  # As decimal (0-1)
    primary_losses: list[LossForm]
    secondary_losses: list[LossForm]
    loss_correlation: float = 0.0
    conditional_secondary: bool = False

    def validate(self):
        """Validate scenario parameters and warn on unusual inputs"""
        # TEF must be non-negative
        if self.tef.minimum < 0:
            raise ValueError("TEF minimum must be >= 0")

        # Vulnerability must be in [0, 1]
        if self.vulnerability.minimum < 0 or self.vulnerability.maximum > 1:
            raise ValueError("Vulnerability must be in [0, 1]")

        # Must have at least one primary loss
        if not self.primary_losses:
            raise ValueError("At least one primary loss form is required")

        # Non-negative loss magnitudes for PERT params
        for lf in self.primary_losses + self.secondary_losses:
            if isinstance(lf.params, PERTParams) and lf.params.minimum < 0:
                raise ValueError(f"Loss form '{lf.name}' has negative minimum loss magnitude")

        # Warnings for unusual inputs
        vuln_mode = self.vulnerability.mode
        if vuln_mode > 0.50:
            warnings.warn(f"Vulnerability mode {vuln_mode:.0%} is unusually high (>50%)")

        tef_mode = self.tef.mode
        if tef_mode > 1000:
            warnings.warn(f"TEF mode {tef_mode} is very high (>1000 events/year)")

    @classmethod
    def from_dict(cls, data: dict) -> 'FAIRScenario':
        """Create scenario from dictionary (e.g., loaded from JSON)"""

        def _parse_params(params_dict: dict) -> Union[PERTParams, LognormalParams]:
            if 'p10' in params_dict and 'p90' in params_dict:
                return LognormalParams(p10=params_dict['p10'], p90=params_dict['p90'])
            return PERTParams(**params_dict)

        scenario = cls(
            name=data['name'],
            tef=PERTParams(**data['tef']),
            vulnerability=PERTParams(**data['vulnerability']),
            primary_losses=[
                LossForm(
                    name=lf['name'],
                    params=_parse_params(lf['params']),
                    probability=lf.get('probability', 1.0)
                )
                for lf in data['primary_losses']
            ],
            secondary_losses=[
                LossForm(
                    name=lf['name'],
                    params=_parse_params(lf['params']),
                    probability=lf.get('probability', 1.0)
                )
                for lf in data.get('secondary_losses', [])
            ],
            loss_correlation=data.get('loss_correlation', 0.0),
            conditional_secondary=data.get('conditional_secondary', False)
        )
        scenario.validate()
        return scenario


class FAIRSimulation:
    """Monte Carlo simulation engine for FAIR analysis"""

    def __init__(self, scenario: FAIRScenario, iterations: int = 10000, seed: Optional[int] = None):
        self.scenario = scenario
        self.iterations = iterations
        self.rng = np.random.default_rng(seed)
        self.results = None

    def run(self) -> dict:
        """Execute Monte Carlo simulation using compound Poisson process"""
        n = self.iterations
        corr = self.scenario.loss_correlation

        # Sample Loss Event Frequency
        tef_samples = self.scenario.tef.sample(n, self.rng)
        vuln_samples = self.scenario.vulnerability.sample(n, self.rng)
        lef_samples = tef_samples * vuln_samples

        # Draw event counts from Poisson distribution
        event_counts = self.rng.poisson(lef_samples)

        # Pre-allocate annual totals
        ale_samples = np.zeros(n)
        primary_totals = np.zeros(n)
        secondary_totals = np.zeros(n)
        primary_breakdown = {lf.name: np.zeros(n) for lf in self.scenario.primary_losses}
        secondary_breakdown = {lf.name: np.zeros(n) for lf in self.scenario.secondary_losses}

        # Process each iteration
        max_events = int(event_counts.max()) if event_counts.max() > 0 else 0

        if max_events > 0:
            # For efficiency, process all iterations that have events in bulk
            has_events = event_counts > 0
            event_iters = np.where(has_events)[0]

            for idx in event_iters:
                num_events = event_counts[idx]

                for _ in range(num_events):
                    if corr > 0:
                        # Shared severity factor model
                        shared_u = self.rng.random()

                        for lf in self.scenario.primary_losses:
                            indep_u = self.rng.random()
                            effective_u = np.clip(corr * shared_u + (1 - corr) * indep_u, 0, 1)
                            sample_val = float(lf.params.sample_at_quantiles(np.array([effective_u]))[0])
                            primary_breakdown[lf.name][idx] += sample_val
                            primary_totals[idx] += sample_val

                        # Compute primary percentile rank for conditional secondary
                        if self.scenario.conditional_secondary and self.scenario.secondary_losses:
                            all_primary_vals = [primary_breakdown[lf.name][idx] for lf in self.scenario.primary_losses]
                            primary_percentile = effective_u  # Use last effective_u as proxy

                        for lf in self.scenario.secondary_losses:
                            prob = lf.probability
                            if self.scenario.conditional_secondary:
                                prob = prob * (0.5 + primary_percentile)

                            if self.rng.random() < prob:
                                indep_u = self.rng.random()
                                effective_u_sec = np.clip(corr * shared_u + (1 - corr) * indep_u, 0, 1)
                                sample_val = float(lf.params.sample_at_quantiles(np.array([effective_u_sec]))[0])
                                secondary_breakdown[lf.name][idx] += sample_val
                                secondary_totals[idx] += sample_val
                    else:
                        # No correlation: independent sampling
                        for lf in self.scenario.primary_losses:
                            sample_val = float(lf.params.sample(1, self.rng)[0])
                            primary_breakdown[lf.name][idx] += sample_val
                            primary_totals[idx] += sample_val

                        for lf in self.scenario.secondary_losses:
                            if self.rng.random() < lf.probability:
                                sample_val = float(lf.params.sample(1, self.rng)[0])
                                secondary_breakdown[lf.name][idx] += sample_val
                                secondary_totals[idx] += sample_val

        ale_samples = primary_totals + secondary_totals

        self.results = {
            'tef': tef_samples,
            'vulnerability': vuln_samples,
            'lef': lef_samples,
            'event_counts': event_counts,
            'primary_loss': primary_totals,
            'secondary_loss': secondary_totals,
            'total_lm': primary_totals + secondary_totals,
            'ale': ale_samples,
            'primary_breakdown': primary_breakdown,
            'secondary_breakdown': secondary_breakdown
        }

        return self.get_statistics()

    def get_statistics(self) -> dict:
        """Calculate summary statistics from simulation results"""
        if self.results is None:
            raise ValueError("Run simulation first")

        ale = self.results['ale']
        lef = self.results['lef']
        lm = self.results['total_lm']
        event_counts = self.results['event_counts']

        percentiles = [10, 25, 50, 75, 90, 95, 99]

        # Conditional ALE stats (years with >= 1 event)
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
            }

        return {
            'scenario_name': self.scenario.name,
            'iterations': self.iterations,
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
            'annual_loss_exposure': {
                'mean': float(np.mean(ale)),
                'median': float(np.median(ale)),
                'std': float(np.std(ale)),
                'var_95': float(np.percentile(ale, 95)),
                'var_99': float(np.percentile(ale, 99)),
                'percentiles': {p: float(np.percentile(ale, p)) for p in percentiles},
                'p_zero_events': p_zero_events,
                'mean_event_count': mean_event_count,
                'conditional_ale': conditional_ale
            }
        }

    def sensitivity_analysis(self) -> dict:
        """
        Perform sensitivity analysis to identify key risk drivers.
        Uses Spearman rank correlation for non-linear FAIR model.
        """
        if self.results is None:
            raise ValueError("Run simulation first")

        ale = self.results['ale']

        correlations = {}

        # Core FAIR components
        corr, _ = sp_stats.spearmanr(self.results['tef'], ale)
        correlations['TEF'] = float(corr) if not np.isnan(corr) else 0.0

        corr, _ = sp_stats.spearmanr(self.results['vulnerability'], ale)
        correlations['Vulnerability'] = float(corr) if not np.isnan(corr) else 0.0

        # Primary loss forms
        for name, samples in self.results['primary_breakdown'].items():
            corr, _ = sp_stats.spearmanr(samples, ale)
            if not np.isnan(corr):
                correlations[f'Primary: {name}'] = float(corr)

        # Secondary loss forms
        for name, samples in self.results['secondary_breakdown'].items():
            corr, _ = sp_stats.spearmanr(samples, ale)
            if not np.isnan(corr):
                correlations[f'Secondary: {name}'] = float(corr)

        # Sort by absolute correlation
        sorted_correlations = dict(
            sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
        )

        return sorted_correlations

    def plot_loss_exceedance_curve(self, output_path: str = 'loss_exceedance.png'):
        """Generate loss exceedance curve visualization"""
        if self.results is None:
            raise ValueError("Run simulation first")

        ale = np.sort(self.results['ale'])
        exceedance_prob = 1 - np.arange(1, len(ale) + 1) / len(ale)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(ale / 1e6, exceedance_prob * 100, 'b-', linewidth=2)

        # Add key percentile markers
        var_95 = np.percentile(ale, 95)
        var_99 = np.percentile(ale, 99)
        mean_ale = np.mean(ale)

        ax.axvline(var_95 / 1e6, color='orange', linestyle='--', label=f'95th %ile: ${var_95/1e6:.1f}M')
        ax.axvline(var_99 / 1e6, color='red', linestyle='--', label=f'99th %ile: ${var_99/1e6:.1f}M')
        ax.axvline(mean_ale / 1e6, color='green', linestyle='--', label=f'Mean: ${mean_ale/1e6:.1f}M')

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

        # Take top 10 drivers
        top_drivers = list(sensitivities.items())[:10]
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

        ale = self.results['ale'] / 1e6  # Convert to millions

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

        # Add individual loss form columns
        for name in self.results['primary_breakdown'].keys():
            headers.append(f'primary_{name}')
        for name in self.results['secondary_breakdown'].keys():
            headers.append(f'secondary_{name}')

        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for i in range(self.iterations):
                row = [
                    i + 1,
                    self.results['tef'][i],
                    self.results['vulnerability'][i],
                    self.results['lef'][i],
                    self.results['event_counts'][i],
                    self.results['primary_loss'][i],
                    self.results['secondary_loss'][i],
                    self.results['total_lm'][i],
                    self.results['ale'][i]
                ]

                for name in self.results['primary_breakdown'].keys():
                    row.append(self.results['primary_breakdown'][name][i])
                for name in self.results['secondary_breakdown'].keys():
                    row.append(self.results['secondary_breakdown'][name][i])

                writer.writerow(row)

        return output_path


def create_sample_scenario() -> FAIRScenario:
    """Create a sample ransomware scenario for demonstration"""
    return FAIRScenario(
        name="Ransomware on Core Banking System",
        tef=PERTParams(minimum=5, mode=15, maximum=30),
        vulnerability=PERTParams(minimum=0.03, mode=0.08, maximum=0.15),
        primary_losses=[
            LossForm(
                name="Productivity",
                params=PERTParams(minimum=2_000_000, mode=10_000_000, maximum=50_000_000)
            ),
            LossForm(
                name="Response",
                params=PERTParams(minimum=500_000, mode=2_000_000, maximum=10_000_000)
            ),
            LossForm(
                name="Restoration",
                params=PERTParams(minimum=1_000_000, mode=5_000_000, maximum=20_000_000)
            )
        ],
        secondary_losses=[
            LossForm(
                name="Regulatory Fines",
                params=PERTParams(minimum=1_000_000, mode=10_000_000, maximum=50_000_000),
                probability=0.6
            ),
            LossForm(
                name="Reputation",
                params=PERTParams(minimum=500_000, mode=5_000_000, maximum=25_000_000),
                probability=0.7
            )
        ],
        loss_correlation=0.7
    )


def main():
    parser = argparse.ArgumentParser(description='FAIR Risk Analysis Monte Carlo Simulation')
    parser.add_argument('--config', type=str, help='Path to scenario configuration JSON')
    parser.add_argument('--iterations', type=int, default=10000, help='Number of simulation iterations')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    parser.add_argument('--output-dir', type=str, default='.', help='Output directory for results')
    parser.add_argument('--demo', action='store_true', help='Run with sample scenario')

    args = parser.parse_args()

    # Load or create scenario
    if args.demo:
        scenario = create_sample_scenario()
    elif args.config:
        with open(args.config) as f:
            scenario = FAIRScenario.from_dict(json.load(f))
    else:
        print("Please provide --config or --demo flag")
        return

    # Run simulation
    sim = FAIRSimulation(scenario, iterations=args.iterations, seed=args.seed)
    stats = sim.run()

    # Output results
    output_dir = args.output_dir

    # Statistics JSON
    stats_path = f"{output_dir}/statistics.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Statistics saved to: {stats_path}")

    # Visualizations
    lec_path = sim.plot_loss_exceedance_curve(f"{output_dir}/loss_exceedance.png")
    print(f"Loss exceedance curve saved to: {lec_path}")

    tornado_path = sim.plot_tornado_diagram(f"{output_dir}/tornado.png")
    print(f"Tornado diagram saved to: {tornado_path}")

    dist_path = sim.plot_ale_distribution(f"{output_dir}/ale_distribution.png")
    print(f"ALE distribution saved to: {dist_path}")

    # Full results CSV
    csv_path = sim.export_results(f"{output_dir}/simulation_results.csv")
    print(f"Full results saved to: {csv_path}")

    # Print summary
    ale_stats = stats['annual_loss_exposure']
    print("\n" + "="*60)
    print(f"FAIR Analysis Summary: {scenario.name}")
    print("="*60)
    print(f"Expected Annual Loss (Mean): ${ale_stats['mean']/1e6:.2f}M")
    print(f"Median Annual Loss: ${ale_stats['median']/1e6:.2f}M")
    print(f"95th Percentile (VaR): ${ale_stats['var_95']/1e6:.2f}M")
    print(f"99th Percentile: ${ale_stats['var_99']/1e6:.2f}M")
    print(f"Loss Event Frequency (Mean): {stats['lef']['mean']:.2f} events/year")
    print(f"P(Zero Loss Year): {ale_stats['p_zero_events']:.1%}")
    print(f"Mean Event Count: {ale_stats['mean_event_count']:.2f}")
    if ale_stats['conditional_ale']:
        print(f"Conditional Mean (given event): ${ale_stats['conditional_ale']['mean']/1e6:.2f}M")
    print("="*60)


if __name__ == '__main__':
    main()
