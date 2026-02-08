# FAIR Risk Analysis Report Template

Use this template structure when generating the final analysis documentation.

---

# [Scenario Name] - FAIR Risk Analysis

**Prepared for:** [Institution Name]  
**Analysis Date:** [Date]  
**Analyst:** [Name]  
**Version:** [1.0]

---

## Executive Summary

### Risk Statement
[One paragraph summarizing the risk scenario, key quantification results, and recommendation]

### Key Figures
| Metric | Value |
|--------|-------|
| Expected Annual Loss (EAL) | $[X.X]M |
| 95th Percentile (VaR) | $[X.X]M |
| Loss Event Frequency | [X.X] events/year |
| Primary Loss Driver | [Component] |

### Recommendation Summary
[2-3 sentences on recommended risk treatment approach]

---

## 1. Scenario Definition

### 1.1 Asset at Risk
- **Asset Name:** [Name]
- **Asset Category:** [Category from taxonomy]
- **Criticality Tier:** [1-5]
- **Key Characteristics:** [Data volume, transaction throughput, user base]

### 1.2 Threat Profile
- **Threat Community:** [Actor type]
- **Threat Motivation:** [Financial, espionage, disruption, etc.]
- **Threat Capability:** [Sophistication level]
- **Historical Context:** [Relevant threat intelligence]

### 1.3 Threat Scenario
- **Action Type:** [Malicious / Error / Failure]
- **Effect:** [Confidentiality / Integrity / Availability]
- **Attack Vector:** [Specific method]
- **Scenario Narrative:** [Brief description of how the scenario unfolds]

### 1.4 Scope Boundaries
- **In Scope:** [What is included]
- **Out of Scope:** [What is excluded]
- **Assumptions:** [Key assumptions made]

---

## 2. Loss Event Frequency Analysis

### 2.1 Threat Event Frequency (TEF)
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Minimum | [X] | [Basis for estimate] |
| Most Likely | [X] | [Basis for estimate] |
| Maximum | [X] | [Basis for estimate] |
| Distribution | PERT | |

**Calibration Sources:**
- [Source 1 and how it informed estimate]
- [Source 2 and how it informed estimate]

**Confidence Level:** [1-5] - [Rationale for confidence]

### 2.2 Vulnerability Assessment

#### Control Environment Summary
| FFIEC CAT Domain | Maturity Level | Key Controls |
|------------------|----------------|--------------|
| Cyber Risk Management | [Level] | [Key controls] |
| Threat Intelligence | [Level] | [Key controls] |
| Cybersecurity Controls | [Level] | [Key controls] |
| External Dependencies | [Level] | [Key controls] |
| Incident Management | [Level] | [Key controls] |

#### Vulnerability Estimate
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Minimum | [X]% | [Basis] |
| Most Likely | [X]% | [Basis] |
| Maximum | [X]% | [Basis] |
| Distribution | PERT | |

**Confidence Level:** [1-5] - [Rationale]

### 2.3 Loss Event Frequency Result
LEF = TEF × Vulnerability

| Statistic | Value |
|-----------|-------|
| Mean LEF | [X.X] events/year |
| Median LEF | [X.X] events/year |
| 10th Percentile | [X.X] events/year |
| 90th Percentile | [X.X] events/year |

---

## 3. Loss Magnitude Analysis

### 3.1 Primary Loss Forms

#### Productivity Loss
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Minimum | $[X] | [Basis] |
| Most Likely | $[X] | [Basis] |
| Maximum | $[X] | [Basis] |

**Calculation Basis:** [Staff affected × hours × rate, or other method]

#### Response Costs
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Minimum | $[X] | [Basis] |
| Most Likely | $[X] | [Basis] |
| Maximum | $[X] | [Basis] |

**Components:** [IR team, forensics, legal, communications, etc.]

#### Replacement/Restoration
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Minimum | $[X] | [Basis] |
| Most Likely | $[X] | [Basis] |
| Maximum | $[X] | [Basis] |

### 3.2 Secondary Loss Forms

#### Probability of Secondary Loss
| Loss Form | Probability | Rationale |
|-----------|-------------|-----------|
| Fines/Judgments | [X]% | [Basis] |
| Competitive Advantage | [X]% | [Basis] |
| Reputation | [X]% | [Basis] |

#### Fines and Judgments (if P > 0)
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Minimum | $[X] | [Regulatory benchmark] |
| Most Likely | $[X] | [Regulatory benchmark] |
| Maximum | $[X] | [Regulatory benchmark] |

**Applicable Regulations:** [OCC, CFPB, State, GDPR, etc.]

#### Competitive Advantage Loss (if P > 0)
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Minimum | $[X] | [Basis] |
| Most Likely | $[X] | [Basis] |
| Maximum | $[X] | [Basis] |

#### Reputation Damage (if P > 0)
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Minimum | $[X] | [Basis] |
| Most Likely | $[X] | [Basis] |
| Maximum | $[X] | [Basis] |

**Components:** [Customer attrition, acquisition costs, brand remediation]

### 3.3 Total Loss Magnitude
| Statistic | Value |
|-----------|-------|
| Mean LM | $[X.X]M |
| Median LM | $[X.X]M |
| 10th Percentile | $[X.X]M |
| 90th Percentile | $[X.X]M |

---

## 4. Risk Quantification Results

### 4.1 Simulation Parameters
- **Iterations:** 10,000
- **Event Modeling:** Compound Poisson process (event counts drawn from Poisson distribution)
- **LEF Distribution:** PERT (min, mode, max)
- **LM Distribution:** PERT (min, mode, max) or Lognormal (p10, p90)
- **Loss Correlation:** [0.0–1.0, shared severity factor]
- **Random Seed:** [For reproducibility]

### 4.2 Annual Loss Exposure Distribution

| Percentile | Annual Loss |
|------------|-------------|
| 10th | $[X]M |
| 25th | $[X]M |
| 50th (Median) | $[X]M |
| 75th | $[X]M |
| 90th | $[X]M |
| 95th (VaR) | $[X]M |
| 99th | $[X]M |

**Expected Annual Loss (Mean):** $[X.X]M
**P(Zero Loss Year):** [X.X]%
**Mean Event Count:** [X.X] events/year
**Conditional Mean (given ≥1 event):** $[X.X]M

### 4.3 Loss Exceedance Curve

[Insert Loss Exceedance Curve visualization]

**Interpretation:** There is a [X]% probability that annual losses will exceed $[Y]M.

### 4.4 Sensitivity Analysis

[Insert Tornado Diagram visualization]

**Key Drivers (by Rank Correlation — Spearman):**
1. [Input 1] - [X.XX] rank correlation
2. [Input 2] - [X.XX] rank correlation
3. [Input 3] - [X.XX] rank correlation

---

## 5. Risk Treatment Options

### 5.1 Option 1: [Control Enhancement]
- **Description:** [What would be implemented]
- **Estimated Cost:** $[X] (one-time) + $[X]/year (ongoing)
- **Expected Risk Reduction:** [X]% reduction in [vulnerability/TEF/LM]
- **Revised EAL:** $[X]M
- **ROI:** [Net present value or payback calculation]

### 5.2 Option 2: [Risk Transfer]
- **Description:** [Insurance or contractual transfer]
- **Estimated Cost:** $[X]/year premium
- **Coverage:** $[X]M limit, $[X] deductible
- **Residual Risk:** $[X]M EAL

### 5.3 Option 3: [Risk Acceptance]
- **Rationale:** [Why acceptance may be appropriate]
- **Conditions:** [Monitoring, triggers for re-evaluation]
- **Accepted Risk Level:** $[X]M EAL

### 5.4 Recommendation
[Recommended treatment option with rationale]

---

## 6. Appendices

### A. Comparable Incidents
| Institution | Date | Scenario | Reported Loss |
|-------------|------|----------|---------------|
| [Name] | [Date] | [Brief description] | $[X]M |
| [Name] | [Date] | [Brief description] | $[X]M |

### B. Data Sources
- [Source 1]: [How used]
- [Source 2]: [How used]

### C. Methodology Notes
- FAIR Taxonomy Version: [Version]
- Simulation Tool: [Tool used]
- Key Methodology Choices: [Any deviations from standard FAIR]

### D. Glossary
- **EAL**: Expected Annual Loss
- **LEF**: Loss Event Frequency
- **LM**: Loss Magnitude
- **TEF**: Threat Event Frequency
- **VaR**: Value at Risk

---

**Document Control**
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | [Date] | [Name] | Initial release |
