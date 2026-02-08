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
import numpy as np
from dataclasses import dataclass
from typing import Optional
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


@dataclass
class PERTParams:
    """PERT distribution parameters (min, mode, max)"""
    minimum: float
    mode: float
    maximum: float
    
    def to_beta_params(self):
        """Convert PERT to Beta distribution parameters"""
        # PERT uses lambda=4 for mode weight
        mean = (self.minimum + 4 * self.mode + self.maximum) / 6
        
        if self.maximum == self.minimum:
            return None, None, self.minimum, self.maximum
            
        # Calculate alpha and beta for beta distribution
        temp = (mean - self.minimum) * (2 * self.mode - self.minimum - self.maximum)
        if abs(self.maximum - self.minimum) < 1e-10:
            alpha = 1
        else:
            temp2 = (self.mode - mean) * (self.maximum - self.minimum)
            if abs(temp2) < 1e-10:
                alpha = 3  # Default when mode equals mean
            else:
                alpha = temp / temp2
                
        beta = alpha * (self.maximum - mean) / (mean - self.minimum) if (mean - self.minimum) > 0 else 1
        
        # Ensure valid parameters
        alpha = max(0.5, min(alpha, 100))
        beta = max(0.5, min(beta, 100))
        
        return alpha, beta, self.minimum, self.maximum

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """Generate n samples from PERT distribution"""
        alpha, beta, low, high = self.to_beta_params()
        
        if alpha is None:
            return np.full(n, low)
        
        samples = rng.beta(alpha, beta, n)
        return low + samples * (high - low)


@dataclass 
class LossForm:
    """A single loss form with its distribution parameters"""
    name: str
    params: PERTParams
    probability: float = 1.0  # For secondary losses
    
    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """Sample loss amounts, accounting for probability"""
        base_samples = self.params.sample(n, rng)
        
        if self.probability < 1.0:
            # Apply probability mask for secondary losses
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
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FAIRScenario':
        """Create scenario from dictionary (e.g., loaded from JSON)"""
        return cls(
            name=data['name'],
            tef=PERTParams(**data['tef']),
            vulnerability=PERTParams(**data['vulnerability']),
            primary_losses=[
                LossForm(
                    name=lf['name'],
                    params=PERTParams(**lf['params']),
                    probability=lf.get('probability', 1.0)
                )
                for lf in data['primary_losses']
            ],
            secondary_losses=[
                LossForm(
                    name=lf['name'],
                    params=PERTParams(**lf['params']),
                    probability=lf.get('probability', 1.0)
                )
                for lf in data.get('secondary_losses', [])
            ]
        )


class FAIRSimulation:
    """Monte Carlo simulation engine for FAIR analysis"""
    
    def __init__(self, scenario: FAIRScenario, iterations: int = 10000, seed: Optional[int] = None):
        self.scenario = scenario
        self.iterations = iterations
        self.rng = np.random.default_rng(seed)
        self.results = None
        
    def run(self) -> dict:
        """Execute Monte Carlo simulation"""
        n = self.iterations
        
        # Sample Loss Event Frequency
        tef_samples = self.scenario.tef.sample(n, self.rng)
        vuln_samples = self.scenario.vulnerability.sample(n, self.rng)
        lef_samples = tef_samples * vuln_samples
        
        # Sample Loss Magnitudes
        primary_totals = np.zeros(n)
        primary_breakdown = {}
        
        for loss_form in self.scenario.primary_losses:
            samples = loss_form.sample(n, self.rng)
            primary_breakdown[loss_form.name] = samples
            primary_totals += samples
            
        secondary_totals = np.zeros(n)
        secondary_breakdown = {}
        
        for loss_form in self.scenario.secondary_losses:
            samples = loss_form.sample(n, self.rng)
            secondary_breakdown[loss_form.name] = samples
            secondary_totals += samples
            
        total_lm = primary_totals + secondary_totals
        
        # Annual Loss Exposure
        ale_samples = lef_samples * total_lm
        
        self.results = {
            'tef': tef_samples,
            'vulnerability': vuln_samples,
            'lef': lef_samples,
            'primary_loss': primary_totals,
            'secondary_loss': secondary_totals,
            'total_lm': total_lm,
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
        
        percentiles = [10, 25, 50, 75, 90, 95, 99]
        
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
                'percentiles': {p: float(np.percentile(ale, p)) for p in percentiles}
            }
        }
    
    def sensitivity_analysis(self) -> dict:
        """
        Perform sensitivity analysis to identify key risk drivers.
        Uses correlation-based approach to measure input influence on output.
        """
        if self.results is None:
            raise ValueError("Run simulation first")
            
        ale = self.results['ale']
        
        correlations = {}
        
        # Core FAIR components
        correlations['TEF'] = float(np.corrcoef(self.results['tef'], ale)[0, 1])
        correlations['Vulnerability'] = float(np.corrcoef(self.results['vulnerability'], ale)[0, 1])
        
        # Primary loss forms
        for name, samples in self.results['primary_breakdown'].items():
            corr = np.corrcoef(samples, ale)[0, 1]
            if not np.isnan(corr):
                correlations[f'Primary: {name}'] = float(corr)
        
        # Secondary loss forms  
        for name, samples in self.results['secondary_breakdown'].items():
            corr = np.corrcoef(samples, ale)[0, 1]
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
        ax.set_xlabel('Correlation with Annual Loss Exposure', fontsize=12)
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
        
        headers = ['iteration', 'tef', 'vulnerability', 'lef', 
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
        ]
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
    print("\n" + "="*60)
    print(f"FAIR Analysis Summary: {scenario.name}")
    print("="*60)
    print(f"Expected Annual Loss (Mean): ${stats['annual_loss_exposure']['mean']/1e6:.2f}M")
    print(f"Median Annual Loss: ${stats['annual_loss_exposure']['median']/1e6:.2f}M")
    print(f"95th Percentile (VaR): ${stats['annual_loss_exposure']['var_95']/1e6:.2f}M")
    print(f"99th Percentile: ${stats['annual_loss_exposure']['var_99']/1e6:.2f}M")
    print(f"Loss Event Frequency (Mean): {stats['lef']['mean']:.2f} events/year")
    print("="*60)


if __name__ == '__main__':
    main()
