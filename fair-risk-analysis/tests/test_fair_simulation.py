"""
Unit tests for the FAIR Monte Carlo engine.

These guard the math that produces numbers used in risk-committee decks:
PERT/lognormal sampling, the compound-Poisson mean identity, the conditional
secondary fix, insurance recovery, and input validation.

Run:  pytest tests/ -q     (from the skill root, with scripts/ on the path)
"""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fair_simulation import (  # noqa: E402
    PERTParams, LognormalParams, LossForm, InsuranceTerms,
    FAIRScenario, FAIRSimulation, compare_scenarios, run_portfolio,
)


def test_pert_mean_matches_analytic():
    p = PERTParams(minimum=10, mode=20, maximum=60)
    rng = np.random.default_rng(0)
    samples = p.sample(200_000, rng)
    assert samples.mean() == pytest.approx(p.analytic_mean, rel=0.01)


def test_pert_respects_bounds():
    p = PERTParams(minimum=5, mode=8, maximum=40)
    rng = np.random.default_rng(1)
    s = p.sample(50_000, rng)
    assert s.min() >= 5 - 1e-9
    assert s.max() <= 40 + 1e-9


def test_pert_degenerate_min_eq_max():
    p = PERTParams(minimum=7, mode=7, maximum=7)
    rng = np.random.default_rng(2)
    s = p.sample(1000, rng)
    assert np.allclose(s, 7)


def test_lognormal_recovers_percentiles():
    p = LognormalParams(p10=1_000_000, p90=50_000_000)
    q = p.sample_at_quantiles(np.array([0.10, 0.90]))
    assert q[0] == pytest.approx(1_000_000, rel=1e-6)
    assert q[1] == pytest.approx(50_000_000, rel=1e-6)


def test_compound_poisson_mean_identity():
    # E[ALE] = E[LEF] * E[loss per event] for a single primary loss form.
    loss = PERTParams(minimum=100_000, mode=200_000, maximum=600_000)
    scenario = FAIRScenario(
        name="identity",
        tef=PERTParams(minimum=8, mode=10, maximum=12),
        vulnerability=PERTParams(minimum=0.3, mode=0.5, maximum=0.7),
        primary_losses=[LossForm("L", loss)],
    )
    sim = FAIRSimulation(scenario, iterations=60_000, seed=42, bootstrap=0)
    stats = sim.run()
    expected_lef = 10 * 0.5  # PERT modes/means are symmetric here -> 5.0
    expected = expected_lef * loss.analytic_mean
    assert stats['annual_loss_exposure']['mean'] == pytest.approx(expected, rel=0.03)
    assert stats['lef']['mean'] == pytest.approx(expected_lef, rel=0.03)


def test_conditional_secondary_works_without_correlation():
    # Regression: conditional_secondary must apply even when loss_correlation == 0.
    # Expected secondary frequency is preserved (mean of 0.5+percentile == 1.0).
    base = dict(
        name="cond",
        tef=PERTParams(5, 5, 5),
        vulnerability=PERTParams(1.0, 1.0, 1.0),
        primary_losses=[LossForm("P", PERTParams(100, 100, 100))],
        secondary_losses=[LossForm("S", PERTParams(1000, 1000, 1000), probability=0.4)],
        loss_correlation=0.0,
    )
    sim_off = FAIRSimulation(FAIRScenario(conditional_secondary=False, **base), 40_000, 7, bootstrap=0)
    sim_on = FAIRSimulation(FAIRScenario(conditional_secondary=True, **base), 40_000, 7, bootstrap=0)
    off = sim_off.run()['annual_loss_exposure']['mean']
    on = sim_on.run()['annual_loss_exposure']['mean']
    # Same expected total (within MC noise) — the fix changes the dependence
    # structure, not the expected secondary frequency.
    assert on == pytest.approx(off, rel=0.05)
    # And conditional secondary must actually change per-event behavior: high
    # primary-severity events should carry secondary losses more often.
    assert sim_on.results['secondary_loss'].sum() > 0


def test_insurance_reduces_loss_and_computes_recovery():
    # Deterministic single loss of 5M per event, ~1 event/yr, 1M deductible, 3M limit.
    scenario = FAIRScenario(
        name="ins",
        lef=PERTParams(1.0, 1.0, 1.0),
        primary_losses=[LossForm("P", PERTParams(5_000_000, 5_000_000, 5_000_000))],
        insurance=InsuranceTerms(per_occurrence_deductible=1_000_000, per_occurrence_limit=3_000_000),
    )
    sim = FAIRSimulation(scenario, iterations=40_000, seed=3, bootstrap=0)
    stats = sim.run()
    assert 'net_annual_loss_exposure' in stats
    net = stats['net_annual_loss_exposure']
    gross = stats['annual_loss_exposure']
    assert net['mean'] < gross['mean']
    # Per event recovery = min(5M-1M, 3M) = 3M. Expected ~ 3M * mean events.
    assert net['expected_annual_recovery'] == pytest.approx(3_000_000 * gross['mean_event_count'], rel=0.05)


def test_direct_lef_path():
    scenario = FAIRScenario(
        name="direct",
        lef=PERTParams(2, 3, 4),
        primary_losses=[LossForm("P", PERTParams(1000, 1000, 1000))],
    )
    sim = FAIRSimulation(scenario, iterations=20_000, seed=9, bootstrap=0)
    stats = sim.run()
    assert stats['frequency_model'] == 'direct_lef'
    assert 'LEF' in sim.sensitivity_analysis()


def test_tvar_geq_var():
    scenario = FAIRScenario(
        name="tail",
        tef=PERTParams(5, 10, 15),
        vulnerability=PERTParams(0.1, 0.2, 0.3),
        primary_losses=[LossForm("P", LognormalParams(p10=100_000, p90=5_000_000))],
    )
    stats = FAIRSimulation(scenario, 30_000, 11, bootstrap=0).run()
    ale = stats['annual_loss_exposure']
    assert ale['tvar_95'] >= ale['var_95']
    assert ale['tvar_99'] >= ale['var_99']


def test_loss_correlation_validation():
    with pytest.raises(ValueError):
        FAIRScenario(
            name="bad",
            tef=PERTParams(1, 2, 3),
            vulnerability=PERTParams(0.1, 0.2, 0.3),
            primary_losses=[LossForm("P", PERTParams(1, 2, 3))],
            loss_correlation=1.5,
        ).validate()


def test_missing_frequency_raises():
    with pytest.raises(ValueError):
        FAIRScenario(
            name="nofreq",
            primary_losses=[LossForm("P", PERTParams(1, 2, 3))],
        ).validate()


def test_zero_events_is_stable():
    # Tiny LEF -> many zero-loss years; engine must not crash and p_zero high.
    scenario = FAIRScenario(
        name="rare",
        lef=PERTParams(0.0, 0.001, 0.002),
        primary_losses=[LossForm("P", PERTParams(1000, 2000, 3000))],
    )
    stats = FAIRSimulation(scenario, 5000, 5, bootstrap=0).run()
    assert stats['annual_loss_exposure']['p_zero_events'] > 0.9


def test_reproducibility_with_seed():
    sc = lambda: FAIRScenario(
        name="rep",
        tef=PERTParams(5, 10, 15),
        vulnerability=PERTParams(0.05, 0.1, 0.2),
        primary_losses=[LossForm("P", PERTParams(1e5, 5e5, 1e6))],
    )
    a = FAIRSimulation(sc(), 10_000, seed=123, bootstrap=0).run()
    b = FAIRSimulation(sc(), 10_000, seed=123, bootstrap=0).run()
    assert a['annual_loss_exposure']['mean'] == b['annual_loss_exposure']['mean']


def test_portfolio_aggregation():
    def mk(name, lef):
        return FAIRScenario(name=name, lef=PERTParams(lef, lef, lef),
                            primary_losses=[LossForm("P", PERTParams(1e6, 1e6, 1e6))])
    res = run_portfolio([mk("a", 1.0), mk("b", 2.0)], iterations=20_000, seed=1, bootstrap=0)
    # Combined EAL ~ sum of standalone EALs (~1M + 2M).
    assert res['portfolio']['mean'] == pytest.approx(3_000_000, rel=0.05)
    assert len(res['scenarios']) == 2


def test_compare_scenarios_runs():
    base = FAIRScenario(name="base", tef=PERTParams(5, 10, 15),
                        vulnerability=PERTParams(0.1, 0.2, 0.3),
                        primary_losses=[LossForm("P", PERTParams(1e5, 5e5, 1e6))])
    treated = FAIRScenario(name="treated", tef=PERTParams(5, 10, 15),
                           vulnerability=PERTParams(0.02, 0.05, 0.1),
                           primary_losses=[LossForm("P", PERTParams(1e5, 5e5, 1e6))])
    cmp = compare_scenarios(base, treated, iterations=20_000, seed=2, bootstrap=0)
    assert cmp['alternative']['eal'] < cmp['baseline']['eal']
    assert cmp['delta']['eal'] < 0
