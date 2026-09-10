"""Stage 2. Harmonize boundaries, reshape, filter. Writes data/interim/.

Crosswalk logic lives here rather than a separate module: the mapping is a
single entry, and splitting it out would cost more in indirection than it
gains in structure.
"""
from pull import PROJECT_ROOT, load_file, RAW_FILES

# Mergers effective between the 2019 reference date and the 2022 census.
# Verified two ways: only 1 of 77 dissolved codes carries a live 2019 value,
# and only 1 district exceeds +/-8% register-2019 vs register-2022 change.
CROSSWALK_2019_TO_2022 = {
    "16056": "16063",   # Eisenach -> Wartburgkreis, 2021-07-01
}

# No separate foreigner count: a shared authority reports these districts'
# cases under a neighbour. All three cases stated in the source file's footer.
FOREIGNER_UNAVAILABLE = {
    "10041", "10042", "10043", "10045", "10046",   # -> 10044 Saarlouis
    "12071",                                        # -> 12052 Cottbus
    "06633",                                        # -> 06611 Kassel Stadt
}
# The receiving districts carry their neighbours' counts and are excluded.
FOREIGNER_INFLATED = {"10044", "12052", "06611"}
# All ten, for the post-join identity assert.
FOREIGNER_MISSING = FOREIGNER_UNAVAILABLE | FOREIGNER_INFLATED

# Gaps in the long-format register, with cause. Named, not tolerated.
KNOWN_GAPS = {("03159", 2011)}   # Göttingen created 2016-11-01 from 03152+03156

YEARS = ["2011", "2016", "2019", "2022", "2025"]


def _numeric(s):
    return s.astype(str).str.strip().str.fullmatch(r"-?\d+")


def harmonize_2019(r):
    """Re-express 2019 register figures on 2022 boundaries."""
    r = r[_numeric(r.value_2019)].copy()
    r["value_2019"] = r.value_2019.astype(int)
    r["kreis_code_2022"] = r.kreis_code.replace(CROSSWALK_2019_TO_2022)
    return r.groupby("kreis_code_2022", as_index=False).value_2019.sum()


def check_harmonize(r, out, zensus_codes):
    """Relabelling and regrouping must conserve population, produce one row
    per 2022 Kreis, and drop only dissolved districts."""
    numeric = _numeric(r.value_2019)

    # Must not drop a surviving Kreis that happens to have missing 2019 data.
    dropped_codes = set(r.loc[~numeric, "kreis_code"])
    survivors_dropped = dropped_codes & zensus_codes
    assert not survivors_dropped, (
        f"Dropped {len(survivors_dropped)} surviving Kreise with missing "
        f"value_2019: {sorted(survivors_dropped)}"
    )

    before = r[numeric].value_2019.astype(int).sum()
    after = out.value_2019.sum()
    assert before == after, f"Population not conserved: {before:,} -> {after:,}"
    assert len(out) == 400, f"Expected 400 rows, got {len(out)}"
    assert out.kreis_code_2022.is_unique, "Duplicate codes after grouping"
    return {"total_2019": int(after), "n_rows": len(out),
            "n_dropped": len(dropped_codes)}


def clean_foreigners(f, zensus_codes, date="2019-12-31"):
    """Filter, never sum. country_group categories are nested - Europe sits
    inside Total, EU-27 and EU-28 are two vintages of the same concept."""
    out = f[(f.reference_date == date)
            & (f.country_group == "Total")
            & (f.kreis_code.isin(zensus_codes))].copy()
    assert len(out) == 400, f"Expected 400, got {len(out)}"

    numeric = _numeric(out.value_total)
    assert set(out.loc[~numeric, "kreis_code"]) == FOREIGNER_UNAVAILABLE, \
        f"Unavailable set changed: {sorted(set(out.loc[~numeric, 'kreis_code']))}"

    out = out[numeric].copy()
    out["value_total"] = out.value_total.astype(int)
    out = out[~out.kreis_code.isin(FOREIGNER_INFLATED)]
    assert len(out) == 390, f"Expected 390, got {len(out)}"
    return out


def clean_zensus(z):
    """Drop the DG row - Germany's national total is a different grain."""
    out = z[z.kreis_code.str.len() == 5].copy()
    out["value"] = out.value.astype(int)
    assert len(out) == 400, f"Expected 400, got {len(out)}"
    return out[["kreis_code", "name", "value"]]


def register_long(r, zensus_codes):
    """Wide (5 date columns) -> long (one row per Kreis-year)."""
    r = r[r.kreis_code.isin(zensus_codes)].copy()
    out = r.melt(
        id_vars=["kreis_code", "name"],
        value_vars=[f"value_{y}" for y in YEARS],
        var_name="year", value_name="population",
    )
    out["year"] = out.year.str.replace("value_", "").astype(int)
    out = out[_numeric(out.population)].copy()
    out["population"] = out.population.astype(int)

    # Assert the identity of the gap, not just the row count. A count stays
    # true if one gap closes and a different one opens.
    expected = {(c, int(y)) for c in zensus_codes for y in YEARS}
    actual = expected - set(zip(out.kreis_code, out.year))
    assert actual == KNOWN_GAPS, f"Gap set changed: {sorted(actual ^ KNOWN_GAPS)}"
    assert out.duplicated(["kreis_code", "year"]).sum() == 0
    return out


def clean_area(a, zensus_codes):
    """Destatis 04-kreise.xlsx, Gebietsstand 31.12.2024. Land rows carry
    2-char codes; Land subtotals have NaN codes. Both drop out on the filter."""
    a = a.copy()
    a.columns = [f"c{i}" for i in range(a.shape[1])]

    # Reconcile against the file's own national total, not a remembered
    # constant. The constant I assumed would have failed.
    national = float(a.loc[a.c1 == "Deutschland", "c4"].iloc[0])

    out = a[a.c0.isin(zensus_codes)].copy()
    out = out.rename(columns={"c0": "kreis_code", "c1": "kreis_type",
                              "c4": "area_km2"})
    out["area_km2"] = out.area_km2.astype(float)

    # BW labels its independent cities "Stadtkreis", not "Kreisfreie Stadt".
    # An exact match on one label classed Stuttgart as rural.
    CITY_TYPES = {"Kreisfreie Stadt", "Stadtkreis"}
    out["is_city"] = out.kreis_type.str.strip().isin(CITY_TYPES)
    assert out.is_city.sum() == 106, f"Expected 106 cities, got {out.is_city.sum()}"

    assert len(out) == 400, f"Expected 400, got {len(out)}"
    assert set(out.kreis_code) == zensus_codes, \
        "Code set mismatch (2024 file vs 2022 boundaries)"

    total = out.area_km2.sum()
    rel = abs(total - national) / national
    print(f"  area: {total:,.1f} km2 vs national {national:,.1f} ({rel:.4%})")
    assert rel < 0.001, f"Area mismatch {total:,.1f} vs {national:,.1f}"

    return out[["kreis_code", "area_km2", "is_city"]]


if __name__ == "__main__":
    r = load_file(RAW_FILES["register"])
    z = load_file(RAW_FILES["zensus"])
    f = load_file(RAW_FILES["foreigners"])
    a = load_file(RAW_FILES["area"])
    zensus_codes = set(z.loc[z.kreis_code.str.len() == 5, "kreis_code"])

    out = harmonize_2019(r)
    report = check_harmonize(r, out, zensus_codes)
    fo = clean_foreigners(f, zensus_codes)
    zk = clean_zensus(z)
    rl = register_long(r, zensus_codes)
    ar = clean_area(a, zensus_codes)

    INTERIM = PROJECT_ROOT / "data" / "interim"
    INTERIM.mkdir(parents=True, exist_ok=True)
    out.to_csv(INTERIM / "register_2019_harmonized.csv", index=False)
    fo.to_csv(INTERIM / "foreigners_2019.csv", index=False)
    zk.to_csv(INTERIM / "zensus_2022.csv", index=False)
    rl.to_csv(INTERIM / "register_long.csv", index=False)
    ar.to_csv(INTERIM / "area.csv", index=False)

    print(f"  harmonized 2019: {report['n_rows']} rows, "
          f"total {report['total_2019']:,}")
    print(f"  foreigners: {len(fo)}   zensus: {len(zk)}   "
          f"long: {len(rl)}   area: {len(ar)}")
    print(f"  wrote 5 files to data/interim/")