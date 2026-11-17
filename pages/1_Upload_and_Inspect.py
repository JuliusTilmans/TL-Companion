"""
Page 1: Upload & Inspect (v9)

2026-10-18: timestamps without fractional seconds are accepted
(`_parse_with_format`: values that do not parse with '.%f' are parsed again
without it). Before, every such row was dropped as a parse failure. Values
with fractional seconds parse exactly as before. Also: 'skipped_subsets'
(page 3) added to DERIVED_STATE_KEYS. Previous version:
_removed_backup/before_ui_cleanup/pages/.

2026-10-17 (time within distance): switched to backend social_analysis_v13 and
streamlit_subsets_v6 (v13 adds the within-distance fraction; every existing
result is unchanged). Previous version of this file:
_removed_backup/before_within_distance/pages/. See FILE_DEPENDENCIES_v1.md.

2026-10-17 (pair proximity): switched to backend social_analysis_v12 and
streamlit_subsets_v5 (v12 adds proximity relative to observed time; every
existing result is unchanged). Previous version of this file:
_removed_backup/before_dyad_proximity/pages/. See FILE_DEPENDENCIES_v1.md.

2026-10-17 (settings memory): loading new data (or 'Clear all loaded data')
now also clears every analysis setting: page 2's remembered settings,
the configuration, dead zones, subjects and page 3's subsets. A new
dataset always starts from the defaults. Previous version:
_removed_backup/before_settings_memory/pages/.

2026-10-07: switched to backend social_analysis_v11 and streamlit_subsets_v4
(memory release, identical results). Previous version of this file:
_removed_backup/before_v11/pages/. See FILE_DEPENDENCIES_v1.md.

Purpose: load tracking CSV files and understand what you have.

v9 changes (BUGFIX: tab-switch wipes uploaded data — final fix):
- ROOT CAUSE: Streamlit's `st.file_uploader` does NOT reliably persist
  uploaded files across multi-page navigation, even with a `key=` argument.
  When the user revisits page 1 after visiting page 2 or 3, the uploader
  re-renders with an empty value. The previous fingerprint logic then
  treated "uploader empty" as "user removed all files," wiping `raw_data`
  plus all derived state.
- HISTORICAL NOTE: v8 attempted to fix this by adding `key="main_uploader"`
  on the assumption that keyed widgets persist across pages. They do for
  most widget types but NOT for file_uploader specifically — this is a
  long-standing Streamlit limitation, well-documented in their forums.
  v8 was therefore an incorrect fix and is superseded.
- FIX (v9): Decouple the data lifecycle from the widget lifecycle. Empty
  uploader is no longer treated as removal intent under any circumstance.
  Real "clear all data" intent is now an explicit user action: a
  confirmation-gated button placed near the uploader. Side effect: when
  the user removes the last file via the X icon, `raw_data` is preserved
  (because we cannot distinguish that from a page revisit). The user
  must click "Clear all data" to wipe explicitly. This is a deliberate
  trade-off — silent state-destruction is worse than requiring an extra
  click to clear.
- The fingerprint check is preserved for the legitimate cases:
  detecting changed file content (different file uploaded) and changed
  timestamp format. These both produce non-empty `uploaded_files` and
  trigger correct reprocessing.

v7 changes:
- NEW: Section 4 "Export Preferences" — radio for Python / R / Both. Sets
  `st.session_state["export_format_pref"]` consumed by page 3's bundle
  download (`build_export_bundle(..., format_pref=...)` in
  social_analysis_v9.py). Default = "both" so the choice does not privilege
  one audience. Note: this is an *output* format choice, not a processing
  parameter — the page-1 "no parameters" rule is preserved in spirit.

v6 changes (correct model: N files per tag, variable N):
- FIXED: Timestamp format auto-detection with user override.
  The old code hardcoded `dayfirst=True` (DD-MM-YYYY) but real TrackLab
  exports use MM/DD/YYYY. This has been silently misparsing dates in
  every run. v6 now detects the format from the data and lets the user
  override via radio button. Format selection is persisted in session
  state; changing it triggers a re-parse.
- REMOVED item 5c (same TagId across multiple files).
  Confirmed spam under the real model — one tag is routinely spread
  across multiple export chunks.
- REWORKED item 5b (coverage anomaly): now aggregates per-tag after
  combining all files. "Tag X's total time span across all its files
  is < 50% of the median tag's span." File-level spans were meaningless
  because TrackLab chunks one tag's recording into multiple files.
- DOWNGRADED item 5a (multi-TagId per file) from critical to medium.
  User confirmed the Tag_1/Tag_2/Tag_3 export pattern is a legitimate
  exception — worth warning but not critical.

v5 features retained:
- Magnitude warning with severity split (>50% critical, 5-50% medium, <5% info).

v4 features retained:
  6. TagId normalization: silent whitespace-strip + warn on case-collisions.
  A. Coordinate sanity checks: all-zero rows, absurd magnitudes, static tags.
  B. Timestamp parse failure count.
  C. Per-file duplicate contribution.
  I. File-change detection + session-state resync (now also triggers on
     format-setting change).

v3 features retained:
- Availability heatmap and per-tag quality table.

Downstream: page 2 (Clean & Configure) reads st.session_state["raw_data"].

NOTE: The downstream pipeline (social_analysis_v9.py, inherited unchanged
from v7) still uses `pd.to_datetime(..., dayfirst=True)` in several places.
v6 fixes the parse at upload time by storing already-parsed timestamps as
strings in the format the downstream expects. Alternatively, the pipeline
itself would need updating — but that's out of scope for this page.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from streamlit_subsets import parsed_timestamps, cached_for_upload
from social_analysis import parse_ddmmyyyy_fast


st.set_page_config(page_title="Upload & Inspect", page_icon="📂", layout="wide")
st.title("📂 Upload & Inspect")
st.caption("Stage 1 of 3 — load your data and understand what's in it.")

# ═════════════════════════════════════════════════════════════════════════════
# v6 — TIMESTAMP FORMAT DETECTION
# TrackLab exports vary by locale (European exports are typically DD/MM/YYYY);
# the old code hardcoded DD-MM-YYYY. Auto-detect per upload, let the user override.
# ═════════════════════════════════════════════════════════════════════════════

# Order matters ONLY for ambiguous ties: max() over equal scores returns the
# first-listed key. DD/MM/YYYY is placed first so that a date like 05/04/2025
# (both DD/MM and MM/DD valid) defaults to the day-first reading, which matches
# the European TrackLab exports this tool's users actually produce. The user is
# still warned on a tie and can override; this only sets the safer default.
TIMESTAMP_FORMATS = {
    "DD/MM/YYYY": "%d/%m/%Y %H:%M:%S.%f",
    "DD-MM-YYYY": "%d-%m-%Y %H:%M:%S.%f",
    "MM/DD/YYYY": "%m/%d/%Y %H:%M:%S.%f",
    "YYYY-MM-DD": "%Y-%m-%d %H:%M:%S.%f",
}


def _parse_with_format(values, format_key):
    """Parse timestamp strings with one of TIMESTAMP_FORMATS.

    2026-10-18: times without fractional seconds ('05/04/2025 10:00:00') are
    accepted too. Values that do not parse with '.%f' are parsed again with the
    same layout without it. Values with fractional seconds parse exactly as
    before: the second pass only sees values the first pass could not read.
    Before this change every row without fractional seconds was dropped as a
    timestamp parse failure.
    """
    fmt = TIMESTAMP_FORMATS[format_key]
    s = values if isinstance(values, pd.Series) else pd.Series(list(values), dtype=object)
    parsed = pd.to_datetime(s, format=fmt, errors="coerce")
    retry = parsed.isna() & s.notna()
    if retry.any():
        parsed.loc[retry] = pd.to_datetime(
            s[retry], format=fmt.replace(".%f", ""), errors="coerce"
        )
    return parsed


def _detect_timestamp_format(sample_strings):
    """Try each known format; pick the one that parses the most strings.

    Parameters
    ----------
    sample_strings : iterable of str
        Timestamp strings sampled from files.

    Returns
    -------
    dict with:
        'best'      : str, the format key that parsed the most samples
        'scores'    : dict of {format_key: fraction_parsed}
        'ambiguous' : bool, True if two formats both parsed > 90%
    """
    samples = [s for s in sample_strings if isinstance(s, str) and s.strip()]
    if not samples:
        return {"best": "DD/MM/YYYY", "scores": {}, "ambiguous": False}

    scores = {}
    for name, fmt in TIMESTAMP_FORMATS.items():
        parsed = _parse_with_format(samples, name)
        score = float(parsed.notna().mean())
        scores[name] = score

    best = max(scores, key=scores.get)

    # Ambiguity: two formats both parse > 90% of samples. Happens when all
    # day values are <= 12 — MM/DD and DD/MM both succeed.
    high_scoring = [k for k, v in scores.items() if v > 0.9]
    ambiguous = len(high_scoring) > 1

    return {"best": best, "scores": scores, "ambiguous": ambiguous}


def _format_ts_ddmmyyyy(parsed):
    """Same strings as parsed.dt.strftime('%d-%m-%Y %H:%M:%S.%f'), vectorised
    (per-row strftime is slow on large recordings). Falls back to strftime for
    NaT-only or tz-aware input, or dates outside 1970-2261."""
    valid = parsed.notna().to_numpy()
    if len(parsed) == 0 or not valid.any() or parsed.dt.tz is not None:
        return parsed.dt.strftime("%d-%m-%Y %H:%M:%S.%f")
    us = parsed.to_numpy().astype("datetime64[us]")
    lo, hi = np.datetime64("1970-01-01", "us"), np.datetime64("2262-01-01", "us")
    ok = us[valid]
    if not ((ok >= lo) & (ok < hi)).all():
        return parsed.dt.strftime("%d-%m-%Y %H:%M:%S.%f")
    iso = np.datetime_as_string(ok, unit="us")            # YYYY-MM-DDTHH:MM:SS.ffffff (26 chars)
    n = len(iso)
    m = iso.astype("<U26").view(np.uint32).reshape(n, 26)
    out = np.empty((n, 26), dtype=np.uint32)
    out[:, 0:2] = m[:, 8:10]                                # DD
    out[:, 2] = ord("-")
    out[:, 3:5] = m[:, 5:7]                                 # MM
    out[:, 5] = ord("-")
    out[:, 6:10] = m[:, 0:4]                                # YYYY
    out[:, 10] = ord(" ")
    out[:, 11:26] = m[:, 11:26]                             # HH:MM:SS.ffffff
    strings = np.ascontiguousarray(out).view("<U26").ravel().astype(object)
    res = np.full(len(parsed), np.nan, dtype=object)
    res[valid] = strings
    return pd.Series(res, index=parsed.index)


def _parse_and_normalize_timestamps(df, format_key):
    """Parse TimeStamp column using given format, then rewrite as DD-MM-YYYY.

    The downstream pipeline (social_analysis_v9.py, inherited unchanged
    from v7) uses `dayfirst=True` in its pd.to_datetime calls. By rewriting
    the TimeStamp column as DD-MM-YYYY HH:MM:SS.fff strings, downstream
    code continues to work unchanged while correctly representing the true
    dates.

    Returns
    -------
    tuple of (df_out, n_failures)
    """
    parsed = _parse_with_format(df["TimeStamp"], format_key)
    n_failures = int(parsed.isna().sum())

    df_out = df.copy()
    # Rewrite as DD-MM-YYYY — matches downstream pipeline's dayfirst=True
    df_out["TimeStamp"] = _format_ts_ddmmyyyy(parsed)
    # Drop rows where parse failed (they'd be all-NaN downstream anyway)
    if n_failures > 0:
        df_out = df_out[parsed.notna()].reset_index(drop=True)
    return df_out, n_failures


# ═════════════════════════════════════════════════════════════════════════════
# KEYS IN SESSION STATE THAT ARE DERIVED FROM raw_data
# When the uploader's file set changes, these must all be cleared to prevent
# downstream pages from displaying results computed from the old data.
# 2026-10-17: settings are cleared as well (decision: a new dataset starts
# from the defaults, so no setting meant for the old data is applied to the
# new data). Before, "config" and "dead_zones" were kept across uploads.
# ═════════════════════════════════════════════════════════════════════════════

DERIVED_STATE_KEYS = [
    # Pipeline outputs (set by page 3)
    "df_proc", "tags_dict", "dates_list",
    "subset_results", "subset_metrics",
    "stationary_df", "critical_distances",
    "child_nan", "x_bounds", "y_bounds",
    "nan_pos_pct", "nan_vel_pct",
    "dz_impact", "dz_episode_comparison",
    "merge_diagnostics", "run_config",
    # Auto-detect cache (page 2)
    "_ad_result",
    # Per-upload caches (parsed timestamps, quality stats, availability)
    "_parsed_ts_cache", "_upload_cache",
    # Settings (2026-10-17): configuration, page 2's remembered settings,
    # dead zones, subjects, velocity-advisor state, page 3's subsets.
    "config", "_page2_settings", "dead_zones", "subject_list",
    "multi_tag_enabled", "_tag_inc_seeded_set",
    "_advisor_approved", "_advisor_view",
    "sub_subsets_v2", "sub_editing_window",
    # 2026-10-18: subsets page 3 could not analyse in the last run.
    "skipped_subsets",
]


def _clear_derived_state():
    """Remove all session-state keys derived from the uploaded data."""
    cleared = 0
    for k in DERIVED_STATE_KEYS:
        if k in st.session_state:
            del st.session_state[k]
            cleared += 1
    # Per-tag include choices from page 2 (one key per tag).
    for k in [k for k in st.session_state.keys() if str(k).startswith("tag_inc_")]:
        del st.session_state[k]
    return cleared


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS — quality stats, availability binning, validation
# ─────────────────────────────────────────────────────────────────────────────

def _compute_tag_quality_stats(raw_df, gap_multiplier=3.0):
    """Compute per-tag quality stats.

    Behaviour change vs v9 (2026-05): gap counting is now per-(tag, date),
    not per-tag. Previously, a tag with data on two recording dates 21
    days apart would count the entire 21-day cross-date span as one
    enormous gap, triggering the "tag has >10 gaps" warning even when
    each individual recording session was internally clean. Aligns the
    gap definition with the pipeline's actual semantics: each date is
    an independent recording session, and "gap" means "interval within
    a recording session longer than 3× that tag's median interval."

    Median interval is also computed per (tag, date) and aggregated as
    the median of per-date medians. For tags with consistent sampling
    across dates this changes nothing; for tags with rate differences
    between dates (rare) the per-date median is more meaningful than
    a global one.
    """
    ts = parsed_timestamps(raw_df)
    df = raw_df.copy()
    df["_ts"] = ts
    df["_date"] = ts.dt.date
    df = df.sort_values(["TagId", "_ts"])

    rows = []
    for tag, g in df.groupby("TagId"):
        n = len(g)
        n_nan = int((g["X"].isna() | g["Y"].isna()).sum())
        nan_pct = (n_nan / n * 100) if n > 0 else 0.0

        t_first = g["_ts"].min()
        t_last = g["_ts"].max()

        # Per-date gap counting: each calendar date is treated as its
        # own session. Gaps that happen to span midnight will be missed
        # (rare for diurnal tracking; documented caveat matches backend).
        per_date_medians = []
        n_gaps = 0
        for date_key, g_date in g.groupby("_date"):
            if len(g_date) < 3:
                continue
            intervals_s = g_date["_ts"].diff().dt.total_seconds().dropna()
            if len(intervals_s) == 0 or intervals_s.median() <= 0:
                continue
            median_iv = intervals_s.median()
            per_date_medians.append(median_iv)
            n_gaps += int((intervals_s > gap_multiplier * median_iv).sum())

        if per_date_medians:
            median_iv_ms = round(float(np.median(per_date_medians)) * 1000, 1)
        else:
            median_iv_ms = np.nan

        rows.append({
            "TagId": tag,
            "samples": n,
            "nan_pct": round(nan_pct, 2),
            "median_interval_ms": median_iv_ms,
            "gap_count": n_gaps,
            "first_timestamp": t_first,
            "last_timestamp": t_last,
        })

    return pd.DataFrame(rows).sort_values("TagId").reset_index(drop=True)


def _compute_availability_matrix(raw_df, bin_seconds=60):
    """Compute per-(tag, date, bin) density matrix for availability heatmap."""
    ts = parsed_timestamps(raw_df)
    df = raw_df.copy()
    df["_ts"] = ts
    df["_date"] = ts.dt.date
    df = df.dropna(subset=["_ts"]).sort_values(["TagId", "_ts"])

    if len(df) == 0:
        return {
            "matrix": pd.DataFrame(),
            "bin_edges": {}, "row_labels": [],
            "tag_date_pairs": [], "single_day": True,
        }

    all_dates = sorted(df["_date"].unique())

    per_date_edges = {}
    for d in all_dates:
        day_ts = df.loc[df["_date"] == d, "_ts"]
        t0 = day_ts.min().floor(f"{bin_seconds}s")
        t1 = day_ts.max().ceil(f"{bin_seconds}s")
        edges = pd.date_range(t0, t1, freq=f"{bin_seconds}s")
        if len(edges) < 2:
            edges = pd.DatetimeIndex([t0, t0 + pd.Timedelta(seconds=bin_seconds)])
        per_date_edges[d] = edges

    tag_median_iv = {}
    for tag, g in df.groupby("TagId"):
        ivs = g["_ts"].diff().dt.total_seconds().dropna()
        if len(ivs) > 0 and ivs.median() > 0:
            tag_median_iv[tag] = ivs.median()
        else:
            tag_median_iv[tag] = bin_seconds

    tags = sorted(df["TagId"].unique(), key=str)

    row_labels = []
    tag_date_pairs = []
    row_data = []
    column_labels_master = []

    single_day = len(all_dates) == 1

    for d in all_dates:
        edges = per_date_edges[d]
        for i in range(len(edges) - 1):
            start = edges[i]
            if single_day:
                column_labels_master.append(start.strftime("%H:%M"))
            else:
                column_labels_master.append(
                    f"{start.strftime('%d-%m')} {start.strftime('%H:%M')}"
                )

    date_col_ranges = {}
    cursor = 0
    for d in all_dates:
        n_bins = len(per_date_edges[d]) - 1
        date_col_ranges[d] = (cursor, cursor + n_bins)
        cursor += n_bins
    total_cols = cursor

    for tag in tags:
        tag_data = df[df["TagId"] == tag]
        tag_dates_present = sorted(tag_data["_date"].unique())
        if len(tag_dates_present) == 0:
            continue

        for d in tag_dates_present:
            row = np.full(total_cols, np.nan)
            day_data = tag_data[tag_data["_date"] == d]
            edges = per_date_edges[d]

            counts, _ = np.histogram(
                day_data["_ts"].astype("int64").values,
                bins=edges.astype("int64").values,
            )

            med_iv = tag_median_iv.get(tag, bin_seconds)
            if med_iv <= 0:
                med_iv = bin_seconds
            expected_per_bin = bin_seconds / med_iv

            if expected_per_bin > 0:
                density = np.clip(counts / expected_per_bin, 0, 1)
            else:
                density = np.zeros_like(counts, dtype=float)

            density = np.where(counts == 0, np.nan, density)

            col_start, col_end = date_col_ranges[d]
            row[col_start:col_end] = density

            row_data.append(row)
            if single_day:
                row_labels.append(str(tag))
            else:
                row_labels.append(f"{tag} · {d.strftime('%d-%m-%Y')}")
            tag_date_pairs.append((tag, d))

    matrix = pd.DataFrame(row_data, index=row_labels, columns=column_labels_master)

    return {
        "matrix": matrix,
        "bin_edges": per_date_edges,
        "row_labels": row_labels,
        "tag_date_pairs": tag_date_pairs,
        "single_day": single_day,
    }


# ═════════════════════════════════════════════════════════════════════════════
# v4 — UPLOAD-TIME QUALITY HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _load_and_validate_file(file_obj):
    """Read one CSV, normalize TagIds, report parse issues.

    Returns
    -------
    dict with:
        'df'                : loaded DataFrame (None if fatal error)
        'filename'          : original filename
        'rows_read'         : int, raw rows loaded
        'timestamp_failures': int, rows where TimeStamp failed to parse
        'whitespace_stripped': int, TagId values with leading/trailing whitespace
                               that were silently stripped
        'raw_tagids'        : list of unique TagIds BEFORE stripping (for
                               downstream case-collision detection across files)
        'error'             : str or None, fatal read error
        't_min', 't_max'    : timestamps spanning the file (None if all failed)
    """
    result = {
        "df": None, "filename": file_obj.name, "rows_read": 0,
        "timestamp_failures": 0, "whitespace_stripped": 0,
        "raw_tagids": [], "error": None,
        # v6: raw TimeStamp samples for format detection
        "timestamp_samples": [],
        # v5: stripped, unique TagIds in this file (for single-tag-per-file
        # check and cross-file duplicate-tag check)
        "stripped_tagids": [],
    }

    try:
        df = pd.read_csv(file_obj, sep=";", decimal=".", dtype={"TagId": str})
    except Exception as e:
        result["error"] = f"Failed to read: {e}"
        return result

    required = {"TimeStamp", "TagId", "X", "Y"}
    missing = required - set(df.columns)
    if missing:
        result["error"] = f"Missing required columns: {missing}"
        return result

    result["rows_read"] = len(df)
    df["TagId"] = df["TagId"].astype(str)

    # Coordinates exported with a decimal comma (e.g. "1,5" on Dutch/European
    # locales) are read as strings by decimal="." — coerce them to float.
    # Unparseable values become NaN and are handled by the missing-X/Y checks.
    for c in ("X", "Y"):
        if df[c].dtype == object:
            df[c] = pd.to_numeric(
                df[c].astype(str).str.strip().str.replace(",", ".", regex=False),
                errors="coerce",
            )

    # Capture raw TagIds (before strip) for case-collision check
    result["raw_tagids"] = df["TagId"].unique().tolist()

    # ── Silent whitespace strip on TagId ──
    stripped = df["TagId"].str.strip()
    n_changed = int((stripped != df["TagId"]).sum())
    if n_changed > 0:
        result["whitespace_stripped"] = n_changed
        df["TagId"] = stripped

    # v5: record the stripped unique TagIds in this file
    result["stripped_tagids"] = sorted(df["TagId"].unique().tolist())

    # v6: sample raw TimeStamp strings for format detection. Do NOT parse
    # here — parsing happens after we've chosen a format.
    ts_col = df["TimeStamp"].dropna().astype(str)
    n_sample = min(50, len(ts_col))
    if n_sample > 0:
        # Sample deterministically from start + middle + end
        indices = np.linspace(0, len(ts_col) - 1, n_sample, dtype=int)
        result["timestamp_samples"] = ts_col.iloc[indices].tolist()

    result["df"] = df
    return result


def _detect_case_collisions(tagid_lists):
    """Detect TagIds that collide only under case-folding.

    Parameters
    ----------
    tagid_lists : list of list[str]
        One list per file (raw, pre-strip) — but we case-fold on the
        stripped version since whitespace was already handled.

    Returns
    -------
    list of dict
        Each dict: {'canonical': lowercase-stripped form,
                    'variants': list of actually-seen forms}
    """
    # Combine all variants across files, using stripped form
    all_variants = set()
    for lst in tagid_lists:
        for t in lst:
            all_variants.add(t.strip())

    # Group by case-folded form
    groups = {}
    for v in all_variants:
        key = v.lower()
        groups.setdefault(key, set()).add(v)

    collisions = []
    for key, variants in groups.items():
        if len(variants) > 1:
            collisions.append({
                "canonical": key,
                "variants": sorted(variants),
            })
    return collisions


def _detect_multi_tag_files(file_results):
    """v5/v6 item 5a: flag files containing more than one TagId.

    v6: downgraded from critical to medium. Confirmed legitimate exceptions
    exist (e.g. Tag_1.csv pattern in TrackLab exports).

    Returns
    -------
    list of dict: {'filename', 'tagids'}
    """
    multi_tag = []
    for r in file_results:
        if r["df"] is None:
            continue
        tids = r["stripped_tagids"]
        if len(tids) > 1:
            multi_tag.append({
                "filename": r["filename"],
                "tagids": tids,
            })
    return multi_tag


def _detect_tag_coverage_anomalies(raw_df, min_coverage_ratio=0.5):
    """v6 item 5b (reworked): per-tag total time coverage after combining.

    Under the real upload model, a single tag is often spread across
    multiple files. So coverage must be computed per TagId across the
    *combined* dataset, not per file.

    Parameters
    ----------
    raw_df : pd.DataFrame
        The combined, timestamp-parsed DataFrame. Must have a datetime
        column named '_ts' (added by the caller after format parsing).
    min_coverage_ratio : float

    Returns
    -------
    list of dict: {'tagid', 'coverage_sec', 'median_sec'}
    """
    if "_ts" not in raw_df.columns or len(raw_df) == 0:
        return []

    spans = {}
    for tag, g in raw_df.groupby("TagId"):
        ts = g["_ts"].dropna()
        if len(ts) >= 2:
            spans[tag] = (ts.max() - ts.min()).total_seconds()

    if len(spans) < 2:
        return []

    median_span = float(np.median(list(spans.values())))
    if median_span <= 0:
        return []

    threshold = median_span * min_coverage_ratio
    anomalies = [
        {"tagid": t, "coverage_sec": s, "median_sec": median_span}
        for t, s in spans.items() if s < threshold
    ]
    anomalies.sort(key=lambda a: a["coverage_sec"])
    return anomalies


def _detect_static_tags(raw_df, movement_threshold_m=0.5):
    """Find tags that never moved more than threshold across the recording.

    Returns list of dicts: {TagId, total_span_m}. A tag in this list is
    almost certainly unworn (sitting on a charger, shelf, etc.) and will
    produce misleading proximity episodes with whoever passes nearby.
    """
    static = []
    for tag, g in raw_df.groupby("TagId"):
        x = g["X"].dropna().values
        y = g["Y"].dropna().values
        if len(x) < 2:
            continue
        span_x = x.max() - x.min()
        span_y = y.max() - y.min()
        total_span = float(np.sqrt(span_x ** 2 + span_y ** 2))
        if total_span < movement_threshold_m:
            static.append({"TagId": tag, "total_span_m": round(total_span, 3)})
    return static


def _detect_magnitude_issues(raw_df, max_plausible_m=1000.0):
    """Check for coordinate magnitudes that suggest wrong-unit export.

    v5 refinement: returns fraction of rows affected so the panel can
    choose severity. >50% → critical (probably wrong units), 5–50% →
    medium (worth checking), <5% → informational (bounds filter catches).
    """
    n_total = len(raw_df)
    if n_total == 0:
        return {
            "n_huge_magnitude": 0, "pct_huge": 0.0,
            "n_zero_rows": 0,
            "x_range": (0.0, 0.0), "y_range": (0.0, 0.0),
        }

    x_abs = raw_df["X"].abs()
    y_abs = raw_df["Y"].abs()

    n_huge = int(((x_abs > max_plausible_m) | (y_abs > max_plausible_m)).sum())
    n_zero = int(((raw_df["X"] == 0) & (raw_df["Y"] == 0)).sum())

    return {
        "n_huge_magnitude": n_huge,
        "pct_huge": n_huge / n_total * 100,
        "n_zero_rows": n_zero,
        "x_range": (float(raw_df["X"].min()), float(raw_df["X"].max())),
        "y_range": (float(raw_df["Y"].min()), float(raw_df["Y"].max())),
    }


# ═════════════════════════════════════════════════════════════════════════════
# UPLOAD
# ═════════════════════════════════════════════════════════════════════════════

st.header("1. Upload Data")

uploaded_files = st.file_uploader(
    "Upload one or more CSV files (semicolon-delimited)",
    type=["csv"],
    accept_multiple_files=True,
    help="Expected columns: TimeStamp, TagId, X, Y. "
         "Use the X button next to each file to remove it.",
)

# ── v9: explicit "clear all data" control ──
# Placed near the uploader so it's discoverable, but inside a popover so
# a misclick can't destroy work. Only shown when there is data to clear.
if "raw_data" in st.session_state:
    with st.popover("🗑️ Clear all loaded data", help="Removes uploaded data and all downstream results. Use this if you want to start over with a different dataset."):
        st.warning(
            "This will delete the loaded data and ALL downstream results "
            "(configuration, subsets, pipeline outputs). This cannot be undone."
        )
        if st.button("Yes, clear everything", type="primary", key="_confirm_clear_all"):
            n_cleared = _clear_derived_state()
            for k in ("raw_data", "uploaded_filenames", "_upload_diagnostics",
                      "_upload_fingerprint", "_ts_format", "_ts_format_override",
                      "_ts_format_detection"):
                if k in st.session_state:
                    del st.session_state[k]
            st.success(
                f"Cleared loaded data and {n_cleared} downstream result(s). "
                "Upload new files to start over."
            )
            st.rerun()

# ── v4/v6/v9: file-change + format-change detection ──
# v6: fingerprint includes the active timestamp format so that changing
# the format setting also triggers a reprocess.
# v9: empty uploader is NEVER treated as removal intent. See module docstring.
#     Real removal is the explicit "Clear all data" popover above.
# Only a MANUAL override persists across uploads; the detected format is
# re-detected for every new set of files.
active_format = st.session_state.get("_ts_format_override", None)
current_fingerprint = (
    tuple(sorted((f.name, f.size) for f in uploaded_files)) if uploaded_files else (),
    active_format,
)

previous_fingerprint = st.session_state.get("_upload_fingerprint")
fingerprint_changed = current_fingerprint != previous_fingerprint

if fingerprint_changed and uploaded_files:
    # Real change: user uploaded new files, replaced files, or changed
    # the timestamp format while files are present. Clear derived state
    # (downstream must recompute) but do NOT wipe raw_data — the upload-
    # processing block below will overwrite it with a freshly-parsed
    # version.
    _clear_derived_state()
    st.session_state["_upload_fingerprint"] = current_fingerprint

elif fingerprint_changed and not uploaded_files:
    # Empty uploader. Could be:
    #   (a) first visit, no upload yet — `raw_data` not in session_state
    #   (b) page revisit after navigation — `raw_data` IS in session_state
    #       (Streamlit's file_uploader does not persist across multi-page
    #        navigation, so the widget shows empty even though the data
    #        is still loaded)
    #   (c) user clicked the X to remove the last file — indistinguishable
    #       from (b) at this point, so we do not act on it; the user must
    #       use the "Clear all data" popover to wipe explicitly
    # In all cases: do nothing. Sync the fingerprint to mark it observed.
    st.session_state["_upload_fingerprint"] = current_fingerprint

# ── Process uploaded files (only if present and fingerprint just changed,
#    OR if raw_data is missing despite files being present — defensive) ──
if uploaded_files and (fingerprint_changed or "raw_data" not in st.session_state):
    with st.spinner(f"Loading {len(uploaded_files)} file(s)..."):
        file_results = [_load_and_validate_file(f) for f in uploaded_files]

        # Any fatal errors? Report and stop for that file only.
        for fr in file_results:
            if fr["error"]:
                st.error(f"❌ {fr['filename']}: {fr['error']}")

        valid_results = [fr for fr in file_results if fr["df"] is not None]
        if not valid_results:
            st.error("No valid files loaded.")
            st.stop()

        # ── v6: timestamp format detection ──
        # Pool samples from all files and detect
        pooled_samples = []
        for fr in valid_results:
            pooled_samples.extend(fr["timestamp_samples"])
        detection = _detect_timestamp_format(pooled_samples)

        # If user has NOT overridden, use the detected best.
        # If the user had previously chosen an override, respect it even
        # across file changes (they may have good reason).
        if active_format is None:
            chosen_format = detection["best"]
        else:
            chosen_format = active_format

        # Parse and normalize timestamps using the chosen format.
        # The parse rewrites TimeStamp as DD-MM-YYYY so downstream code
        # (which uses dayfirst=True) sees dates correctly.
        parsed_results = []
        total_ts_failures = 0
        for fr in valid_results:
            df_parsed, n_fail = _parse_and_normalize_timestamps(
                fr["df"], chosen_format
            )
            fr["df"] = df_parsed
            fr["timestamp_failures"] = n_fail
            total_ts_failures += n_fail
            parsed_results.append(fr)

        # Combine
        combined = pd.concat([fr["df"] for fr in parsed_results], ignore_index=True)

        # Dedup + track per-file contribution
        before_dedup = len(combined)
        combined_deduped = combined.drop_duplicates(
            subset=["TimeStamp", "TagId"], keep="first"
        )
        n_dups = before_dedup - len(combined_deduped)

        # v4: per-file contribution check (item C)
        seen_keys = set()
        per_file_contribution = []
        for fr in parsed_results:
            df_i = fr["df"]
            keys = set(zip(df_i["TimeStamp"].astype(str), df_i["TagId"].astype(str)))
            new_keys = keys - seen_keys
            per_file_contribution.append({
                "filename": fr["filename"],
                "rows_in_file": fr["rows_read"],
                "new_rows": len(new_keys),
            })
            seen_keys |= keys

        # v6: checks adapted to N-files-per-tag model
        multi_tag_files = _detect_multi_tag_files(parsed_results)

        # Build a temporary parsed-timestamp column for coverage detection
        combined_for_coverage = combined_deduped.copy()
        _fast_ts = parse_ddmmyyyy_fast(combined_for_coverage["TimeStamp"])
        combined_for_coverage["_ts"] = _fast_ts if _fast_ts is not None else pd.to_datetime(
            combined_for_coverage["TimeStamp"], format="%d-%m-%Y %H:%M:%S.%f",
            errors="coerce",
        )
        coverage_anomalies = _detect_tag_coverage_anomalies(
            combined_for_coverage, min_coverage_ratio=0.5
        )

        # Case collisions across all files (item 6)
        case_collisions = _detect_case_collisions(
            [fr["raw_tagids"] for fr in parsed_results]
        )

        # Totals for whitespace
        total_whitespace_stripped = sum(
            fr["whitespace_stripped"] for fr in parsed_results
        )

        # Store
        st.session_state["raw_data"] = combined_deduped
        st.session_state["uploaded_filenames"] = [
            fr["filename"] for fr in parsed_results
        ]
        st.session_state["_ts_format"] = chosen_format
        st.session_state["_ts_format_detection"] = detection
        st.session_state["_upload_diagnostics"] = {
            "n_dups": n_dups,
            "per_file_contribution": per_file_contribution,
            "multi_tag_files": multi_tag_files,
            "coverage_anomalies": coverage_anomalies,
            "case_collisions": case_collisions,
            "total_whitespace_stripped": total_whitespace_stripped,
            "total_ts_failures": total_ts_failures,
            "chosen_format": chosen_format,
            "detected_format": detection["best"],
            "format_ambiguous": detection["ambiguous"],
            "format_scores": detection["scores"],
        }

    raw = st.session_state["raw_data"]
    st.success(
        f"Loaded {len(raw):,} rows from {len(parsed_results)} file(s) — "
        f"**{raw['TagId'].nunique()} tags** · "
        f"timestamp format: **{chosen_format}**"
    )

# v6: format override control — shown whenever data is loaded.
# Placed immediately after the success message so it's visible but
# not in the user's way. Changing this triggers a reparse on next run.
if "raw_data" in st.session_state and "_upload_diagnostics" in st.session_state:
    _diag = st.session_state["_upload_diagnostics"]
    with st.expander(
        f"📅 Timestamp format: **{_diag['chosen_format']}** "
        + ("(auto-detected)" if st.session_state.get("_ts_format_override") is None
           else "(manual override)"),
        expanded=_diag.get("format_ambiguous", False),
    ):
        if _diag.get("format_ambiguous"):
            st.warning(
                "⚠️ Multiple formats parse your timestamps successfully — "
                "the correct one is ambiguous from the data alone. "
                "Verify that dates below look correct; if not, override the "
                "format here."
            )

        # Show detection scores for transparency
        scores_txt = " · ".join(
            f"{k}: {v*100:.0f}%" for k, v in _diag["format_scores"].items()
        )
        st.caption(f"Detection scores — {scores_txt}")

        # Show a few sample parsed timestamps for sanity check
        sample_ts = pd.to_datetime(
            st.session_state["raw_data"]["TimeStamp"].head(3),
            format="%d-%m-%Y %H:%M:%S.%f", errors="coerce",
        )
        st.caption(
            "First 3 parsed timestamps: "
            + ", ".join(str(t) for t in sample_ts)
        )

        override = st.radio(
            "Override format:",
            options=["Auto-detect"] + list(TIMESTAMP_FORMATS.keys()),
            index=0 if st.session_state.get("_ts_format_override") is None
                  else list(TIMESTAMP_FORMATS.keys()).index(
                      st.session_state["_ts_format_override"]
                  ) + 1,
            horizontal=True,
            key="_ts_format_radio",
        )
        new_override = None if override == "Auto-detect" else override
        if new_override != st.session_state.get("_ts_format_override"):
            st.session_state["_ts_format_override"] = new_override
            st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# v4 — DATA QUALITY WARNINGS PANEL
# Displayed between upload and data overview. Auto-expands if any warnings.
# ═════════════════════════════════════════════════════════════════════════════

if "raw_data" in st.session_state and "_upload_diagnostics" in st.session_state:
    raw = st.session_state["raw_data"]
    diag = st.session_state["_upload_diagnostics"]

    # Content-quality checks that run on the combined data
    static_tags = _detect_static_tags(raw, movement_threshold_m=0.5)
    mag_info = _detect_magnitude_issues(raw)

    # Build the list of warnings to display, grouped by severity.
    critical = []   # something is probably wrong
    medium = []     # worth investigating
    informational = []  # FYI, silent fixes applied

    # CRITICAL: case-collision TagIds
    for c in diag["case_collisions"]:
        critical.append(
            f"**Case-collision TagIds:** variants {c['variants']} "
            f"differ only in capitalization. If these are the same tag "
            f"with a typo, rows are currently being treated as **separate tags**. "
            f"Check the source CSV."
        )

    # CRITICAL: timestamp parse failures
    if diag["total_ts_failures"] > 0:
        critical.append(
            f"**Timestamp parse failures:** {diag['total_ts_failures']:,} rows "
            f"had unparseable TimeStamp values (could not be read with the "
            f"detected format). "
            "These rows will be silently dropped downstream."
        )

    # v6 item 5a: multi-TagId files (MEDIUM — confirmed legitimate exceptions exist)
    for m in diag["multi_tag_files"]:
        tag_list = ", ".join(str(t) for t in m["tagids"][:8])
        extra = f" (+{len(m['tagids']) - 8} more)" if len(m["tagids"]) > 8 else ""
        medium.append(
            f"**Multi-tag file:** `{m['filename']}` contains "
            f"{len(m['tagids'])} different TagIds: {tag_list}{extra}. "
            "Most TrackLab exports contain one tag per file. Confirm this "
            "is intentional (some export patterns, e.g. Tag_1.csv, may "
            "legitimately bundle multiple tags)."
        )

    # v5: magnitude issues split by severity
    mag_pct = mag_info["pct_huge"]
    if mag_info["n_huge_magnitude"] > 0:
        range_str = (
            f"X∈[{mag_info['x_range'][0]:.1f}, {mag_info['x_range'][1]:.1f}], "
            f"Y∈[{mag_info['y_range'][0]:.1f}, {mag_info['y_range'][1]:.1f}]"
        )
        if mag_pct > 50:
            critical.append(
                f"**Coordinate units likely wrong:** {mag_info['n_huge_magnitude']:,} "
                f"rows ({mag_pct:.1f}% of data) have |X| or |Y| > 1000. "
                f"Observed range: {range_str}. The pipeline expects meters — "
                "your data may be in millimeters or a different unit entirely. "
                "If uncorrected, proximity thresholds will be meaningless."
            )
        elif mag_pct >= 5:
            medium.append(
                f"**Large-magnitude coordinates:** {mag_info['n_huge_magnitude']:,} "
                f"rows ({mag_pct:.1f}%) have |X| or |Y| > 1000. "
                f"Range: {range_str}. Check whether a subset of your data is "
                "in different units than the rest."
            )
        else:
            informational.append(
                f"**Coordinate outliers:** {mag_info['n_huge_magnitude']:,} rows "
                f"({mag_pct:.2f}%) have |X| or |Y| > 1000. "
                "The spatial bounds filter on page 2 will exclude these."
            )

    # v6 item 5b (reworked): per-tag coverage anomalies
    if diag["coverage_anomalies"]:
        median_sec = diag["coverage_anomalies"][0]["median_sec"]
        median_min = median_sec / 60
        lines = []
        for a in diag["coverage_anomalies"][:5]:
            span_min = a["coverage_sec"] / 60
            pct = a["coverage_sec"] / median_sec * 100 if median_sec > 0 else 0
            lines.append(
                f"- Tag `{a['tagid']}`: "
                f"{span_min:.1f} min ({pct:.0f}% of median)"
            )
        extra = (
            f"\n- …and {len(diag['coverage_anomalies']) - 5} more"
            if len(diag["coverage_anomalies"]) > 5 else ""
        )
        medium.append(
            f"**Short-coverage tags:** {len(diag['coverage_anomalies'])} tag(s) "
            f"have total time coverage less than 50% of the median tag "
            f"({median_min:.1f} min). These tags may have been offline for "
            "most of the recording or mis-exported.\n\n"
            + "\n".join(lines) + extra
        )

    # MEDIUM: static tags (probably unworn)
    if len(static_tags) > 0:
        tag_summary = ", ".join(
            f"{s['TagId']} (span: {s['total_span_m']}m)"
            for s in static_tags[:5]
        )
        extra = f" +{len(static_tags) - 5} more" if len(static_tags) > 5 else ""
        medium.append(
            f"**Static tags:** {len(static_tags)} tag(s) moved < 0.5m across the "
            f"entire recording. These tags were likely not worn (left on a "
            f"charger or shelf) and will produce misleading proximity episodes. "
            f"Consider excluding on page 2. Tags: {tag_summary}{extra}"
        )

    # MEDIUM: all-zero position rows
    if mag_info["n_zero_rows"] > 0:
        medium.append(
            f"**All-zero coordinate rows:** {mag_info['n_zero_rows']:,} rows have "
            "X=0 AND Y=0. This often indicates tracking errors rather than "
            "actual position at the origin."
        )

    # INFORMATIONAL: duplicate file contribution
    for pf in diag["per_file_contribution"]:
        if (pf["rows_in_file"] > 0 and pf["new_rows"] == 0
                and pf is not diag["per_file_contribution"][0]):
            informational.append(
                f"**No new data from `{pf['filename']}`:** all "
                f"{pf['rows_in_file']:,} rows in this file duplicate rows "
                "already present in earlier-uploaded files. You may have "
                "uploaded the same file twice."
            )

    # INFORMATIONAL: whitespace stripped
    if diag["total_whitespace_stripped"] > 0:
        informational.append(
            f"**Whitespace auto-stripped:** {diag['total_whitespace_stripped']:,} "
            "TagId values had leading or trailing whitespace (silently removed). "
            "This is usually a CSV-export artifact and safe to ignore."
        )

    # INFORMATIONAL: deduplication
    if diag["n_dups"] > 0:
        informational.append(
            f"**Duplicate rows removed:** {diag['n_dups']:,} duplicate "
            "(TimeStamp, TagId) rows dropped during combination."
        )

    # Render the panel
    n_warnings = len(critical) + len(medium) + len(informational)
    if n_warnings > 0:
        # Auto-expand if any critical or medium warnings exist
        auto_expand = len(critical) > 0 or len(medium) > 0
        icon = "🚨" if critical else ("⚠️" if medium else "ℹ️")
        label = f"{icon} Data quality warnings ({n_warnings})"

        with st.expander(label, expanded=auto_expand):
            if critical:
                st.markdown("##### 🚨 Critical")
                for w in critical:
                    st.error(w)
            if medium:
                st.markdown("##### ⚠️ Worth investigating")
                for w in medium:
                    st.warning(w)
            if informational:
                st.markdown("##### ℹ️ Informational")
                for w in informational:
                    st.info(w)
    else:
        st.success("✅ No data quality issues detected at upload.")

# ═════════════════════════════════════════════════════════════════════════════
# DATA OVERVIEW (unchanged from v3)
# ═════════════════════════════════════════════════════════════════════════════

if "raw_data" in st.session_state:
    raw = st.session_state["raw_data"]

    st.header("2. Data Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total rows", f"{len(raw):,}")
    col2.metric("Tags", raw["TagId"].nunique())

    ts = parsed_timestamps(raw)
    n_dates = ts.dt.normalize().nunique()
    col3.metric("Recording days", n_dates)
    col4.metric("Time span", f"{(ts.max() - ts.min())}")

    # ── Multi-date advisory (v10) ──
    # Surfaces the tool's per-date semantics so users with multi-day data
    # know what they're getting. The pipeline already analyses each date
    # as an independent session (episode detection, distance stats, and
    # metrics are all per-date). Without this notice, a user with 14 days
    # of livestock data could reasonably assume the tool aggregates across
    # the study period — it doesn't, and the resulting CSVs would be
    # misinterpreted. Wording is descriptive of present behaviour and
    # does not commit to or rule out future aggregated multi-day support.
    if n_dates > 1:
        date_list = sorted(pd.Timestamp(d).date() for d in ts.dt.normalize().dropna().unique())
        date_list_str = ", ".join(d.strftime("%d-%m-%Y") for d in date_list[:6])
        if len(date_list) > 6:
            date_list_str += f" (+{len(date_list) - 6} more)"
        st.warning(
            f"**Multi-date data detected: {n_dates} recording dates "
            f"({date_list_str}).**\n\n"
            "Each date will be analysed as a separate session. "
            "Episodes and statistics are reported per date — they do not "
            "span date boundaries. If you want aggregated multi-day "
            "analysis, you'll need to combine results manually after running."
        )

    with st.expander("Raw data sample", expanded=False):
        st.dataframe(raw.head(100), use_container_width=True)

    with st.expander("Spatial overview", expanded=True):
        fig = px.scatter(
            raw.sample(min(5000, len(raw)), random_state=42),
            x="X", y="Y", color="TagId",
            opacity=0.3,
            title="Position scatter (sampled)",
            height=500, render_mode='svg',
        )
        fig.update_yaxes(scaleanchor="x", scaleratio=1)
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3))
        st.plotly_chart(fig, use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────
    # DATA AVAILABILITY & QUALITY (unchanged from v3)
    # ─────────────────────────────────────────────────────────────────────────

    st.header("3. Data Availability & Quality")
    st.caption(
        "Per-tag inspection of the raw data. Use this to spot tags with "
        "poor coverage, long dropouts, or timing irregularities before "
        "configuring the pipeline."
    )

    quality_df = cached_for_upload(
        "quality_stats", raw, 3.0,
        lambda: _compute_tag_quality_stats(raw, gap_multiplier=3.0),
    )

    display_quality = quality_df.copy()
    display_quality["first_timestamp"] = display_quality["first_timestamp"].dt.strftime(
        "%d-%m-%Y %H:%M:%S"
    )
    display_quality["last_timestamp"] = display_quality["last_timestamp"].dt.strftime(
        "%d-%m-%Y %H:%M:%S"
    )
    display_quality = display_quality.rename(columns={
        "TagId": "Tag",
        "samples": "Samples",
        "nan_pct": "NaN %",
        "median_interval_ms": "Median Δt (ms)",
        "gap_count": "Gaps (>3× median)",
        "first_timestamp": "First sample",
        "last_timestamp": "Last sample",
    })

    st.markdown("**Per-tag quality summary**")
    st.caption(
        "Gaps = intervals between consecutive samples (within the same "
        "recording date) longer than 3× that tag's own median interval. "
        "Gaps across recording dates are not counted — each date is "
        "treated as a separate session. A high gap count means the tag "
        "was intermittently offline during a recording session."
    )

    styled = (
        display_quality.style
        .background_gradient(subset=["NaN %"], cmap="Reds", vmin=0, vmax=50)
        .background_gradient(subset=["Gaps (>3× median)"], cmap="Oranges")
        .format({"NaN %": "{:.2f}", "Median Δt (ms)": "{:.1f}"})
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    high_nan_tags = quality_df[quality_df["nan_pct"] > 10]["TagId"].tolist()
    high_gap_tags = quality_df[quality_df["gap_count"] > 10]["TagId"].tolist()

    if len(high_nan_tags) > 0:
        st.warning(
            f"⚠️ {len(high_nan_tags)} tag(s) have >10% NaN positions: "
            f"{', '.join(str(t) for t in high_nan_tags[:10])}"
            + (f" (+{len(high_nan_tags)-10} more)" if len(high_nan_tags) > 10 else "")
        )
    if len(high_gap_tags) > 0:
        st.warning(
            f"⚠️ {len(high_gap_tags)} tag(s) have >10 gaps: "
            f"{', '.join(str(t) for t in high_gap_tags[:10])}"
            + (f" (+{len(high_gap_tags)-10} more)" if len(high_gap_tags) > 10 else "")
        )

    # ── Availability timeline ──
    st.markdown("**Per-tag availability timeline**")

    tl_col1, tl_col2 = st.columns([1, 3])
    with tl_col1:
        bin_sec = st.selectbox(
            "Bin size",
            options=[30, 60, 120, 300],
            index=1,
            format_func=lambda s: f"{s}s" if s < 60 else f"{s // 60} min",
            help="Time resolution of the availability heatmap. "
                 "Smaller = more detail but noisier.",
            key="availability_bin_size",
        )
    with tl_col2:
        st.caption(
            "Each row is a tag. Color density = fraction of expected samples "
            "present in that time bin (relative to the tag's own median "
            "sampling interval). **Blank cells** = no samples at all "
            "(tag absent or fully offline). **Dark cells** = tag present but "
            "low packet density."
        )

    avail = cached_for_upload(
        "availability", raw, bin_sec,
        lambda: _compute_availability_matrix(raw, bin_seconds=bin_sec),
    )
    matrix = avail["matrix"]

    if matrix.empty:
        st.info("No data to display in timeline.")
    else:
        y_labels = [str(v) for v in matrix.index]
        x_labels = [str(v) for v in matrix.columns]

        fig_heat = go.Figure(data=go.Heatmap(
            z=matrix.values,
            x=x_labels,
            y=y_labels,
            colorscale="Viridis",
            zmin=0, zmax=1,
            colorbar=dict(title="Density", tickvals=[0, 0.5, 1.0]),
            hovertemplate="Tag: %{y}<br>Time: %{x}<br>Density: %{z:.2f}<extra></extra>",
        ))

        n_rows = len(y_labels)
        height = max(200, min(800, 25 * n_rows + 100))

        n_cols = len(x_labels)
        tick_stride = max(1, n_cols // 24)
        tick_positions = list(range(0, n_cols, tick_stride))
        tick_labels = [x_labels[i] for i in tick_positions]

        fig_heat.update_layout(
            height=height,
            xaxis=dict(
                type="category",
                title="Time of day",
                tickmode="array",
                tickvals=tick_labels,
                ticktext=tick_labels,
                tickangle=-45,
            ),
            yaxis=dict(
                type="category",
                title="Tag" if avail["single_day"] else "Tag · Date",
                autorange="reversed",
                categoryorder="array",
                categoryarray=y_labels,
            ),
            margin=dict(l=80, r=20, t=30, b=80),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        st.caption(
            f"Timeline shows {len(matrix.index)} row(s) across "
            f"{len(matrix.columns)} bins of {bin_sec}s each. "
            "Density values are clipped to [0, 1]."
        )

    st.markdown("---")

    # ═════════════════════════════════════════════════════════════════════════
    # 4. EXPORT PREFERENCES (v7)
    # ═════════════════════════════════════════════════════════════════════════
    # Output-format choice. Strictly speaking page 1 was meant to be parameter-
    # free, but this is an *output* preference (what gets written when results
    # download), not a *processing* parameter — so the spirit of the rule
    # holds. Put here so it's set once at session start; page 3's bundle
    # download reads st.session_state["export_format_pref"].
    st.header("4. Export Preferences")
    st.caption(
        "Choose which loader script to include with the results bundle. "
        "All exports are CSV — this only controls which `load_results.*` "
        "helper script is bundled. You can change this later if needed."
    )

    _fmt_options = {
        "Both (Python + R)": "both",
        "Python (pandas)":   "python",
        "R (readr / tidyverse)": "r",
    }
    _fmt_labels = list(_fmt_options.keys())

    # Default = "both" so neither audience is privileged. Persist across reruns.
    _current_pref = st.session_state.get("export_format_pref", "both")
    _default_index = next(
        (i for i, lbl in enumerate(_fmt_labels) if _fmt_options[lbl] == _current_pref),
        0,
    )

    _chosen_label = st.radio(
        "Bundle loader script",
        _fmt_labels,
        index=_default_index,
        horizontal=True,
        help=(
            "**Both**: includes both `load_results.py` and `load_results.R`. "
            "Recommended if you don't know which language users prefer.\n\n"
            "**Python**: includes only `load_results.py` (uses pandas).\n\n"
            "**R**: includes only `load_results.R` (uses readr + jsonlite). "
            "CSVs are identical in all three cases."
        ),
        key="export_format_radio",
    )
    st.session_state["export_format_pref"] = _fmt_options[_chosen_label]

    st.markdown("---")
    st.success(
        "✅ Data loaded. Go to **Clean & Configure** in the sidebar "
        "to set processing parameters."
    )

else:
    st.info("👆 Upload CSV files to get started.")
