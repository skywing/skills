---
name: fair-risk-analysis
description: Interactive FAIR (Factor Analysis of Information Risk) risk scenario analysis for banking and financial services. Guide analysts through probabilistic risk quantification using Monte Carlo simulation, providing expert-suggested inputs based on industry benchmarks. Use when users request risk scenario analysis, cyber risk quantification, operational risk assessment, FAIR analysis, loss event frequency estimation, or risk case documentation for banking/financial institutions.
---

# FAIR Risk Scenario Analysis

Guide banking risk analysts through rigorous, probabilistic FAIR risk scenario analysis. Provide expert-suggested inputs based on industry benchmarks while building analyst calibration skills. Produce standalone documentation suitable for risk committee presentation, regulatory examination support, or risk register population.

## Analysis Workflow

The FAIR analysis follows five sequential phases:

1. **Scenario Scoping** → Define asset, threat, and effect
2. **Loss Event Frequency (LEF)** → Estimate TEF × Vulnerability
3. **Loss Magnitude (LM)** → Quantify primary and secondary losses
4. **Monte Carlo Simulation** → Run probabilistic analysis
5. **Documentation** → Generate comprehensive report

## Phase 1: Scenario Scoping

### Asset Identification

Present banking asset categories and prompt for selection:

- Core banking systems (transaction processing, account management)
- Payment infrastructure (SWIFT, ACH, wire transfer, card processing)
- Customer data repositories (PII, account data, transaction history)
- Trading platforms and market data systems
- Risk and Compliance (RSCA, Third-party, Loss Events, Business Resiliency, Model Risk, Issue Management, AML, Sanctions)
- ATM/branch networks
- Digital banking channels (mobile, web)
- Third-party integrations and APIs

Capture: asset name, criticality tier (1-5), data volume/sensitivity, transaction throughput if applicable.

### Threat Community

Present banking-relevant threat actors with frequency benchmarks:

| Threat Actor       | Typical TEF Range (annual)           | Primary Motivation      |
| ------------------ | ------------------------------------ | ----------------------- |
| Nation-state       | 5-20 targeted attempts               | Espionage, disruption   |
| Organized crime    | 50-500 opportunistic, 10-50 targeted | Financial gain          |
| Hacktivists        | 10-100 depending on profile          | Reputation damage       |
| Malicious insider  | 2-20 depending on controls           | Financial gain, revenge |
| Negligent insider  | 20-200 error events                  | Unintentional           |
| Third-party/vendor | 5-50 depending on ecosystem          | Varies                  |

Source benchmarks from: FS-ISAC threat briefings, Verizon DBIR financial sector, ORX loss data.

### Threat Type and Effect

Map to FAIR taxonomy:

- **Action**: Malicious, Error, Failure
- **Effect**: Confidentiality, Integrity, Availability (or combination)

Suggest likely attack vectors based on threat community selection.

## Phase 2: Loss Event Frequency (LEF)

LEF = Threat Event Frequency (TEF) × Vulnerability

### Threat Event Frequency (TEF)

Provide calibrated estimates based on:

- Threat community selected
- Asset exposure (internet-facing vs. internal)
- Industry vertical targeting patterns

**Calibration prompt**: "For [threat actor] targeting [asset type], industry data suggests [X-Y] attempts annually. How does your threat intelligence compare?"

### Vulnerability Estimation

Walk through control environment assessment using FFIEC CAT domains:

- Cyber Risk Management & Oversight
- Threat Intelligence & Collaboration
- Cybersecurity Controls
- External Dependency Management
- Cyber Incident Management & Resilience

Suggest vulnerability ranges by control maturity:

| Maturity Level | Vulnerability Range | Description                               |
| -------------- | ------------------- | ----------------------------------------- |
| Baseline       | 15-40%              | Minimum regulatory compliance             |
| Evolving       | 8-20%               | Risk-informed practices emerging          |
| Intermediate   | 3-12%               | Integrated risk management                |
| Advanced       | 1-5%                | Proactive, automated controls             |
| Innovative     | 0.5-2%              | Leading practices, continuous improvement |

## Phase 3: Loss Magnitude (LM)

Estimate using PERT distributions (min, most likely, max) or lognormal (10th, 90th percentile).

### Primary Loss Forms

**Productivity Loss**

- Calculate: affected staff × hourly rate × downtime hours
- Banking benchmark: $50K-500K/hour for core systems

**Response Costs**

- Incident response team (internal + external)
- Forensics and investigation
- Legal counsel
- Banking benchmark: $500K-$5M for significant incidents (Ponemon financial sector data)

**Replacement/Restoration**

- System rebuild and hardening
- Data restoration
- Banking benchmark: varies widely by asset

### Secondary Loss Forms

Estimate probability of secondary loss occurring (0-100%), then magnitude if it occurs.

**Fines and Judgments**

- OCC civil money penalties: $1M-$100M+ for BSA/AML violations
- CFPB enforcement: $5K-$1M per day
- State AG actions: $1M-$50M typical settlements
- GDPR (if applicable): up to 4% global revenue
- Class action settlements: $50-$200 per affected record typical

**Competitive Advantage Loss**

- Customer attrition: 3-7% elevated churn post-breach (banking sector studies)
- Market share impact: model based on breach materiality

**Reputation Damage**

- Stock price impact: 3-7% decline for material breaches (short-term)
- Brand remediation costs
- Customer acquisition cost increases

### Calibration Aids

For each estimate, offer:

1. **Reference class**: "Similar incidents at comparable institutions resulted in [range]"
2. **Confidence check**: "Rate your confidence 1-5 in this estimate"
3. **Decomposition prompt**: "Would it help to break this into components?"

See `references/loss-benchmarks.md` for detailed industry data.

## Phase 4: Monte Carlo Simulation

Generate simulation parameters for 10,000 iterations using a **compound Poisson process**:

```
LEF Distribution: PERT(min, mode, max) → per-iteration LEF rate
Event Counts: Poisson(LEF) → number of loss events per simulated year
LM Distribution: PERT(min, mode, max) or Lognormal(p10, p90)
ALE: Sum of independently sampled loss magnitudes across all events in each year
```

**Distribution choices:**
- **PERT**: Specified via minimum, mode, maximum. Good when analysts think in three-point estimates.
- **Lognormal**: Specified via 10th and 90th percentile values (`p10`, `p90`). Better for heavy-tailed loss magnitudes where extreme outcomes are plausible. The engine back-solves for the underlying normal parameters automatically.

**Correlation modeling:**
- Loss forms within the same event can be correlated using a shared severity factor model (configurable via `loss_correlation`, default 0.0). When enabled, a shared uniform draw blends with independent draws per loss form to produce correlated quantile-based samples.
- Secondary loss probability can optionally scale with primary loss severity (`conditional_secondary: true`), so larger primary losses increase the chance of regulatory/reputation impacts.

Present results:

- **Loss Exceedance Curve**: Probability of exceeding loss thresholds
- **VaR (95th percentile)**: "There is a 5% chance annual losses exceed $X"
- **Expected Annual Loss (EAL)**: Mean of distribution
- **P(Zero Loss Year)**: Probability of no loss events occurring
- **Mean Event Count**: Average number of loss events per year
- **Conditional ALE**: Mean/VaR statistics only for years with at least one event
- **Key Driver Analysis**: Spearman rank correlation identifies which inputs most influence variance (robust to non-linear relationships in the FAIR model)

Use `scripts/fair_simulation.py` to execute simulation and generate visualizations.

## Phase 5: Documentation

Generate comprehensive report using `references/report-template.md`:

1. **Executive Summary** (1 page)
   - Risk statement with key figures
   - Recommendation summary
2. **Scenario Definition**
   - Asset, threat, effect specification
   - Scope boundaries and assumptions
3. **Input Parameters**
   - All estimates with rationale
   - Calibration sources cited
   - Confidence levels noted
4. **Methodology**
   - FAIR taxonomy mapping
   - Distribution choices justified
   - Simulation parameters
5. **Results**
   - Loss exceedance curve
   - VaR and EAL figures
   - Sensitivity analysis (tornado diagram)
6. **Risk Treatment Options**
   - Control improvements with cost-benefit
   - Acceptance rationale if applicable
7. **Appendices**
   - Comparable incidents
   - Data sources
   - Calculation details

Output format: Markdown with embedded charts, convertible to PDF/DOCX.

## Calibration Training Mode

When requested, run calibration exercises before analysis:

1. Present 10 questions with known answers (historical loss events)
2. Have analyst estimate ranges
3. Score calibration (should hit ~80% at 80% confidence)
4. Provide feedback on over/under-confidence patterns

## Banking-Specific Context

### Regulatory Framework References

- OCC Heightened Standards (12 CFR Part 30)
- Federal Reserve SR 11-7 (Model Risk Management)
- FFIEC IT Examination Handbook
- NIST Cybersecurity Framework (financial sector profile)

### Common Scenario Starters

When analyst needs help scoping, offer these common banking scenarios:

- Ransomware on core banking system
- Business email compromise targeting wire transfers
- Third-party data breach (vendor with customer data)
- Insider fraud in payment operations
- DDoS on digital banking channels
- ATM jackpotting/malware
- SWIFT/payment network compromise

See `references/scenario-library.md` for detailed starter scenarios.
