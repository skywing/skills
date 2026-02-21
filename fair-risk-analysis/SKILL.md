---
name: fair-risk-analysis
description: Interactive FAIR (Factor Analysis of Information Risk) risk scenario analysis for banking and financial services. Guides analysts through probabilistic risk quantification using Monte Carlo simulation, with expert-suggested inputs based on industry benchmarks. Use this skill whenever a user mentions risk analysis, cyber risk, loss quantification, FAIR, operational risk, threat modeling, risk scenarios, or asks to estimate or quantify any banking or financial risk — even if they don't explicitly say "FAIR" or "Monte Carlo". Also trigger for requests like "what's our exposure if X happens", "help me put numbers on this risk", or "I need something for the risk committee".
license: MIT
compatibility: Requires Python 3.8+, numpy, scipy, and matplotlib. Designed for Claude Code.
metadata:
  version: "1.0"
---

# FAIR Risk Scenario Analysis

Guide banking risk analysts through rigorous, probabilistic FAIR risk scenario analysis. Provide expert-suggested inputs based on industry benchmarks while building analyst calibration skills. Produce standalone documentation suitable for risk committee presentation, regulatory examination support, or risk register population.

## Analysis Workflow

The FAIR analysis follows five sequential phases (with an optional calibration warm-up):

0. **Analyst Calibration** *(optional)* → Build confidence in estimates before starting
1. **Scenario Scoping** → Define asset, threat, and effect
2. **Loss Event Frequency (LEF)** → Estimate TEF × Vulnerability
3. **Loss Magnitude (LM)** → Quantify primary and secondary losses
4. **Monte Carlo Simulation** → Run probabilistic analysis
5. **Documentation** → Generate comprehensive report

**Scope note**: Benchmarks and regulatory references are US-focused (OCC, CFPB, FFIEC, Fedwire). International users should substitute applicable frameworks (DORA, PRA, APRA) and scale regulatory fine ranges accordingly.

## Phase 0: Analyst Calibration (Optional)

Offer this before starting the analysis, especially with analysts new to probabilistic estimation. It takes ~10 minutes and meaningfully improves estimate quality.

1. Present 10 questions with known historical answers (loss events, breach costs, frequency data)
2. Have the analyst provide 80% confidence interval estimates (low and high bounds)
3. Score calibration — a well-calibrated analyst should capture the true answer ~80% of the time within their stated 80% intervals
4. Provide feedback on over-confidence patterns (intervals too narrow) or under-confidence (intervals too wide)
5. Use the calibration results to set realistic confidence levels throughout the analysis

## Phase 1: Scenario Scoping

For common banking scenarios, see [`references/scenario-library.md`](references/scenario-library.md) — pre-built templates for ransomware, BEC, insider fraud, DDoS, SWIFT compromise, and more. Use them as starting points or jump straight to scoping a custom scenario.

### Asset Identification

Classify the target asset using the Basel/BCBS-aligned taxonomy below and prompt the analyst for selection:

**Financial Assets** — Systems that directly hold, process, or transfer monetary value:
- Core banking systems (transaction processing, account management, general ledger)
- Payment infrastructure (SWIFT, ACH, Fedwire, card processing, real-time payments)
- Trading platforms and market data systems (execution, pricing, settlement)
- Treasury and liquidity management (cash management, funding, interest rate hedging)
- Loan origination and servicing (mortgage, commercial, consumer credit)

**Physical Assets** — Tangible infrastructure, facilities, and hardware:
- ATM and branch networks (cash dispensers, kiosks, branch equipment)
- Data centers and network infrastructure (servers, firewalls, switches, cabling)
- Physical security systems (vault controls, surveillance, access control)

**Business Services** — Operational processes, applications, and service delivery:
- Digital banking channels (mobile apps, online banking portals)
- Fraud detection and transaction monitoring (real-time scoring, AML monitoring)
- Contact center and CRM (customer service platforms, telephony, IVR)
- Third-party integrations and APIs (vendor connections, open banking, fintech partnerships)
- Cloud infrastructure and hosted services (IaaS/PaaS/SaaS workloads)

**Information Assets** — Data repositories, records, models, and knowledge:
- Customer data repositories (PII, account data, transaction history)
- Risk and compliance data (loss events, model risk, AML/sanctions, issue management)
- Data warehouses and regulatory reporting (data lakes, BI, CCAR/DFAST, Call Reports)
- Identity directories and credentials (Active Directory, authentication tokens, cryptographic keys)

Capture: asset name, asset category, criticality tier (1-5), data volume/sensitivity, transaction throughput if applicable.

### Threat Community

Present banking-relevant threat actors with frequency benchmarks:

| Threat Actor        | Typical TEF Range (annual)             | Primary Motivation      |
| ------------------- | -------------------------------------- | ----------------------- |
| Nation-state        | 5-20 targeted attempts                 | Espionage, disruption   |
| Organized crime     | 50-500 opportunistic, 10-50 targeted   | Financial gain          |
| Hacktivists         | 10-100 depending on profile            | Reputation damage       |
| Malicious insider   | 2-20 depending on controls             | Financial gain, revenge |
| Negligent insider   | 20-200 error events                    | Unintentional           |
| Third-party/vendor  | 5-50 depending on ecosystem            | Varies                  |
| Fraudulent customer | 100-1000+ depending on product mix     | Financial gain          |
| Former employee     | 1-10 concentrated post-separation      | Revenge, financial gain |

Source benchmarks from: FS-ISAC threat briefings, Verizon DBIR financial sector, ORX loss data, CERT Insider Threat Center, FTC consumer fraud data.

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
   - **1** — Little basis; rough order-of-magnitude guess
   - **2** — Some analogies but significant uncertainty
   - **3** — Reasonable benchmarks; moderate uncertainty
   - **4** — Good data or direct experience; low uncertainty
   - **5** — Strong empirical basis; high confidence
3. **Decomposition prompt**: "Would it help to break this into components?"

See [`references/loss-benchmarks.md`](references/loss-benchmarks.md) for detailed industry data.

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

### Running the Simulation

Build a `params.json` from the analyst's estimates and run:

```bash
python scripts/fair_simulation.py --config params.json --iterations 10000 --seed 42 --output-dir ./results
```

The config format uses PERT params (`minimum`, `mode`, `maximum`) or lognormal (`p10`, `p90`) for any loss form. Secondary losses require an additional `probability` field (0–1). See [`references/simulation-config.md`](references/simulation-config.md) for the complete schema, full examples, and output field definitions.

### Presenting Results to Different Audiences

Once simulation outputs are available, tailor the framing:

**Executive / board**: Lead with EAL and VaR in dollar terms. "There is a 5% chance we lose more than $X in a single year." Connect to risk appetite and capital buffers. Skip distribution details.

**Risk committee**: Present the loss exceedance curve and the top 2–3 sensitivity drivers from the tornado diagram. Explain what controls would move the numbers and by how much.

**Regulator / audit**: Emphasize methodology rigor — FAIR taxonomy, FFIEC CAT maturity levels, industry benchmark sources, simulation parameters, and reproducibility (seed value). Highlight assumptions and confidence levels explicitly.

**Analyst / model validation**: Walk through the full sensitivity analysis and note which inputs dominate variance. Discuss distribution choice rationale (PERT vs. lognormal) and correlation assumptions.

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

## Banking-Specific Context

### Regulatory Framework References

- OCC Heightened Standards (12 CFR Part 30)
- Federal Reserve SR 11-7 (Model Risk Management)
- FFIEC IT Examination Handbook
- NIST Cybersecurity Framework (financial sector profile)

### Common Scenario Starters

Common banking scenarios covered in [`references/scenario-library.md`](references/scenario-library.md):

- Ransomware on core banking system
- Business email compromise targeting wire transfers
- Third-party data breach (vendor with customer data)
- Insider fraud in payment operations
- DDoS on digital banking channels
- ATM jackpotting/malware
- SWIFT/payment network compromise
