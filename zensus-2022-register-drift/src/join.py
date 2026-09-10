"""Stage 3. Build the analytical table. Writes data/processed/.

One row = one Kreis, on 2022 boundaries. n = 400.
"""
from pull import PROJECT_ROOT, load_file, RAW_FILES
from clean import (harmonize_2019, clean_foreigners, clean_zensus,
                   clean_area, register_long, FOREIGNER_MISSING)


def build(z, r, f, a, zensus_codes):
    zk = clean_zensus(z).rename(columns={"value": "zensus_2022"})
    r19 = harmonize_2019(r).rename(columns={"kreis_code_2022": "kreis_code",
                                            "value_2019": "register_2019"})
    fo = clean_foreigners(f, zensus_codes)[["kreis_code", "value_total"]] \
        .rename(columns={"value_total": "foreigners_2019"})
    ar = clean_area(a, zensus_codes)

    # Inner joins with an assert: 400 rows out proves both sides matched.
    # A left join returns 400 whether every key matched or half NaN-filled.
    m = zk.merge(r19, on="kreis_code", how="inner")
    assert len(m) == 400, f"join 1: expected 400, got {len(m)}"

    # Left here on purpose - all 400 have population data, only 390 have
    # foreigner data. Inner would shrink the table for a reason that only
    # affects one predictor.
    m = m.merge(fo, on="kreis_code", how="left")
    assert len(m) == 400, f"join 2: expected 400, got {len(m)}"
    assert set(m.loc[m.foreigners_2019.isna(), "kreis_code"]) == FOREIGNER_MISSING, \
        f"missing set changed: {sorted(set(m.loc[m.foreigners_2019.isna(), 'kreis_code']))}"

    m = m.merge(ar, on="kreis_code", how="inner")
    assert len(m) == 400, f"join 3: expected 400, got {len(m)}"
    assert m.kreis_code.is_unique, "duplicate codes after join"
    assert m[["zensus_2022", "register_2019", "area_km2"]].notna().all().all(), \
        "nulls in core columns"

    # decline_pct spans 2011-2019, entirely before the outcome window, so it
    # cannot be contaminated by the 2022 correction.
    rl = register_long(r, zensus_codes)
    p11 = rl[rl.year == 2011].set_index("kreis_code").population
    p19 = rl[rl.year == 2019].set_index("kreis_code").population
    m["decline_pct"] = (m.kreis_code.map(p19) / m.kreis_code.map(p11) - 1) * 100

    # Outcome keeps register_2019 in the denominator - that is drift.
    m["gap_pct"] = (m.zensus_2022 / m.register_2019 - 1) * 100
    # Predictors use zensus_2022 so they don't share the outcome's error.
    m["foreign_pct"] = m.foreigners_2019 / m.zensus_2022 * 100
    m["density"] = m.zensus_2022 / m.area_km2
    # Berlin (11) is False here and excluded downstream, not counted as West.
    m["is_east"] = m.kreis_code.str[:2].isin({"12", "13", "14", "15", "16"})
    return m


if __name__ == "__main__":
    z = load_file(RAW_FILES["zensus"])
    r = load_file(RAW_FILES["register"])
    f = load_file(RAW_FILES["foreigners"])
    a = load_file(RAW_FILES["area"])
    codes = set(z.loc[z.kreis_code.str.len() == 5, "kreis_code"])

    m = build(z, r, f, a, codes)

    PROCESSED = PROJECT_ROOT / "data" / "processed"
    PROCESSED.mkdir(parents=True, exist_ok=True)
    m.to_csv(PROCESSED / "analytical_table.csv", index=False)

    print(f"  {len(m)} rows, {len(m.columns)} cols   "
          f"cities {m.is_city.sum()}   east {m.is_east.sum()}   "
          f"foreign_pct n={m.foreign_pct.notna().sum()}")
    print("  wrote data/processed/analytical_table.csv")