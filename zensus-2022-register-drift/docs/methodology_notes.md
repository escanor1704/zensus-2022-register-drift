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
**Q2a** — do corrected districts "grow" fast again, suggesting phantoms rebuild?
**Q2b** — does the city effect from Q1 hold beyond the extreme tail?

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

**Q2a's artifact, bounded then made moot.** Post-correction growth divides by `register_2022`, which was set equal to the census — the same quantity in `gap_pct`'s numerator. A census undercount would shrink the denominator and inflate growth, producing exactly the predicted correlation. Bounded by algebra: the numerator is a difference of two figures on the same base, so census error cancels out of it and survives only in the denominator, giving an artifact slope of roughly `growth/100`. Second-order, unlike Q1's case. The placebo then made it moot — the artifact can only touch `growth_post`, which is the weaker correlation in both regions.

**Göttingen 2011 gap.** Long format has 1,999 rows, not 2,000. Göttingen (03159) did not exist in 2011 — created 2016-11-01. Real gap, not a reshape artifact. Not backfilled: it needs a second crosswalk entry for a year the analysis does not use.

**Berlin excluded** from East/West (n = 399). The Land-code rule would call it East; most of its population is former West Berlin. Every option misrepresents it.

**Sign test chosen as primary for Q2b, before extraction.** Trier and Bamberg motivated the analysis and would have driven any mean-based verdict. The prediction (28–33 of 40 negative, mean −2 to −3pp) was recorded in writing first.

### Rejected

**Merging the Kassel and Cottbus pairs** — would recover 4 districts of foreign-share coverage, at the cost of changing the grain permanently and leaving two rows carrying double population weight. Saarland stays unrecoverable either way, so the character of the missingness does not change. *This decision was not originally made; it was dropped and only defended when the row count was questioned.*

**Density over the kreisfrei flag** — argued on the grounds that turnover is continuous and legal status is frozen. Density (r = +0.011) then performed worse than the flag it replaced. Both null, so it did not matter — but the better argument produced the worse measure.

**Student enrolment data** — published by university location, not `kreis_code`, needing a hand-built crosswalk that breaks on multi-campus institutions. The paired comparison holds region, labour market and growth constant by construction, where a students-per-capita regression would still be confounded with density and city status. Weaker evidence at higher cost.

---

## The recurring lesson: pooled numbers average unlike populations

Three times, a single number concealed the finding.

| Where | Pooled | What it hid |
|---|---|---|
| Q1, decline vs drift | r = +0.198 | East +0.587, West −0.002 |
| Q2a, gap vs post-growth | r = +0.154 | East +0.444, West −0.047 |
| Q2b, city vs ring | mean −0.70pp | median +0.10pp, five outliers at −4 to −7 |

The first two are the same failure: a real effect in one region averaged with a null in another, producing a weak-looking coefficient that misrepresents both. The third is a variant — a mean dragged by a small severe tail while the bulk sits at zero.

In every case the correct number only appeared after splitting, or after choosing a rank-based statistic. Reported pooled, all three would have described a weak universal effect where none exists.

**The habit:** before reporting a coefficient, ask what population it describes and whether that population is one thing. If a plausible grouping variable exists, split on it first. And where a few extreme cases motivated the analysis, pick a rank-based test before seeing the result — otherwise those same cases will hand back the answer that prompted the question.

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
| Stale DataFrame snapshot | `KeyError` on a column added after the subset | Analysis run on a frame missing its newest variables |

Two of these generalise. **Enumerate a categorical before matching it** — `value_counts()` was run on `country_group` and skipped on district type, which cost Stuttgart. **Structure and reconciliation checks fail in different places** — a Land row with a padded 5-digit code looks exactly like a district; only the area total catches it.

---

## Limitations

**Boundary check deferred.** Destatis's *Gebietsänderungen* record for 2020–2022 was located but not consulted. A district can gain or lose territory without dissolving, leaving no trace in the source. At 1,500 people (0.96% of the median district) contamination could exceed the median absolute gap of 1.18%. Group-level findings are protected — transfers are zero-sum — but per-district rankings carry unquantified exposure.

**Ten districts lack foreign-resident data.** Seven share an immigration authority with a neighbour (five Saarland under Saarlouis, Spree-Neiße under Cottbus, Kassel Landkreis under Kassel Stadt); the three receivers were excluded as inflated. Administrative consolidation, not small-count suppression — so missingness tracks *Land*, not size or foreign share. Complete-case at n = 390, identities pinned as a set.

**Q2b covers West German mid-sized cities only.** 30 pairs survived name-matching; 80 dropped, list retained. Every East German city fell out except Potsdam and Leipzig. All large cities dropped — Köln, Frankfurt, Stuttgart, Hamburg, the Ruhr — along with Kempten, Heidelberg, Freiburg, Münster and Jena, so two of Q1's five tail cases are excluded by construction. The test says nothing about large cities.

One doubtful pair was kept: Potsdam-Mittelmark borders Potsdam rather than enclosing it. Its difference (+0.46pp) sits near zero and cannot swing the result.

**The Q1 tail list was threshold-dependent.** Ansbach appears in Q2b at −5.86 against its ring but was absent from Q1's tail, because its gap of −5.26 sits just above the −5.5 cutoff I chose. A sixth case with the same signature, excluded by my own selection rule.

**Also:** predictors mix a 2019 numerator with a 2022 denominator; COVID sits inside the window; nothing here separates phantom registrations from genuine in-migration.

---

## What I got wrong

My headline hypothesis was falsified and the sign ran backwards.

My pre-registered Q2b prediction was wrong — I expected 28–33 of 40 pairs negative and got 14 of 30, p = 0.708. Cities do not systematically overcount relative to their rings, and the five-of-five observation I built on was tail selection.

My Q1 tail list was threshold-dependent in a way I did not acknowledge at the time; a −5.5 cutoff excluded Ansbach, which has the same signature as the cases I did report.

My density argument was theoretically better and empirically worse than the flag I rejected. I let the merge decision drop and had no defence for n = 400 until asked. I skipped a check I had already learned to run, which cost me Stuttgart. I deferred the boundary check rather than closing it.

---