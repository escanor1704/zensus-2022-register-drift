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


if __name__ == "__main__":
    r = load_file(RAW_FILES["register"])
    z = load_file(RAW_FILES["zensus"])
    zensus_codes = set(z.loc[z.kreis_code.str.len() == 5, "kreis_code"])
    out = harmonize_2019(r)
    report = check_harmonize(r, out, zensus_codes)
    print(f"rows: {report['n_rows']}   total 2019: {report['total_2019']:,}"
          f"   dropped: {report['n_dropped']}")
    print(out[out.kreis_code_2022 == "16063"])
    print(f"{report['n_dropped']} survivors were dropped.")