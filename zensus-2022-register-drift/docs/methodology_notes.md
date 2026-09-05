# Data notes

## Stage 0 — what's actually in the raw files

### Structure

| file | header rows | footer rows | rows loaded | cols |
|---|---|---|---|---|
| 1000A-0000_en.csv (zensus) | 0 | 3 | 401 | 6 |
| 12411-0015_en.csv (register) | 6 | 4 | 477 | 12 |
| 12521-0041_en.csv (foreigners) | 6 | 4 | 97,785 | 10 |

None of the three has a header row worth using, so column names are supplied by hand
through `names=`. The zensus file goes straight into data on line 1 — no title block at all.

Encoding is UTF-8 and the umlauts survive the round trip. Pinned it anyway. On a Windows
box with a cp1252 locale the same file would decode into garbage without raising anything,
and silent corruption is worse than a crash.

`skipfooter` only works with `engine="python"`. The default C engine ignores it.

### Grain

- **zensus** — one Kreis per row (400 of them), plus a `DG` row for Germany. Two grains
  in one file.
- **register** — one Kreis per row, but wide: five reference dates (2011, 2016, 2019,
  2022, 2025) stapled across the row as repeating value/flag pairs.
- **foreigners** — one row per Kreis × reference date × country group. Long format,
  the date lives in its own column.

Keys: `["kreis_code"]` for zensus and register, `["kreis_code", "reference_date",
"country_group"]` for foreigners. Checking foreigners on `kreis_code` alone reported
97,313 duplicates. All fake — the code repeats by design, once per date and group.

### Findings

**1. Mixed grain in zensus.** `DG` is Germany, 82,719,540 persons. Not a district. Kept
aside as a reference total rather than deleted.

**2. Seventy-seven dissolved Kreise in the register.** Every one carries `(until
YYYY-MM-DD)` in its name — `13051 Bad Doberan (until 2011-09-03)`, `14171 Annaberg
(until 2008-07-31)`, `15151 Anhalt-Zerbst (until 2007-06-30)`. These are historical
districts left over from state reforms, not Länder totals.

There's no code pattern to catch them. All 477 codes are five digits, and
`~kreis_code.str.endswith("00")` drops nothing at all. The only reliable filter is
membership in the Zensus 400. 477 − 77 = 400, which checks out.

**3. The values don't add up.** The 400 districts sum to 82,711,282 against a stated
national figure of 82,719,540 — short by 8,258, or 0.0100%. Zensus 2022 runs published
cells through Cell-Key disclosure control, which nudges individual figures, so sub-values
aren't guaranteed to reconcile to totals. Worth flagging: perturbations of ±1 or ±2 spread
over 400 cells shouldn't accumulate to 8,258. Something else is contributing and I haven't
identified it.

**4. One merger lands inside the analysis window.** Eisenach `16056` folded into
Wartburgkreis `16063` on 2021-07-01. Of the 77 dissolved rows, exactly one still carries a
live 2019 value — Eisenach, at 42,250.

Wartburgkreis reads 118,974 in 2019 and 156,566 in 2022. Taken at face value that's
**+31.6%**. Add Eisenach back into the 2019 side (118,974 + 42,250 = 161,224) and the real
change is **−2.9%**. Wrong sign, off by 42,000 people, and it would have been the largest
apparent drift in the dataset. This is the argument for the crosswalk.

Göttingen and Osterode merged in 2016, before the window opens, so they cause no trouble.

**Blind spot.** This only catches mergers where the old code vanishes from the file. If
territory moved between two districts that both still exist, nothing here would see it.

### Still open

The zensus file states no reference date anywhere in it. Its vintage is undocumented, so
there's no proof yet that it's comparable to the register's dated columns.

### How correctness is checked

By set difference against an independent list — the Zensus 400 — not by counting rows.
Hitting 400 proves nothing on its own, since dropping one real Kreis while keeping one
non-Kreis also lands on 400. A set difference names the district that went missing.

The sum tolerance is 0.02%: twice the observed 0.0100%, and comfortably under the
smallest Kreis at roughly 34,000 people (0.04%). Lose a district and the assert fires.

### Design

`pull.py` reads, profiles, and asserts. It never touches a frame.