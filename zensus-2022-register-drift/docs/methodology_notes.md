# Methodology Notes

**zensus-2022-register-drift** · one row = one Kreis, 2022 boundaries, n = 400

---

## Findings (Q1)

| Hypothesis | Verdict |
|---|---|
| Foreign share drives drift | **Falsified.** r = +0.089, R² = 0.008, n = 390 — and the sign runs backwards. Offenbach is 42.7% foreign with a gap of −0.61% |
| Cities drift more | **Falsified.** Density r = +0.011, log density +0.074 |
| East drifts more | **Held.** Mann-Whitney p = 2.1×10⁻⁴, mean diff +0.894pp, CI [+0.395, +1.394] |

The East/West median difference (1.28pp) exceeds the mean difference (0.89pp), so the whole distribution shifts — not a few outliers pulling an average.

### The pooled correlation was hiding two worlds

Population decline 2011–2019 against drift:
pooled r = +0.198 n = 399
within East r = +0.587 n = 75
within West r = −0.002 n = 323


East is not merely a label for decline — if it were, decline would predict drift in the West too. And decline is not a general mechanism — it works in one region only.

### The Western city effect

Seven Western districts drift below −5.5%. Two are shrinking Landkreise (Goslar, Holzminden). Five are **growing** cities that all host universities: Köln, Trier, Landshut, Bamberg, Kempten.

Landshut settles it: **+14.2% population growth, −7.5% drift.** No decline mechanism produces that sign.

Each city against its own surrounding Landkreis — same region, same labour market, same growth:

| | gap | growth 11–19 |
|---|---|---|
| Trier, Stadt | −7.89 | +4.93 |
| Trier-Saarburg | −1.07 | +4.85 |
| Bamberg, Stadt | −5.96 | +9.42 |
| Bamberg, Landkreis | −0.21 | +2.38 |

The city overcounts 6–8× more than the ring around it. City-specific, not regional.

**The effect is demonstrated. The mechanism is not identified.** Two different claims.

---

## What is being measured

Germany's population register runs on paperwork. You file when you move in and you are supposed to file when you move out. Nobody checks. People leave and stay on the list.

May 2022, the state ran an actual headcount. It disagreed with the register.

gap_pct = (zensus_2022 − register_2019) / register_2019 × 100


Negative means the register claimed people who were not there.

**Q1** — how big was the correction, and what predicts it?
**Q2** — do corrected districts "grow" fast again, suggesting phantoms rebuild?

**Baseline is 2019, not 2022**, because the 2022 register figure already contains the correction. The source file confirms it: *"From 2011: Results based on the 2011 Census. From 2022: Results based on the 2022 Census."* That line is what the whole design rests on — and it marks a series break at 2019→2022.

---

## Sources

| File | One row = | Vintage |
|---|---|---|
| `1000A-0000_en.csv` | district | Zensus, 15 May 2022 |
| `12411-0015_en.csv` | district × 5 years, wide | 2019-12-31 |
| `12521-0041_en.csv` | district × date × country group | 2019-12-31 |
| `04-kreise.xlsx` | district | 31.12.2024 |

The area file post-dates the window, so its code set was asserted equal to the 400. It matched.

---

## Decisions

**Eisenach crosswalk.** Eisenach (16056) merged into Wartburgkreis (16063) on 2021-07-01 — inside the window. Raw, Wartburgkreis shows +31.6% drift, the largest number in the dataset and entirely artificial. Relabelled and summed: 118,974 + 42,250 = 161,224, giving −2.9%. Verified by conservation — national total identical before and after (83,166,711), 400 rows, no duplicate codes.

**Foreigners filtered, not summed.** The `country_group` categories are nested: Europe sits inside Total, EU-27 and EU-28 are two vintages of the same concept. Summing inflates unpredictably. Filtered to `Total`.

**Shared denominator removed.** `gap_pct`, `foreign_pct` and `density` all originally divided by `register_2019`. An overstated register would push the outcome negative and the predictor smaller — manufacturing a correlation from nothing. Predictors now use `zensus_2022`. Note the artifact would have pushed *toward* H1, so the null survives the correction that would have flattered it.

**Göttingen 2011 gap.** Long format has 1,999 rows, not 2,000. Göttingen (03159) did not exist in 2011 — created 2016-11-01. Real gap, not a reshape artifact. Not backfilled: it needs a second crosswalk entry for a year Q1 does not use.

**Berlin excluded** from East/West (n = 399). The Land-code rule would call it East; most of its population is former West Berlin. Every option misrepresents it.

### Rejected

**Merging the Kassel and Cottbus pairs** — would recover 4 districts of foreign-share coverage, at the cost of changing the grain permanently and leaving two rows carrying double population weight. Saarland stays unrecoverable either way, so the character of the missingness does not change. *This decision was not originally made; it was dropped and only defended when the row count was questioned.*

**Density over the kreisfrei flag** — argued on the grounds that turnover is continuous and legal status is frozen. Density (r = +0.011) then performed worse than the flag it replaced. Both null, so it did not matter — but the better argument produced the worse measure.

**Student enrolment data** — published by university location, not `kreis_code`, needing a hand-built crosswalk that breaks on multi-campus institutions. The city/Landkreis pairs already hold region and growth constant, so a students-per-capita regression would be weaker evidence.

---

## Defects found

| Defect | Caught by | Would have caused |
|---|---|---|
| Footers parsed as data | `key_lengths` showing codes far over 5 chars | Copyright text as districts |
| Wrong key on foreigners | 97,313 false duplicates | An alarm you learn to ignore |
| `isnull()` missing `-` markers | 0.00% null vs 15.93% non-numeric | 76 rows of `-` as valid data |
| Dates compared as strings | `b.31.07.2008` sorts after any digit | Right answer, wrong logic |
| Hanau has no until-date | NaN silently skipped | A row the method cannot evaluate, invisible |
| `is_city` exact-matched one label | Stuttgart was not flagged a city | 9 BW Stadtkreise classed rural |
| Assumed a national area constant | Used the file's own total | The planned band would have failed |

Two of these generalise. **Enumerate a categorical before matching it** — `value_counts()` was run on `country_group` and skipped on district type, which cost Stuttgart. **Structure and reconciliation checks fail in different places** — a Land row with a padded 5-digit code looks exactly like a district; only the area total catches it.

---

## Limitations

**Boundary check deferred.** Destatis's *Gebietsänderungen* record for 2020–2022 was located but not consulted. A district can gain or lose territory without dissolving, leaving no trace in the source. At 1,500 people (0.96% of the median district) contamination could exceed the median absolute gap of 1.18%. Group-level findings are protected — transfers are zero-sum — but per-district rankings carry unquantified exposure.

**Ten districts lack foreign-resident data.** Seven share an immigration authority with a neighbour (five Saarland under Saarlouis, Spree-Neiße under Cottbus, Kassel Landkreis under Kassel Stadt); the three receivers were excluded as inflated. Administrative consolidation, not small-count suppression — so missingness tracks *Land*, not size or foreign share. Complete-case at n = 390, identities pinned as a set.

**The university cities are a selected tail.** Found by looking at the extreme end of the outcome. The base rate across Germany's other university cities was never measured. Five of five is a pattern, not a test.

**Also:** predictors mix a 2019 numerator with a 2022 denominator; COVID sits inside the window; nothing here separates phantom registrations from genuine in-migration.

---

## What I got wrong

My headline hypothesis was falsified and the sign ran backwards. My density argument was theoretically better and empirically worse than the flag I rejected. I let the merge decision drop and had no defence for n = 400 until asked. I skipped a check I had already learned to run, which cost me Stuttgart. I deferred the boundary check rather than closing it.

---

## Reproduction
python src/pull.py # profile sources, validate district universe
python src/clean.py # harmonize boundaries, reshape, filter
python src/join.py # build analytical table
python src/analyze.py # tests and figures