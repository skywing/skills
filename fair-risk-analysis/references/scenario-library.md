# Banking Risk Scenario Library

Pre-built scenario templates for common banking cyber and operational risks. Use as starting points, then customize based on institution-specific context.

## Scenario 1: Ransomware on Core Banking System

### Scenario Definition
- **Asset**: Core banking platform (account management, transaction processing)
- **Threat Community**: Organized crime (ransomware-as-a-service operators)
- **Threat Type**: Malicious
- **Effect**: Availability (primary), Integrity (secondary concern)

### Suggested Parameters

**Threat Event Frequency**
- Ransomware targeting financial services: 50-200 attempts/year for mid-size banks
- Targeted campaigns against specific institution: 5-20/year
- Suggested TEF: 10-30 meaningful attempts annually

**Vulnerability**
- With baseline controls: 15-25%
- With mature EDR, segmentation, MFA: 3-8%
- With advanced zero-trust architecture: 1-3%

**Loss Magnitude Ranges**
| Loss Form | Min | Mode | Max |
|-----------|-----|------|-----|
| Productivity (downtime) | $2M | $10M | $50M |
| Response costs | $500K | $2M | $10M |
| Restoration | $1M | $5M | $20M |
| Regulatory (if reportable) | $1M | $10M | $50M |
| Reputation | $500K | $5M | $25M |

### Key Considerations
- Business interruption insurance coverage
- Ransomware payment policy (and legal implications)
- Recovery time objective vs. actual capability
- Regulatory notification requirements (72-hour rules)

---

## Scenario 2: Business Email Compromise (Wire Transfer Fraud)

### Scenario Definition
- **Asset**: Wire transfer operations, treasury management
- **Threat Community**: Organized crime (BEC specialists)
- **Threat Type**: Malicious (social engineering)
- **Effect**: Integrity (fraudulent transaction execution)

### Suggested Parameters

**Threat Event Frequency**
- BEC attempts targeting treasury/finance: 100-500/year
- Targeted spear-phishing at executives: 20-50/year
- Suggested TEF: 50-150 meaningful attempts annually

**Vulnerability**
- Without verification controls: 5-15%
- With callback verification: 1-5%
- With automated controls + training: 0.5-2%

**Loss Magnitude Ranges**
| Loss Form | Min | Mode | Max |
|-----------|-----|------|-----|
| Direct fraud loss | $50K | $250K | $5M |
| Investigation costs | $25K | $100K | $500K |
| Recovery efforts | $10K | $50K | $200K |
| Insurance deductible | $25K | $100K | $500K |

### Key Considerations
- Wire transfer limits and approval workflows
- Callback verification procedures
- Fraud insurance coverage and recovery rates
- Customer notification if customer funds affected

---

## Scenario 3: Third-Party Data Breach (Vendor with Customer Data)

### Scenario Definition
- **Asset**: Customer PII held by third-party vendor
- **Threat Community**: External attacker (via vendor)
- **Threat Type**: Malicious
- **Effect**: Confidentiality

### Suggested Parameters

**Threat Event Frequency**
- Vendor security incidents (reportable): 2-10/year in ecosystem
- Incidents affecting your specific data: 0.5-2/year
- Suggested TEF: 1-3 material vendor incidents annually

**Vulnerability**
- Baseline vendor management: 20-40%
- Mature third-party risk program: 10-20%
- Advanced continuous monitoring: 5-10%

**Loss Magnitude Ranges**
| Loss Form | Min | Mode | Max |
|-----------|-----|------|-----|
| Customer notification | $500K | $2M | $10M |
| Credit monitoring | $1M | $5M | $25M |
| Regulatory fines | $1M | $10M | $100M |
| Class action settlement | $2M | $20M | $200M |
| Reputation/churn | $1M | $10M | $50M |

### Key Considerations
- Contract indemnification clauses
- Insurance coverage (yours and vendor's)
- Data minimization in vendor relationships
- Regulatory expectations (OCC 2013-29)

---

## Scenario 4: Insider Fraud in Payment Operations

### Scenario Definition
- **Asset**: Payment processing systems, customer accounts
- **Threat Community**: Malicious insider (operations staff)
- **Threat Type**: Malicious
- **Effect**: Integrity (unauthorized transactions)

### Suggested Parameters

**Threat Event Frequency**
- Insider fraud attempts: 5-20/year depending on controls
- Successful schemes (before detection): 1-5/year
- Suggested TEF: 3-10 attempted schemes annually

**Vulnerability**
- Baseline segregation of duties: 10-25%
- Enhanced monitoring + rotation: 5-15%
- Continuous monitoring + analytics: 2-8%

**Loss Magnitude Ranges**
| Loss Form | Min | Mode | Max |
|-----------|-----|------|-----|
| Direct fraud loss | $50K | $500K | $5M |
| Investigation | $50K | $200K | $1M |
| Legal/prosecution | $25K | $100K | $500K |
| Control remediation | $100K | $500K | $2M |
| Customer restitution | $25K | $250K | $2M |

### Key Considerations
- Background check and screening programs
- Segregation of duties and access controls
- Transaction monitoring thresholds
- Whistleblower programs

---

## Scenario 5: DDoS Attack on Digital Banking Channels

### Scenario Definition
- **Asset**: Online banking, mobile banking, APIs
- **Threat Community**: Hacktivists, organized crime (extortion), nation-state (disruption)
- **Threat Type**: Malicious
- **Effect**: Availability

### Suggested Parameters

**Threat Event Frequency**
- DDoS attempts on financial services: 50-200/year
- Significant attacks (>1 hour impact): 5-20/year
- Suggested TEF: 10-50 meaningful attacks annually

**Vulnerability**
- Without DDoS protection: 30-60%
- With basic CDN/scrubbing: 10-25%
- With advanced multi-layer protection: 2-8%

**Loss Magnitude Ranges**
| Loss Form | Min | Mode | Max |
|-----------|-----|------|-----|
| Revenue loss (downtime) | $100K | $500K | $5M |
| Mitigation costs | $50K | $200K | $1M |
| Customer compensation | $25K | $100K | $500K |
| Reputation | $100K | $500K | $2M |

### Key Considerations
- SLAs with DDoS mitigation providers
- Failover and redundancy capabilities
- Customer communication during outages
- Regulatory reporting requirements

---

## Scenario 6: SWIFT/Payment Network Compromise

### Scenario Definition
- **Asset**: SWIFT messaging, Fedwire, correspondent banking
- **Threat Community**: Nation-state, sophisticated organized crime
- **Threat Type**: Malicious
- **Effect**: Integrity, Confidentiality

### Suggested Parameters

**Threat Event Frequency**
- Targeted attacks on payment infrastructure: 2-10/year
- Successful reconnaissance: 1-5/year
- Suggested TEF: 2-5 serious attempts annually

**Vulnerability**
- Baseline SWIFT CSP compliance: 5-15%
- Full CSP + enhanced monitoring: 2-8%
- Zero-trust architecture: 1-3%

**Loss Magnitude Ranges**
| Loss Form | Min | Mode | Max |
|-----------|-----|------|-----|
| Fraudulent transfers | $1M | $20M | $200M |
| Investigation/forensics | $500K | $2M | $10M |
| Regulatory response | $5M | $25M | $100M |
| Correspondent relationship impact | $1M | $10M | $50M |
| Reputation | $5M | $25M | $100M |

### Key Considerations
- SWIFT Customer Security Programme (CSP) compliance
- Payment verification and limits
- Correspondent bank relationships
- Recovery and clawback possibilities

---

## Scenario 7: ATM Jackpotting/Malware

### Scenario Definition
- **Asset**: ATM network, cash dispensing systems
- **Threat Community**: Organized crime (ATM fraud specialists)
- **Threat Type**: Malicious
- **Effect**: Integrity (unauthorized dispensing)

### Suggested Parameters

**Threat Event Frequency**
- ATM compromise attempts: 10-50/year for large networks
- Successful jackpotting incidents: 1-5/year
- Suggested TEF: 5-15 attempts annually

**Vulnerability**
- Legacy ATMs, baseline controls: 15-30%
- Updated software, hardened configs: 5-15%
- Advanced encryption, continuous monitoring: 2-8%

**Loss Magnitude Ranges**
| Loss Form | Min | Mode | Max |
|-----------|-----|------|-----|
| Cash loss | $50K | $250K | $2M |
| ATM replacement/repair | $25K | $100K | $500K |
| Investigation | $25K | $100K | $500K |
| Network-wide remediation | $100K | $500K | $5M |

### Key Considerations
- ATM software update cycles
- Physical security and monitoring
- Network segmentation
- Insurance coverage for cash losses

---

## Usage Instructions

1. Select most appropriate scenario template
2. Review and adjust threat community based on institution threat intelligence
3. Calibrate TEF against your specific exposure and threat data
4. Adjust vulnerability based on control environment assessment
5. Scale loss magnitudes for institution size and complexity
6. Add/remove loss forms based on scenario specifics
7. Document all calibration rationale
