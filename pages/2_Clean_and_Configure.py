"""
Page 2: Clean & Configure (v7)

2026-10-18 (UI cleanup, no result changes):
- Removed the "Teacher / adult tags" selector. It belonged to the out-of-seat
  pipeline (pages removed 2026-09-19); nothing read config['adult_tags'].
- "Position error (m)" removed from section 1. Its only use was the margin
  around an auto-detected basket dead zone, so that margin is now its own
  input inside the auto-detect expander ("Margin around detected zone (m)",
  default 0.3 m, same proposed zone as before at the default). It is an
  entry field like the other auto-detect inputs (not remembered, not in config).
- config no longer contains 'adult_tags' or 'position_error'.
Previous version: _removed_backup/before_ui_cleanup/pages/.

2026-10-17 (time within distance): switched to backend social_analysis_v13 and
streamlit_subsets_v6 (v13 adds the within-distance fraction; every existing
result is unchanged). Previous version of this file:
_removed_backup/before_within_distance/pages/. See FILE_DEPENDENCIES_v1.md.

2026-10-17 (pair proximity): switched to backend social_analysis_v12 and
streamlit_subsets_v5 (v12 adds proximity relative to observed time; every
existing result is unchanged). Previous version of this file:
_removed_backup/before_dyad_proximity/pages/. See FILE_DEPENDENCIES_v1.md.

2026-10-17 (settings memory): Streamlit forgets a page's widget values when
you switch to another page, so returning to page 2 used to reset every
setting to its default — and page 2 then saved those defaults as the
configuration page 3 uses. Every setting now has a key, gets its value
from st.session_state['_page2_settings'] (or its default) before the widget
is drawn, and is written back there at the end of each run. Page 1 deletes
_page2_settings, config, dead zones and subjects when new data is loaded,
so a new dataset always starts from the defaults.
Previous version: _removed_backup/before_settings_memory/pages/.
2026-10-17 (speed): facts about the uploaded data (tag and day counts, tag
list, coordinate quantiles, samples per tag, dead-zone preview, sampling
intervals) are computed once per upload instead of on every click. New
timestep check: warns when the timestep is much finer than the tags'
median sampling interval and offers a 'Use X ms' button. The velocity
advisor runs on its own only when the timestep fits the data and the
recording is small; otherwise it waits for a 'Compute' click.
Previous version: _removed_backup/before_page2_speed/pages/.
2026-10-17: the velocity-advisor histogram is counted on the computer and
only the 80 bar counts are sent to the browser (fixes MessageSizeError on
large recordings). Previous version: _removed_backup/before_histogram_fix/pages/.
2026-10-07: switched to backend social_analysis_v11 and streamlit_subsets_v4
(memory release, identical results). Previous version of this file:
_removed_backup/before_v11/pages/. See FILE_DEPENDENCIES_v1.md.
The velocity advisor now calls compute_velocity_distribution_from_raw
(same result as resample -> reindex -> compute_velocity_distribution,
computed one date at a time).

Purpose: set all data cleaning and processing parameters.

v7 changes (bugfix pass — see bugs_and_issues_v2.txt):
- D3 fix: velocity advisor "Apply X m/s" button now writes the
  unrounded recommendation to the max_velocity input. The input's
  step was changed from 0.5 → 0.1 so the displayed value and the
  applied value match. Previously, clicking "Apply 5.73 m/s" wrote
  5.5 silently.
- Display-precision consistency: max_velocity input now formats to
  2 decimals so the histogram's "current:" annotation, the
  recommendation text, and the input itself all use the same
  precision.
- #3 fix: section 3 manual spatial bounds now validate that
  x_min < x_max and y_min < y_max. On error, the bounds are
  rejected (manual_x_bounds / manual_y_bounds set to None so the
  pipeline falls back to auto-detect) and a clear error is shown.
  Previously, inverted bounds silently rejected every point at
  pipeline run time.
- #4 fix: section 4 manual dead zone "Add" button now validates
  x_min < x_max and y_min < y_max before appending. Invalid input
  shows an error and does not modify session state. Previously,
  inverted dead zones were appended silently and either matched
  no points or behaved unpredictably depending on apply_dead_zones
  masking semantics.
- #5 fix: manual dead zone "Add" now also checks for duplicate
  labels (matching the basket auto-add behaviour at line ~1016).
  Adding two zones with the same custom label now shows an error;
  previously they were appended without complaint and were
  indistinguishable in the list.
- #6 fix: dead zone list removal no longer calls list.pop(i) from
  inside enumerate(). The index-to-remove is captured during the
  loop and applied after, eliminating the same fragile pattern
  A10 flagged for the subset builder.

v6 changes (bugfix pass — see bugs_and_issues_v1.txt):
- A1 fix: section 5 tag-selection error states now write
  `selected_tags = []` (empty list) as an explicit error sentinel,
  distinct from `None` (which means "use all tags"). Page 3 v5 reads
  this and blocks the run. Previously, an error in tag selection
  silently fell through to "use all tags" — the opposite of what
  the user requested.
- A4 fix: velocity advisor now reads `selected_tags` from the
  previously-saved config (one-rerun lag) instead of hardcoding
  None. First render after upload still uses None (no config yet).
- A5 fix: critical_distances parse error no longer saves a partial
  list. On parse_error, `critical_distances` is set back to a safe
  default (the previously-saved value if any, else [1.0]) so the
  config snapshot doesn't capture half-typed garbage.
- A6 fix: dead zone impact preview now respects `selected_tags`
  from the previously-saved config (one-rerun lag). First render
  uses full raw data; on rerun the preview matches the actual
  pipeline scope.

v5 changes:
- BACKEND: bumped import from social_analysis_v8 to social_analysis_v9.
  v9 is purely additive over v8 (adds `build_export_bundle` for page 3);
  all v8 functions used here (`dead_zone_impact`, `resample_data`,
  `reindex_data`, `compute_velocity_distribution`) are unchanged.
  The bump is for consistency only — page 3 v4 imports from v9 and
  running two backend versions in the same Streamlit session is a
  footgun. No logic change here.

v4 changes:
- NEW: Optional rolling-median smoothing controls in section 1. Off by
  default. When enabled, runs inside filter_data between out-of-bounds
  rejection and velocity calculation. Window specified in seconds, with
  live conversion to odd sample count shown to the user.
- NEW: Velocity advisor — expander beneath max_velocity input that shows
  the empirical velocity distribution and a percentile-based threshold
  recommendation. Single-click "Apply X m/s" button writes to the
  max_velocity input via session state. Recomputes live when bounds,
  smoothing, selected tags, or the percentile knob change.
- BACKEND: now imports from social_analysis_v8 (for apply_smoothing,
  compute_velocity_distribution; new optional kwargs on filter_data /
  process_all). v8 keeps v7 signatures backward-compatible.

Note on advisor bounds: the advisor uses auto-detected bounds (data
quantiles) regardless of section 3's bounds mode. If the user later
selects manual bounds, the advisor's recommendation is computed against
slightly different bounds than filter_data will eventually use. The
discrepancy is small (typically <1m at the edges) and the recommendation
is approximate by nature; flagged in the advisor's caption.

v3 changes:
- Tag selection (section 5) reworked: per-tag rows now show an availability
  timeline strip alongside an exclusion checkbox. Rationale: reveals temporal
  patterns of data loss that the aggregate NaN% obscures (e.g., distinguishing
  uniformly-bad tags from intermittently-bad tags at a glance).
- Bin resolution is inherited from page 1's `availability_bin_size` session
  key — no separate selector here, to avoid two controls that can disagree.
- The `_compute_availability_matrix` function is duplicated from page 1
  (Streamlit page filenames make direct import awkward). If a shared utils
  module is introduced later, this duplication should be collapsed.

NOTE on scope: the tag-selection widget is whole-tag exclusion only.
Time-bounded per-tag exclusion windows (originally Group C in the
development plan) are deferred to future work; v3 consolidates the
existing whole-tag exclusion with the availability timeline rather
than introducing time-range inputs.

v2 changes (merged from two forked lineages):
- NEW: Multiple critical distances — comma-separated list for sensitivity sweep
- NEW: Stationary time parameters (displacement threshold, window duration)
- NEW: Dead zone impact preview on raw data (before running pipeline)
- PRESERVED: Multi-tag subject mapping (from v1)
- PRESERVED: Basket auto-detection (from v1)

Contents:
1. Processing parameters (resampling, filtering, smoothing, advisor)
2. Stationary time estimation parameters
3. Spatial bounds
4. Dead zones (with auto-detect + impact preview)
5. Tag selection (with per-tag availability timeline)
6. Subject mapping (multi-tag)

Upstream: requires st.session_state["raw_data"] from page 1.
Downstream: page 3 reads st.session_state["config"].
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from streamlit_subsets_v6 import parsed_timestamps, cached_for_upload
from social_analysis_v13 import (
    dead_zone_impact,
    compute_velocity_distribution_from_raw,
)


# ─────────────────────────────────────────────────────────────────────────────
# AVAILABILITY MATRIX HELPER
#
# Duplicated from 1_Upload_Inspect_v7.py because Streamlit page filenames
# (leading digit) make direct import awkward. Keep these two copies in sync
# until a shared utils module is introduced.
# ─────────────────────────────────────────────────────────────────────────────

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


def _per_tag_strip(matrix, tag_date_pairs, tag, height=60):
    """Build a compact heatmap strip for a single tag (all its date rows)."""
    tag_rows = [(i, d) for i, (t, d) in enumerate(tag_date_pairs) if t == tag]
    if not tag_rows:
        return None

    row_indices = [i for i, _ in tag_rows]
    submatrix = matrix.iloc[row_indices]

    y_labels = [str(matrix.index[i]) for i in row_indices]
    x_labels = [str(c) for c in matrix.columns]

    fig = go.Figure(data=go.Heatmap(
        z=submatrix.values,
        x=x_labels,
        y=y_labels,
        colorscale="Viridis",
        zmin=0, zmax=1,
        showscale=False,
        hovertemplate="Time: %{x}<br>Density: %{z:.2f}<extra></extra>",
    ))

    n_cols = len(x_labels)
    tick_stride = max(1, n_cols // 12)
    tick_positions = list(range(0, n_cols, tick_stride))

    fig.update_layout(
        height=max(height, 30 * len(row_indices) + 30),
        margin=dict(l=0, r=0, t=5, b=20),
        xaxis=dict(
            tickmode="array",
            tickvals=[x_labels[i] for i in tick_positions],
            ticktext=[x_labels[i] for i in tick_positions],
            tickfont=dict(size=9),
        ),
        yaxis=dict(
            tickfont=dict(size=10),
            showticklabels=len(row_indices) > 1,  # hide "Tag" label when single row
        ),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# VELOCITY ADVISOR HELPERS
#
# The advisor needs the post-out-of-bounds, post-smoothing velocity
# distribution that filter_data will threshold against. We replicate
# the first three steps of the pipeline (resample → reindex → partial
# filter) here, then call compute_velocity_distribution.
#
# The result is cached because:
#   1. The resample + reindex steps are non-trivial on large datasets.
#   2. Streamlit reruns the whole script on any input change, so without
#      caching, every keystroke on the percentile knob would re-resample.
#
# Cache key includes everything that affects the distribution, including
# the user's tag selection. max_velocity is intentionally NOT in the key
# (the recommendation must not depend on the value it's recommending).
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _advisor_compute_distribution(raw_df_id, timestep_ms, max_interpolation,
                                  max_gap_factor,
                                  x_bounds, y_bounds,
                                  smoothing_enabled, smoothing_window_sec,
                                  selected_tags_tuple):
    """Run resample → reindex → partial-filter and return velocity dist.

    Parameters
    ----------
    raw_df_id : int
        id() of the raw_df object used to invalidate the cache when
        a new dataset is uploaded. The actual DataFrame is read from
        st.session_state because raw DataFrames are unhashable.
    selected_tags_tuple : tuple of str or None
        Tag IDs to include. None means all tags. Tuple (not list) for
        cache-key hashability.
    Returns
    -------
    velocities : np.ndarray
        Aggregated finite velocities, one number per (Date,TagId,sample).
    per_tag : dict[str, np.ndarray]
        Per-tag finite velocity arrays.
    """
    raw = st.session_state["raw_data"]

    selected = list(selected_tags_tuple) if selected_tags_tuple is not None else None

    # v11 backend: resample -> reindex -> velocity distribution, one date at
    # a time (same result as running the three steps on the whole recording).
    velocities, per_tag = compute_velocity_distribution_from_raw(
        raw,
        timestep_ms=timestep_ms,
        max_interpolation=max_interpolation,
        x_bounds=x_bounds,
        y_bounds=y_bounds,
        max_gap_factor=max_gap_factor,
        smoothing_enabled=smoothing_enabled,
        smoothing_window_sec=smoothing_window_sec,
        selected_tags=selected,
    )
    return velocities, per_tag


def _advisor_auto_bounds(raw_df, margin=1.0):
    """Compute auto-detected bounds for the advisor.

    Mirrors the auto-bounds logic that section 3 will eventually use
    (data quantiles ± margin). Used by the advisor regardless of whether
    the user has set bounds in section 3, because section 3 is rendered
    after section 1 in the page flow.
    """
    x_min = float(raw_df["X"].quantile(0.001)) - margin
    x_max = float(raw_df["X"].quantile(0.999)) + margin
    y_min = float(raw_df["Y"].quantile(0.001)) - margin
    y_max = float(raw_df["Y"].quantile(0.999)) + margin
    return (x_min, x_max), (y_min, y_max)


# ─────────────────────────────────────────────────────────────────────────────
# BASKET AUTO-DETECTION (3-step gap-based method)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# 2026-10-17 (speed): PER-UPLOAD FACTS
#
# Streamlit reruns this page on every click. On a large recording (46 tags x
# 8 days, ~15 M rows) the facts below cost ~4 s per click, and the dead-zone
# preview ~27 s per click. They only change when new data is uploaded (or,
# for the preview, when dead zones / tag selection change), so they are
# computed once and kept with cached_for_upload. Each value is computed with
# the same expression as before, so it is identical.
# ─────────────────────────────────────────────────────────────────────────────

# Above this many time slots (estimated rows after resampling) the velocity
# advisor waits for a click instead of running on its own. A 25-tag, 2-hour
# classroom recording at 100 ms is ~1.8 M slots.
_ADVISOR_AUTO_MAX_ROWS = 5_000_000


def _page2_upload_facts(raw_df, ts_parsed):
    """Counts, tag list, quantiles and samples per tag for the current upload."""
    return {
        "n_tags": raw_df["TagId"].nunique(),
        # same count as ts.dt.date.nunique(), without building 15 M date objects
        "n_days": ts_parsed.dt.normalize().nunique(),
        "all_tags": sorted(raw_df["TagId"].unique(), key=str),
        "x_q001": raw_df["X"].quantile(0.001),
        "x_q999": raw_df["X"].quantile(0.999),
        "y_q001": raw_df["Y"].quantile(0.001),
        "y_q999": raw_df["Y"].quantile(0.999),
        "tag_samples": raw_df.groupby("TagId").agg(samples=("X", "size")).to_dict("index"),
    }


def _page2_sampling_facts(raw_df, ts_parsed):
    """Per-tag median sampling interval (page 1's definition) and the
    recording span of every (tag, date).

    Page 1's 'Median Δt': per (tag, date) the median interval between
    consecutive samples (dates with < 3 samples or a median <= 0 skipped),
    then per tag the median of those per-date medians.
    """
    t_all = ts_parsed.to_numpy()
    valid = ~np.isnat(t_all)
    tag_codes, tag_names = pd.factorize(raw_df["TagId"].to_numpy()[valid])
    t = t_all[valid]
    day = t.astype("datetime64[D]")
    order = np.lexsort((t, day, tag_codes))
    t, day, tag_codes = t[order], day[order], tag_codes[order]
    if len(t) == 0:
        return {"tag_median_s": {}, "spans": []}
    new_group = np.ones(len(t), dtype=bool)
    new_group[1:] = (tag_codes[1:] != tag_codes[:-1]) | (day[1:] != day[:-1])
    starts = np.flatnonzero(new_group)
    ends = np.concatenate((starts[1:], [len(t)]))
    gaps_s = np.diff(t).astype("timedelta64[ns]").astype(np.int64) / 1e9
    per_tag = {}
    spans = []
    for a, b in zip(starts, ends):
        tag = tag_names[tag_codes[a]]
        spans.append((tag, float((t[b - 1] - t[a]) / np.timedelta64(1, "s"))))
        if b - a < 3:
            continue
        med = float(np.median(gaps_s[a:b - 1]))
        if med > 0:
            per_tag.setdefault(tag, []).append(med)
    return {
        "tag_median_s": {tag: float(np.median(v)) for tag, v in per_tag.items()},
        "spans": spans,
    }


def _estimated_slots(spans, timestep_ms, tags=None):
    """Rows resampling will create: one per timestep across each (tag, date) span."""
    keep = None if tags is None else set(str(t) for t in tags)
    return int(sum(int(span_s * 1000 // timestep_ms) + 1
                   for tag, span_s in spans if keep is None or str(tag) in keep))


def find_dropoff_pickup_positions(raw_df, gap_threshold_sec=30):
    """Find where tags disappear and reappear based on temporal gaps."""
    dropoffs = []
    pickups = []

    for tag, tdata in raw_df.groupby("TagId"):
        tdata = tdata.dropna(subset=["X", "Y"]).copy()
        tdata["_ts"] = pd.to_datetime(tdata["TimeStamp"], dayfirst=True)
        tdata = tdata.sort_values("_ts").reset_index(drop=True)
        if len(tdata) < 2:
            continue

        ts = tdata["_ts"].values
        xs = tdata["X"].values
        ys = tdata["Y"].values

        dt_sec = np.diff(ts) / np.timedelta64(1, "s")

        for i in range(len(dt_sec)):
            if dt_sec[i] >= gap_threshold_sec:
                dropoffs.append({
                    "TagId": tag,
                    "x": float(xs[i]),
                    "y": float(ys[i]),
                    "gap_start": pd.Timestamp(ts[i]),
                    "gap_duration_sec": float(dt_sec[i]),
                })
                pickups.append({
                    "TagId": tag,
                    "x": float(xs[i + 1]),
                    "y": float(ys[i + 1]),
                    "gap_end": pd.Timestamp(ts[i + 1]),
                    "gap_duration_sec": float(dt_sec[i]),
                })

    return pd.DataFrame(dropoffs), pd.DataFrame(pickups)


def _grid_density(positions_df, cell_size=0.5):
    """Count unique tags per spatial grid cell."""
    if len(positions_df) == 0:
        return pd.DataFrame({"cx": [], "cy": [], "n_tags": [], "tags": [], "count": []})

    df = positions_df.copy()
    df["gx"] = (df["x"] / cell_size).apply(np.floor) * cell_size + cell_size / 2
    df["gy"] = (df["y"] / cell_size).apply(np.floor) * cell_size + cell_size / 2

    grouped = df.groupby(["gx", "gy"]).agg(
        n_tags=("TagId", "nunique"),
        tags=("TagId", lambda s: set(s)),
        count=("TagId", "size"),
    ).reset_index()
    grouped.columns = ["cx", "cy", "n_tags", "tags", "count"]
    return grouped.sort_values("n_tags", ascending=False).reset_index(drop=True)


def detect_basket(raw_df, gap_threshold_sec=30, cell_size=0.5, min_tags=3):
    """Detect basket location using 3-step gap-based method."""
    result = {
        "detected": False, "x": None, "y": None,
        "n_tags_dropoff": 0, "n_tags_pickup": 0, "n_tags_shared": 0,
        "symmetry_confirmed": False, "dominance_ratio": 0.0,
        "confidence": "none",
        "dropoffs_df": pd.DataFrame(), "pickups_df": pd.DataFrame(),
        "drop_grid": pd.DataFrame(), "pick_grid": pd.DataFrame(),
    }

    dropoffs, pickups = find_dropoff_pickup_positions(raw_df, gap_threshold_sec)
    result["dropoffs_df"] = dropoffs
    result["pickups_df"] = pickups

    if len(dropoffs) == 0:
        return result

    drop_grid = _grid_density(dropoffs, cell_size)
    result["drop_grid"] = drop_grid

    if len(drop_grid) == 0:
        return result

    best = drop_grid.iloc[0]
    n_tags_drop = int(best["n_tags"])

    if n_tags_drop < min_tags:
        result["x"] = float(best["cx"])
        result["y"] = float(best["cy"])
        result["n_tags_dropoff"] = n_tags_drop
        return result

    result["detected"] = True
    result["x"] = float(best["cx"])
    result["y"] = float(best["cy"])
    result["n_tags_dropoff"] = n_tags_drop

    if len(pickups) > 0:
        pick_grid = _grid_density(pickups, cell_size)
        result["pick_grid"] = pick_grid

        match = pick_grid[(pick_grid["cx"] == best["cx"]) & (pick_grid["cy"] == best["cy"])]
        if len(match) > 0:
            pick_tags = match.iloc[0]["tags"]
            drop_tags = best["tags"]
            shared = drop_tags & pick_tags
            result["n_tags_pickup"] = int(match.iloc[0]["n_tags"])
            result["n_tags_shared"] = len(shared)
            result["symmetry_confirmed"] = len(shared) >= min_tags

    second_count = int(drop_grid.iloc[1]["count"]) if len(drop_grid) > 1 else 0
    best_count = int(best["count"])
    ratio = best_count / second_count if second_count > 0 else float("inf")
    result["dominance_ratio"] = round(ratio, 1)

    if result["symmetry_confirmed"] and ratio >= 3.0:
        result["confidence"] = "high"
    elif result["symmetry_confirmed"] or ratio >= 3.0:
        result["confidence"] = "moderate"
    else:
        result["confidence"] = "low"

    return result


# ─────────────────────────────────────────────────────────────────────────────
# PAGE SETUP & PREREQUISITE CHECK
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Clean & Configure", page_icon="🧹", layout="wide")
st.title("🧹 Clean & Configure")
st.caption("Stage 2 of 3 — set processing parameters and data exclusions.")

if "raw_data" not in st.session_state:
    st.warning("No data loaded. Go to **Upload & Inspect** first.")
    st.stop()

raw = st.session_state["raw_data"]
ts = parsed_timestamps(raw)

# ── 2026-10-17: remember page-2 settings between page visits ──
# Streamlit deletes a widget's value when its page is not shown, so each
# setting below is created without a value= argument and gets its value
# from here (or the default) just before it is drawn. All values are written
# back at the end of the page. Page 1 deletes this store on new data.
_p2_saved = st.session_state.setdefault("_page2_settings", {})


def _restore(key, default):
    """Give a settings widget its remembered value (or `default`) before it is drawn."""
    if key not in st.session_state:
        st.session_state[key] = _p2_saved.get(key, default)
_facts = cached_for_upload("page2_facts", raw, None,
                           lambda: _page2_upload_facts(raw, ts))
_sampling = cached_for_upload("page2_sampling", raw, None,
                              lambda: _page2_sampling_facts(raw, ts))

st.info(
    f"Working with {len(raw):,} rows from {_facts['n_tags']} tags "
    f"across {_facts['n_days']} day(s)."
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. PROCESSING PARAMETERS
# ─────────────────────────────────────────────────────────────────────────────

st.header("1. Processing Parameters")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Resampling & Filtering")

    # Default 100 ms set through session state (no value= argument), so the
    # "Use X ms" button below can change it without a Streamlit warning.
    _restore("timestep_ms_input", 100)
    timestep_ms = st.number_input(
        "Timestep (ms)",
        min_value=10, max_value=5000, step=10,
        help="Resampling interval. 100ms = 10 Hz.",
        key="timestep_ms_input",
    )

    _restore("max_interpolation_input", 5)
    max_interpolation = st.number_input(
        "Max interpolation (samples)",
        min_value=1, max_value=100, step=1,
        help="Maximum consecutive NaN samples to fill via linear interpolation.",
        key="max_interpolation_input",
    )

    # ── 2026-10-17: does the timestep fit the data? ──
    # Reference = median over tags of page 1's 'Median Δt'. If the timestep
    # is so fine that more empty slots sit between two samples than
    # interpolation fills, most slots end up without a position (and
    # resampling creates many more rows than there are samples).
    _tag_medians = list(_sampling["tag_median_s"].values())
    _timestep_mismatch = False
    if _tag_medians:
        _ref_dt_ms = float(np.median(_tag_medians)) * 1000
        _suggested_ms = int(min(5000, max(10, round(_ref_dt_ms / 10) * 10)))
        _empty_slots = _ref_dt_ms / timestep_ms - 1
        _timestep_mismatch = _empty_slots > max_interpolation
        if _timestep_mismatch:
            st.warning(
                f"⚠️ **Timestep does not fit this data.** The tags send a position "
                f"about every **{_ref_dt_ms:,.0f} ms** (median over tags), but the "
                f"timestep is **{timestep_ms} ms**. That leaves about "
                f"{_empty_slots:.0f} empty slots between two samples — more than the "
                f"{max_interpolation} that interpolation fills — so most time slots "
                f"will have no position, and processing creates far more rows than "
                f"there are samples."
            )

            def _use_suggested_timestep(value: int) -> None:
                st.session_state["timestep_ms_input"] = int(value)

            st.button(
                f"Use {_suggested_ms} ms",
                key="use_suggested_timestep_btn",
                help="Sets the timestep to the median sampling interval of the tags "
                     "(rounded to 10 ms). The choice of timestep stays yours.",
                on_click=_use_suggested_timestep,
                args=(_suggested_ms,),
            )

    _restore("max_gap_factor_input", 3)
    max_gap_factor = st.number_input(
        "Max gap factor",
        min_value=1, max_value=10, step=1,
        help="Velocity set to NaN if time gap > factor × timestep.",
        key="max_gap_factor_input",
    )

    # ── Smoothing (v4) ──────────────────────────────────────────────────────
    _restore("smoothing_enabled_input", False)
    smoothing_enabled = st.checkbox(
        "Apply rolling-median smoothing",
        key="smoothing_enabled_input",
        help=(
            "Optional pre-processing step. Replaces each (X, Y) sample with "
            "the rolling median over a configurable window. Off by default."
        ),
    )

    if smoothing_enabled:
        _restore("smoothing_window_input", 0.5)
        smoothing_window_sec = st.number_input(
            "Smoothing window (s)",
            min_value=0.1, max_value=5.0, step=0.1,
            help="Window length in seconds; rounded up to an odd sample count.",
            key="smoothing_window_input",
        )
        # Live conversion: seconds → odd sample count.
        _samples = max(1, int(round(smoothing_window_sec / (timestep_ms / 1000))))
        if _samples % 2 == 0:
            _samples += 1
        st.caption(
            f"Window: {smoothing_window_sec:.2f} s "
            f"({_samples} samples at {int(timestep_ms)}ms timestep)"
        )
        st.caption(
            "Replaces each position with the rolling median over the window. "
            "Robust to single-sample spikes the velocity filter doesn't catch, "
            "but distorts fine-grained movement on short time scales. Use with "
            "care for analyses depending on instantaneous position (e.g. gait, "
            "fine-scale interaction)."
        )
    else:
        smoothing_window_sec = None

    _restore("max_velocity_input", 6.5)
    max_velocity = st.number_input(
        "Max velocity (m/s)",
        min_value=0.5, max_value=20.0, step=0.1,
        format="%.2f",
        help=(
            "Positions implying faster movement are set to NaN. "
            "Default is set to  6.5 m/s. "
            "Please carefully consider which maximum speed is appropiate for the species you are studying. "
            "Step is 0.1 m/s; values are displayed to 2 decimal places. "

        ),
        key="max_velocity_input",
    )

    # ── Velocity Advisor (v4) ───────────────────────────────────────────────
    with st.expander("📊 Velocity advisor — see your data's distribution", expanded=True):
        _restore("advisor_percentile", 99.5)
        advisor_percentile = st.number_input(
            "Percentile",
            min_value=95.0, max_value=99.99, step=0.1,
            help=(
                "Higher percentile = more permissive threshold (lets through more "
                "extreme samples). Default 99.5 is a conservative balance."
            ),
            key="advisor_percentile",
        )

        # Build cache key inputs.
        # 2026-10-17: same values as _advisor_auto_bounds(raw, margin=1.0),
        # from the quantiles computed once per upload.
        _adv_x_bounds = (float(_facts["x_q001"]) - 1.0, float(_facts["x_q999"]) + 1.0)
        _adv_y_bounds = (float(_facts["y_q001"]) - 1.0, float(_facts["y_q999"]) + 1.0)
        # A4 fix (v6): read tag filter from previous rerun's saved config.
        # On first render after upload there's no config yet → None (all tags).
        # On subsequent reruns this reflects whatever the user picked in
        # section 5 on the previous render. Empty list (A1 error sentinel)
        # is treated as None for the advisor — we still want a recommendation
        # even when tag selection is in an error state.
        _prev_cfg = st.session_state.get("config", {})
        _prev_selected = _prev_cfg.get("selected_tags")
        if _prev_selected:  # non-empty list
            _adv_selected_tuple = tuple(sorted(_prev_selected))
        else:  # None or [] → no filter
            _adv_selected_tuple = None
        # raw_id ties cache to current raw_data; reupload invalidates it.
        _raw_id = id(st.session_state["raw_data"])

        _adv_args = (
            _raw_id,
            int(timestep_ms),
            int(max_interpolation),
            int(max_gap_factor),
            _adv_x_bounds,
            _adv_y_bounds,
            bool(smoothing_enabled),
            float(smoothing_window_sec) if smoothing_window_sec else None,
            _adv_selected_tuple,
        )

        # 2026-10-17: run on its own only when the timestep fits the data and
        # the recording is small; otherwise wait for a click. A click is
        # remembered for exactly these settings (results are cached), so a
        # rerun does not ask again; changing a setting does.
        _adv_approved = st.session_state.setdefault("_advisor_approved", set())
        _est_slots = _estimated_slots(_sampling["spans"], int(timestep_ms),
                                      _adv_selected_tuple)
        _adv_run = (_adv_args in _adv_approved) or (
            not _timestep_mismatch and _est_slots <= _ADVISOR_AUTO_MAX_ROWS)

        def _approve_advisor(args) -> None:
            st.session_state.setdefault("_advisor_approved", set()).add(args)

        velocities = np.array([])
        per_tag_vels = {}
        if not _adv_run:
            if _timestep_mismatch:
                st.info(
                    "The advisor is waiting: the timestep does not fit this data "
                    "(see the warning above). Set the timestep first, or compute "
                    f"anyway (about {_est_slots:,} time slots)."
                )
                _btn_label = "Compute anyway"
            else:
                st.info(
                    f"The advisor has not run yet: at {int(timestep_ms)} ms this "
                    f"recording gives about **{_est_slots:,} time slots**, which takes "
                    "a while to compute. It runs once per setting; changing the "
                    "timestep, interpolation, gap factor, smoothing or tag selection "
                    "asks again."
                )
                _btn_label = "Compute velocity distribution"
            st.button(_btn_label, key="advisor_compute_btn",
                      on_click=_approve_advisor, args=(_adv_args,))
        else:
            try:
                with st.spinner("Computing velocity distribution..."):
                    velocities, per_tag_vels = _advisor_compute_distribution(*_adv_args)
            except Exception as exc:
                st.warning(f"Could not compute velocity distribution: {exc}")
                velocities = np.array([])
                per_tag_vels = {}

        if not _adv_run:
            pass
        elif len(velocities) == 0:
            st.info("No velocity data available — check that raw data is loaded.")
        else:
            # 2026-10-17: the numbers shown below (recommendation, chart bars,
            # per-tag table) only change with the advisor settings, the
            # percentile or the max velocity, so they are kept between clicks.
            _view_key = (_adv_args, float(advisor_percentile), float(max_velocity))
            _view = st.session_state.get("_advisor_view")
            if _view is None or _view[0] != _view_key:
                _rec = float(np.percentile(velocities, advisor_percentile))
                _p99 = float(np.percentile(velocities, 99))
                _hmax = max(_p99 * 1.1, _rec * 1.1, max_velocity * 1.1)
                _cnt, _edg = np.histogram(velocities, bins=80, range=(0.0, _hmax))
                _rows = []
                for tag, tag_vels in sorted(per_tag_vels.items()):
                    _rows.append({
                        "Tag": tag,
                        "n samples": len(tag_vels),
                        f"p{advisor_percentile}": (
                            round(float(np.percentile(tag_vels, advisor_percentile)), 2)
                            if len(tag_vels) > 0 else None
                        ),
                        "max": (
                            round(float(np.max(tag_vels)), 2)
                            if len(tag_vels) > 0 else None
                        ),
                    })
                _view = (_view_key, {"recommended": _rec, "max_for_hist": _p99,
                                     "hist_max": _hmax, "counts": _cnt, "edges": _edg,
                                     "rows": _rows})
                st.session_state["_advisor_view"] = _view
            recommended = _view[1]["recommended"]

            cap_smooth = "with smoothing" if smoothing_enabled else "without smoothing"
            st.caption(
                f"**Recommended: {recommended:.2f} m/s** "
                f"(p{advisor_percentile} of empirical distribution, {cap_smooth}, "
                f"n={len(velocities):,} velocity samples)"
            )
            st.caption(
                "Distribution computed on positions after out-of-bounds "
                "rejection (auto-bounds) and any smoothing — matching what "
                "the velocity filter will threshold against. Bounds here are "
                "auto-detected from data quantiles; if you set manual bounds "
                "in section 3, the advisor's recommendation may shift slightly."
            )

            # Apply button uses on_click callback rather than post-click
            # session-state write. Streamlit forbids modifying a widget's
            # session-state key after the widget has been instantiated, so
            # the assignment must happen inside a callback (which runs
            # before the next rerun's widget instantiation).
            #
            # `args=` captures the recommendation at button-render time so
            # the callback uses the value the user actually saw on the
            # button, not whatever `recommended` happens to be on rerun.
            #
            # v7 (D3 fix): no longer rounds to 0.5 step. The number_input's
            # step is now 0.1 so the unrounded recommendation can be
            # written directly. Rounded to 2 decimals to match the input's
            # display format and avoid floating-point noise in the saved
            # config.
            def _apply_velocity_recommendation(value: float) -> None:
                st.session_state["max_velocity_input"] = round(float(value), 2)

            st.button(
                f"Apply {recommended:.2f} m/s",
                key="advisor_apply_btn",
                help="Sets the Max velocity input above to this value.",
                on_click=_apply_velocity_recommendation,
                args=(recommended,),
            )

            # Histogram. Cap the x-axis at the 99th percentile so the heavy
            # tail doesn't squash the visible bulk into one or two bins.
            # Keep the cap generous enough to still show the current threshold
            # and recommendation if either falls beyond p99.
            _max_for_hist = _view[1]["max_for_hist"]
            _hist_max = _view[1]["hist_max"]
            # 2026-10-17: bars are counted here and only the 80 counts are
            # sent to the browser. Before, every velocity sample was sent and
            # the browser counted them; with large recordings (46 tags x 8 days
            # at 1 s: ~17 M samples) that message was larger than Streamlit's
            # 200 MB limit (MessageSizeError). The recommendation above is
            # still computed from all samples, so it is unchanged.
            _counts, _edges = _view[1]["counts"], _view[1]["edges"]
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=(_edges[:-1] + _edges[1:]) / 2,
                y=_counts,
                customdata=np.column_stack([_edges[:-1], _edges[1:]]),
                hovertemplate="%{customdata[0]:.2f}–%{customdata[1]:.2f} m/s: %{y:,} samples<extra></extra>",
                marker_color="#4C78A8",
                showlegend=False,
            ))
            # Mark the current threshold (red) and the recommendation (green).
            # v7 (#2): "current" annotation now matches the 2-decimal display
            # of max_velocity input and the recommendation annotation.
            fig.add_vline(
                x=max_velocity, line_color="red", line_dash="solid",
                annotation_text=f"current: {max_velocity:.2f}",
                annotation_position="top",
            )
            fig.add_vline(
                x=recommended, line_color="green", line_dash="dash",
                annotation_text=f"recommended: {recommended:.2f}",
                annotation_position="bottom",
            )
            fig.update_layout(
                height=240,
                margin=dict(l=0, r=0, t=10, b=20),
                xaxis_title="Velocity (m/s)",
                yaxis_title="Count",
                bargap=0.05,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Per-tag breakdown (diagnostic only — recommendation stays aggregate).
            with st.expander("Per-tag breakdown (diagnostic)"):
                if not per_tag_vels:
                    st.caption("No per-tag data available.")
                else:
                    rows = _view[1]["rows"]
                    st.dataframe(
                        pd.DataFrame(rows),
                        use_container_width=True,
                        hide_index=True,
                    )
                    st.caption(
                        "Per-tag percentiles are diagnostic only. The pipeline "
                        "applies a single threshold to all tags; per-tag thresholds "
                        "are not currently supported. If one tag's max velocity is "
                        "wildly different from the others, consider excluding it "
                        "in section 5."
                    )

with col_right:
    st.subheader("Proximity & Episodes")

    st.markdown("**Critical distances (m)**")
    st.caption(
        "Enter one or more distance thresholds separated by commas. "
        "The pipeline will run episode detection at each threshold for comparison."
    )
    _restore("critical_distances_input", "1.2")
    critical_distances_str = st.text_input(
        "Critical distances",
        help="Comma-separated list, e.g.: 0.6, 1.2, 1.8",
        key="critical_distances_input",
        label_visibility="collapsed",
    )

    # Parse and validate
    critical_distances = []
    parse_error = False
    for part in critical_distances_str.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            val = float(part)
            if val <= 0:
                st.error(f"Distance must be positive, got: {val}")
                parse_error = True
            else:
                critical_distances.append(val)
        except ValueError:
            st.error(f"Invalid number: '{part}'")
            parse_error = True

    if not critical_distances and not parse_error:
        st.error("Enter at least one critical distance.")
    elif not parse_error:
        critical_distances = sorted(set(critical_distances))
        if len(critical_distances) > 1:
            st.info(f"Will compare {len(critical_distances)} thresholds: {critical_distances}")

    # A5 fix (v6): on parse error, do NOT save the partial-parse list to
    # config. Fall back to the previously-saved value (so the user's last
    # known-good config is preserved across edits) or a safe default.
    if parse_error or not critical_distances:
        _prev_cfg_cd = st.session_state.get("config", {})
        _prev_cd = _prev_cfg_cd.get("critical_distances", [1.2])
        critical_distances = list(_prev_cd) if _prev_cd else [1.2]
        st.warning(
            f"⚠️ Using last valid critical distances: **{critical_distances}** "
            f"(input not saved until parse errors are resolved)."
        )

    _restore("min_episode_duration_input", 5.0)
    critical_duration = st.number_input(
        "Min episode duration (s)",
        min_value=0.5, max_value=60.0, step=0.5,
        help="Minimum duration for a proximity episode to be counted.",
        key="min_episode_duration_input",
    )

# ─────────────────────────────────────────────────────────────────────────────
# 2. STATIONARY TIME ESTIMATION
# ─────────────────────────────────────────────────────────────────────────────

st.header("2. Stationary Time Estimation")
st.caption(
    "Estimates per-entity time spent without meaningful movement using "
    "rolling displacement. Not a sitting detector — just measures stillness. "
    "Works for both single-tag and multi-tag (subject) data."
)

stat_col1, stat_col2 = st.columns(2)
with stat_col1:
    _restore("displacement_threshold_input", 0.3)
    displacement_threshold = st.number_input(
        "Displacement threshold (m)",
        min_value=0.05, max_value=2.0, step=0.05,
        key="displacement_threshold_input",
        help="Max displacement within window to count as stationary. "
             "Default 0.3m ≈ one UWB position error.",
    )
with stat_col2:
    _restore("stationary_window_input", 3.0)
    stationary_window_sec = st.number_input(
        "Window duration (s)",
        min_value=0.5, max_value=30.0, step=0.5,
        key="stationary_window_input",
        help="Rolling window for displacement calculation. "
             "Longer = more robust to noise, less sensitive.",
    )

# ─────────────────────────────────────────────────────────────────────────────
# 3. SPATIAL BOUNDS
# ─────────────────────────────────────────────────────────────────────────────

st.header("3. Spatial Bounds")

_restore("bounds_mode_input", "Auto-detect from data")
bounds_mode = st.radio(
    "Bounds mode",
    ["Auto-detect from data", "Manual"],
    horizontal=True,
    key="bounds_mode_input",
)

_restore("spatial_margin_input", 1.0)
spatial_margin = st.number_input(
    "Spatial margin (m)", min_value=0.0, max_value=5.0, step=0.1,
    help="Added to auto-detected bounds.",
    key="spatial_margin_input",
)

manual_x_bounds = None
manual_y_bounds = None

if bounds_mode == "Manual":
    bc1, bc2 = st.columns(2)
    with bc1:
        _restore("manual_x_min_input", float(_facts["x_q001"] - 1))
        _restore("manual_x_max_input", float(_facts["x_q999"] + 1))
        x_min = st.number_input("X min (m)", key="manual_x_min_input")
        x_max = st.number_input("X max (m)", key="manual_x_max_input")
    with bc2:
        _restore("manual_y_min_input", float(_facts["y_q001"] - 1))
        _restore("manual_y_max_input", float(_facts["y_q999"] + 1))
        y_min = st.number_input("Y min (m)", key="manual_y_min_input")
        y_max = st.number_input("Y max (m)", key="manual_y_max_input")

    # v7 (#3 fix): validate inverted ranges before saving.
    # Same class of bug as A1/A5/A6 — bad input must not propagate silently.
    # If invalid, leave manual_*_bounds as None so the downstream pipeline
    # falls back to auto-detect rather than rejecting every point.
    _bounds_ok_x = x_min < x_max
    _bounds_ok_y = y_min < y_max

    if not _bounds_ok_x:
        st.error(
            f"⛔ X bounds invalid: min ({x_min}) must be less than max ({x_max}). "
            "Reverting to auto-detect for X until corrected."
        )
    if not _bounds_ok_y:
        st.error(
            f"⛔ Y bounds invalid: min ({y_min}) must be less than max ({y_max}). "
            "Reverting to auto-detect for Y until corrected."
        )

    if _bounds_ok_x:
        manual_x_bounds = (x_min, x_max)
    if _bounds_ok_y:
        manual_y_bounds = (y_min, y_max)

# ─────────────────────────────────────────────────────────────────────────────
# 4. DEAD ZONES
# ─────────────────────────────────────────────────────────────────────────────

st.header("4. Dead Zones")
st.caption("Rectangular regions to exclude from analysis (e.g., doorways, storage).")

if "dead_zones" not in st.session_state:
    st.session_state["dead_zones"] = []

# ── Auto-detect basket ──
with st.expander("🔍 Auto-detect dead zones (tag deposit location)", expanded=False):
    st.caption(
        "Detects problematic areas where where tags disappear and reappear. "
        "Originally developed for the detection of a basket (which location was unknown) where tags were deposited. "
    )

    adc1, adc2 = st.columns(2)
    with adc1:
        ad_cell_size = st.number_input(
            "Grid cell size (m)", value=0.50, min_value=0.10, max_value=2.0, step=0.05,
            help="Size of spatial grid cells for density counting.",
            key="ad_cell_size",
        )
        ad_min_tags = st.number_input(
            "Min tags in cell", value=3, min_value=2, max_value=30, step=1,
            help="How many distinct tags must drop off in the same cell to call it a basket.",
            key="ad_min_tags",
        )
    with adc2:
        ad_gap_sec = st.number_input(
            "Gap threshold (s)", value=30, min_value=5, max_value=300, step=5,
            help="Minimum gap duration to count as a real tag disappearance.",
            key="ad_gap_sec",
        )
        # 2026-10-18: was the section-1 "Position error (m)" setting, whose
        # only use was this margin. Same default (0.3 m).
        ad_margin = st.number_input(
            "Margin around detected zone (m)", value=0.30, min_value=0.0,
            max_value=2.0, step=0.05,
            help="Added on every side of the detected grid cell when the dead "
                 "zone is proposed. Default 0.3 m, about one UWB position error.",
            key="ad_margin",
        )

    if st.button("🔎 Detect basket", key="ad_detect"):
        with st.spinner("Scanning for basket location..."):
            basket_result = detect_basket(
                raw,
                gap_threshold_sec=ad_gap_sec,
                cell_size=ad_cell_size,
                min_tags=ad_min_tags,
            )
            st.session_state["_ad_result"] = basket_result

    basket_result = st.session_state.get("_ad_result")

    if basket_result is not None:
        dropoffs = basket_result["dropoffs_df"]
        pickups = basket_result["pickups_df"]

        if len(dropoffs) == 0:
            st.warning(
                f"No tag disappearances detected (no gaps ≥ {ad_gap_sec}s). "
                "Try lowering the gap threshold."
            )
        elif not basket_result["detected"]:
            st.info(
                f"Found {len(dropoffs)} disappearance events across "
                f"{dropoffs['TagId'].nunique()} tags, but the best cell only has "
                f"{basket_result['n_tags_dropoff']} tags (need ≥ {ad_min_tags}). "
                "Try lowering Min tags or increasing Grid cell size."
            )
        else:
            st.success(
                f"**Basket detected** at ({basket_result['x']:.2f}, "
                f"{basket_result['y']:.2f}) — "
                f"{basket_result['n_tags_dropoff']} tags drop off here"
            )

            if basket_result["symmetry_confirmed"]:
                st.info(
                    f"✅ **Reappearance confirmed:** "
                    f"{basket_result['n_tags_shared']} tags both disappear "
                    f"and reappear at this location"
                )
            else:
                n_shared = basket_result["n_tags_shared"]
                if n_shared > 0:
                    st.warning(
                        f"⚠️ **Weak reappearance:** only {n_shared} tag(s) "
                        f"reappear at the same cell (need ≥ {ad_min_tags})"
                    )
                else:
                    st.warning(
                        "⚠️ **No reappearance:** tags disappear here but "
                        "none reappear — may be end-of-recording dropoffs"
                    )

            ratio = basket_result["dominance_ratio"]
            conf = basket_result["confidence"]
            conf_emoji = {"high": "🟢", "moderate": "🟡", "low": "🔴"}
            st.markdown(
                f"{conf_emoji.get(conf, '⚪')} **Confidence: {conf}** — "
                f"dominance ratio {ratio}× "
                f"(best cell has {ratio}× more events than runner-up)"
            )

        if len(dropoffs) > 0:
            fig = px.scatter(
                dropoffs, x="x", y="y", color="TagId",
                opacity=0.6,
                hover_data=["gap_duration_sec"],
                title="Drop-off positions (last known position before disappearance)",
                labels={"x": "X [m]", "y": "Y [m]"},
                height=450,
            )
            fig.update_yaxes(scaleanchor="x", scaleratio=1)
            fig.update_traces(marker=dict(size=7))

            if len(pickups) > 0:
                fig.add_trace(go.Scatter(
                    x=pickups["x"], y=pickups["y"],
                    mode="markers",
                    marker=dict(size=7, symbol="x", color="rgba(0,0,0,0.3)"),
                    name="Pickup positions",
                    hovertext=[
                        f"Pickup: {row.TagId} (gap {row.gap_duration_sec:.0f}s)"
                        for _, row in pickups.iterrows()
                    ],
                ))

            if basket_result["x"] is not None:
                half = ad_cell_size / 2
                is_detected = basket_result["detected"]
                color = "red" if is_detected else "orange"
                label = "DETECTED" if is_detected else "Best candidate"

                fig.add_shape(
                    type="rect",
                    x0=basket_result["x"] - half,
                    x1=basket_result["x"] + half,
                    y0=basket_result["y"] - half,
                    y1=basket_result["y"] + half,
                    line=dict(color=color, width=2.5, dash="dash"),
                    fillcolor=f"rgba({'255,0,0' if is_detected else '255,165,0'},0.08)",
                )
                fig.add_annotation(
                    x=basket_result["x"],
                    y=basket_result["y"] + half + 0.2,
                    text=f"{label} ({basket_result['n_tags_dropoff']} tags)",
                    showarrow=False,
                    font=dict(color=color, size=12),
                )

            fig.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=-0.35),
                margin=dict(t=40, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)

        if basket_result is not None and basket_result["detected"]:
            margin = ad_margin
            half = ad_cell_size / 2
            proposed_zone = {
                "x_min": round(basket_result["x"] - half - margin, 2),
                "x_max": round(basket_result["x"] + half + margin, 2),
                "y_min": round(basket_result["y"] - half - margin, 2),
                "y_max": round(basket_result["y"] + half + margin, 2),
                "label": "Basket (auto-detected)",
            }
            st.markdown(
                f"**Proposed dead zone** (cell ± {margin}m margin): "
                f"X=[{proposed_zone['x_min']:.2f}, {proposed_zone['x_max']:.2f}], "
                f"Y=[{proposed_zone['y_min']:.2f}, {proposed_zone['y_max']:.2f}]"
            )
            if st.button("✅ Add as dead zone", key="ad_add_dz", type="primary"):
                existing_labels = [dz["label"] for dz in st.session_state["dead_zones"]]
                if proposed_zone["label"] in existing_labels:
                    st.warning("An auto-detected basket dead zone already exists. Remove it first to re-add.")
                else:
                    st.session_state["dead_zones"].append(proposed_zone)
                    st.rerun()

# ── Manual dead zone entry ──
with st.expander("Add dead zone manually", expanded=False):
    dz_col1, dz_col2 = st.columns(2)
    with dz_col1:
        dz_x_min = st.number_input("DZ X min", value=0.0, key="dz_xmin")
        dz_x_max = st.number_input("DZ X max", value=1.0, key="dz_xmax")
    with dz_col2:
        dz_y_min = st.number_input("DZ Y min", value=0.0, key="dz_ymin")
        dz_y_max = st.number_input("DZ Y max", value=1.0, key="dz_ymax")
    dz_label = st.text_input("Label (optional)", value="", key="dz_label")

    if st.button("Add dead zone"):
        # v7 (#4 + #5 fix): validate bounds and label before appending.
        # Previously, inverted ranges and duplicate labels were silently
        # accepted. Bounds validation matches the section 3 pattern;
        # duplicate-label check matches the basket auto-add at line ~1016.
        _candidate_label = (dz_label or
                            f"Zone {len(st.session_state['dead_zones']) + 1}")
        _existing_labels = [dz["label"] for dz in st.session_state["dead_zones"]]
        _errors = []
        if dz_x_min >= dz_x_max:
            _errors.append(
                f"X bounds invalid: min ({dz_x_min}) must be less than max "
                f"({dz_x_max})."
            )
        if dz_y_min >= dz_y_max:
            _errors.append(
                f"Y bounds invalid: min ({dz_y_min}) must be less than max "
                f"({dz_y_max})."
            )
        if _candidate_label in _existing_labels:
            _errors.append(
                f"A dead zone labelled '{_candidate_label}' already exists. "
                "Use a different label or remove the existing one first."
            )

        if _errors:
            for _e in _errors:
                st.error(f"⛔ {_e}")
        else:
            st.session_state["dead_zones"].append({
                "x_min": dz_x_min, "x_max": dz_x_max,
                "y_min": dz_y_min, "y_max": dz_y_max,
                "label": _candidate_label,
            })
            st.rerun()

# ── List of defined dead zones ──
if st.session_state["dead_zones"]:
    st.write(f"**{len(st.session_state['dead_zones'])} dead zone(s) defined:**")
    # v7 (#6 fix): collect the index to remove during iteration, then pop
    # after the loop. Prevents the fragile pattern of pop(i) inside
    # enumerate() — same class of code smell A10 flagged for the subset
    # builder. The st.rerun() exit normally protects this, but if the
    # rerun is ever removed or moved, iteration would corrupt.
    _idx_to_remove = None
    for i, dz in enumerate(st.session_state["dead_zones"]):
        col_dz, col_rm = st.columns([4, 1])
        col_dz.write(
            f"  `{dz['label']}`: X=[{dz['x_min']:.1f}, {dz['x_max']:.1f}], "
            f"Y=[{dz['y_min']:.1f}, {dz['y_max']:.1f}]"
        )
        if col_rm.button("Remove", key=f"rm_dz_{i}"):
            _idx_to_remove = i
    if _idx_to_remove is not None:
        st.session_state["dead_zones"].pop(_idx_to_remove)
        st.rerun()

    # ── Dead zone impact preview ──
    st.markdown("**📊 Dead Zone Impact Preview**")
    st.caption("Shows how dead zones affect data quality before running the pipeline.")

    # A6 fix (v6): apply tag filter from previous rerun's saved config so the
    # preview matches the actual pipeline scope. First render after upload
    # has no config → preview uses full raw (acceptable). On subsequent
    # reruns the preview reflects whatever the user selected in section 5.
    # Empty list (A1 error sentinel) treated as no filter — show full impact.
    _prev_cfg_dz = st.session_state.get("config", {})
    _prev_selected_dz = _prev_cfg_dz.get("selected_tags")
    # 2026-10-17: computed once per (upload, dead zones, tag selection) —
    # ~27 s per click on a 15 M-row recording otherwise. Same rules as before:
    # filter to the previously selected tags; if that leaves nothing, use all.
    _dz_list = list(st.session_state["dead_zones"])
    _dz_key = tuple(tuple(sorted(z.items())) for z in _dz_list)
    _dz_sel_key = tuple(_prev_selected_dz) if _prev_selected_dz else None

    def _dz_preview():
        if _dz_sel_key:
            _sub = raw[raw["TagId"].isin(list(_dz_sel_key))]
            if len(_sub) > 0:
                return dead_zone_impact(_sub, _dz_list), True
        return dead_zone_impact(raw, _dz_list), False

    impact, _dz_preview_filtered = cached_for_upload(
        "page2_dz_impact", raw, (_dz_key, _dz_sel_key), _dz_preview)
    if _dz_preview_filtered:
        st.caption(
            f"_Preview filtered to {len(_prev_selected_dz)} selected tag(s) "
            f"from your previous configuration._"
        )

    if impact["total_affected"] > 0:
        tag_df = impact["per_tag"]

        total_samples = tag_df["total_samples"].sum()
        total_valid_before = tag_df["valid_before"].sum()
        total_valid_after = tag_df["valid_after"].sum()
        nan_pct_before = (1 - total_valid_before / total_samples) * 100 if total_samples > 0 else 0
        nan_pct_after = (1 - total_valid_after / total_samples) * 100 if total_samples > 0 else 0
        nan_increase = nan_pct_after - nan_pct_before

        col_imp1, col_imp2, col_imp3 = st.columns(3)
        col_imp1.metric(
            "Positions nullified by dead zones",
            f"{nan_increase:.1f}%",
            help="Percentage of junk positions inside dead zones that will be removed.",
        )
        col_imp2.metric(
            "Useful position data remaining",
            f"{100 - nan_pct_after:.1f}%",
            help=f"Before dead zones: {100 - nan_pct_before:.1f}%",
        )
        col_imp3.metric(
            "Samples affected",
            f"{impact['total_affected']:,}",
        )

        st.caption(
            "⚠️ Velocity impact cannot be previewed here — it depends on "
            "resampling and filtering which only happen during the pipeline run. "
            "See the full comparison after running the pipeline."
        )

        # Per-zone breakdown
        for zinfo in impact["per_zone"]:
            st.markdown(
                f"  `{zinfo['label']}`: **{zinfo['samples_affected']:,}** samples "
                f"({zinfo['pct_of_total']:.1f}%) across **{zinfo['tags_affected']}** tags"
            )

        # Per-tag before/after table
        if len(tag_df) > 0:
            with st.expander("Per-tag NaN rate comparison", expanded=False):
                display_cols = [
                    "TagId", "total_samples", "in_dead_zone",
                    "nan_pct_before", "nan_pct_after", "increase_pct",
                ]
                fmt = {
                    "nan_pct_before": "{:.1f}",
                    "nan_pct_after": "{:.1f}",
                    "increase_pct": "{:.1f}",
                }
                st.dataframe(
                    tag_df[display_cols].style
                        .format(fmt)
                        .background_gradient(subset=["increase_pct"], cmap="Reds"),
                    use_container_width=True, hide_index=True,
                )

                tag_labels = tag_df["TagId"].astype(str).tolist()
                fig_impact = go.Figure()
                fig_impact.add_trace(go.Bar(
                    x=tag_labels,
                    y=tag_df["valid_after"],
                    name="Valid samples remaining",
                    marker_color="#66BB6A",
                ))
                fig_impact.add_trace(go.Bar(
                    x=tag_labels,
                    y=tag_df["in_dead_zone"],
                    name="Samples in dead zone (removed)",
                    marker_color="#EF5350",
                ))
                fig_impact.update_layout(
                    barmode="stack",
                    title="Per-Tag Sample Impact from Dead Zones",
                    xaxis_title="Tag ID",
                    yaxis_title="Number of samples",
                    height=400,
                )
                fig_impact.update_xaxes(type="category")
                st.plotly_chart(fig_impact, use_container_width=True)
    else:
        st.info("No raw data samples fall within the defined dead zones.")

# ─────────────────────────────────────────────────────────────────────────────
# 5. TAG SELECTION
# ─────────────────────────────────────────────────────────────────────────────

st.header("5. Tag Selection")

all_tags = _facts["all_tags"]

_restore("tags_mode", "all")
tag_mode = st.radio(
    "Which tags to analyze?",
    options=["all", "select"],
    format_func={
        "all": f"All tags ({len(all_tags)})",
        "select": "Select specific tags",
    }.get,
    horizontal=True,
    key="tags_mode",
)

if tag_mode == "all":
    selected_tags = None
else:
    # Inherit bin resolution from page 1; fall back to 60s if user never
    # visited the timeline section there.
    bin_sec = st.session_state.get("availability_bin_size", 60)

    avail = cached_for_upload(
        "availability", raw, bin_sec,
        lambda: _compute_availability_matrix(raw, bin_seconds=bin_sec),
    )
    matrix = avail["matrix"]
    tag_date_pairs = avail["tag_date_pairs"]

    # Per-tag aggregate stats for the row label.
    # NaN % intentionally omitted: TrackLab exports strip NaN rows
    # server-side, so it's always 0% and conveys no information.
    tag_info = _facts["tag_samples"]

    st.caption(
        "Each row shows one tag's data availability over time alongside an "
        "**Include** checkbox. The timeline reveals temporal patterns of data "
        "loss — uniformly thin tags vs. tags that drop out only at certain "
        "times — that the aggregate sample count alone obscures. Bin resolution "
        f"({bin_sec}s) is inherited from page 1's timeline."
    )

    # Initialize per-tag include state on first render or when tag set changes.
    # v8 fix (bug #7): the per-tag checkboxes below are keyed widgets
    # (key="tag_inc_<tag>"), so Streamlit owns those keys and ignores the
    # checkbox `value=` arg on every rerun after the first. The old code kept a
    # separate "tag_include_state" dict and had the bulk buttons write to *that*
    # dict, which never drove the widgets — so "Include/Exclude all" silently
    # no-opped. Fix: seed and write the widget keys directly; drop the shadow.
    current_tag_set = set(str(t) for t in all_tags)
    prev_seeded = st.session_state.get("_tag_inc_seeded_set", set())

    if prev_seeded != current_tag_set:
        # Default: include everything. Preserve any prior choice for tags that
        # still exist (a surviving tag's widget key is already in session_state,
        # so we don't overwrite it). Matches v7's preserve-on-tag-set-change
        # contract.
        for t in all_tags:
            k = f"tag_inc_{str(t)}"
            if k not in st.session_state:
                st.session_state[k] = _p2_saved.get(k, True)
        st.session_state["_tag_inc_seeded_set"] = current_tag_set

    # Bulk-action row.
    bulk_col1, bulk_col2, bulk_col3 = st.columns([1, 1, 4])
    with bulk_col1:
        if st.button("Include all", key="tag_include_all"):
            for t in all_tags:
                st.session_state[f"tag_inc_{str(t)}"] = True
            st.rerun()
    with bulk_col2:
        if st.button("Exclude all", key="tag_exclude_all"):
            for t in all_tags:
                st.session_state[f"tag_inc_{str(t)}"] = False
            st.rerun()

    st.markdown("---")

    if matrix.empty:
        st.warning(
            "Could not build availability timeline (no parseable timestamps). "
            "Falling back to plain checkboxes — the per-tag rows below will "
            "show stats only."
        )

    # Per-tag row: checkbox + label/stats + timeline strip.
    chosen = []
    for tag in all_tags:
        tag_str = str(tag)
        info = tag_info.get(tag, {"samples": 0})

        row_col1, row_col2, row_col3 = st.columns([1, 2, 6])

        with row_col1:
            # v8 fix (bug #7): no `value=` — the keyed widget reads/writes its
            # own session_state key, which the bulk buttons and the seed loop
            # above now set. Passing both `value=` and a pre-set key would also
            # trip Streamlit's "set via value and session_state" warning.
            # 2026-10-17: after visiting another page Streamlit has dropped this
            # key; give it back its remembered value (default: included).
            _restore(f"tag_inc_{tag_str}", True)
            included = st.checkbox(
                "Include",
                key=f"tag_inc_{tag_str}",
                label_visibility="collapsed",
            )

        with row_col2:
            st.markdown(
                f"**Tag {tag_str}**  \n"
                f"<span style='font-size:0.85em;color:#666'>"
                f"{info['samples']:,} samples"
                f"</span>",
                unsafe_allow_html=True,
            )

        with row_col3:
            if not matrix.empty:
                fig = _per_tag_strip(matrix, tag_date_pairs, tag)
                if fig is not None:
                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key=f"tag_strip_{tag_str}",
                    )
                else:
                    st.caption("_(no timestamped data for this tag)_")

        if included:
            chosen.append(tag)

    st.markdown("---")

    if not chosen:
        st.error("You must select at least 2 tags for pairwise analysis.")
        # A1 fix (v6): empty list is the explicit error sentinel.
        # None means "use all tags" (legitimate state); [] means
        # "user is in a tag-selection error state, do not run pipeline".
        # Page 3 v5 detects [] and blocks the Run button.
        selected_tags = []
    elif len(chosen) < 2:
        st.error(
            f"Only **{len(chosen)}** tag selected — pairwise analysis "
            f"requires at least 2."
        )
        # A1 fix (v6): see comment above. Empty list = error sentinel.
        selected_tags = []
    else:
        n_excluded = len(all_tags) - len(chosen)
        if n_excluded > 0:
            excluded = [t for t in all_tags if t not in chosen]
            st.caption(
                f"**{len(chosen)}** tags included, "
                f"**{n_excluded}** excluded: {', '.join(str(t) for t in excluded)}"
            )
        else:
            st.caption(f"**{len(chosen)}** tags included (none excluded).")

        # Preserve prior contract: None means "all tags", a list means subset.
        selected_tags = chosen if len(chosen) < len(all_tags) else None

# ─────────────────────────────────────────────────────────────────────────────
# 6. SUBJECT MAPPING (multi-tag support)
# ─────────────────────────────────────────────────────────────────────────────

st.header("6. Subject Mapping")

_restore("multi_tag_toggle", st.session_state.get("multi_tag_enabled", False))
multi_tag_enabled = st.toggle(
    "Subjects have multiple tags",
    key="multi_tag_toggle",
    help="Enable when individual subjects wore more than one UWB tag.",
)
st.session_state["multi_tag_enabled"] = multi_tag_enabled

subject_mapping = None
inter_tag_threshold = 1.0
dz_mode = "permissive"

if multi_tag_enabled:
    st.caption(
        "Map physical tags to the subjects who wore them. "
        "Positions from multiple tags on the same subject are merged "
        "into a centroid at each timestep."
    )

    mt_col1, mt_col2 = st.columns(2)
    with mt_col1:
        _restore("inter_tag_thresh", 1.0)
        inter_tag_threshold = st.number_input(
            "Inter-tag distance threshold (m)",
            min_value=0.1, max_value=5.0, step=0.1,
            help="If two tags on the same subject are farther apart than this, "
                 "the position is set to NaN. Typical body-part offsets are 0.2–0.5m.",
            key="inter_tag_thresh",
        )
    with mt_col2:
        _restore("dz_mode_radio", "conservative")
        dz_mode = st.radio(
            "Dead zone handling",
            options=["conservative", "permissive"],
            format_func={
                "conservative": "Conservative — if any tag is in a dead zone, NaN the whole subject",
                "permissive": "Permissive — only NaN the specific tag in the dead zone",
            }.get,
            key="dz_mode_radio",
            help="Conservative is safer (avoids phantom positions near the basket). "
                 "Permissive gives more data.",
        )

    if "subject_list" not in st.session_state:
        st.session_state["subject_list"] = []

    # A1 fix (v6): treat both None (all tags) and [] (error sentinel) as
    # "no valid tag filter" for the purposes of subject mapping. This keeps
    # the subject mapping UI usable while the user is fixing a tag-selection
    # error in section 5. The actual pipeline gate is enforced in page 3 v5.
    if selected_tags:  # non-empty list (truthy)
        available_tags = [t for t in all_tags if t in selected_tags]
    else:
        available_tags = list(all_tags)

    assigned_tags = set()
    for subj in st.session_state["subject_list"]:
        assigned_tags.update(subj["tags"])

    if st.session_state["subject_list"]:
        st.markdown("**Defined subjects:**")

    for idx, subj in enumerate(st.session_state["subject_list"]):
        n_tags = len(subj["tags"])
        icon = "👤" if n_tags == 1 else "👥"
        with st.expander(f"{icon} {subj['name']} — {n_tags} tag(s): {', '.join(subj['tags'])}", expanded=False):
            st.write(f"Tags: `{'`, `'.join(subj['tags'])}`")

            if st.button(f"Delete subject", key=f"del_subj_{idx}", type="secondary"):
                st.session_state["subject_list"].pop(idx)
                st.rerun()

    st.markdown("---")
    with st.expander("➕ Add subject", expanded=len(st.session_state["subject_list"]) == 0):
        subj_name = st.text_input(
            "Subject name",
            placeholder="e.g., Child 1, Alice, Subject A...",
            key="new_subj_name",
        )

        unassigned = [t for t in available_tags if t not in assigned_tags]

        subj_tags = st.multiselect(
            "Assign tags to this subject",
            options=unassigned,
            key="new_subj_tags",
            help="Select which tag(s) this subject wore.",
        )

        can_create = bool(subj_name and subj_name.strip() and subj_tags)
        existing_names = [s["name"] for s in st.session_state["subject_list"]]

        if subj_name and subj_name.strip() in existing_names:
            st.error(f"Subject name '{subj_name.strip()}' already exists.")
            can_create = False

        if st.button("Create subject", key="create_subj", type="primary", disabled=not can_create):
            new_subj = {
                "name": subj_name.strip(),
                "tags": list(subj_tags),
            }
            st.session_state["subject_list"].append(new_subj)
            st.rerun()

    unassigned_after = [t for t in available_tags if t not in assigned_tags]
    if unassigned_after:
        st.info(
            f"**{len(unassigned_after)} unassigned tag(s)** will become "
            f"single-tag subjects automatically: {', '.join(unassigned_after)}"
        )

    subject_mapping = {}
    for subj in st.session_state["subject_list"]:
        subject_mapping[subj["name"]] = subj["tags"]
    for tag in unassigned_after:
        subject_mapping[str(tag)] = [str(tag)]

    total_subjects = len(subject_mapping)

    if total_subjects < 2:
        st.error(f"Need at least 2 subjects for pairwise analysis (currently {total_subjects}).")

    for name, tags in subject_mapping.items():
        if len(tags) >= 3:
            st.warning(
                f"⚠️ Subject '{name}' has **{len(tags)} tags** — "
                f"this is unusual. Double-check the mapping."
            )

    n_multi = sum(1 for t in subject_mapping.values() if len(t) > 1)
    n_single = sum(1 for t in subject_mapping.values() if len(t) == 1)
    st.markdown(
        f"**{total_subjects} subjects** total: "
        f"{n_multi} multi-tag, {n_single} single-tag"
    )

# ─────────────────────────────────────────────────────────────────────────────
# STORE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")

timestep_s = timestep_ms / 1000

config = {
    "timestep_ms": timestep_ms,
    "timestep_s": timestep_s,
    "max_interpolation": max_interpolation,
    "max_velocity": max_velocity,
    "max_gap_factor": max_gap_factor,
    # Smoothing (v4)
    "smoothing_enabled": smoothing_enabled,
    "smoothing_window_sec": smoothing_window_sec,
    "critical_distances": critical_distances,
    "critical_duration_s": critical_duration,
    "min_episode_samples": math.ceil(critical_duration / timestep_s),
    # Stationary time
    "displacement_threshold": displacement_threshold,
    "stationary_window_sec": stationary_window_sec,
    # Bounds & zones
    "spatial_margin": spatial_margin,
    "manual_x_bounds": manual_x_bounds,
    "manual_y_bounds": manual_y_bounds,
    "dead_zones": st.session_state.get("dead_zones", []),
    # Tags
    "selected_tags": selected_tags,
    # Multi-tag
    "multi_tag_enabled": multi_tag_enabled,
    "subject_mapping": subject_mapping,
    "inter_tag_threshold": inter_tag_threshold,
    "dz_mode": dz_mode,
}

st.session_state["config"] = config

# 2026-10-17: remember every setting for the next visit to this page.
_P2_SETTING_KEYS = [
    "timestep_ms_input", "max_interpolation_input", "max_gap_factor_input",
    "smoothing_enabled_input", "smoothing_window_input",
    "max_velocity_input", "advisor_percentile", "critical_distances_input",
    "min_episode_duration_input", "displacement_threshold_input",
    "stationary_window_input", "bounds_mode_input", "spatial_margin_input",
    "manual_x_min_input", "manual_x_max_input", "manual_y_min_input",
    "manual_y_max_input", "tags_mode", "multi_tag_toggle", "inter_tag_thresh",
    "dz_mode_radio",
]
for _k in _P2_SETTING_KEYS:
    if _k in st.session_state:
        _p2_saved[_k] = st.session_state[_k]
for _k in list(st.session_state.keys()):
    if str(_k).startswith("tag_inc_"):
        _p2_saved[_k] = st.session_state[_k]

st.success(
    "✅ Configuration saved. Go to **Define Analysis & Run** in the sidebar "
    "to define subsets and process the data."
)
