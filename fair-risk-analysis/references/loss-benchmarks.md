# Banking Industry Loss Benchmarks

Reference data for calibrating FAIR loss magnitude estimates. Sources include Ponemon Institute, IBM Cost of a Breach, ORX operational loss data, and regulatory enforcement databases.

## Breach Cost Benchmarks (Financial Services)

### Overall Breach Costs
| Metric | Value | Source |
|--------|-------|--------|
| Average total cost | $5.9M | IBM/Ponemon 2024 |
| Cost per record | $181 | IBM/Ponemon 2024 |
| Mean time to identify | 197 days | IBM/Ponemon 2024 |
| Mean time to contain | 69 days | IBM/Ponemon 2024 |

### Cost by Attack Vector
| Vector | Average Cost | Frequency |
|--------|-------------|-----------|
| Compromised credentials | $4.8M | 16% |
| Phishing | $4.9M | 15% |
| Cloud misconfiguration | $4.4M | 11% |
| Business email compromise | $5.0M | 9% |
| Malicious insider | $4.9M | 8% |
| Social engineering | $4.8M | 7% |

### Cost Amplifiers
| Factor | Cost Impact |
|--------|-------------|
| Security AI/automation (reduces) | -$1.8M |
| Extensive cloud migration (increases) | +$0.5M |
| Remote workforce (increases) | +$0.2M |
| Compliance failures (increases) | +$0.3M |
| Third-party involvement (increases) | +$0.4M |

## Regulatory Enforcement Data

### OCC Civil Money Penalties (2019-2024)
| Violation Type | Range | Median |
|----------------|-------|--------|
| BSA/AML deficiencies | $5M - $500M | $30M |
| Unsafe/unsound practices | $1M - $100M | $15M |
| Consumer compliance | $1M - $50M | $8M |
| Cybersecurity failures | $10M - $80M | $25M |

### CFPB Enforcement Actions
| Violation Type | Typical Range |
|----------------|---------------|
| UDAAP violations | $5M - $100M |
| Fair lending | $10M - $200M |
| Mortgage servicing | $5M - $50M |
| Consumer restitution | Often exceeds penalties |

### State AG Actions
| Type | Typical Settlement |
|------|-------------------|
| Multi-state data breach | $10M - $200M |
| Single state action | $1M - $25M |
| Consumer restitution component | 50-200% of penalty |

### Class Action Settlements (Data Breaches)
| Breach Size | Settlement Range | Per Record |
|-------------|-----------------|------------|
| < 1M records | $1M - $10M | $10-50 |
| 1-10M records | $10M - $100M | $25-75 |
| 10-100M records | $50M - $500M | $50-150 |
| > 100M records | $200M - $1B+ | $100-200 |

## Operational Loss Categories

### System Downtime Costs
| System Type | Hourly Cost Range |
|-------------|-------------------|
| Core banking | $100K - $1M |
| Payment processing | $500K - $5M |
| Trading platforms | $1M - $10M |
| Digital channels | $50K - $500K |
| ATM network | $25K - $250K |

### Incident Response Costs
| Component | Range |
|-----------|-------|
| Internal team mobilization | $50K - $200K |
| External IR firm | $200K - $2M |
| Forensics investigation | $100K - $1M |
| Legal counsel | $100K - $500K |
| Crisis communications | $50K - $500K |
| Customer notification | $1 - $5 per customer |
| Credit monitoring (per person/year) | $50 - $150 |

### Fraud Loss Benchmarks
| Fraud Type | Average Loss |
|------------|-------------|
| Wire transfer fraud (BEC) | $125K per incident |
| Account takeover | $12K per account |
| Card fraud | $150 per card |
| Check fraud | $1,500 per incident |
| Internal fraud | $150K per incident |

## Reputation and Market Impact

### Stock Price Impact (Material Breaches)
| Timeframe | Average Impact |
|-----------|----------------|
| Day of disclosure | -3% to -7% |
| 30 days post | -2% to -5% |
| 90 days post | Often recovers |
| Long-term (material) | -1% to -3% sustained |

### Customer Attrition
| Breach Severity | Elevated Churn |
|-----------------|----------------|
| Minor (no PII) | 0.5% - 1% |
| Moderate (PII exposed) | 2% - 4% |
| Severe (financial data) | 4% - 7% |
| Major (fraud occurred) | 7% - 15% |

### Brand Remediation Costs
| Activity | Range |
|----------|-------|
| PR/communications campaign | $500K - $5M |
| Customer outreach programs | $1M - $10M |
| Enhanced security marketing | $500K - $2M |
| Trust rebuilding initiatives | $1M - $5M |

## Third-Party Risk Benchmarks

### Vendor Breach Impact Multipliers
| Vendor Type | Cost Multiplier |
|-------------|----------------|
| Payment processor | 1.5x - 2.5x |
| Cloud provider | 1.3x - 2.0x |
| Core system vendor | 1.5x - 3.0x |
| Data analytics vendor | 1.2x - 1.8x |

### Supply Chain Incident Costs
| Impact Level | Range |
|--------------|-------|
| Single vendor, contained | $500K - $5M |
| Multiple customers affected | $5M - $50M |
| Widespread ecosystem impact | $50M - $500M+ |

## Usage Notes

When calibrating estimates:
1. Start with benchmark as baseline
2. Adjust for institution size (assets, customers, employees)
3. Adjust for control environment maturity
4. Adjust for regulatory profile (consent orders, enhanced supervision)
5. Consider geographic scope (multi-jurisdictional adds complexity)
6. Factor in any prior incidents (regulators watch repeat offenders)
