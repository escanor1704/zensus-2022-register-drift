from pull import load_file, RAW_FILES
from clean import harmonize_2019, clean_foreigners, clean_zensus, clean_area


def build(z, r, f, a, zensus_codes):
    """One row = one Kreis on 2022 boundaries."""
    zk = clean_zensus(z).rename(columns={"value": "zensus_2022"})
    r19 = harmonize_2019(r).rename(
        columns={"kreis_code_2022": "kreis_code", "value_2019": "register_2019"})
    fo = clean_foreigners(f, zensus_codes)[["kreis_code", "value_total"]] \
        .rename(columns={"value_total": "foreigners_2019"})
    ar = clean_area(a, zensus_codes)

    m = zk.merge(r19, on="kreis_code", how="inner")
    assert len(m) == 400, f"join 1: expected 400, got {len(m)}"

    m = m.merge(fo, on="kreis_code", how="left")
    assert len(m) == 400, f"join 2: expected 400, got {len(m)}"
    assert m.foreigners_2019.notna().sum() == 390, \
        f"expected 390 with foreigner data, got {m.foreigners_2019.notna().sum()}"

    m = m.merge(ar, on="kreis_code", how="inner")
    assert len(m) == 400, f"join 3: expected 400, got {len(m)}"
    assert m.kreis_code.is_unique, "duplicate codes after join"
    assert m[["zensus_2022", "register_2019", "area_km2"]].notna().all().all(), \
        "nulls in core columns"

    # Outcome keeps register_2019 as denominator - that is the definition of drift.
    m["gap_pct"] = (m.zensus_2022 / m.register_2019 - 1) * 100
    # Predictors use zensus_2022 to avoid sharing the outcome's denominator error.
    m["foreign_pct"] = m.foreigners_2019 / m.zensus_2022 * 100
    m["density"] = m.zensus_2022 / m.area_km2
    m["is_east"] = m.kreis_code.str[:2].isin({"12", "13", "14", "15", "16"})
    return m


if __name__ == "__main__":
    z = load_file(RAW_FILES["zensus"])
    r = load_file(RAW_FILES["register"])
    f = load_file(RAW_FILES["foreigners"])
    a = load_file(RAW_FILES["area"])
    codes = set(z.loc[z.kreis_code.str.len() == 5, "kreis_code"])

    m = build(z, r, f, a, codes)
    print(f"\njoined: {len(m)} rows, {len(m.columns)} cols")
    print(m[["gap_pct", "foreign_pct", "density"]].describe())
    print(f"\ncities: {m.is_city.sum()}   east: {m.is_east.sum()}")