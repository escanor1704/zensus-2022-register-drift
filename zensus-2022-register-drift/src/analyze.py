"""Stage 5. Tests the Q1 predictors and writes the three figures.

gap_pct is the outcome (zensus 2022 vs register 2019).
Predictors: foreign_pct, density, is_city, is_east, decline_pct.
"""
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from scipy import stats

from pull import load_file, RAW_FILES
from join import build

z = load_file(RAW_FILES["zensus"])
r = load_file(RAW_FILES["register"])
f = load_file(RAW_FILES["foreigners"])
a = load_file(RAW_FILES["area"])
codes = set(z.loc[z.kreis_code.str.len() == 5, "kreis_code"])
m = build(z, r, f, a, codes)   # all the asserts run in here

d = m.dropna(subset=["foreign_pct"])    # 390 rows, H1 only
nb = m[m.kreis_code != "11000"]         # Berlin is neither East nor West

FIG_DIR = Path(__file__).parent.parent / "outputs" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Fig 3. Separate fit per region. The two slopes are the whole point:
# pooled r=+0.198 was a real East effect averaged with a West null.
fig, ax = plt.subplots(figsize=(9, 6))
for is_east, colour, label in [(False, "#4477aa", "West"), (True, "#cc6677", "East")]:
    g = nb[nb.is_east == is_east].dropna(subset=["decline_pct"])
    ax.scatter(g.decline_pct, g.gap_pct, s=20, alpha=0.6, c=colour, label=label)
    b, a_ = np.polyfit(g.decline_pct, g.gap_pct, 1)
    xs = np.linspace(g.decline_pct.min(), g.decline_pct.max(), 50)
    ax.plot(xs, b * xs + a_, c=colour, lw=2)

# Goslar and Holzminden fit the decline story. Trier and Bamberg don't.
for nm in ["Trier, kreisfreie Stadt", "Bamberg, Kreisfreie Stadt", "Goslar", "Holzminden"]:
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

# Fig 2. The one hypothesis that held. n goes on the labels.
fig, ax = plt.subplots(figsize=(7, 5))
ax.boxplot([nb.loc[~nb.is_east, "gap_pct"], nb.loc[nb.is_east, "gap_pct"]],
           tick_labels=[f"West (n={(~nb.is_east).sum()})", f"East (n={nb.is_east.sum()})"])
ax.axhline(0, lw=0.8, color="grey")
ax.set_ylabel("register drift (%)")
ax.set_title("East overcounts more: median -1.47 vs -0.19, p=0.0002")
plt.tight_layout()
plt.savefig(FIG_DIR / "fig2_east_west.png", dpi=120)
plt.close()

# Fig 1. Nothing there, and the plot should say so.
fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(d.foreign_pct, d.gap_pct, s=18, alpha=0.6)
ax.axhline(0, lw=0.8, color="grey")
ax.set_xlabel("foreign share 2019 (%)")
ax.set_ylabel("register drift (%)")
ax.set_title(f"H1 falsified: no relationship (r=+0.09, n={len(d)})")
plt.tight_layout()
plt.savefig(FIG_DIR / "fig1_foreign_null.png", dpi=120)
plt.close()

print(f"saved 3 figures to {FIG_DIR}")

# H1. Spearman too, in case it's curved and Pearson misses it.
r_p = d.gap_pct.corr(d.foreign_pct)
r_s = d.gap_pct.corr(d.foreign_pct, method="spearman")
print(f"\nH1 - foreign share vs drift:")
print(f"  Pearson  r = {r_p:+.3f}   n = {len(d)}")
print(f"  Spearman r = {r_s:+.3f}")

# These two tables barely overlap. That's H1 dying.
print("\n  worst drift:")
print(d.nsmallest(6, "gap_pct")[["name", "gap_pct", "foreign_pct"]].to_string())
print("\n  highest foreign share:")
print(d.nlargest(6, "foreign_pct")[["name", "gap_pct", "foreign_pct"]].to_string())

# Mann-Whitney, not a t-test. Haven't checked normality and the medians
# are doing the work anyway.
w = nb.loc[~nb.is_east, "gap_pct"]
e = nb.loc[nb.is_east, "gap_pct"]
u, p = stats.mannwhitneyu(w, e)
print(f"\nEast vs West drift (Berlin excluded):")
print(f"  Mann-Whitney U = {u:.0f}, p = {p:.2e}")

diff = w.mean() - e.mean()
se = (w.var() / len(w) + e.var() / len(e)) ** 0.5
print(f"  mean diff = {diff:+.3f}  95% CI [{diff - 1.96 * se:+.3f}, {diff + 1.96 * se:+.3f}]")

# decline_pct runs 2011-2019, so it ends before the outcome window opens.
# Can't be contaminated by the 2022 correction.
s = m[["gap_pct", "decline_pct"]].dropna()
print(f"\ndecline vs drift, pooled: r = {s.gap_pct.corr(s.decline_pct):+.3f}  n = {len(s)}")

print("\ndecline_pct 2011-2019 by region (Berlin excluded):")
print(nb.groupby("is_east").decline_pct.agg(["count", "mean", "median"]))

# Each city next to its own Landkreis. Same region, same growth, and the
# city overcounts 6-8x more. Trier grew 4.9%, Bamberg 9.4%. Wrong sign
# for decline to be the explanation out West.
print("\nkey cases (city vs its own Landkreis):")
print(m[m.name.str.contains("Goslar|Holzminden|Trier|Bamberg", na=False)]
      [["name", "gap_pct", "decline_pct", "is_east"]].to_string())

# If East were just a label for decline, decline would show up in the West too.
east_only = nb[nb.is_east]
west_only = nb[~nb.is_east]
print(f"\ndecline vs drift, r within East: {east_only.gap_pct.corr(east_only.decline_pct):+.3f}")
print(f"decline vs drift, r within West: {west_only.gap_pct.corr(west_only.decline_pct):+.3f}")