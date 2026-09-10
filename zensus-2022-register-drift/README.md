# German register drift: Zensus 2022 vs the population register

**Question:** Germany's population register is built from paperwork — you file when you move in, you're supposed to file when you move out. Nobody checks it. In May 2022 the state ran an actual headcount and it disagreed with the register. How large was that disagreement per district, and what predicts it?

400 districts. Negative means the register claimed people who weren't there.

---

## Headline finding

Both of my main hypotheses were falsified. What the data actually shows:

**Register drift in East Germany tracks population decline (r = +0.587). The same relationship is absent in the West (r = −0.002).** Pooled, it reads +0.198 — a real mechanism averaged with a null one.

And a handful of mid-sized Bavarian cities overcount by 4–7pp more than the rural district around them, for reasons this data cannot identify.

---

## Research Questions

### Q1 — How big was the 2022 correction, and what predicts it?

For the Kreise where I've got both a Zensus figure and a register figure, how far off was the register? I'm comparing Zensus population (May 2022) against the last pre-Zensus register count (Dec 2019) — not Dec 2022, since that number already has the correction baked in.

Then comes the harder question: what predicts the size of that gap? Foreign-resident share. Urban vs. rural. East vs. West.

**H1:** My guess is the gaps run bigger where foreign-resident share is higher, and bigger in cities. It tracks — people who move around a lot tend to skip the deregistration step, so registers drift furthest wherever turnover is highest. One thing I can't ignore: 2019 to 2022 covers COVID. Mobility and registration both got scrambled during that stretch. So some of what looks like chronic drift might just be pandemic noise.

> **Outcome: H1 falsified.**
>
> Foreign share does not predict drift (r = +0.089, Spearman +0.157, explains 0.8% of variance) and the sign runs opposite to prediction. Offenbach, the most foreign district in Germany at 42.7%, has a gap of −0.61%.
>
> Density is null (r = +0.011; log density +0.074). The crude *kreisfrei* flag I argued against performed slightly better than the density measure I preferred.
>
> East vs West holds: p = 2.1×10⁻⁴, mean difference +0.89pp, 95% CI [+0.40, +1.39], medians −1.47 vs −0.19. The median difference exceeds the mean difference, so the whole distribution shifts rather than a few outliers dragging an average.
>
> **Unplanned finding.** Population decline predicts drift in the East (r = +0.587, n=75) and not at all in the West (r = −0.002, n=324). The pooled +0.198 was averaging a real effect with a null one. This also answers the confounding worry: East is not merely a label for decline — if it were, decline would predict drift in the West too.
>
> The COVID caveat stands and is unresolved.

### Q2 — Does the correction stick, or does it creep back?

Do the Kreise with the biggest 2022 corrections show more apparent growth in the years right after, 2022 through 2025?

**H2:** I'd bet yes — the most heavily corrected Kreise "grow" fastest afterward, which would point to phantom registrations quietly rebuilding rather than actual people showing up. But there's a plain-vanilla explanation sitting right next to that one: places with high turnover might just genuinely pull in more new residents, full stop. Nothing in this dataset lets me tell those two stories apart. That would take migration data, or another census point down the road.

> **Outcome: H2 falsified.**
>
> | | post (2022–25) | pre (2016–19) |
> |---|---|---|
> | East (n=75) | +0.444 | +0.528 |
> | West (n=324) | −0.047 | +0.035 |
>
> The sign is positive throughout — bigger overcounts grow *slower*, not faster.
>
> More decisively: if the correction caused the growth, the relationship should appear only after 2022. It appears before as well, and more strongly, in a window closing three years before the correction happened. Something that hasn't occurred yet cannot produce an effect. Both variables are downstream of decline instead.
>
> This also settles the artifact concern about `zensus_2022` appearing in both variables — that could only inflate the post-period correlation, which is the weaker one in both regions.
>
> No evidence of phantom registrations rebuilding.

### Q2b — Does the city effect hold outside the extreme tail?

Q1's city finding came from two pairs selected by looking at the outcome. Q2b tests it systematically: each *kreisfreie Stadt* against the Landkreis of the same name — adjacent territory, holding region, labour market and growth constant by construction rather than statistically.

**Prediction, recorded before extraction:** 28–33 of 40 pairs negative, mean difference −2 to −3pp. Sign test chosen as primary in advance, because Trier and Bamberg — the cases that motivated the analysis — would otherwise drive a mean-based verdict.

> **Outcome: prediction wrong.**
>
> City more negative in 14 of 30 pairs. Sign test p = 0.708, median +0.10pp, Wilcoxon p = 0.516. Cities do not systematically overcount relative to their rings.
>
> What exists is a null distribution with a small severe tail: five pairs at −4 to −7pp (Landshut, Trier, Ansbach, Bamberg, Straubing) against 25 scattered around zero. The five-of-five observation in Q1 was tail selection.
>
> Choosing the sign test before seeing the data is what stopped this being written up as a −0.70pp city effect driven entirely by five outliers.

---

## What I predicted

1. Districts with more foreign residents drift more
2. Cities drift more than rural districts
3. East drifts more than West
4. Heavily corrected districts "grow" fast again afterwards, as phantoms rebuild

## What I found

**1 and 2 were wrong.** Foreign share: r = +0.089, and the sign runs backwards. Density: r = +0.011. Offenbach is 42.7% foreign with a gap of −0.61%.

**3 held.** East −1.47 median vs West −0.19, p = 2.1×10⁻⁴.

**4 was wrong.** If the correction caused later growth, the effect should show up only after 2022. It shows up before as well, and more strongly.

**What I didn't predict, and is the real result:** decline predicts drift in the East (r = +0.587) and not at all in the West (r = −0.002). Pooled it reads +0.198 — a real mechanism averaged with a null.

---

## Data

Four Destatis tables, all at district level.

| File | Contents | Vintage used |
|---|---|---|
| `1000A-0000_en.csv` | Zensus population | 15 May 2022 |
| `12411-0015_en.csv` | Register population, five reference dates | 2019-12-31 |
| `12521-0041_en.csv` | Foreign residents by country group | 2019-12-31 |
| `04-kreise.xlsx` | Area and district type | 31.12.2024 |

### Key variables

| Variable | Definition |
|---|---|
| `gap_pct` | `(zensus_2022 − register_2019) / register_2019 × 100`. Negative = register overcounted |
| `foreign_pct` | Foreign residents 2019 as a share of `zensus_2022` |
| `density` | `zensus_2022 / area_km2` |
| `decline_pct` | Register population change 2011 → 2019, % |
| `is_east` | Land codes 11–16. Berlin excluded (n = 399) |
| `is_city` | *Kreisfreie Stadt*, *Stadtkreis*, *Kreis*, *Regionalverband* — 106 districts |

---

## Method: three decisions worth knowing

**The baseline is Dec 2019, not Dec 2022.** The 2022 register figure already contains the correction, so comparing it to the census would compare the census with itself. The source file's own footnote confirms 2011/2016/2019 sit on the old census base: *"From 2011: Results based on the 2011 Census. From 2022: Results based on the 2022 Census."*

**2019 is harmonized onto 2022 boundaries.** Eisenach was a separate district in 2019 and was absorbed into Wartburgkreis in July 2021. Compared raw, Wartburgkreis shows +31.6% drift — the largest number in the dataset, and pure artifact. After harmonization it's unremarkable. Validated by conservation: national total identical (83,166,711), 400 rows, no duplicate codes.

**Predictors use the 2022 denominator, the outcome uses 2019.** Otherwise the same register error appears on both sides of the relationship and manufactures a correlation. The artifact would have pushed *toward* H1 — so the null survives the correction that would have flattered it.

---

## Where I got it wrong

- My headline hypothesis died, with the sign reversed.
- I found five university cities in the extreme tail and thought it was a pattern. Tested across 30 city/rural pairs: 14 of 30, p = 0.708. It was tail selection.
- I argued for density over a crude city flag on good theoretical grounds. Density performed worse.
- An exact string match classed Stuttgart as rural — Baden-Württemberg says *Stadtkreis*, not *Kreisfreie Stadt*. Nine districts affected.
- I deferred the official boundary-change cross-check rather than closing it.
- I let a decision about merging districts drop entirely, and had no defence for my sample size until it was questioned.

One thing that went right: I chose the sign test as primary *before* extracting the pairs. Mean difference was −0.70pp, median +0.10pp. A mean-based verdict would have reported a city effect driven entirely by five outliers.

---

## Still open

Five mid-sized cities overcount 4–7pp more than the district around them while 25 comparable pairs sit at zero. Landshut grew 14.2% and still overcounts 7.5%, so decline can't explain it. No mechanism identified.

Four of the five are Bavarian: Landshut, Ansbach, Bamberg, Straubing, plus Trier.

---

## Limitations

**Boundary check deferred.** Destatis's official *Gebietsänderungen* record for 2020–2022 was not consulted. A district can gain or lose territory without dissolving, leaving no trace in the source file. Materiality threshold: 1,500 people ≈ 0.96% of the median district, against a median absolute gap of 1.18%. Group findings are protected — transfers are zero-sum, so no group pattern can be manufactured. Per-district rankings carry unquantified exposure.

**Saarland is absent from all foreign-share analysis.** Ten districts share immigration authorities and have no separate count (documented in the source footer). This is administrative consolidation, not small-count suppression — so missingness correlates with *Land*, not with size or foreign share. Complete-case at n = 390.

**Q2b tests West German mid-sized cities only.** Every East German city dropped except Potsdam and Leipzig, and all large cities dropped for lack of a same-named ring — Köln, Frankfurt, Stuttgart, Hamburg, the Ruhr. Two of the five tail cases are excluded. The test says nothing about large cities.

**COVID sits inside the 2019–2022 window.** Mobility and registration behaviour were both disrupted, so some apparent chronic drift may be pandemic-specific.

**Correlation is not causation,** and nothing here separates phantom registrations from genuine in-migration. That would need migration data or another census point.

---

## Running it

```bash
pip install -r requirements.txt
python src/run_all.py
```

Or stage by stage:

```bash
python src/pull.py      # profile raw sources, validate the district universe
python src/clean.py     # harmonize boundaries, reshape, filter  → data/interim/
python src/join.py      # build the analytical table            → data/processed/
python src/analyze.py   # correlations, tests, figures          → outputs/
```

Raw data isn't committed — four Destatis files go in `data/raw/`: `1000A-0000_en.csv`, `12411-0015_en.csv`, `12521-0041_en.csv`, `04-kreise.xlsx`.

### Expected outputs

- `data/interim/` — 5 cleaned files
- `data/processed/analytical_table.csv` — 400 rows, 12 columns
- `outputs/figures/` — 3 figures
- `outputs/tables/` — 3 tables, including the dropped-pair list

`data/raw/` is immutable and never written to.

---

## Repository

```
├── src/
│   ├── pull.py         # acquisition and profiling
│   ├── clean.py        # cleaning, harmonization, reshaping
│   ├── crosswalk.py    # boundary crosswalk (2019 → 2022)
│   ├── join.py         # analytical table assembly
│   └── analyze.py      # statistics and figures
├── notebooks/
│   └── narrative.ipynb # presentation layer only
├── docs/
│   └── methodology_notes.md
├── data/{raw,interim,processed}/
└── outputs/{figures,tables}/
```

Full decision record, including options considered and rejected, is in `docs/methodology_notes.md`.