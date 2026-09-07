from pull import load_file, RAW_FILES

# Mergers effective between the 2019 reference date and the 2022 census.
# Verified two ways: only 1 of 77 dissolved codes carries a live 2019 value,
# and only 1 district exceeds +/-8% register-2019 vs register-2022 change.
CROSSWALK_2019_TO_2022 = {
    "16056": "16063",   # Eisenach -> Wartburgkreis, 2021-07-01
}


def harmonize_2019(r):
    """Re-express 2019 register figures on 2022 boundaries."""
    r = r.copy()
    numeric = r.value_2019.astype(str).str.strip().str.fullmatch(r"-?\d+")
    r = r[numeric].copy()
    r["value_2019"] = r.value_2019.astype(int)
    r["kreis_code_2022"] = r.kreis_code.replace(CROSSWALK_2019_TO_2022)
    return r.groupby("kreis_code_2022", as_index=False).value_2019.sum()


def check_harmonize(r, out, zensus_codes):
    """Harmonization relabels and regroups. It must conserve total population,
    produce one row per 2022 Kreis, and drop only dissolved districts."""
    numeric = r.value_2019.astype(str).str.strip().str.fullmatch(r"-?\d+")

    # The drop step must not remove a surviving Kreis with missing 2019 data.
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


# Districts with no separate foreigner count: a shared authority reports
# their cases under a neighbouring district.
FOREIGNER_UNAVAILABLE = {
    "10041", "10042", "10043", "10045", "10046",  # -> 10044 Saarlouis
    "12071",                                       # -> 12052 Cottbus
    "06633",                                       # -> 06611 Kassel Stadt (verify)
}
# The receiving districts are correspondingly inflated.
FOREIGNER_INFLATED = {"10044", "12052", "06611"}


def clean_foreigners(f, zensus_codes, date="2019-12-31"):
    out = f[(f.reference_date == date)
            & (f.country_group == "Total")
            & (f.kreis_code.isin(zensus_codes))].copy()
    assert len(out) == 400, f"Expected 400, got {len(out)}"

    numeric = out.value_total.astype(str).str.strip().str.fullmatch(r"-?\d+")
    assert set(out.loc[~numeric, "kreis_code"]) == FOREIGNER_UNAVAILABLE, \
        f"Unavailable set changed: {sorted(set(out.loc[~numeric,'kreis_code']))}"

    out = out[numeric].copy()
    out["value_total"] = out.value_total.astype(int)
    out = out[~out.kreis_code.isin(FOREIGNER_INFLATED)]
    return out


def clean_zensus(z):
    out = z[z.kreis_code.str.len() == 5].copy()
    out["value"] = out.value.astype(int)
    assert len(out) == 400
    return out[["kreis_code", "name", "value"]]


def register_long(r, zensus_codes):
    """Wide (5 date columns) -> long (one row per Kreis-year)."""
    years = ["2011", "2016", "2019", "2022", "2025"]
    r = r[r.kreis_code.isin(zensus_codes)].copy()

    out = r.melt(
        id_vars=["kreis_code", "name"],
        value_vars=[f"value_{y}" for y in years],
        var_name="year", value_name="population",
    )
    out["year"] = out.year.str.replace("value_", "").astype(int)
    numeric = out.population.astype(str).str.strip().str.fullmatch(r"-?\d+")
    out = out[numeric].copy()
    out["population"] = out.population.astype(int)

    # 03159 Göttingen was created 2016-11-01 from 03152 + 03156, so it has no
    # 2011 value. Long format legitimately has one fewer row than 400 x 5.
    assert len(out) == 1999, f"Expected 1999, got {len(out)}"
    assert out.duplicated(["kreis_code", "year"]).sum() == 0
    KNOWN_GAPS = {("03159", 2011)}  # Göttingen created 2016-11-01
    actual = {(c, y) for c in zensus_codes for y in [int(x) for x in years]} \
             - set(zip(out.kreis_code, out.year))
    assert actual == KNOWN_GAPS, f"Gap set changed: {sorted(actual ^ KNOWN_GAPS)}"
    return out


if __name__ == "__main__":
    r = load_file(RAW_FILES["register"])
    z = load_file(RAW_FILES["zensus"])
    f = load_file(RAW_FILES["foreigners"])
    zensus_codes = set(z.loc[z.kreis_code.str.len() == 5, "kreis_code"])

    out = harmonize_2019(r)
    report = check_harmonize(r, out, zensus_codes)
    print(f"rows: {report['n_rows']}   total 2019: {report['total_2019']:,}")

    fo = clean_foreigners(f, zensus_codes)
    print(f"foreigners 2019: {len(fo)} rows")

    zk = clean_zensus(z)
    print(f"zensus: {len(zk)} rows")

    rl = register_long(r, zensus_codes)
    print(f"register long: {len(rl)} rows")