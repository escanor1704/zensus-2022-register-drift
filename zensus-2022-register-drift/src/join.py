from pull import load_file, RAW_FILES
from clean import harmonize_2019, clean_foreigners, clean_zensus


def build(z, r, f, zensus_codes):
    """One row = one Kreis on 2022 boundaries."""
    zk = clean_zensus(z).rename(columns={"value": "zensus_2022"})
    r19 = harmonize_2019(r).rename(
        columns={"kreis_code_2022": "kreis_code", "value_2019": "register_2019"})
    fo = clean_foreigners(f, zensus_codes)[["kreis_code", "value_total"]] \
        .rename(columns={"value_total": "foreigners_2019"})

    m = zk.merge(r19, on="kreis_code", how="inner")
    assert len(m) == 400, f"join 1: expected 400, got {len(m)}"

    m = m.merge(fo, on="kreis_code", how="left")
    assert len(m) == 400, f"join 2: expected 400, got {len(m)}"
    assert m.kreis_code.is_unique, "duplicate codes after join"
    assert m.foreigners_2019.notna().sum() == 390, \
        f"expected 390 with foreigner data, got {m.foreigners_2019.notna().sum()}"
    assert m[["zensus_2022", "register_2019"]].notna().all().all(), \
        "nulls in population columns"

    m["gap_pct"] = (m.zensus_2022 / m.register_2019 - 1) * 100
    m["foreign_pct"] = m.foreigners_2019 / m.register_2019 * 100
    return m

if __name__ == "__main__":
    z = load_file(RAW_FILES["zensus"])
    r = load_file(RAW_FILES["register"])
    f = load_file(RAW_FILES["foreigners"])
    codes = set(z.loc[z.kreis_code.str.len() == 5, "kreis_code"])

    m = build(z, r, f, codes)
    print(f"joined: {len(m)} rows, {len(m.columns)} cols")
    print(m[["gap_pct", "foreign_pct"]].describe())