"""Stage 1. Read raw sources, profile them, assert structural invariants.

Observes only. Never modifies a frame - filtering and transformation belong
in clean.py.
"""
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"

RAW_FILES = {
    "zensus": {
        "path": RAW_DIR / "1000A-0000_en.csv",
        "sep": ";",
        "names": ["kreis_code", "name", "variable", "unit", "value", "flag"],
        "skipfooter": 3,
        "key": ["kreis_code"],
    },
    "register": {
        "path": RAW_DIR / "12411-0015_en.csv",
        "sep": ";",
        "skiprows": 6,
        "names": ["kreis_code", "name", "value_2011", "flag_2011",
                  "value_2016", "flag_2016", "value_2019", "flag_2019",
                  "value_2022", "flag_2022", "value_2025", "flag_2025"],
        "skipfooter": 4,
        "key": ["kreis_code"],
    },
    "foreigners": {
        "path": RAW_DIR / "12521-0041_en.csv",
        "sep": ";",
        "skiprows": 6,
        "names": ["reference_date", "kreis_code", "name", "country_group",
                  "value_male", "flag_male", "value_female", "flag_female",
                  "value_total", "flag_total"],
        "skipfooter": 4,
        "key": ["kreis_code", "reference_date", "country_group"],
    },
    "area": {
        "path": RAW_DIR / "04-kreise.xlsx",
        "key": ["kreis_code"],
    },
}


def load_file(entry):
    """Everything as str. Numeric casting happens in clean.py, after the
    Destatis missing-value markers ('-', '.', '/') have been identified."""
    if entry["path"].suffix in (".xls", ".xlsx"):
        return pd.read_excel(entry["path"], dtype=str, header=None)
    return pd.read_csv(
        entry["path"], sep=entry["sep"],
        skiprows=entry.get("skiprows", 0),
        skipfooter=entry.get("skipfooter", 0),
        engine="python",              # the C engine ignores skipfooter
        names=entry["names"],
        encoding=entry.get("encoding", "utf-8"),
        dtype=str,
    )


def non_numeric_rate(df):
    """Destatis writes missing data as '-', '.', '...', '/'. With dtype=str
    those pass isnull(). Whitelist actual numbers instead."""
    out = {}
    for col in df.columns:
        if col.startswith("value_") or col == "value":
            s = df[col].astype(str).str.strip()
            out[col] = (~s.str.fullmatch(r"-?\d+")).mean()
    return out


def profile_file(name, entry):
    df = load_file(entry)
    return {
        "filename": entry["path"].name,
        "n_rows": df.shape[0],
        "n_cols": df.shape[1],
        "columns": list(df.columns),
        "null_rate": df.isnull().mean().to_dict(),
        "key_lengths": df["kreis_code"].str.len().value_counts().to_dict(),
        "n_unique_keys": len(df) - df.duplicated(subset=entry["key"]).sum(),
        "n_duplicate_keys": df.duplicated(subset=entry["key"], keep=False).sum(),
        "non_numeric_rate": non_numeric_rate(df),
    }


def check_files_exist():
    for entry in RAW_FILES.values():
        if not entry["path"].exists():
            raise FileNotFoundError(f"File not found: {entry['path']}")


def print_profile(name, profile):
    print(f"\n{'=' * 60}")
    print(f"  {name.upper()}  —  {profile['filename']}")
    print(f"{'=' * 60}")
    print(f"  rows: {profile['n_rows']:,}    cols: {profile['n_cols']}")
    print(f"  unique keys: {int(profile['n_unique_keys']):,}"
          f"    duplicate keys: {int(profile['n_duplicate_keys']):,}")
    print(f"  key_lengths: {profile['key_lengths']}")

    print("\n  columns & null rate:")
    for col in profile["columns"]:
        rate = profile["null_rate"][col]
        n_null = round(rate * profile["n_rows"])
        mark = "  <-- CHECK" if 0 < rate < 0.01 else ""
        print(f"    {col:<16} {rate:7.2%}  ({n_null:>6,} nulls){mark}")

    if profile["non_numeric_rate"]:
        print("\n  value columns — non-numeric (real missingness):")
        for vcol, vrate in profile["non_numeric_rate"].items():
            n = round(vrate * profile["n_rows"])
            print(f"    {vcol:<16} {vrate:7.2%}  ({n:>6,} non-numeric)")


def validate_kreise(z, r):
    """Assert structural invariants. Returns a report, not data."""
    national_total = int(z.loc[z.kreis_code == "DG", "value"].iloc[0])
    z_kreise = z[z.kreis_code.str.len() == 5]
    zensus_codes = set(z_kreise.kreis_code)

    present = zensus_codes & set(r.kreis_code)
    missing = zensus_codes - set(r.kreis_code)
    assert not missing, f"Register lacks real Kreise: {sorted(missing)}"
    assert len(present) == 400, f"Expected 400, got {len(present)}"

    # Zensus 2022 applies Cell-Key disclosure control, so district values are
    # not guaranteed to sum to the published national total. Observed 0.0100%.
    # Tolerance 0.02% = 2x observed, below the smallest Kreis (~34k = 0.04%),
    # so losing a whole district still trips this.
    diff = abs(national_total - z_kreise.value.astype(int).sum())
    rel = diff / national_total
    print(f"  sum diff: {diff:,} ({rel:.4%})")
    assert rel < 0.0002, f"Sum mismatch {diff:,} ({rel:.4%})"

    # Dissolutions after the 2019 reference date sit inside the comparison
    # window and need a crosswalk entry in clean.py.
    dropped = r[~r.kreis_code.isin(zensus_codes)].copy()
    until = dropped.name.str.extract(r"(\d{4}-\d{2}-\d{2}|b\.\d{2}\.\d{2}\.\d{4})")[0]
    until = until.str.replace(r"^b\.(\d{2})\.(\d{2})\.(\d{4})$", r"\3-\2-\1", regex=True)
    dropped["until_dt"] = pd.to_datetime(until, errors="coerce")

    in_window = dropped[dropped.until_dt > "2019-12-31"]
    print(f"  dissolutions after 2019-12-31: {len(in_window)}")
    for _, row in in_window.iterrows():
        print(f"    {row.kreis_code}  {row['name']}  value_2019={row.value_2019}")

    # A row with no date cannot be evaluated by a date filter. Surface it
    # rather than letting the NaN disappear.
    undated = dropped[dropped.until_dt.isna()]
    if len(undated):
        print(f"  WARNING: {len(undated)} dissolved rows have no parseable until-date")
        for _, row in undated.iterrows():
            print(f"    {row.kreis_code}  {row['name']}")

    return {
        "n_current_kreise": len(present),
        "n_dissolved": len(dropped),
        "dissolved_codes": sorted(dropped.kreis_code),
        "national_total": national_total,
        "sum_diff": int(diff),
    }


if __name__ == "__main__":
    check_files_exist()
    print("All raw files found.")

    for name, entry in RAW_FILES.items():
        if name == "area":       # no kreis_code column until cleaned
            continue
        print_profile(name, profile_file(name, entry))

    z = load_file(RAW_FILES["zensus"])
    r = load_file(RAW_FILES["register"])
    report = validate_kreise(z, r)
    print(f"\nvalidate_kreise: OK — {report['n_current_kreise']} current Kreise, "
          f"{report['n_dissolved']} dissolved")