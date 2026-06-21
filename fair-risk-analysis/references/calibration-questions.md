# Calibration Question Bank

Phase 0 warm-up. The goal is **not** to test banking knowledge — it is to train
the analyst to produce honest **90% confidence intervals** (some banks use 80%;
state which you use and keep it consistent). A well-calibrated analyst's true
answers fall inside their stated intervals about 90% of the time. Most people are
badly *over*-confident on the first try (intervals too narrow), which is exactly
the bias that wrecks FAIR estimates.

## How to run it

1. Ask the analyst for a **low** and **high** bound for each question such that
   they are 90% sure the true answer lies between them. They are *not* guessing
   the exact value.
2. Do not reveal answers until all questions are done.
3. Score: count how many true answers fell within the stated intervals.
   - Out of 10 questions, a calibrated analyst gets **~9 inside**.
   - **≤7 inside → over-confident** (the common case): intervals are too narrow.
     Coach them to widen until the bound "feels too wide," then widen a bit more.
   - **10/10 inside with very wide ranges → under-confident**: they can tighten.
4. Use two tricks that improve calibration immediately:
   - **Equivalent bet**: "Would you rather win $1,000 if the answer is inside
     your range, or spin a wheel with a 90% chance to win $1,000?" If the wheel
     feels better, the range is too narrow — widen it.
   - **Absurdity test**: state a bound so extreme it's obviously wrong, then pull
     it in until it stops being absurd.

Mix general-knowledge items (which neutralize domain expertise so the analyst
practices the *skill* of intervals) with a few banking items.

## General-knowledge items (trivia — neutralizes expertise bias)

| # | Question | Answer | Source |
|---|----------|--------|--------|
| 1 | Air distance, New York to Los Angeles (miles) | ~2,450 mi | Great-circle distance |
| 2 | Year Alexander Graham Bell was born | 1847 | Historical record |
| 3 | Length of the Nile river (miles) | ~4,130 mi | Geographic surveys |
| 4 | Wingspan of a Boeing 747-400 (feet) | ~211 ft | Boeing specs |
| 5 | Number of bones in the adult human body | 206 | Standard anatomy |
| 6 | Diameter of the Moon (miles) | ~2,159 mi | NASA |
| 7 | Year the first iPhone was released | 2007 | Apple |
| 8 | Boiling point of water at the top of Mt. Everest (°F) | ~160 °F (~71 °C) | Pressure/altitude tables |

## Banking / risk items (use current figures; treat as approximate)

> These figures drift year to year. Before using them as "the answer," confirm
> against a current source — the point is interval discipline, not the exact
> number. Cite the year you used.

| # | Question | Approx. answer | Source to confirm |
|---|----------|----------------|-------------------|
| 9 | Average total cost of a financial-sector data breach | ~$6M | IBM/Ponemon Cost of a Data Breach (latest) |
| 10 | Mean days to *identify* a breach (all sectors) | ~190–200 days | IBM/Ponemon (latest) |
| 11 | Largest single OCC/FinCEN BSA-AML penalty to date (USD) | Multiple > $1B (e.g., $1.3B+ settlements) | OCC / FinCEN enforcement actions |
| 12 | Typical class-action settlement, per record, for a 1–10M record breach | ~$25–$75 / record | Reported breach settlements |
| 13 | SWIFT Bangladesh Bank heist attempted theft (2016, USD) | ~$951M attempted, ~$81M lost | Public reporting |
| 14 | Number of U.S. commercial banks (FDIC-insured, approx.) | ~4,000–4,500 | FDIC BankFind |

## Important caveats

- **Do not invent "historical answers."** Use the values above (or confirm a
  current source) and tell the analyst when a figure is approximate or dated.
- The banking items double as a benchmark-literacy check, but their purpose is
  still interval calibration, not trivia scoring.
- Re-run a short set periodically — calibration is a trainable skill that decays.

See [`loss-benchmarks.md`](loss-benchmarks.md) for the full benchmark tables used
later in loss-magnitude estimation.
