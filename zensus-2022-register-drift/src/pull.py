from pathlib import Path   ## to read the file path
import pandas as pd

## path setup
PROJECT_ROOT = Path(__file__).parent.parent  
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DOCS_DIR = PROJECT_ROOT / "docs"


## configuration of the raw files to be read
RAW_FILES = {
    "zensus": {
        "path": RAW_DIR / "1000A-0000_en.csv",
        "sep": ";",
        "names": ['kreis_code', 'name', 'variable', 'unit', 'value', 'flag'],
        "dtype": {'kreis_code': str},
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
        "dtype": {"kreis_code": str},
        "skipfooter": 4,
        "key": ["kreis_code"],
    },
    "foreigners": {
        "path": RAW_DIR / "12521-0041_en.csv",
        "sep": ";",
        "skiprows": 6,
        "names": ['reference_date', 'kreis_code', 'name', 'country_group',
                  'value_male', 'flag_male', 'value_female', 'flag_female',
                  'value_total', 'flag_total'],
        "dtype": {"kreis_code": str},
        "skipfooter": 4,
        "key": ["kreis_code", "reference_date", "country_group"],
    },
}

## the reader function for raw files
def load_file(entry):
    return pd.read_csv(
        entry["path"], sep=entry["sep"],
        skiprows=entry.get("skiprows", 0),   ## use it to get rid junk rows in toprows, or else "0" to skip
        skipfooter=entry.get("skipfooter", 0),  ## use it to get rid junk rows in bottomrows, or else "0" to skip
        engine="python", names=entry["names"],
        encoding=entry.get("encoding", "utf-8"), dtype=str,
    )


def non_numeric_rate(df):
    """Destatis writes missing data as '-', '.', '...', '/' — strings, not NaN.
    With dtype=str these pass isnull(). Whitelist actual numbers instead."""
    out = {}
    for col in df.columns:
        if col.startswith("value_") or col == "value":
            s = df[col].astype(str).str.strip()
            out[col] = (~s.str.fullmatch(r"-?\d+")).mean()
    return out


## the measurement function for raw files
def profile_file(name, entry):
    df = load_file(entry)
    dup_mask = df.duplicated(subset=entry["key"], keep=False)

    profile = {
        "filename": entry["path"].name,
        "n_rows": df.shape[0],
        "n_cols": df.shape[1],
        "columns": list(df.columns),
        "null_rate": df.isnull().mean().to_dict(),
        "key_lengths": df["kreis_code"].str.len().value_counts().to_dict(),
        "n_unique_keys": len(df) - df.duplicated(subset=entry["key"]).sum(),
        "n_duplicate_keys": dup_mask.sum(),
        "non_numeric_rate": non_numeric_rate(df),
    }
    return profile


## the guard function for checking the datasets
def check_files_exist():
    for name, entry in RAW_FILES.items():
        if not entry["path"].exists():
            raise FileNotFoundError(f"File not found: {entry['path']}")
    print("All raw files found.")


## print the profile of raw files
def print_profile(name, profile):
    print(f"\n{'='*60}")
    print(f"  {name.upper()}  —  {profile['filename']}")
    print(f"{'='*60}")
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


## the validation function for Kreise of correctioness
def validate_kreise(z, r):
    """Assert structural invariants across zensus and register. Returns a report.
    Does NOT filter — dissolved Kreise are tagged in clean.py, not dropped here."""
    national_total = int(z.loc[z.kreis_code == "DG", "value"].iloc[0])
    z_kreise = z[z.kreis_code.str.len() == 5]
    zensus_codes = set(z_kreise.kreis_code)
    filtered = r[r.kreis_code.isin(zensus_codes)].copy()
    missing = zensus_codes - set(filtered.kreis_code)
    assert not missing, f"Dropped real Kreise: {sorted(missing)}"
    assert len(filtered) == 400, f"Expected 400, got {len(filtered)}"
    # Zensus 2022 applies Cell-Key disclosure control, so district values are not
    # guaranteed to sum to the published national total. Observed gap: 0.0100%.
    # Tolerance 0.02% = 2x observed, and below the smallest Kreis (~34k = 0.04%),
    # so losing a whole district still trips this assert.
    diff = abs(national_total - z_kreise.value.astype(int).sum())
    rel = diff / national_total
    print(f"  sum diff: {diff:,} ({rel:.4%})")
    assert rel < 0.0002, f"Sum mismatch {diff:,} ({rel:.4%})"
    dropped = r[~r.kreis_code.isin(zensus_codes)]
    live_2019 = dropped[dropped.value_2019.astype(str).str.strip().str.fullmatch(r"-?\d+")]
    if len(live_2019):
        print(f"  dissolved rows with live value_2019: {len(live_2019)}")
        for _, row in live_2019.iterrows():
            print(f"    {row.kreis_code}  {row['name']}  {int(row.value_2019):,}")
    return {
        "n_current_kreise": len(zensus_codes & set(r.kreis_code)),
        "n_dissolved": len(dropped),
        "dissolved_codes": sorted(dropped.kreis_code),
        "national_total": national_total,
        "sum_diff": int(diff),
    }


## Orchestration of all functions.
if __name__ == "__main__":
    check_files_exist()
    for name, entry in RAW_FILES.items():
        print_profile(name, profile_file(name, entry))

    z = load_file(RAW_FILES["zensus"])
    r = load_file(RAW_FILES["register"])
    report = validate_kreise(z, r)
    print(f"\nvalidate_kreise: OK — {report['n_current_kreise']} current Kreise, "
          f"{report['n_dissolved']} dissolved")