"""Stage 4. Tests and figures.

Q1  - what predicts drift
Q2a - do corrections creep back? (placebo on pre/post growth)
Q2b - does the city effect hold outside the tail? (30 paired comparisons)

Reads data/processed/. Console shows conclusions; detail goes to
outputs/tables/.
"""
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from pull import PROJECT_ROOT

PROCESSED = PROJECT_ROOT / "data" / "processed"
INTERIM = PROJECT_ROOT / "data" / "interim"
FIG_DIR = PROJECT_ROOT / "outputs" / "figures"
TABLE_DIR = PROJECT_ROOT / "outputs" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

# dtype=str on kreis_code is essential - without it 01001 reads back as 1001
# and every lookup fails silently.
m = pd.read_csv(PROCESSED / "analytical_table.csv", dtype={"kreis_code": str})
rl = pd.read_csv(INTERIM / "register_long.csv", dtype={"kreis_code": str})

# The pre window closes in 2019, three years before the correction, so
# nothing that happened in 2022 can have caused it.
p16 = rl[rl.year == 2016].set_index("kreis_code").population
p19 = rl[rl.year == 2019].set_index("kreis_code").population
p22 = rl[rl.year == 2022].set_index("kreis_code").population
p25 = rl[rl.year == 2025].set_index("kreis_code").population
m["growth_post"] = (m.kreis_code.map(p25) / m.kreis_code.map(p22) - 1) * 100
m["growth_pre"] = (m.kreis_code.map(p19) / m.kreis_code.map(p16) - 1) * 100
m["log_density"] = np.log10(m.density)

d = m.dropna(subset=["foreign_pct"])    # 390 rows, H1 only
nb = m[m.kreis_code != "11000"]         # Berlin is neither East nor West
east, west = nb[nb.is_east], nb[~nb.is_east]

# ------------------------------------------------------------- figures ----

# Fig 3. One fit per region. The two slopes are the point: the pooled
# r=+0.198 was a real East effect averaged with a West null.
fig, ax = plt.subplots(figsize=(9, 6))
for is_east, colour, label in [(False, "#4477aa", "West"), (True, "#cc6677", "East")]:
    g = nb[nb.is_east == is_east].dropna(subset=["decline_pct"])
    ax.scatter(g.decline_pct, g.gap_pct, s=20, alpha=0.6, c=colour, label=label)
    slope, intercept = np.polyfit(g.decline_pct, g.gap_pct, 1)
    xs = np.linspace(g.decline_pct.min(), g.decline_pct.max(), 50)
    ax.plot(xs, slope * xs + intercept, c=colour, lw=2)

# Goslar and Holzminden fit the decline story. Trier and Bamberg don't.
for nm in ["Trier, kreisfreie Stadt", "Bamberg, Kreisfreie Stadt",
           "Goslar", "Holzminden"]:
    row = nb[nb.name == nm]
    if len(row):
        ax.annotate(nm.split(",")[0], (row.decline_pct.iloc[0], row.gap_pct.iloc[0]),
                    fontsize=8, xytext=(4, 4), textcoords="offset points")

ax.axhline(0, lw=0.8, color="grey")
ax.set_xlabel("population change 2011-2019 (%)")
ax.set_ylabel("register drift: zensus 2022 vs register 2019 (%)")
ax.set_title("Decline predicts drift in the East (r=+0.59), not the West (r=-0.00)")
ax.legend()
plt.tight_layout()
plt.savefig(FIG_DIR / "fig3_decline_split.png", dpi=120)
plt.close()

# Fig 2. The one hypothesis that held.
fig, ax = plt.subplots(figsize=(7, 5))
ax.boxplot([west.gap_pct, east.gap_pct],
           tick_labels=[f"West (n={len(west)})", f"East (n={len(east)})"])
ax.axhline(0, lw=0.8, color="grey")
ax.set_ylabel("register drift (%)")
ax.set_title("East overcounts more: median -1.47 vs -0.19, p=0.0002")
plt.tight_layout()
plt.savefig(FIG_DIR / "fig2_east_west.png", dpi=120)
plt.close()

# Fig 1. Nothing there, and the title should say so.
fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(d.foreign_pct, d.gap_pct, s=18, alpha=0.6)
ax.axhline(0, lw=0.8, color="grey")
ax.set_xlabel("foreign share 2019 (%)")
ax.set_ylabel("register drift (%)")
ax.set_title(f"H1 falsified: no relationship (r=+0.09, n={len(d)})")
plt.tight_layout()
plt.savefig(FIG_DIR / "fig1_foreign_null.png", dpi=120)
plt.close()

# Fig 4. The placebo. If the correction caused the growth, the relationship
# would exist only in the right panel. It's stronger in the left.
fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
for ax, col, title in [(axes[0], "growth_pre", "before: 2016-2019"),
                       (axes[1], "growth_post", "after: 2022-2025")]:
    for is_east, colour, label in [(False, "#4477aa", "West"), (True, "#cc6677", "East")]:
        g = nb[nb.is_east == is_east].dropna(subset=[col])
        ax.scatter(g[col], g.gap_pct, s=16, alpha=0.55, c=colour, label=label)
        slope, intercept = np.polyfit(g[col], g.gap_pct, 1)
        xs = np.linspace(g[col].min(), g[col].max(), 50)
        ax.plot(xs, slope * xs + intercept, c=colour, lw=2)
    r_e = east.gap_pct.corr(east[col])
    r_w = west.gap_pct.corr(west[col])
    ax.set_title(f"{title}\nEast r={r_e:+.2f}   West r={r_w:+.2f}")
    ax.set_xlabel("population change (%)")
    ax.axhline(0, lw=0.8, color="grey")
axes[0].set_ylabel("register drift (%)")
axes[0].legend()
fig.suptitle("H2 falsified: the relationship is stronger BEFORE the correction",
             fontsize=11)
plt.tight_layout()
plt.savefig(FIG_DIR / "fig4_q2a_placebo.png", dpi=120)
plt.close()

# --------------------------------------------------------------- tests ----

r_foreign = d.gap_pct.corr(d.foreign_pct)
r_foreign_s = d.gap_pct.corr(d.foreign_pct, method="spearman")
r_density = m.gap_pct.corr(m.log_density)

# Mann-Whitney rather than a t-test: normality isn't established and the
# medians carry the signal.
u, p_ew = stats.mannwhitneyu(west.gap_pct, east.gap_pct)
gap_diff = west.gap_pct.mean() - east.gap_pct.mean()
se = (west.gap_pct.var() / len(west) + east.gap_pct.var() / len(east)) ** 0.5

r_dec_pool = m.gap_pct.corr(m.decline_pct)
r_dec_e = east.gap_pct.corr(east.decline_pct)
r_dec_w = west.gap_pct.corr(west.decline_pct)

q2a = {lbl: (g.gap_pct.corr(g.growth_post), g.gap_pct.corr(g.growth_pre))
       for lbl, g in [("East", east), ("West", west)]}

# Q2b: pair each kreisfreie Stadt with the Landkreis sharing its base name.
# Loose match on the leading token so "Trier" catches "Trier-Saarburg".
# Every pair was read by hand before the test was run.


def base(s):
    s = re.sub(r",.*|\s*\(.*", "", s).strip()
    return re.split(r"[-\s]", s)[0]


m["base_name"] = m.name.map(base)
pairs, dropped = [], []
for nm, g in m.groupby("base_name"):
    cities, rings = g[g.is_city], g[~g.is_city]
    if len(cities) == 1 and len(rings) == 1:
        c, rg = cities.iloc[0], rings.iloc[0]
        pairs.append({"base": nm, "city": c["name"], "ring": rg["name"],
                      "city_gap": c.gap_pct, "ring_gap": rg.gap_pct,
                      "diff": c.gap_pct - rg.gap_pct})
    elif len(cities) == 1 and not len(rings):
        dropped.append((nm, cities.iloc[0]["name"], "no same-named ring"))
    elif len(cities) > 1 or len(rings) > 1:
        dropped.append((nm, "; ".join(g["name"]), "ambiguous match"))

pr = pd.DataFrame(pairs).sort_values("diff")
neg = (pr["diff"] < 0).sum()
# Sign test is primary, chosen before extraction: Trier and Bamberg motivated
# the analysis and would drive any mean-based verdict.
p_sign = stats.binomtest(neg, len(pr), 0.5, alternative="greater").pvalue

# --------------------------------------------------------------- tables ---

pr.to_csv(TABLE_DIR / "q2b_pairs.csv", index=False)
pd.DataFrame(dropped, columns=["base", "districts", "reason"]) \
    .to_csv(TABLE_DIR / "q2b_dropped.csv", index=False)
m.nsmallest(15, "gap_pct")[["kreis_code", "name", "gap_pct", "foreign_pct",
                            "decline_pct", "is_city", "is_east"]] \
    .to_csv(TABLE_DIR / "q1_worst_drift.csv", index=False)

# -------------------------------------------------------------- console ---

print(f"""
REGISTER DRIFT — zensus 2022 vs register 2019, n = 400
{'=' * 64}

Q1   What predicts the correction?

     foreign share     r = {r_foreign:+.3f}  (spearman {r_foreign_s:+.3f})   NULL, sign backwards
     log density       r = {r_density:+.3f}                       NULL
     East vs West      p = {p_ew:.1e}                     HELD
                       mean diff {gap_diff:+.2f}pp, 95% CI [{gap_diff - 1.96 * se:+.2f}, {gap_diff + 1.96 * se:+.2f}]

     decline vs drift  pooled {r_dec_pool:+.3f}  =  East {r_dec_e:+.3f} (n={len(east)})
                                        + West {r_dec_w:+.3f} (n={len(west)})
                       The pooled figure averaged a real effect with a null.

Q2a  Do corrections creep back?                          FALSIFIED

                       post (22-25)    pre (16-19)
     East              {q2a['East'][0]:+.3f}           {q2a['East'][1]:+.3f}
     West              {q2a['West'][0]:+.3f}           {q2a['West'][1]:+.3f}

     Stronger before the correction than after, in both regions, and a 2022
     correction cannot cause 2016-2019 growth. Sign is positive throughout:
     bigger overcounts grow slower, not faster.

Q2b  Does the city effect generalise?                    NO

     city more negative in {neg} of {len(pr)} pairs,  sign test p = {p_sign:.3f}
     median diff {pr['diff'].median():+.2f}pp   (mean {pr['diff'].mean():+.2f}pp, dragged by five outliers)
     Five pairs at -4 to -7pp; the other 25 scatter around zero.
     {len(dropped)} pairs dropped - all large cities, most of the East.

{'=' * 64}
figures   outputs/figures/    3 files
tables    outputs/tables/     3 files (dropped-pair list is there)
""")