"""
Social Interaction Analysis v13 — time within distance (2026-10-17).

2026-10-18 (documentation text only, edited in place; no function changed):
export texts say "TrackLab-Companion" instead of "TrackLab-assist" (column
dictionary title, README, Python and R loader headers). Column dictionary:
`cleaned_trajectories.csv` lists `Time` (the exported column) instead of
`TimeStamp`; `stationary_time.csv` lists the columns actually exported
(total_valid_samples, stationary_samples, stationary_time_sec,
total_valid_time_sec, stationary_pct) instead of total_time_sec.
Previous version: _removed_backup/before_ui_cleanup/social_analysis_v13.py.

Adds, without changing any value v12 produced:
- Within-distance counts: for every pair, date and threshold, the number of
  samples at which both members had a valid position and were closer than the
  threshold (the same comparison the episode mask uses), with no minimum
  duration. Counted in `_analyse_dates` while each row of distances is in
  memory (`_within_for_row`); returned as a new 'within' entry
  (TagId_A, TagId_B, within_samples, Date) next to 'prox' and 'dist' by
  `run_analysis` and `run_analysis_multi_distance`.
- `compute_dyad_proximity(..., within_df=None)` / `build_dyad_proximity_table`:
  two columns appended: within_distance_sec and within_distance_fraction
  (= within_distance_sec / joint_observed_sec).
- `compute_metrics`: key within_distance_fraction appended after the v12 keys.
- Column dictionary: both fractions explained; the v12 sentence that the
  fraction "does not" grow with recording time is corrected.

Why: proximity_fraction (v12) counts only episodes of at least the minimum
duration. A gap splits an episode and pieces shorter than the minimum are
dropped, so with random gaps only a share q^(m-1) * (1 + (m-1)(1-q)) of the
close time survives (q = share of samples observed, m = minimum episode
samples), which still rises with coverage. On the 46-cow data, the most
fragmented quarter of pairs kept 0.75 of their within-distance time as episode
time, the least fragmented quarter 0.83 (1.2 m). within_distance_fraction has
no minimum duration: if missing data is unrelated to whether the pair is
close, the observed samples are a random selection of all samples and the
expected fraction equals the true share of time within the distance, for any
amount of observed time.

v12 is kept unchanged next to this file.

--- v12 notes below ---

Social Interaction Analysis v12 — proximity relative to observed time (2026-10-17).

Adds, without changing any value the pipeline already produced:
- `compute_dyad_proximity(prox_df, dist_df, timestep_ms, low_joint_fraction=0.25)`:
  per pair and date, plus one row per pair over all dates (Date = 'all'):
  joint observed time (both entities had a valid position), proximity time,
  proximity fraction (= proximity time / joint observed time), episode count,
  episodes per joint observed hour, and a low-joint-time flag (joint time
  below 25 % of the median pair's joint time in the same period).
- `build_dyad_proximity_table(subset_results, timestep_ms, ...)`: the same for
  every (subset, distance), long format, for page 3 and the export.
- `compute_metrics(result_data, timestep_ms=None)`: three keys appended after
  the existing ones: joint_observed_sec, proximity_fraction,
  episodes_per_joint_hour (NaN without timestep_ms). Existing keys unchanged.
- `build_export_bundle(..., dyad_proximity=None)`: writes dyad_proximity.csv
  when given. metrics_summary.csv gains the three columns above at the end.
  Existing files and columns are unchanged.
- Column dictionary: dyad_proximity.csv and the new metrics_summary columns
  documented; the proximity_episodes.csv entry now lists the columns that
  are actually exported (start, end, mean_dist, min_dist, max_dist; Date as
  DD-MM-YYYY).
- Loaders (Python, R) also return 'dyad_proximity'.

Why: total proximity time grows with how long both entities were recorded.
When recording time differs between entities (46-cow data: 11 h to 149 h of
joint observed time per pair), proximity time partly measures tag coverage.
The fraction compares pairs on the time they could actually be seen together.

v11 is kept unchanged next to this file.

--- v11 notes below ---

Social Interaction Analysis v11 — memory release (2026-10-07).

Goal: let large multi-day recordings (e.g. 46 tags x 8 days, ~15 M rows)
run on an ordinary laptop. Every number the pipeline produces is identical
to v10 (verified with exact equality, see CHANGES.md). v10 is kept
unchanged next to this file so the app can be switched back.

Changes from v10 (all result-identical):
- `parse_ddmmyyyy_fast` parses in blocks of 1,000,000 rows. The old version
  needed ~260 bytes of scratch memory per row at once (~4 GB for 15 M rows).
- `process_all` runs resample -> reindex -> filter one calendar date at a
  time and joins the days afterwards. Every one of these steps already
  worked per (date, tag), so the joined result equals the v10 result row
  for row; only the temporary copies are smaller. Multi-tag merge, dead
  zones and velocity recalculation then run on the joined table exactly
  as in v10.
- New `compute_velocity_distribution_from_raw` for the page-2 velocity
  advisor: same result as resample_data -> reindex_data ->
  compute_velocity_distribution on the whole recording, computed one date
  at a time.
- `run_analysis` and `run_analysis_multi_distance` handle one date at a
  time and no longer build the full (time x tags x tags) distance matrix.
  Distances are computed one row of tag pairs at a time with the same
  arithmetic, so episodes and dyad statistics are identical. The internal
  '_pairwise' entry of the result is now an empty list (nothing outside
  this module read it; it held every day's distance matrices).
- `calc_pairwise_distances`, `calc_pairwise`, `extract_episodes` and
  `calc_distance_metrics` are kept unchanged for other callers.
- `calc_stationary_time` reads each (date, tag) block straight from the X / Y
  arrays when the table is sorted by (Date, TagId), as process_all returns
  it (v10 made a sorted copy of the whole processed table first; that path
  is kept as fallback for unsorted input).

Unchanged from v10: all function names and signatures, defaults, pipeline
order, metric definitions, export format.

--- v10 / v9 notes below ---

Social Interaction Analysis v9 — adds export bundle assembly for the
researcher pilot release. Otherwise unchanged from v8.

Changes from v8:
- New `build_export_bundle(...)` function — assembles a ZIP (in memory)
  containing all pipeline outputs as flat CSVs plus a loader script
  (Python, R, or both, controlled by `format_pref`). Designed so that
  researchers can drop the ZIP into either language and immediately
  reconstruct the nested results structure. Includes a column dictionary
  and a config snapshot for reproducibility. Pure additive — does not
  touch any existing function.
- All v8 signatures preserved unchanged.

Carried forward from v8:
- Optional rolling-median smoothing (`apply_smoothing`,
  `compute_velocity_distribution`, `filter_data` smoothing kwargs,
  `process_all` smoothing kwargs).
- All v7 functionality (multi-tag merge, dead zones, multi-distance,
  stationary time, etc.) — unchanged.

Signature compatibility:
- v8 callers work unchanged. The new export-bundle function is purely
  additive; no existing call site is modified. `build_export_bundle`
  accepts None for any optional dataset, so partial bundles (e.g.
  results without a multi-tag merge diagnostic) work cleanly.
"""

import io
import json
import logging
import warnings
import zipfile
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore', message='.*Pyarrow.*', category=DeprecationWarning)

log = logging.getLogger('social_analysis')

# Rows per block for timestamp parsing (bounds temporary memory; output identical).
_PARSE_BLOCK_ROWS = 1_000_000

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(x, **kwargs): return x


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def validate_dataframe(df, required_cols, name="DataFrame"):
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"{name} must be a pandas DataFrame, got {type(df).__name__}")
    if df.empty:
        raise ValueError(f"{name} is empty")
    missing = set(required_cols) - set(df.columns) - set(df.index.names)
    if missing:
        raise ValueError(f"{name} is missing columns: {missing}")


def validate_positive(value, name="value"):
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"{name} must be a positive number, got {value}")


# =============================================================================
# TIMESTAMP PARSING
# =============================================================================

def parse_ddmmyyyy_fast(col):
    """Vectorised parse of 'DD-MM-YYYY HH:MM:SS.ffffff' strings.

    Returns None whenever the input does not fit that layout exactly (or holds
    an impossible date/time), so the caller falls back to pandas and behaves
    as before, errors included.

    v11: works through the column in blocks of `_PARSE_BLOCK_ROWS` rows.
    Every row is parsed independently, and the column is accepted only if
    every block is accepted, so the result (including when None is
    returned) is the same as parsing the whole column at once.
    """
    if col.dtype != object or len(col) <= _PARSE_BLOCK_ROWS:
        return _parse_ddmmyyyy_block(col)
    parts = []
    for a in range(0, len(col), _PARSE_BLOCK_ROWS):
        part = _parse_ddmmyyyy_block(col.iloc[a:a + _PARSE_BLOCK_ROWS])
        if part is None:
            return None
        parts.append(part)
    out = pd.concat(parts)
    out.name = col.name
    return out


def _parse_ddmmyyyy_block(col):
    """v10 `parse_ddmmyyyy_fast`, unchanged; applied to one block of rows."""
    if col.dtype != object or len(col) == 0:
        return None
    try:
        text = col.to_numpy().astype(str)
    except (TypeError, ValueError):
        return None
    if text.dtype.itemsize != 26 * 4:                     # longest string must be 26 chars
        return None
    m = text.view(np.uint32).reshape(len(text), 26)
    seps = {2: '-', 5: '-', 10: ' ', 13: ':', 16: ':', 19: '.'}
    digit_cols = [i for i in range(26) if i not in seps]
    if any((m[:, c] != ord(ch)).any() for c, ch in seps.items()):
        return None
    dig = m[:, digit_cols].astype(np.int64) - 48
    if ((dig < 0) | (dig > 9)).any():
        return None
    m = None
    num = lambda cols: sum(dig[:, digit_cols.index(c)] * 10 ** (len(cols) - 1 - k) for k, c in enumerate(cols))
    day, month, year = num([0, 1]), num([3, 4]), num([6, 7, 8, 9])
    hour, minute, sec, micro = num([11, 12]), num([14, 15]), num([17, 18]), num([20, 21, 22, 23, 24, 25])
    if ((month < 1) | (month > 12) | (day < 1) | (hour > 23) | (minute > 59) | (sec > 59)).any():
        return None
    if ((year < 1970) | (year > 2261)).any():
        return None
    months = (year - 1970).astype('datetime64[Y]').astype('datetime64[M]') + (month - 1).astype('timedelta64[M]')
    days = months.astype('datetime64[D]') + (day - 1).astype('timedelta64[D]')
    if (days.astype('datetime64[M]') != months).any():     # e.g. 31-02
        return None
    us = (days.astype('datetime64[us]')
          + ((hour * 60 + minute) * 60 + sec).astype('timedelta64[s]').astype('timedelta64[us]')
          + micro.astype('timedelta64[us]'))
    return pd.Series(us.astype('datetime64[ns]'), index=col.index, name=col.name)


def parse_timestamps(col, errors='raise'):
    """`pd.to_datetime(col, dayfirst=True, errors=errors)`, but fast for the
    normalised 'DD-MM-YYYY HH:MM:SS.ffffff' strings the upload page produces
    (the pandas string parser dominates pipeline time on large recordings)."""
    fast = parse_ddmmyyyy_fast(col)
    if fast is not None:
        return fast
    return pd.to_datetime(col, dayfirst=True, errors=errors)


# =============================================================================
# DEAD ZONE FILTERING
# =============================================================================

def apply_dead_zones(df, dead_zones, subject_mapping=None, dz_mode='permissive'):
    """Mark positions inside dead zones as NaN.

    Parameters
    ----------
    df : pd.DataFrame
        Processed DataFrame with MultiIndex (Date, TagId) and columns
        including X, Y, Time.
    dead_zones : list of dict
        Each dict has x_min, x_max, y_min, y_max, and optionally label.
    subject_mapping : dict or None
        {subject_name: [tag1, tag2, ...]}. Only used in conservative mode.
        When None (default), behaves as single-tag mode: no propagation.
    dz_mode : str
        'permissive' (default) — NaN only the specific tag in the dead zone.
        'conservative' — if ANY tag of a multi-tag subject is in a dead zone
        at a given timestep, NaN ALL tags for that subject at that timestep.

    Returns
    -------
    pd.DataFrame
        DataFrame with dead-zone positions set to NaN.
    """
    if not dead_zones:
        return df

    df = df.copy()

    # ── Identify all per-tag dead-zone hits ──
    in_any_zone = np.zeros(len(df), dtype=bool)

    for zone in dead_zones:
        label = zone.get('label', f"({zone['x_min']:.1f}-{zone['x_max']:.1f}, "
                         f"{zone['y_min']:.1f}-{zone['y_max']:.1f})")
        in_zone = (
            (df['X'] >= zone['x_min']) & (df['X'] <= zone['x_max']) &
            (df['Y'] >= zone['y_min']) & (df['Y'] <= zone['y_max'])
        )
        count = in_zone.sum()
        in_any_zone |= in_zone.values
        log.info(f"  Dead zone '{label}': {count:,} per-tag hits")

    # ── Conservative propagation for multi-tag subjects ──
    if dz_mode == 'conservative' and subject_mapping:
        tag_to_subject = {}
        multi_subjects = set()
        for subject, tags in subject_mapping.items():
            if len(tags) > 1:
                multi_subjects.add(subject)
                for tag in tags:
                    tag_to_subject[tag] = subject

        if tag_to_subject and in_any_zone.any():
            df_reset = df.reset_index()
            df_reset['_row_idx'] = np.arange(len(df_reset))
            df_reset['_subject'] = df_reset['TagId'].map(tag_to_subject)
            df_reset['_in_dz'] = in_any_zone

            has_subj = df_reset['_subject'].notna()
            dz_hits = df_reset.loc[has_subj & df_reset['_in_dz'],
                                   ['Date', 'Time', '_subject']].drop_duplicates()

            if len(dz_hits) > 0:
                flagged = df_reset[has_subj].merge(
                    dz_hits, on=['Date', '_subject', 'Time'], how='inner'
                )
                propagated_indices = flagged['_row_idx'].values
                n_before = in_any_zone.sum()
                in_any_zone[propagated_indices] = True
                n_propagated = in_any_zone.sum() - n_before
                log.info(f"  Conservative mode: propagated {n_propagated:,} additional NaNs "
                         f"across multi-tag subjects")

    total_removed = in_any_zone.sum()
    df.loc[in_any_zone, ['X', 'Y']] = np.nan
    log.info(f"  Total dead zone samples nullified: {total_removed:,} (mode: {dz_mode})")

    return df


def dead_zone_impact(raw_df, dead_zones):
    """Preview how dead zones affect data quality WITHOUT running the pipeline.

    Operates on raw data (before resampling). Counts how many raw position
    samples per tag fall inside each dead zone.

    Parameters
    ----------
    raw_df : pd.DataFrame
        Raw data with columns X, Y, TagId.
    dead_zones : list of dict
        Each dict has x_min, x_max, y_min, y_max, label.

    Returns
    -------
    dict with:
        'per_zone' : list of dict — per-zone impact stats
        'per_tag'  : pd.DataFrame — per-tag before/after NaN rates
        'total_affected' : int — total samples that would be nullified
        'total_samples'  : int — total samples in raw data
    """
    if not dead_zones:
        return {
            'per_zone': [],
            'per_tag': pd.DataFrame(),
            'total_affected': 0,
            'total_samples': len(raw_df),
        }

    valid_before = raw_df['X'].notna() & raw_df['Y'].notna()

    in_any_zone = np.zeros(len(raw_df), dtype=bool)
    per_zone = []

    for zone in dead_zones:
        label = zone.get('label', 'Unnamed')
        in_zone = (
            (raw_df['X'] >= zone['x_min']) & (raw_df['X'] <= zone['x_max']) &
            (raw_df['Y'] >= zone['y_min']) & (raw_df['Y'] <= zone['y_max'])
        )
        count = in_zone.sum()
        tags_affected = raw_df.loc[in_zone, 'TagId'].nunique() if count > 0 else 0
        per_zone.append({
            'label': label,
            'samples_affected': int(count),
            'tags_affected': int(tags_affected),
            'pct_of_total': count / len(raw_df) * 100 if len(raw_df) > 0 else 0,
        })
        in_any_zone |= in_zone.values

    tags = sorted(raw_df['TagId'].unique(), key=str)
    tag_rows = []
    for tag in tags:
        tag_mask = raw_df['TagId'] == tag
        n_total = tag_mask.sum()
        n_valid_before = (tag_mask & valid_before).sum()
        n_in_zone = (tag_mask & in_any_zone).sum()
        n_valid_after = n_valid_before - n_in_zone

        nan_pct_before = (1 - n_valid_before / n_total) * 100 if n_total > 0 else 0
        nan_pct_after = (1 - n_valid_after / n_total) * 100 if n_total > 0 else 0

        tag_rows.append({
            'TagId': tag,
            'total_samples': int(n_total),
            'valid_before': int(n_valid_before),
            'in_dead_zone': int(n_in_zone),
            'valid_after': int(n_valid_after),
            'nan_pct_before': round(nan_pct_before, 1),
            'nan_pct_after': round(nan_pct_after, 1),
            'increase_pct': round(nan_pct_after - nan_pct_before, 1),
        })

    return {
        'per_zone': per_zone,
        'per_tag': pd.DataFrame(tag_rows),
        'total_affected': int(in_any_zone.sum()),
        'total_samples': len(raw_df),
    }


# =============================================================================
# TIME WINDOW FILTERING
# =============================================================================

def _time_of_day_us(ts):
    """Microseconds since midnight per row (same resolution as Series.dt.time)."""
    return ((ts - ts.dt.normalize()) // pd.Timedelta(microseconds=1)).to_numpy()


def _clock_us(t):
    """datetime.time -> microseconds since midnight."""
    return ((t.hour * 60 + t.minute) * 60 + t.second) * 1_000_000 + t.microsecond


def apply_exclusions(df, exclusion_periods):
    """Remove rows falling within specified time exclusion windows."""
    if not exclusion_periods:
        return df
    validate_dataframe(df, ['TimeStamp'], "apply_exclusions input")

    df = df.copy()
    # TODO(thesis-cleanup): redundant re-parse — TimeStamp is already DD-MM-YYYY
    # from upload-layer normalization. Refactor to pass datetimes through
    # and delete this line. See README/handoff notes on dayfirst workaround.
    df['TimeStamp'] = parse_timestamps(df['TimeStamp'])
    mask = np.zeros(len(df), dtype=bool)
    day = df['TimeStamp'].dt.normalize()
    tod = _time_of_day_us(df['TimeStamp'])

    for date_str, periods in exclusion_periods.items():
        target_date = pd.to_datetime(date_str, dayfirst=True).date()
        date_match = (day == pd.Timestamp(target_date)).to_numpy()
        for start_str, end_str in periods:
            start_us = _clock_us(pd.to_datetime(start_str).time())
            end_us = _clock_us(pd.to_datetime(end_str).time())
            period_mask = date_match & (tod >= start_us) & (tod <= end_us)
            if period_mask.sum() > 0:
                log.info(f"    Excluded {date_str} {start_str}-{end_str}: {period_mask.sum():,} rows")
            mask = mask | period_mask

    return df[~mask].reset_index(drop=True)


def apply_inclusions(df, inclusion_periods):
    """Keep ONLY rows falling within specified time windows."""
    if not inclusion_periods:
        return df

    validate_dataframe(df, ['TimeStamp'], "apply_inclusions input")

    df = df.copy()
    # TODO(thesis-cleanup): redundant re-parse — TimeStamp is already DD-MM-YYYY
    # from upload-layer normalization. Refactor to pass datetimes through
    # and delete this line. See README/handoff notes on dayfirst workaround.
    df['TimeStamp'] = parse_timestamps(df['TimeStamp'])
    keep_mask = np.zeros(len(df), dtype=bool)
    day = df['TimeStamp'].dt.normalize()
    tod = _time_of_day_us(df['TimeStamp'])

    total_kept = 0
    for date_str, periods in inclusion_periods.items():
        target_date = pd.to_datetime(date_str, dayfirst=True).date()
        date_match = (day == pd.Timestamp(target_date)).to_numpy()
        for start_str, end_str in periods:
            start_us = _clock_us(pd.to_datetime(start_str).time())
            end_us = _clock_us(pd.to_datetime(end_str).time())
            period_mask = date_match & (tod >= start_us) & (tod <= end_us)
            n_rows = period_mask.sum()
            if n_rows > 0:
                log.info(f"    Included {date_str} {start_str}-{end_str}: {n_rows:,} rows")
                total_kept += n_rows
            keep_mask = keep_mask | period_mask

    n_removed = len(df) - keep_mask.sum()
    log.info(
        f"    Inclusion filter: kept {total_kept:,} rows, "
        f"removed {n_removed:,} rows ({n_removed/len(df)*100:.1f}%)"
    )
    return df[keep_mask].reset_index(drop=True)


def filter_subset_windows(df_proc, windows, window_mode):
    """Filter a processed (MultiIndex) DataFrame by time windows."""
    if not windows or not window_mode:
        return df_proc

    df = df_proc.copy()
    times = pd.to_datetime(df['Time'])
    tod = _time_of_day_us(times)
    dates = df.index.get_level_values('Date')

    hit = np.zeros(len(df), dtype=bool)
    for w in windows:
        start_us = _clock_us(pd.to_datetime(w['start']).time())
        end_us = _clock_us(pd.to_datetime(w['end']).time())
        hit |= np.asarray(dates == w['date']) & (tod >= start_us) & (tod <= end_us)

    df = df[hit] if window_mode == 'include' else df[~hit]

    return df


# =============================================================================
# RESAMPLE / REINDEX / FILTER
# =============================================================================

def _long_nan_runs(na, max_len):
    """Boolean mask: True where `na` lies inside a run of True longer than max_len."""
    edges = np.diff(np.concatenate(([0], na.astype(np.int8), [0])))
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1)
    mask = np.zeros(len(na), dtype=bool)
    for a, b in zip(starts, ends):
        if b - a > max_len:
            mask[a:b] = True
    return mask


def resample_data(dataframes, timestep_ms, max_interpolation=5):
    """Resample tracking data to regular time intervals per (tag, date).

    Behaviour change vs v9 (2026-05): resampling is now grouped by
    (TagId, calendar-date) instead of by TagId alone. This avoids
    pathological behaviour when a tag has data on multiple non-adjacent
    dates: pandas' resample() previously generated a regular-grid index
    spanning the full TimeStamp range of each tag, including the days
    between recording sessions. For two recording dates 21 days apart at
    a 100 ms timestep, that meant ~18 million empty bins per tag and
    per-tag resample times of ~50 seconds. Grouping by (TagId, Date)
    keeps each resample call confined to a single recording day.

    Numerical equivalence on single-date data: when each tag's data
    falls on exactly one calendar date, the (TagId, Date) groupby is
    identical in behaviour to the original TagId-only groupby. Existing
    single-day test outputs are byte-identical.

    Known caveat: recordings that cross midnight are split at the date
    boundary. Continuous sessions spanning two calendar dates will have
    their resample grid reset at 00:00, and interpolation will not
    bridge across the boundary. For diurnal animal tracking this is
    rarely an issue; for nocturnal or 24h studies, this function would
    need to be replaced with a gap-based segmentation strategy.
    Documented as future work.
    """
    validate_positive(timestep_ms, "timestep_ms")
    results = []
    for df_i in dataframes:
        validate_dataframe(df_i, ['TimeStamp', 'TagId'], "resample_data input")
        df_i = df_i.copy()
        df_i['TagId'] = df_i['TagId'].astype(str)
        # TODO(thesis-cleanup): redundant re-parse — TimeStamp is already DD-MM-YYYY
        # from upload-layer normalization. Refactor to pass datetimes through
        # and delete this line. See README/handoff notes on dayfirst workaround.
        df_i['TimeStamp'] = parse_timestamps(df_i['TimeStamp'])
        # Calendar-date key for the (tag, date) grouping. Kept out of the
        # frame so the numeric-column selection below is unchanged.
        date_key = df_i['TimeStamp'].dt.normalize()

        resampled = []
        # One groupby pass instead of a full-frame boolean mask per (tag, date)
        # pair (that was O(pairs x rows)). sort=False keeps first-appearance
        # order and each group keeps its original row order, so every
        # per-group resample sees exactly the input it did before.
        # tqdm desc unchanged so existing progress-bar matching stays meaningful.
        groups = df_i.groupby([df_i['TagId'], date_key], sort=False)
        for (tag, _), tag_data in tqdm(list(groups), desc='    Resample', leave=False):
            tag_data = tag_data.set_index('TimeStamp').sort_index()
            numeric = tag_data.select_dtypes(include='number').resample(f'{timestep_ms}ms').mean()
            observed_na = numeric.isna()
            numeric = numeric.interpolate('linear', limit_direction='both', limit_area='inside', limit=max_interpolation)
            # pandas' `limit` fills the first N samples of a gap of ANY length,
            # which invents positions at the edges of long gaps. Only gaps of
            # <= max_interpolation samples may be bridged; longer ones stay NaN.
            for col in numeric.columns:
                na = observed_na[col].to_numpy()
                if na.any():
                    long_gap = _long_nan_runs(na, max_interpolation)
                    if long_gap.any():
                        numeric.loc[long_gap, col] = np.nan
            numeric['TagId'] = tag
            resampled.append(numeric.reset_index())
        results.append(pd.concat(resampled, ignore_index=True))
    return results


def reindex_data(dataframes, timestep_ms):
    """Consolidate resampled data, date/time, and build tag index."""
    df = pd.concat(dataframes, ignore_index=True) if isinstance(dataframes, list) else dataframes.copy()
    validate_dataframe(df, ['TimeStamp', 'TagId'], "reindex_data input")

    # TODO(thesis-cleanup): redundant re-parse — TimeStamp is already DD-MM-YYYY
    # from upload-layer normalization. Refactor to pass datetimes through
    # and delete this line. See README/handoff notes on dayfirst workaround.
    df['TimeStamp'] = parse_timestamps(df['TimeStamp'])
    # Format each distinct day once instead of strftime-ing every row.
    codes, days = pd.factorize(df['TimeStamp'].dt.normalize())
    if (codes < 0).any():
        df['Date'] = df['TimeStamp'].dt.strftime('%d-%m-%Y')
    else:
        labels = np.asarray(pd.DatetimeIndex(days).strftime('%d-%m-%Y'), dtype=object)
        df['Date'] = labels[codes]
    df['Time'] = df['TimeStamp']

    df['TagId'] = df['TagId'].astype(str)
    tags = dict(enumerate(df['TagId'].unique()))
    dates = df['Date'].unique()
    df = df.drop(columns=['TimeStamp', 'Z'], errors='ignore').set_index(['Date', 'TagId'])
    return df, tags, dates


def calc_velocity(df, timestep_ms, max_gap_factor=3):
    """Calculate velocity for each tag, handling time gaps."""
    return _velocity_by_group(df, timestep_ms, max_gap_factor)


def _velocity_by_group(df, timestep_ms, max_gap_factor):
    """Vectorised per-(Date, TagId) velocity.

    Rows are stably ordered by group key (what groupby(sort=True) yields), then
    one diff over the whole array is taken with the first row of every group
    masked to NaN. Same arithmetic as the old per-group loop, without the loop.
    """
    validate_positive(timestep_ms, "timestep_ms")
    max_gap_s = max_gap_factor * (timestep_ms / 1000)

    codes = df.groupby(['Date', 'TagId'], sort=True).ngroup().to_numpy()
    order = np.argsort(codes, kind='stable')
    codes = codes[order]
    n = len(order)

    x = df['X'].to_numpy(dtype=float)[order]
    y = df['Y'].to_numpy(dtype=float)[order]
    times = df['Time'].to_numpy()[order]

    first = np.ones(n, dtype=bool)
    first[1:] = codes[1:] != codes[:-1]

    dt_s = np.full(n, np.nan)
    dx = np.full(n, np.nan)
    dy = np.full(n, np.nan)
    if n > 1:
        dt_s[1:] = np.diff(times).astype('timedelta64[ns]').astype(float) / 1e9
        dx[1:] = np.diff(x)
        dy[1:] = np.diff(y)
    dt_s[first] = np.nan
    dx[first] = np.nan
    dy[first] = np.nan

    velocity = np.sqrt(dx**2 + dy**2) / np.where(dt_s > 0, dt_s, np.nan)
    velocity[dt_s > max_gap_s] = np.nan

    return pd.DataFrame({'Time': times, 'Velocity': velocity.astype(float)},
                        index=df.index[order])


def refresh_velocity(df, timestep_ms, max_gap_factor=3):
    """Recompute Velocity from the current X/Y (e.g. after dead zones NaN'd
    positions), so Velocity is never finite where the position is NaN."""
    df = df.sort_index().copy()
    df['Velocity'] = calc_velocity(df, timestep_ms, max_gap_factor)['Velocity'].values
    return df


def apply_smoothing(df, window_seconds, timestep_ms):
    """Apply a per-tag rolling-median smoothing to X and Y positions.

    Window is specified in seconds and converted to an odd sample count
    (rounded up to the next odd number). This makes the smoothing window
    behavior invariant to the resampling rate at the second-level — the
    same `window_seconds` value gives equivalent temporal smoothing across
    datasets sampled at different rates.

    NaN handling within the rolling window uses majority rule:
    `min_periods = (N + 1) // 2`. Smoothing requires at least a majority
    of in-window samples to be non-NaN; otherwise the output is NaN. This
    fades smoothing to NaN at the edges of long gaps rather than producing
    false-confidence smoothed values from one or two surviving samples.

    Smoothing is applied per-tag (per (Date, TagId) group) so the rolling
    window never crosses tag boundaries.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with MultiIndex (Date, TagId) and X, Y columns. NaN
        positions (e.g. from out-of-bounds rejection) are honored by the
        rolling median.
    window_seconds : float
        Smoothing window in seconds. Must be positive.
    timestep_ms : int
        Sampling interval in milliseconds. Used to convert seconds → samples.

    Returns
    -------
    pd.DataFrame
        Copy of df with X and Y columns replaced by their smoothed values.
        Other columns are passed through unchanged.

    Notes
    -----
    The thesis-defensible framing is: smoothing reduces the noise floor
    of the trajectory before velocity is measured, which makes the
    velocity threshold less sensitive to single-sample artifacts. It is
    NOT a "catch sub-threshold jumps the velocity filter missed" feature
    — that framing contradicts the position of smoothing in the pipeline
    (smoothing runs before velocity is computed, so velocity sees only
    smoothed positions).
    """
    validate_positive(window_seconds, "window_seconds")
    validate_positive(timestep_ms, "timestep_ms")

    samples = max(1, int(round(window_seconds / (timestep_ms / 1000))))
    if samples % 2 == 0:
        samples += 1
    min_periods = (samples + 1) // 2

    df = df.copy()
    df = df.sort_index()

    # Group by (Date, TagId) so the rolling window does not cross tags.
    # transform applies the rolling median within each group and aligns
    # the result back to the original index.
    grouped = df.groupby(level=['Date', 'TagId'])
    df['X'] = grouped['X'].transform(
        lambda s: s.rolling(window=samples, min_periods=min_periods, center=True).median()
    )
    df['Y'] = grouped['Y'].transform(
        lambda s: s.rolling(window=samples, min_periods=min_periods, center=True).median()
    )

    log.info(f"  Smoothing applied: window={window_seconds}s ({samples} samples), "
             f"min_periods={min_periods}")
    return df


def filter_data(df, max_velocity, timestep_ms, x_bounds, y_bounds, max_gap_factor=3,
                smoothing_enabled=False, smoothing_window_sec=None):
    """Filter positions outside spatial bounds and above max velocity.

    Pipeline (per-tag, applied to all tags simultaneously via groupby):
        1. Out-of-bounds → NaN (rectangular spatial bounds)
        2. Optional rolling-median smoothing on X, Y (if smoothing_enabled)
        3. Velocity calculation on (possibly smoothed) positions
        4. Velocity > max_velocity → NaN on X, Y, Velocity

    The optional smoothing step (2) sits between out-of-bounds rejection
    and velocity calculation. This means:
      - Out-of-bounds artifacts do not contaminate the rolling median.
      - The velocity filter operates on smoothed positions, so the
        threshold is applied to a noise-reduced signal.

    Parameters
    ----------
    df : pd.DataFrame
        Resampled, reindexed DataFrame with MultiIndex (Date, TagId)
        and X, Y, Time columns.
    max_velocity : float
        Velocity threshold in m/s.
    timestep_ms : int
        Sampling interval in milliseconds.
    x_bounds, y_bounds : tuple of (float, float)
        Spatial bounds (min, max) for the rectangular bounding box.
    max_gap_factor : int, default 3
        Velocity is set to NaN if dt > max_gap_factor * (timestep_ms/1000).
    smoothing_enabled : bool, default False
        If True, apply rolling-median smoothing between bounds rejection
        and velocity calculation.
    smoothing_window_sec : float or None, default None
        Smoothing window in seconds. Required when smoothing_enabled=True.

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame with X, Y, Velocity columns. NaN where filtered.
    """
    df = df.copy()
    df = df.sort_index()

    out_of_bounds = (
        (df['X'] < x_bounds[0]) | (df['X'] > x_bounds[1]) |
        (df['Y'] < y_bounds[0]) | (df['Y'] > y_bounds[1])
    )
    df.loc[out_of_bounds, ['X', 'Y']] = np.nan

    if smoothing_enabled:
        if smoothing_window_sec is None:
            raise ValueError(
                "smoothing_enabled=True but smoothing_window_sec is None. "
                "Pass a positive window in seconds."
            )
        df = apply_smoothing(df, smoothing_window_sec, timestep_ms)

    vel_df = calc_velocity(df, timestep_ms, max_gap_factor)
    df['Velocity'] = vel_df['Velocity'].values
    too_fast = (df['Velocity'] > max_velocity).fillna(False)
    df.loc[too_fast, ['X', 'Y', 'Velocity']] = np.nan

    return df


def compute_velocity_distribution(df, timestep_ms, x_bounds, y_bounds,
                                  max_gap_factor=3,
                                  smoothing_enabled=False,
                                  smoothing_window_sec=None,
                                  selected_tags=None):
    """Compute the empirical velocity distribution for the velocity advisor.

    Mirrors the first three steps of `filter_data` exactly:
        out-of-bounds NaN → optional smoothing → velocity calculation
    but stops *before* the velocity threshold is applied. This is the
    distribution the velocity threshold will operate on, so a percentile
    of this distribution is the right basis for a recommended threshold.

    The velocity threshold itself is intentionally NOT in the dependency
    graph — that would be circular: the recommendation must not depend
    on the value it's recommending.

    Parameters
    ----------
    df : pd.DataFrame
        Resampled, reindexed DataFrame (output of `reindex_data`).
    timestep_ms : int
        Sampling interval in milliseconds.
    x_bounds, y_bounds : tuple of (float, float)
        Spatial bounds (min, max).
    max_gap_factor : int, default 3
        Same meaning as in `filter_data`.
    smoothing_enabled : bool, default False
        If True, apply smoothing before velocity calc (mirrors filter_data).
    smoothing_window_sec : float or None, default None
        Smoothing window in seconds. Required when smoothing_enabled=True.
    selected_tags : list of str or None, default None
        If provided, restrict the distribution to these tag IDs only.
        None means use all tags in df.

    Returns
    -------
    velocities : np.ndarray
        1D array of finite velocity values (NaN samples dropped).
        These are the values from which a percentile-based recommendation
        should be drawn.
    per_tag : dict[str, np.ndarray]
        Mapping from TagId → finite velocity array, for the per-tag
        breakdown view. Tags with no finite velocities are included with
        empty arrays.
    """
    df = df.copy()
    df = df.sort_index()

    if selected_tags is not None:
        mask = df.index.get_level_values('TagId').isin(selected_tags)
        df = df.loc[mask]
        if len(df) == 0:
            return np.array([]), {}

    out_of_bounds = (
        (df['X'] < x_bounds[0]) | (df['X'] > x_bounds[1]) |
        (df['Y'] < y_bounds[0]) | (df['Y'] > y_bounds[1])
    )
    df.loc[out_of_bounds, ['X', 'Y']] = np.nan

    if smoothing_enabled:
        if smoothing_window_sec is None:
            raise ValueError(
                "smoothing_enabled=True but smoothing_window_sec is None."
            )
        df = apply_smoothing(df, smoothing_window_sec, timestep_ms)

    vel_df = calc_velocity(df, timestep_ms, max_gap_factor)
    velocities_full = vel_df['Velocity'].values
    finite = velocities_full[np.isfinite(velocities_full)]

    per_tag = {}
    # factorize keeps first-appearance order, same as .unique() did.
    tag_codes, tag_names = pd.factorize(vel_df.index.get_level_values('TagId'))
    for k, tag in enumerate(tag_names):
        tag_vels = velocities_full[tag_codes == k]
        per_tag[str(tag)] = tag_vels[np.isfinite(tag_vels)]

    return finite, per_tag


# =============================================================================
# MULTI-TAG MERGE
# =============================================================================

def merge_tags_to_subjects(df, subject_mapping, inter_tag_threshold=1.0):
    """Merge multi-tag data into per-subject positions.

    For single-tag subjects, renames TagId → subject name.
    For multi-tag subjects:
      - Both valid & inter-tag distance < threshold → centroid (mean)
      - Both valid & distance ≥ threshold → NaN (consistency failure)
      - One valid → use that tag (single-tag fallback)
      - None valid → NaN
    """
    if not subject_mapping:
        return df, {}

    single_tag_map = {}
    multi_tag_map = {}
    for subject, tags in subject_mapping.items():
        if len(tags) == 1:
            single_tag_map[subject] = tags[0]
        else:
            multi_tag_map[subject] = tags

    keep_cols = ['Time', 'X', 'Y']
    extra_cols = [c for c in df.columns if c not in keep_cols and c != 'Velocity']
    keep_cols.extend(extra_cols)
    keep_cols = [c for c in keep_cols if c in df.columns]

    merged_chunks = []
    diagnostics = {}

    # Single-tag subjects
    for subject, tag in single_tag_map.items():
        tag_data = df.loc[df.index.get_level_values('TagId') == tag, keep_cols].copy()
        if len(tag_data) == 0:
            continue
        tag_data = tag_data.reset_index()
        tag_data['TagId'] = subject
        merged_chunks.append(tag_data)

    # Multi-tag subjects
    for subject, tags in multi_tag_map.items():
        log.info(f"  Merging {len(tags)} tags for subject '{subject}': {tags}")
        diag = {
            'n_total': 0,
            'n_centroid': 0,
            'n_fallback': 0,
            'n_consistency_fail': 0,
            'n_all_nan': 0,
            'inter_tag_distances': [],
        }

        if len(tags) == 2:
            df_merged_subj = _merge_two_tags(
                df, tags[0], tags[1], subject,
                inter_tag_threshold, diag, keep_cols,
            )
        else:
            df_merged_subj = _merge_n_tags(
                df, tags, subject,
                inter_tag_threshold, diag, keep_cols,
            )

        if df_merged_subj is not None and len(df_merged_subj) > 0:
            merged_chunks.append(df_merged_subj)

        diagnostics[subject] = diag
        total = diag['n_total']
        if total > 0:
            log.info(
                f"    {subject}: {total:,} timesteps — "
                f"{diag['n_centroid']/total*100:.1f}% centroid, "
                f"{diag['n_fallback']/total*100:.1f}% fallback, "
                f"{diag['n_consistency_fail']/total*100:.1f}% consistency fail, "
                f"{diag['n_all_nan']/total*100:.1f}% all NaN"
            )

    if not merged_chunks:
        raise ValueError("No data remaining after merge — check subject mapping")

    df_out = pd.concat(merged_chunks, ignore_index=True)
    df_out = df_out.set_index(['Date', 'TagId'])

    return df_out, diagnostics


def _merge_two_tags(df, tag_a, tag_b, subject_name, threshold, diag, keep_cols):
    """Vectorized merge for exactly 2 tags."""
    mask_a = df.index.get_level_values('TagId') == tag_a
    mask_b = df.index.get_level_values('TagId') == tag_b
    data_a = df.loc[mask_a, ['Time', 'X', 'Y']].reset_index()
    data_b = df.loc[mask_b, ['Time', 'X', 'Y']].reset_index()

    if len(data_a) == 0 and len(data_b) == 0:
        return None

    data_a = data_a.rename(columns={'X': 'Xa', 'Y': 'Ya'}).drop(columns=['TagId'])
    data_b = data_b.rename(columns={'X': 'Xb', 'Y': 'Yb'}).drop(columns=['TagId'])

    aligned = pd.merge(data_a, data_b, on=['Date', 'Time'], how='outer')

    a_valid = aligned['Xa'].notna() & aligned['Ya'].notna()
    b_valid = aligned['Xb'].notna() & aligned['Yb'].notna()
    both_valid = a_valid & b_valid

    inter_dist = np.full(len(aligned), np.nan)
    if both_valid.any():
        inter_dist[both_valid] = np.sqrt(
            (aligned.loc[both_valid, 'Xa'] - aligned.loc[both_valid, 'Xb'])**2 +
            (aligned.loc[both_valid, 'Ya'] - aligned.loc[both_valid, 'Yb'])**2
        ).values

    consistent = both_valid & (inter_dist < threshold)
    inconsistent = both_valid & (inter_dist >= threshold)

    merged_x = np.full(len(aligned), np.nan)
    merged_y = np.full(len(aligned), np.nan)

    merged_x[consistent] = (aligned.loc[consistent, 'Xa'].values +
                            aligned.loc[consistent, 'Xb'].values) / 2
    merged_y[consistent] = (aligned.loc[consistent, 'Ya'].values +
                            aligned.loc[consistent, 'Yb'].values) / 2

    only_a = a_valid & ~b_valid
    merged_x[only_a] = aligned.loc[only_a, 'Xa'].values
    merged_y[only_a] = aligned.loc[only_a, 'Ya'].values

    only_b = b_valid & ~a_valid
    merged_x[only_b] = aligned.loc[only_b, 'Xb'].values
    merged_y[only_b] = aligned.loc[only_b, 'Yb'].values

    n = len(aligned)
    diag['n_total'] = n
    diag['n_centroid'] = int(consistent.sum())
    diag['n_fallback'] = int(only_a.sum() + only_b.sum())
    diag['n_consistency_fail'] = int(inconsistent.sum())
    diag['n_all_nan'] = int((~a_valid & ~b_valid).sum())
    diag['inter_tag_distances'] = inter_dist[both_valid].tolist()

    result = pd.DataFrame({
        'Date': aligned['Date'],
        'TagId': subject_name,
        'Time': aligned['Time'],
        'X': merged_x,
        'Y': merged_y,
    })

    return result


def _merge_n_tags(df, tags, subject_name, threshold, diag, keep_cols):
    """General merge for N tags (N >= 3).

    Vectorised over timesteps: each (Date, Time) group is laid out as one row of
    a (groups x N) array, so distances, consistency checks and centroids are
    computed for all timesteps at once. Results, diagnostics counts and the
    order of `inter_tag_distances` match the earlier per-timestep loop.
    """
    tag_mask = df.index.get_level_values('TagId').isin(tags)
    tag_data = df.loc[tag_mask, ['Time', 'X', 'Y']].reset_index()

    if len(tag_data) == 0:
        return None

    gb = tag_data.groupby(['Date', 'Time'], sort=True)
    gid = gb.ngroup().to_numpy()
    slot = gb.cumcount().to_numpy()
    keys = gb.size().index
    n_groups = len(keys)
    width = int(slot.max()) + 1

    X = np.full((n_groups, width), np.nan)
    Y = np.full((n_groups, width), np.nan)
    X[gid, slot] = tag_data['X'].to_numpy(dtype=float)
    Y[gid, slot] = tag_data['Y'].to_numpy(dtype=float)

    valid = ~np.isnan(X) & ~np.isnan(Y)
    n_valid = valid.sum(axis=1)

    # Pairwise distances between valid slots, group-major then (a, b) order.
    pair_d = []
    for a in range(width):
        for b in range(a + 1, width):
            both = valid[:, a] & valid[:, b]
            d = np.full(n_groups, np.nan)
            dx = X[both, a] - X[both, b]
            dy = Y[both, a] - Y[both, b]
            # np.power with an array exponent uses libm pow, which is what the
            # old scalar loop used; `**2` on arrays is a plain square and can
            # differ in the last bit.
            two = np.full(len(dx), 2.0)
            d[both] = np.sqrt(np.power(dx, two) + np.power(dy, two))
            pair_d.append(d)
    if pair_d:
        D = np.column_stack(pair_d)
        finite = ~np.isnan(D)
        max_dist = np.where(finite, D, 0.0).max(axis=1)
        diag['inter_tag_distances'].extend(D[finite].tolist())
    else:
        max_dist = np.zeros(n_groups)

    centroid = (n_valid >= 2) & (max_dist < threshold)
    fallback = n_valid == 1

    out_x = np.full(n_groups, np.nan)
    out_y = np.full(n_groups, np.nan)

    # Single valid tag → use it.
    if fallback.any():
        first_valid = np.argmax(valid, axis=1)
        rows = np.flatnonzero(fallback)
        out_x[rows] = X[rows, first_valid[rows]]
        out_y[rows] = Y[rows, first_valid[rows]]

    # Centroid. np.mean of fewer than 8 values is a plain left-to-right sum
    # divided by the count; reproduce that so the result is bit-identical.
    # Longer arrays use a different summation scheme, so those (rare) rows go
    # through np.mean directly.
    rows = np.flatnonzero(centroid)
    if len(rows):
        # move valid values to the front of each row, preserving their order
        srt = np.argsort(~valid[rows], axis=1, kind='stable')
        nv = n_valid[rows]
        for out, arr in ((out_x, X), (out_y, Y)):
            compact = np.take_along_axis(arr[rows], srt, axis=1)
            total = np.zeros(len(rows))
            for k in range(width):
                total = total + np.where(k < nv, np.nan_to_num(compact[:, k]), 0.0)
            mean = total / nv
            for r in np.flatnonzero(nv >= 8):
                mean[r] = float(np.mean(compact[r, :nv[r]]))
            out[rows] = mean

    diag['n_total'] += n_groups
    diag['n_all_nan'] += int((n_valid == 0).sum())
    diag['n_fallback'] += int(fallback.sum())
    diag['n_centroid'] += int(centroid.sum())
    diag['n_consistency_fail'] += int(((n_valid >= 2) & ~centroid).sum())

    return pd.DataFrame({
        'Date': keys.get_level_values('Date'),
        'TagId': subject_name,
        'Time': keys.get_level_values('Time'),
        'X': out_x,
        'Y': out_y,
    })


def calc_velocity_for_merged(df, timestep_ms, max_gap_factor=3):
    """Recalculate velocity on merged subject-level data.

    Same logic as calc_velocity but designed to be called after merge.
    Does NOT filter by max_velocity — this is metadata only.
    """
    return _velocity_by_group(df.sort_index(), timestep_ms, max_gap_factor)


# =============================================================================
# MAIN PROCESSING PIPELINE
# =============================================================================

def _index_days(frames):
    """Calendar date of every raw row, plus the tag and date order v10 used.

    Returns a dict with
      'row_days' : per input frame, a datetime64 array with each row's date
                   (midnight), from the same timestamp parser resample_data uses
      'days'     : list of (date, 'DD-MM-YYYY' label), oldest first
      'tags'     : {i: TagId} in order of first appearance across the frames,
                   which is the order v10's reindex_data produced
      'dates'    : array of 'DD-MM-YYYY' labels in order of first appearance,
                   which is the order v10's reindex_data produced

    Why the orders match v10: resample_data groups each frame by
    (TagId, date) in order of first appearance and reindex_data then takes
    TagId / Date in the order the groups come out. A tag's (or date's) first
    group starts at its first raw row, so first appearance in the raw rows
    gives the same order.
    """
    row_days, tag_seen, day_seen = [], {}, {}
    for df_i in frames:
        validate_dataframe(df_i, ['TimeStamp', 'TagId'], "resample_data input")
        days = parse_timestamps(df_i['TimeStamp']).dt.normalize().to_numpy()
        row_days.append(days)
        valid = ~np.isnat(days)   # resample_data's groupby drops rows without a date
        for t in pd.unique(df_i['TagId'].astype(str).to_numpy()[valid]):
            tag_seen.setdefault(t, None)
        for d in pd.unique(days[valid]):
            day_seen.setdefault(d, None)
    first_seen = list(day_seen)
    labels = dict(zip(first_seen,
                      pd.DatetimeIndex(first_seen).strftime('%d-%m-%Y')))
    return {
        'row_days': row_days,
        'days': [(d, labels[d]) for d in sorted(first_seen)],
        'tags': dict(enumerate(np.array(list(tag_seen), dtype=object))),
        'dates': np.array([labels[d] for d in first_seen], dtype=object),
    }


def _rows_on_day(frames, row_days, day):
    """The rows of each frame that fall on `day` (frames with no rows are skipped)."""
    out = []
    for df_i, days in zip(frames, row_days):
        mask = days == day
        if mask.any():
            out.append(df_i[mask])
    return out


def compute_velocity_distribution_from_raw(raw_df, timestep_ms, max_interpolation,
                                           x_bounds, y_bounds, max_gap_factor=3,
                                           smoothing_enabled=False,
                                           smoothing_window_sec=None,
                                           selected_tags=None):
    """Velocity-advisor distribution straight from raw data, one date at a time.

    Same result as
        resample_data([raw_df], ...) -> reindex_data(...) ->
        compute_velocity_distribution(...)
    on the whole recording (the v10 page-2 advisor path), but only one date
    is held in memory at a time.

    Rows of tags outside `selected_tags` are dropped before resampling. Every
    step works per (date, tag), so this changes nothing in the result; it only
    saves work.

    Returns
    -------
    velocities : np.ndarray
        Finite velocities in the order v10 returned them (date label, then
        TagId, then time).
    per_tag : dict[str, np.ndarray]
        TagId -> finite velocities, keys in the order v10 produced them.
    """
    if selected_tags is not None:
        raw_df = raw_df[raw_df['TagId'].astype(str).isin([str(t) for t in selected_tags])]
        if len(raw_df) == 0:
            return np.array([]), {}
    day_index = _index_days([raw_df])
    by_label = {}
    for day, label in day_index['days']:
        day_frames = _rows_on_day([raw_df], day_index['row_days'], day)
        resampled = resample_data(day_frames, timestep_ms, max_interpolation)
        del day_frames
        df_day, _, _ = reindex_data(resampled, timestep_ms)
        del resampled
        by_label[label] = compute_velocity_distribution(
            df_day, timestep_ms=timestep_ms, x_bounds=x_bounds, y_bounds=y_bounds,
            max_gap_factor=max_gap_factor, smoothing_enabled=smoothing_enabled,
            smoothing_window_sec=smoothing_window_sec, selected_tags=None)
        del df_day
    order = sorted(by_label)          # v10 sorted the whole table by Date label
    velocities = np.concatenate([by_label[k][0] for k in order]) if order else np.array([])
    pieces = {}
    for k in order:
        for tag, arr in by_label[k][1].items():
            pieces.setdefault(tag, []).append(arr)
    per_tag = {tag: np.concatenate(arrs) for tag, arrs in pieces.items()}
    return velocities, per_tag


def process_all(raw_data, timestep_ms, max_velocity,
                x_bounds, y_bounds, max_gap_factor=3,
                max_interpolation=5,
                subject_mapping=None, inter_tag_threshold=1.0,
                dead_zones=None, dz_mode='permissive',
                smoothing_enabled=False, smoothing_window_sec=None):
    """Run the full processing pipeline.

    Pipeline (no multi-tag):
        resample → reindex → filter [out-of-bounds → (smoothing) → velocity]

    Pipeline (with multi-tag):
        resample → reindex → filter (per-tag) → dead zones (per-tag)
        → merge tags → subjects → recalculate velocity (per-subject)

    When subject_mapping is None, behavior is single-tag mode — dead
    zones are NOT applied here (the caller must apply them afterwards
    via apply_dead_zones). This matches the original uploaded behavior.

    The optional smoothing step is applied per-tag inside `filter_data`
    (between out-of-bounds rejection and velocity calculation). It
    runs BEFORE the multi-tag merge in multi-tag mode, so each tag's
    trajectory is smoothed before being centroided into a subject.
    Note: in multi-tag mode, the post-merge velocity recalculation
    operates on the centroid of already-smoothed positions, so there
    is no separate post-merge smoothing step.

    Returns
    -------
    df : pd.DataFrame
    tags : dict
    dates : array
    merge_diagnostics : dict or None
        None in single-tag mode.
    """
    # v11: resample -> reindex -> filter one calendar date at a time.
    # Each of these steps works per (date, tag), so joining the days in the
    # order filter_data's sort_index would give reproduces the v10 table.
    log.info("Steps 1-3: Resampling, reindexing, filtering (one date at a time)...")
    frames = raw_data if isinstance(raw_data, list) else [raw_data]
    day_index = _index_days(frames)
    per_day = {}
    for day, label in day_index['days']:
        day_frames = _rows_on_day(frames, day_index['row_days'], day)
        resampled = resample_data(day_frames, timestep_ms, max_interpolation)
        del day_frames
        df_day, _, _ = reindex_data(resampled, timestep_ms)
        del resampled
        per_day[label] = filter_data(df_day, max_velocity, timestep_ms, x_bounds, y_bounds,
                                     max_gap_factor,
                                     smoothing_enabled=smoothing_enabled,
                                     smoothing_window_sec=smoothing_window_sec)
        del df_day
    df = pd.concat([per_day.pop(label) for label in sorted(per_day)])
    tags = day_index['tags']
    dates = day_index['dates']

    merge_diagnostics = None

    if subject_mapping:
        # ── Dead zones (per-tag, before merge) ──
        if dead_zones:
            log.info("Step 4: Applying dead zones (per-tag, before merge)...")
            df = apply_dead_zones(df, dead_zones, subject_mapping, dz_mode)

        # ── Merge tags → subjects ──
        log.info("Step 5: Merging tags to subjects...")
        df, merge_diagnostics = merge_tags_to_subjects(
            df, subject_mapping, inter_tag_threshold
        )

        # ── Recalculate velocity on merged data ──
        log.info("Step 6: Recalculating velocity (per-subject)...")
        vel_df = calc_velocity_for_merged(df, timestep_ms, max_gap_factor)
        df = df.sort_index()
        vel_df = vel_df.sort_index()
        df['Velocity'] = vel_df['Velocity'].values

        tags = dict(enumerate(df.index.get_level_values('TagId').unique()))

        log.info(f"Processing complete ({len(tags)} subjects).")
    else:
        log.info("Processing complete (single-tag mode, no merge).")

    return df, tags, dates, merge_diagnostics


# =============================================================================
# STATIONARY TIME
# =============================================================================

def _sorted_date_tag_runs(df):
    """[(key, start, end)] if df's (Date, TagId) groups are contiguous blocks
    in strictly increasing key order (exactly the order groupby(sort=True)
    yields), otherwise None. Uses only the index codes; nothing is copied."""
    idx = df.index
    if (not isinstance(idx, pd.MultiIndex) or list(idx.names) != ['Date', 'TagId']
            or 'Date' in df.columns or 'TagId' in df.columns or len(df) == 0):
        return None
    c0, c1 = idx.codes
    if (c0 < 0).any() or (c1 < 0).any():
        return None
    change = (c0[1:] != c0[:-1]) | (c1[1:] != c1[:-1])
    starts = np.concatenate(([0], np.flatnonzero(change) + 1))
    ends = np.concatenate((starts[1:], [len(df)]))
    keys = [(idx.levels[0][c0[s]], idx.levels[1][c1[s]]) for s in starts]
    try:
        increasing = all(keys[k] < keys[k + 1] for k in range(len(keys) - 1))
    except TypeError:
        return None
    if not increasing:
        return None
    return [(key, int(a), int(b)) for key, a, b in zip(keys, starts, ends)]


def calc_stationary_time(df, timestep_ms, displacement_threshold=0.3,
                         window_sec=3.0):
    """Estimate per-entity stationary time using rolling displacement.

    Instantaneous velocity is too noisy at typical UWB position errors
    (~0.3m) to distinguish stationary from slow movement. Instead, this
    function computes displacement over a rolling window and classifies
    samples where displacement < threshold as stationary.

    Works on processed data regardless of whether multi-tag merge was
    applied — it groups by ('Date', 'TagId'), and 'TagId' values will
    be subject names if merge was applied, or tag names otherwise.

    Parameters
    ----------
    df : pd.DataFrame
        Processed data with MultiIndex (Date, TagId) and columns X, Y.
    timestep_ms : int
        Sampling interval in milliseconds.
    displacement_threshold : float
        Maximum displacement (m) within the window to count as stationary.
    window_sec : float
        Rolling window duration in seconds.

    Returns
    -------
    pd.DataFrame
        Per-entity stationary summary.
    """
    window_samples = max(2, int(round(window_sec / (timestep_ms / 1000))))
    results = []

    # v11: the processed table is normally already sorted by (Date, TagId),
    # so each group is one contiguous block of rows and can be read straight
    # from the X / Y arrays. Iterating df.groupby(...) instead makes a sorted
    # copy of the whole table first (v10 behaviour, still used as fallback
    # whenever the table is not sorted that way). Same groups, same order,
    # same values either way.
    runs = _sorted_date_tag_runs(df)
    if runs is None:
        groups = ((key, g['X'].values, g['Y'].values)
                  for key, g in df.groupby(['Date', 'TagId']))
    else:
        X_all = df['X'].to_numpy()
        Y_all = df['Y'].to_numpy()
        groups = ((key, X_all[a:b], Y_all[a:b]) for key, a, b in runs)

    for (date, tag), x_g, y_g in groups:
        x = x_g.astype(float)
        y = y_g.astype(float)

        if len(x) <= window_samples:
            continue

        dx = x[window_samples:] - x[:-window_samples]
        dy = y[window_samples:] - y[:-window_samples]
        displacement = np.sqrt(dx**2 + dy**2)

        valid_mask = ~np.isnan(displacement)
        if valid_mask.sum() == 0:
            continue

        stationary = displacement[valid_mask] < displacement_threshold
        n_valid = int(valid_mask.sum())
        n_stationary = int(stationary.sum())

        results.append({
            'Date': date,
            'TagId': tag,
            'total_valid_samples': n_valid,
            'stationary_samples': n_stationary,
            'stationary_pct': round(n_stationary / n_valid * 100, 1) if n_valid > 0 else 0,
            'stationary_time_sec': round(n_stationary * timestep_ms / 1000, 1),
            'total_valid_time_sec': round(n_valid * timestep_ms / 1000, 1),
        })

    result_df = pd.DataFrame(results)

    if len(result_df) > 0:
        agg = result_df.groupby('TagId').agg(
            total_valid_samples=('total_valid_samples', 'sum'),
            stationary_samples=('stationary_samples', 'sum'),
            stationary_time_sec=('stationary_time_sec', 'sum'),
            total_valid_time_sec=('total_valid_time_sec', 'sum'),
        ).reset_index()
        agg['stationary_pct'] = (
            agg['stationary_samples'] / agg['total_valid_samples'] * 100
        ).round(1)
        return agg

    return pd.DataFrame(columns=[
        'TagId', 'total_valid_samples', 'stationary_samples',
        'stationary_pct', 'stationary_time_sec', 'total_valid_time_sec',
    ])


# =============================================================================
# PAIRWISE ANALYSIS
# =============================================================================

def calc_pairwise_distances(df_date, tags):
    """Compute pairwise distance matrix for one date (no thresholding).

    Separated from proximity thresholding so the expensive O(n²·t)
    distance computation runs once and can be reused for multiple
    critical distance thresholds.

    Returns
    -------
    dict with 'times', 'tags', 'Dist', 'both_position', 'Velocity'.
    """
    validate_dataframe(df_date, ['Time', 'X', 'Y', 'Velocity'], "calc_pairwise_distances input")

    df_date = df_date.reset_index()

    # Dedup guard — duplicate (Time, TagId) rows crash pivot
    n_before = len(df_date)
    df_date = df_date.drop_duplicates(subset=['Time', 'TagId'], keep='first')
    n_dropped = n_before - len(df_date)
    if n_dropped > 0:
        log.warning(f"  Dropped {n_dropped} duplicate (Time, TagId) rows before pivot")

    times = sorted(df_date['Time'].unique())
    n_times = len(times)
    n_tags = len(tags)

    pivot = df_date.pivot(index='Time', columns='TagId', values=['X', 'Y', 'Velocity'])
    X = np.full((n_times, n_tags), np.nan)
    Y = np.full((n_times, n_tags), np.nan)
    V = np.full((n_times, n_tags), np.nan)

    for j, tag in enumerate(tags):
        if ('X', tag) in pivot.columns:
            X[:, j] = pivot[('X', tag)].values
            Y[:, j] = pivot[('Y', tag)].values
        if ('Velocity', tag) in pivot.columns:
            V[:, j] = pivot[('Velocity', tag)].values

    # Squared differences are accumulated in place so only one (t, n, n)
    # float array is alive besides the result (was three).
    Dist = X[:, :, None] - X[:, None, :]
    np.square(Dist, out=Dist)
    dY = Y[:, :, None] - Y[:, None, :]
    np.square(dY, out=dY)
    Dist += dY
    del dY
    np.sqrt(Dist, out=Dist)

    has_pos = ~np.isnan(X) & ~np.isnan(Y)
    both_have_position = has_pos[:, :, None] & has_pos[:, None, :]

    return {
        'times': times,
        'tags': tags,
        'Dist': Dist,
        'both_position': both_have_position,
        'Velocity': V,
    }


def calc_pairwise(df_date, tags, critical_distance):
    """Backward-compatible wrapper: compute distances + proximity mask."""
    result = calc_pairwise_distances(df_date, tags)
    result['prox'] = result['Dist'] < critical_distance
    return result


def find_episodes(boolean_array, min_samples):
    """Find contiguous True episodes of at least min_samples length."""
    arr = np.asarray(boolean_array, dtype=float)
    arr = np.where(np.isnan(arr), 0, arr).astype(int)

    padded = np.concatenate([[0], arr, [0]])
    diff = np.diff(padded)

    starts = np.where(diff == 1)[0]
    ends = np.where(diff == -1)[0]

    return [(s, e) for s, e in zip(starts, ends) if (e - s) >= min_samples]


def extract_episodes(pairwise, tags, min_episode_samples, timestep_ms,
                     critical_distance=None):
    """Extract proximity episodes from pairwise data.

    If critical_distance is provided, computes proximity from the Dist
    matrix (for multi-distance mode). Otherwise uses the pre-computed
    'prox' key (backward compat with calc_pairwise).
    """
    Dist = pairwise['Dist']
    both_pos = pairwise['both_position']
    n_tags = len(tags)

    episodes = []

    # Rows are only adjacent in time if the timestamps are one timestep apart.
    # After a time-window subset removes rows, neighbouring rows can be minutes
    # apart; an episode must never span such a hole. Runs are therefore cut at
    # block boundaries. Computed once per pairwise dict and timestep.
    block_start, block_last = _time_blocks(pairwise, timestep_ms)
    times = pairwise['times']

    # One row of the pair matrix at a time: Dist[:, i, i+1:] is contiguous in
    # its last axis, and transposing it gives contiguous per-pair time series
    # (a strided Dist[:, i, j] read is a cache miss per sample).
    for i in range(n_tags - 1):
        if critical_distance is not None:
            prox_rows = Dist[:, i, i + 1:] < critical_distance
        else:
            prox_rows = pairwise['prox'][:, i, i + 1:]
        prox_rows = np.ascontiguousarray((prox_rows & both_pos[:, i, i + 1:]).T)
        has_prox = prox_rows.any(axis=1)
        if not has_prox.any():
            continue
        dist_rows = np.ascontiguousarray(Dist[:, i, i + 1:].T)

        for k in np.flatnonzero(has_prox):
            j = i + 1 + k
            tag_a, tag_b = tags[i], tags[j]
            distances = dist_rows[k]
            prox_mask = prox_rows[k]

            # start = True with no True directly before it in the same block;
            # end   = True with no True directly after it in the same block.
            prev = np.zeros(len(prox_mask), dtype=bool)
            prev[1:] = prox_mask[:-1]
            prev &= ~block_start
            nxt = np.zeros(len(prox_mask), dtype=bool)
            nxt[:-1] = prox_mask[1:]
            nxt &= ~block_last
            starts = np.flatnonzero(prox_mask & ~prev)
            ends = np.flatnonzero(prox_mask & ~nxt) + 1
            keep = (ends - starts) >= min_episode_samples

            for start, end in zip(starts[keep], ends[keep]):
                segment = distances[start:end]
                valid_segment = segment[~np.isnan(segment)]
                episodes.append({
                    'TagId_A': tag_a,
                    'TagId_B': tag_b,
                    'start': times[start],
                    'end': times[end - 1],
                    'duration_sec': (end - start) * timestep_ms / 1000,
                    'mean_dist': np.nanmean(segment),
                    'min_dist': np.nanmin(valid_segment) if len(valid_segment) > 0 else np.nan,
                    'max_dist': np.nanmax(valid_segment) if len(valid_segment) > 0 else np.nan,
                })

    return episodes


def _time_blocks(pairwise, timestep_ms):
    """Boolean arrays marking the first / last row of each contiguous time block."""
    cache = pairwise.setdefault('_blocks', {})
    if timestep_ms not in cache:
        n = len(pairwise['times'])
        step = np.diff(pd.DatetimeIndex(pairwise['times'])) != pd.Timedelta(milliseconds=timestep_ms)
        block_start = np.zeros(n, dtype=bool)
        block_last = np.zeros(n, dtype=bool)
        if n:
            block_start[0] = True
            block_start[1:] = step
            block_last[-1] = True
            block_last[:-1] = step
        cache[timestep_ms] = (block_start, block_last)
    return cache[timestep_ms]


def calc_distance_metrics(pairwise, tags):
    """Compute summary distance statistics per pair."""
    # Independent of the critical distance, so multi-distance runs reuse it.
    cached = pairwise.get('_dist_metrics')
    if cached is not None and cached[0] == tuple(tags):
        return [dict(r) for r in cached[1]]

    Dist = pairwise['Dist']
    both_pos = pairwise['both_position']
    n_tags = len(tags)

    results = []

    for i in range(n_tags - 1):
        # contiguous per-pair series (see extract_episodes)
        d_rows = np.ascontiguousarray(Dist[:, i, i + 1:].T)
        m_rows = np.ascontiguousarray(both_pos[:, i, i + 1:].T)
        for k in range(n_tags - i - 1):
            j = i + 1 + k
            d = d_rows[k]
            mask = m_rows[k]
            valid = d[mask & ~np.isnan(d)]
            if len(valid) > 0:
                results.append({
                    'TagId_A': tags[i],
                    'TagId_B': tags[j],
                    'mean': np.mean(valid),
                    'median': np.median(valid),
                    'min': np.min(valid),
                    'max': np.max(valid),
                    'std': np.std(valid, ddof=1),
                    'n_samples': len(valid),
                })

    pairwise['_dist_metrics'] = (tuple(tags), [dict(r) for r in results])
    return results


# =============================================================================
# MAIN ANALYSIS
# =============================================================================

# v11: the analysis below works through one date at a time and never builds
# the full (time x tags x tags) distance matrix. For each tag i it computes
# the distances to tags i+1..n (one "row" of pairs) with exactly the same
# arithmetic as calc_pairwise_distances, uses that row for episodes and
# dyad statistics, and drops it. Memory per date is then
# (time x tags) instead of (time x tags x tags); results are identical.

def _pairwise_inputs(df_date, tags):
    """Per-tag X, Y, Velocity on one time axis for one date.

    This is the first half of calc_pairwise_distances, unchanged (same
    duplicate guard, same pivot, same column order), without building the
    distance matrix.
    """
    validate_dataframe(df_date, ['Time', 'X', 'Y', 'Velocity'], "calc_pairwise_distances input")

    df_date = df_date.reset_index()

    # Dedup guard — duplicate (Time, TagId) rows crash pivot
    n_before = len(df_date)
    df_date = df_date.drop_duplicates(subset=['Time', 'TagId'], keep='first')
    n_dropped = n_before - len(df_date)
    if n_dropped > 0:
        log.warning(f"  Dropped {n_dropped} duplicate (Time, TagId) rows before pivot")

    times = sorted(df_date['Time'].unique())
    n_times = len(times)
    n_tags = len(tags)

    pivot = df_date.pivot(index='Time', columns='TagId', values=['X', 'Y', 'Velocity'])
    X = np.full((n_times, n_tags), np.nan)
    Y = np.full((n_times, n_tags), np.nan)
    V = np.full((n_times, n_tags), np.nan)

    for j, tag in enumerate(tags):
        if ('X', tag) in pivot.columns:
            X[:, j] = pivot[('X', tag)].values
            Y[:, j] = pivot[('Y', tag)].values
        if ('Velocity', tag) in pivot.columns:
            V[:, j] = pivot[('Velocity', tag)].values

    has_pos = ~np.isnan(X) & ~np.isnan(Y)
    return {'times': times, 'tags': tags, 'X': X, 'Y': Y, 'Velocity': V, 'has_pos': has_pos}


def _distance_row(inputs, i):
    """Dist[:, i, i+1:] and both_position[:, i, i+1:] as calc_pairwise_distances
    would compute them (same operations in the same order: difference,
    square, add, square root)."""
    X, Y = inputs['X'], inputs['Y']
    D = X[:, i, None] - X[:, i + 1:]
    np.square(D, out=D)
    dY = Y[:, i, None] - Y[:, i + 1:]
    np.square(dY, out=dY)
    D += dY
    del dY
    np.sqrt(D, out=D)
    has_pos = inputs['has_pos']
    both = has_pos[:, i, None] & has_pos[:, i + 1:]
    return D, both


def _episodes_for_row(i, D, both, tags, times, block_start, block_last,
                      min_episode_samples, timestep_ms, critical_distance):
    """extract_episodes' loop body for tag i (unchanged logic)."""
    episodes = []
    prox_rows = np.ascontiguousarray(((D < critical_distance) & both).T)
    has_prox = prox_rows.any(axis=1)
    if not has_prox.any():
        return episodes
    dist_rows = np.ascontiguousarray(D.T)

    for k in np.flatnonzero(has_prox):
        j = i + 1 + k
        tag_a, tag_b = tags[i], tags[j]
        distances = dist_rows[k]
        prox_mask = prox_rows[k]

        # start = True with no True directly before it in the same block;
        # end   = True with no True directly after it in the same block.
        prev = np.zeros(len(prox_mask), dtype=bool)
        prev[1:] = prox_mask[:-1]
        prev &= ~block_start
        nxt = np.zeros(len(prox_mask), dtype=bool)
        nxt[:-1] = prox_mask[1:]
        nxt &= ~block_last
        starts = np.flatnonzero(prox_mask & ~prev)
        ends = np.flatnonzero(prox_mask & ~nxt) + 1
        keep = (ends - starts) >= min_episode_samples

        for start, end in zip(starts[keep], ends[keep]):
            segment = distances[start:end]
            valid_segment = segment[~np.isnan(segment)]
            episodes.append({
                'TagId_A': tag_a,
                'TagId_B': tag_b,
                'start': times[start],
                'end': times[end - 1],
                'duration_sec': (end - start) * timestep_ms / 1000,
                'mean_dist': np.nanmean(segment),
                'min_dist': np.nanmin(valid_segment) if len(valid_segment) > 0 else np.nan,
                'max_dist': np.nanmax(valid_segment) if len(valid_segment) > 0 else np.nan,
            })
    return episodes


def _metrics_for_row(i, D, both, tags):
    """calc_distance_metrics' loop body for tag i (unchanged logic)."""
    results = []
    d_rows = np.ascontiguousarray(D.T)
    m_rows = np.ascontiguousarray(both.T)
    for k in range(len(tags) - i - 1):
        j = i + 1 + k
        d = d_rows[k]
        mask = m_rows[k]
        valid = d[mask & ~np.isnan(d)]
        if len(valid) > 0:
            results.append({
                'TagId_A': tags[i],
                'TagId_B': tags[j],
                'mean': np.mean(valid),
                'median': np.median(valid),
                'min': np.min(valid),
                'max': np.max(valid),
                'std': np.std(valid, ddof=1),
                'n_samples': len(valid),
            })
    return results


def _within_for_row(i, D, both, tags, critical_distance):
    """v13: per pair (i, j > i), samples with both positions valid and
    distance below the threshold (the episode mask, without a minimum
    duration). One row per pair with at least one jointly observed sample,
    i.e. exactly the pairs that get a dyad-distance row."""
    observed = both.sum(axis=0)
    close = ((D < critical_distance) & both).sum(axis=0)
    rows = []
    for k in np.flatnonzero(observed > 0):
        rows.append({
            'TagId_A': tags[i],
            'TagId_B': tags[i + 1 + k],
            'within_samples': int(close[k]),
        })
    return rows


def _analyse_dates(df, thresholds, min_episode_samples, timestep_ms,
                   process_dates=None, desc='    Dates', within=None):
    """Episodes per threshold and dyad statistics, one date at a time.

    Output order equals v10: dates in index order; within a date, pairs in
    (i, j) order; one episode list per threshold.

    v13: when `within` is a dict {threshold: []}, it is filled with the
    within-distance counts per (date, pair) (see `_within_for_row`).
    Episodes and dyad statistics are unchanged.
    """
    dates = df.index.get_level_values('Date').unique()
    if process_dates:
        dates = [d for d in dates if d in process_dates]

    prox = {d: [] for d in thresholds}
    dist = {d: [] for d in thresholds}
    for date in tqdm(dates, desc=desc):
        date_df = df[df.index.get_level_values('Date') == date].copy()
        tags = list(date_df.index.get_level_values('TagId').unique())
        if len(tags) < 2:
            continue
        inputs = _pairwise_inputs(date_df, tags)
        del date_df
        block_start, block_last = _time_blocks(inputs, timestep_ms)
        times = inputs['times']

        date_eps = {d: [] for d in thresholds}
        date_within = {d: [] for d in thresholds}
        date_metrics = []
        for i in range(len(tags) - 1):
            D, both = _distance_row(inputs, i)
            for d in thresholds:
                date_eps[d].extend(_episodes_for_row(
                    i, D, both, tags, times, block_start, block_last,
                    min_episode_samples, timestep_ms, d))
                if within is not None:
                    date_within[d].extend(_within_for_row(i, D, both, tags, d))
            date_metrics.extend(_metrics_for_row(i, D, both, tags))
            del D, both
        del inputs

        if within is not None:
            for d in thresholds:
                for w in date_within[d]:
                    w['Date'] = date
                within[d].extend(date_within[d])

        for d in thresholds:
            for ep in date_eps[d]:
                ep['Date'] = date
            prox[d].extend(date_eps[d])
            for m in date_metrics:
                entry = dict(m)
                entry['Date'] = date
                dist[d].append(entry)
    return prox, dist


# v13: columns of the 'within' entry returned by run_analysis /
# run_analysis_multi_distance.
WITHIN_COLUMNS = ['TagId_A', 'TagId_B', 'within_samples', 'Date']


def run_analysis(df, critical_distance, min_episode_samples,
                 timestep_ms, process_dates=None):
    """Run full pairwise analysis at a SINGLE distance threshold.

    v11: one date at a time, no full distance matrix (identical results).
    '_pairwise' is returned as an empty list.
    """
    within = {critical_distance: []}
    prox, dist = _analyse_dates(df, [critical_distance], min_episode_samples,
                                timestep_ms, process_dates, desc='    Dates',
                                within=within)
    return {
        'prox': pd.DataFrame(prox[critical_distance]),
        'dist': pd.DataFrame(dist[critical_distance]),
        '_pairwise': [],
        'within': pd.DataFrame(within[critical_distance], columns=WITHIN_COLUMNS),
    }


def run_analysis_multi_distance(df, critical_distances, min_episode_samples,
                                timestep_ms, process_dates=None):
    """Run pairwise analysis once, extract episodes at multiple distances.

    v11: one date at a time; each date's distances are computed once and
    used for every threshold, then dropped (identical results to v10).

    Returns
    -------
    dict mapping distance (float) → result dict with 'prox', 'dist', '_pairwise'
    ('_pairwise' is an empty list in v11).
    """
    thresholds = list(dict.fromkeys(critical_distances))
    within = {d: [] for d in thresholds}
    prox, dist = _analyse_dates(df, thresholds, min_episode_samples, timestep_ms,
                                process_dates, desc='    Distance matrices',
                                within=within)
    return {
        d: {'prox': pd.DataFrame(prox[d]), 'dist': pd.DataFrame(dist[d]), '_pairwise': [],
            'within': pd.DataFrame(within[d], columns=WITHIN_COLUMNS)}
        for d in thresholds
    }


# =============================================================================
# METRICS
# =============================================================================

def compute_metrics(result_data, timestep_ms=None):
    """Compute summary metrics from episode and distance DataFrames.

    Mean distance is weighted by n_samples per dyad.
    Median distance is the median of per-dyad medians (unweighted).

    v12: three keys are appended after the existing ones (see
    `_observed_time_metrics`): joint_observed_sec, proximity_fraction and
    episodes_per_joint_hour. They need `timestep_ms` and are NaN without it.
    The existing keys and their values are unchanged.

    v13: key within_distance_fraction appended (needs result_data['within'],
    which run_analysis / run_analysis_multi_distance return from v13 on).
    """
    prox_df = result_data['prox']
    dist_df = result_data['dist']

    if len(dist_df) > 0 and 'n_samples' in dist_df.columns:
        weights = dist_df['n_samples'].values
        total_w = weights.sum()
        if total_w > 0:
            mean_dist = np.average(dist_df['mean'].values, weights=weights)
        else:
            mean_dist = 0
        median_dist = dist_df['median'].median() if len(dist_df) > 0 else 0
    elif len(dist_df) > 0:
        mean_dist = dist_df['mean'].mean()
        median_dist = dist_df['median'].median()
    else:
        mean_dist = 0
        median_dist = 0

    metrics = {
        'mean_distance_m':        mean_dist,
        'median_distance_m':      median_dist,
        'min_distance_m':         dist_df['min'].min() if len(dist_df) > 0 else 0,
        'max_distance_m':         dist_df['max'].max() if len(dist_df) > 0 else 0,
        'proximity_episodes':     len(prox_df),
        'proximity_time_sec':     prox_df['duration_sec'].sum() if len(prox_df) > 0 else 0,
        'proximity_mean_dur_sec': prox_df['duration_sec'].mean() if len(prox_df) > 0 else 0,
    }
    metrics.update(_observed_time_metrics(prox_df, dist_df, timestep_ms))
    metrics['within_distance_fraction'] = _within_fraction(
        result_data.get('within'), dist_df)
    return metrics


def _within_fraction(within_df, dist_df):
    """v13: all samples within the threshold (both observed, no minimum
    duration) / all jointly observed samples, over every dyad and date.
    NaN when the run has no within counts or no joint observed samples."""
    if (within_df is None or len(within_df) == 0 or len(dist_df) == 0
            or 'n_samples' not in dist_df.columns):
        return float('nan')
    joint = float(dist_df['n_samples'].sum())
    if joint <= 0:
        return float('nan')
    return float(within_df['within_samples'].sum()) / joint


# =============================================================================
# PROXIMITY RELATIVE TO OBSERVED TIME (v12)
# =============================================================================

# A pair's proximity time can only accumulate while both members have a valid
# position. dyad n_samples counts exactly those samples, so
# n_samples x timestep is the time during which proximity could have been
# detected at all ("joint observed time"). Dividing by it compares pairs on
# equal footing when entities were recorded for different lengths of time.
# Only observed time is used; nothing is assumed about unobserved time.

def _observed_time_metrics(prox_df, dist_df, timestep_ms):
    """Whole-group proximity relative to joint observed time.

    joint_observed_sec      : sum over dyads and dates of n_samples x timestep
    proximity_fraction      : proximity_time_sec / joint_observed_sec
    episodes_per_joint_hour : number of episodes / joint observed hours

    All NaN when timestep_ms is None; the two ratios are NaN when there is
    no joint observed time.
    """
    nan = float('nan')
    out = {
        'joint_observed_sec':      nan,
        'proximity_fraction':      nan,
        'episodes_per_joint_hour': nan,
    }
    if timestep_ms is None:
        return out
    joint = 0.0
    if len(dist_df) > 0 and 'n_samples' in dist_df.columns:
        joint = float(dist_df['n_samples'].sum()) * timestep_ms / 1000
    out['joint_observed_sec'] = joint
    if joint > 0:
        prox_time = float(prox_df['duration_sec'].sum()) if len(prox_df) > 0 else 0.0
        out['proximity_fraction'] = prox_time / joint
        out['episodes_per_joint_hour'] = len(prox_df) / (joint / 3600)
    return out


DYAD_PROXIMITY_COLUMNS = [
    'Date', 'TagId_A', 'TagId_B',
    'joint_observed_sec', 'proximity_time_sec', 'proximity_fraction',
    'n_episodes', 'episodes_per_joint_hour', 'low_joint_time',
    'within_distance_sec', 'within_distance_fraction',          # v13
]


def compute_dyad_proximity(prox_df, dist_df, timestep_ms, low_joint_fraction=0.25,
                           within_df=None):
    """Per-pair proximity relative to the time both members were observed.

    Parameters
    ----------
    prox_df : pd.DataFrame or None
        Episodes for one (subset, distance) as returned by run_analysis
        (TagId_A, TagId_B, duration_sec, Date, ...).
    dist_df : pd.DataFrame or None
        Dyad distance rows for the same run (TagId_A, TagId_B, n_samples,
        Date, ...).
    timestep_ms : int
        Sampling interval the analysis ran at.
    low_joint_fraction : float
        A row is flagged `low_joint_time` when its joint observed time is
        below this fraction of the median joint time of all pairs in the
        same period (same Date; all pairs for the 'all' rows).

    Returns
    -------
    pd.DataFrame with columns DYAD_PROXIMITY_COLUMNS: one row per
    (Date, pair) with joint observed time, then one row per pair over all
    dates with Date = 'all'.

    - joint_observed_sec : samples where both had a valid position
                           (dyad n_samples) x timestep.
    - proximity_time_sec : summed episode durations. Only episodes of at
                           least the minimum episode duration count, while
                           joint time counts every sample.
    - proximity_fraction : proximity_time_sec / joint_observed_sec (0-1).
    - n_episodes, episodes_per_joint_hour (= n_episodes / joint hours).
    - within_distance_sec (v13): samples with both positions valid and
                           distance below the threshold, no minimum duration,
                           x timestep (from `within_df`; NaN without it).
    - within_distance_fraction (v13): within_distance_sec / joint_observed_sec.
                           Use this one to compare pairs: with gaps unrelated
                           to closeness it is unbiased for the share of time
                           within the distance. proximity_fraction drops
                           slightly with fragmented data (gaps split episodes).

    Pairs that were never observed together have no rows (no claim is
    possible). Pairs observed together but never close have proximity 0.
    Pair order (A, B) is taken from the input rows; for the 'all' rows a
    pair is matched regardless of order and keeps the first order seen.
    """
    cols = list(DYAD_PROXIMITY_COLUMNS)
    if dist_df is None or len(dist_df) == 0 or 'n_samples' not in dist_df.columns:
        return pd.DataFrame(columns=cols)

    key = ['Date', 'TagId_A', 'TagId_B']
    step_s = timestep_ms / 1000

    joint = dist_df.groupby(key, sort=False)['n_samples'].sum() * step_s
    daily = pd.DataFrame({'joint_observed_sec': joint.astype(float)})
    if prox_df is not None and len(prox_df) > 0:
        g = prox_df.groupby(key, sort=False)['duration_sec']
        daily['proximity_time_sec'] = g.sum().reindex(daily.index).fillna(0.0)
        daily['n_episodes'] = g.size().reindex(daily.index).fillna(0).astype(int)
    else:
        daily['proximity_time_sec'] = 0.0
        daily['n_episodes'] = 0
    has_within = within_df is not None and 'within_samples' in getattr(within_df, 'columns', [])
    if has_within:
        w = within_df.groupby(key, sort=False)['within_samples'].sum() * step_s
        daily['within_distance_sec'] = w.reindex(daily.index).astype(float)
    else:
        daily['within_distance_sec'] = np.nan
    daily = daily.reset_index()

    a = daily['TagId_A'].astype(str).to_numpy()
    b = daily['TagId_B'].astype(str).to_numpy()
    whole = (daily.assign(_lo=np.where(a <= b, a, b), _hi=np.where(a <= b, b, a))
             .groupby(['_lo', '_hi'], sort=False)
             .agg(TagId_A=('TagId_A', 'first'),
                  TagId_B=('TagId_B', 'first'),
                  joint_observed_sec=('joint_observed_sec', 'sum'),
                  proximity_time_sec=('proximity_time_sec', 'sum'),
                  n_episodes=('n_episodes', 'sum'),
                  within_distance_sec=('within_distance_sec', 'sum'))
             .reset_index(drop=True))
    whole.insert(0, 'Date', 'all')
    if not has_within:
        whole['within_distance_sec'] = np.nan

    out = pd.concat([daily, whole], ignore_index=True)
    out['n_episodes'] = out['n_episodes'].astype(int)
    out['proximity_fraction'] = out['proximity_time_sec'] / out['joint_observed_sec']
    out['episodes_per_joint_hour'] = out['n_episodes'] / (out['joint_observed_sec'] / 3600)
    period_median = out.groupby('Date', sort=False)['joint_observed_sec'].transform('median')
    out['low_joint_time'] = out['joint_observed_sec'] < low_joint_fraction * period_median
    out['within_distance_fraction'] = out['within_distance_sec'] / out['joint_observed_sec']
    return out[cols]


def build_dyad_proximity_table(subset_results, timestep_ms, low_joint_fraction=0.25):
    """compute_dyad_proximity for every (subset, distance), long format.

    subset_results : {subset_name: {distance: {'prox': df, 'dist': df}}}
    Returns a DataFrame with 'subset' and 'distance_threshold_m' in front of
    DYAD_PROXIMITY_COLUMNS (same nesting columns as the other exports).
    """
    lead = ['subset', 'distance_threshold_m']
    parts = []
    for subset_name, by_dist in (subset_results or {}).items():
        for distance, results in by_dist.items():
            if not isinstance(results, dict):
                continue
            t = compute_dyad_proximity(results.get('prox'), results.get('dist'),
                                       timestep_ms, low_joint_fraction,
                                       within_df=results.get('within'))
            if len(t) == 0:
                continue
            t.insert(0, 'distance_threshold_m', distance)
            t.insert(0, 'subset', subset_name)
            parts.append(t)
    if not parts:
        return pd.DataFrame(columns=lead + DYAD_PROXIMITY_COLUMNS)
    return pd.concat(parts, ignore_index=True)


# =============================================================================
# EXPORT BUNDLE (v9)
# =============================================================================

# Column dictionary as Markdown — mirrors columns produced by the pipeline.
# Kept in code (not a separate file) so the module is self-contained and the
# Streamlit pages don't need extra path handling.
_COLUMN_DICTIONARY_MD = """\
# TrackLab-Companion export — column dictionary

## proximity_episodes.csv
One row per proximity episode (a continuous stretch of time during which a pair
of subjects was within the critical distance threshold).

| Column | Type | Meaning |
|---|---|---|
| `subset` | str | Name of the subset/time-window the episode belongs to. |
| `distance_threshold_m` | float | Critical distance threshold (meters) used. |
| `TagId_A` / `TagId_B` (or `Subject_A` / `Subject_B`) | str | The two entities involved. Named `Subject_*` when multi-tag merging was used. |
| `start` / `end` | datetime | Timestamp of the first and of the last sample of the episode. |
| `duration_sec` | float | Episode duration in seconds (number of samples x timestep). |
| `mean_dist` | float | Mean inter-entity distance during the episode (meters). |
| `min_dist` / `max_dist` | float | Minimum / maximum inter-entity distance during the episode (meters). |
| `Date` | str | Recording date (DD-MM-YYYY). |

## dyad_distances.csv
One row per (Date × distance_threshold × dyad), summarising the distance
distribution across the whole subset for that pair on that day.

| Column | Type | Meaning |
|---|---|---|
| `subset` | str | Subset name. |
| `distance_threshold_m` | float | Critical distance threshold (meters). |
| `Subject_A` / `Subject_B` (or `TagId_A` / `TagId_B`) | str | The pair. |
| `Date` | str | Recording date. |
| `mean` / `median` / `min` / `max` / `std` | float | Distance summary stats (meters). |
| `n_samples` | int | Number of valid distance samples used: samples at which both members had a valid position. |

## metrics_summary.csv
One row per (subset × distance_threshold). Summary statistics across all dyads.

| Column | Type | Meaning |
|---|---|---|
| `subset` | str | Subset name. |
| `distance_threshold_m` | float | Critical distance threshold (meters). |
| `mean_distance_m` | float | Sample-weighted mean of dyad mean distances. |
| `median_distance_m` | float | Median of per-dyad medians. |
| `min_distance_m` / `max_distance_m` | float | Extrema across dyads. |
| `proximity_episodes` | int | Total number of proximity episodes for this (subset, distance). |
| `proximity_time_sec` | float | Total time (seconds) spent in proximity. |
| `proximity_mean_dur_sec` | float | Mean episode duration (seconds). |
| `joint_observed_sec` | float | Total time (seconds) both members of a dyad had a valid position, summed over all dyads and dates (v12). |
| `proximity_fraction` | float | `proximity_time_sec` / `joint_observed_sec` (0-1): the share of jointly observed time spent in proximity episodes (v12). |
| `episodes_per_joint_hour` | float | `proximity_episodes` per hour of joint observed time (v12). |
| `within_distance_fraction` | float | Time pairs were closer than the threshold (both observed, no minimum duration) / joint observed time, over all dyads and dates (v13). |

## dyad_proximity.csv
Per-pair proximity relative to the time both members were observed (v12).
One row per (subset x distance_threshold x Date x dyad), plus one row per
(subset x distance_threshold x dyad) over all dates with `Date` = `all`.
Use `within_distance_fraction` to compare pairs (v13). Total proximity time grows
with how long both tags were recorded. If missing data is unrelated to whether a
pair is close, `within_distance_fraction` is an unbiased estimate of the share of
time the pair was within the distance, however long they were recorded.
`proximity_fraction` counts only episodes of at least the minimum duration: a gap
splits an episode and pieces shorter than the minimum are dropped, so it is
slightly lower for pairs whose data has many gaps.

| Column | Type | Meaning |
|---|---|---|
| `subset` | str | Subset name. |
| `distance_threshold_m` | float | Critical distance threshold (meters). |
| `Date` | str | Recording date (DD-MM-YYYY), or `all` for the whole subset. |
| `TagId_A` / `TagId_B` (or `Subject_A` / `Subject_B`) | str | The pair. |
| `joint_observed_sec` | float | Time (seconds) both members had a valid position (`n_samples` in dyad_distances.csv x timestep). |
| `proximity_time_sec` | float | Summed duration of the pair's proximity episodes (seconds). Only episodes of at least the minimum episode duration count. |
| `proximity_fraction` | float | `proximity_time_sec` / `joint_observed_sec` (0-1). Episode-based; see the note above. |
| `n_episodes` | int | Number of proximity episodes. |
| `episodes_per_joint_hour` | float | `n_episodes` per hour of joint observed time. Gaps can split or drop episodes, so this also depends slightly on data gaps. |
| `low_joint_time` | bool | True when `joint_observed_sec` is below 25 % of the median pair's joint observed time in the same period (same Date, or all pairs for `all`). Fractions on little joint time are unreliable. |
| `within_distance_sec` | float | Time (seconds) both members had a valid position and were closer than the threshold, with no minimum duration (v13). |
| `within_distance_fraction` | float | `within_distance_sec` / `joint_observed_sec` (0-1). Use this to compare pairs (v13). |

Pairs never observed together have no row (no claim is possible). Pairs
observed together but never in proximity have `proximity_time_sec` = 0.

## cleaned_trajectories.csv
The processed positional data after resampling, out-of-bounds rejection,
optional smoothing, velocity filtering, and (if applicable) multi-tag merging
to subjects. This is the data the analysis was actually run on.

| Column | Type | Meaning |
|---|---|---|
| `Date` | str | Recording date. |
| `TagId` | str | Tag (or Subject, after merging) identifier. |
| `Time` | datetime | Time of the sample on the regular resampling grid (written as YYYY-MM-DD HH:MM:SS with fractional seconds). |
| `X` / `Y` | float | Position (meters). |
| `Velocity` | float | Sample velocity (m/s). |

## stationary_time.csv
Estimated stationary time per tag (or per subject when multi-tag merging was
used), over the whole processed recording (all dates; not per subset). A sample
counts as stationary when the straight-line distance between the position at
that sample and the position one window later is below the displacement
threshold. Present only if stationary time could be computed.

| Column | Type | Meaning |
|---|---|---|
| `TagId` | str | Tag, or subject name when multi-tag merging was used. |
| `total_valid_samples` | int | Samples at which the displacement over the window could be computed (position valid at both ends). |
| `stationary_samples` | int | Of those, samples classified as stationary. |
| `stationary_time_sec` | float | `stationary_samples` x timestep (seconds). |
| `total_valid_time_sec` | float | `total_valid_samples` x timestep (seconds). |
| `stationary_pct` | float | `stationary_samples` / `total_valid_samples` x 100. |

## merge_diagnostics.json
Per-subject quality numbers from the multi-tag merge step. Present only when
multi-tag merging was used. See the README for fields.

## config_used.json
The full configuration dict used for this run. Useful for reproducibility.
"""


_LOADER_PYTHON = """\
\"\"\"Load a TrackLab-Companion export bundle into a nested dict structure.

Usage:
    results = load_results()           # uses current directory
    results = load_results('path/to')  # uses specified directory

Returns:
    dict with keys:
      'episodes': dict[subset_name][distance] -> DataFrame
      'distances': dict[subset_name][distance] -> DataFrame
      'dyad_proximity': dict[subset_name][distance] -> DataFrame (v12 exports)
      'metrics': dict[subset_name][distance] -> dict
      'trajectories': DataFrame (if cleaned_trajectories.csv present)
      'stationary': DataFrame (if stationary_time.csv present)
      'config': dict (parsed config_used.json)
      'merge_diagnostics': dict or None
\"\"\"
import json
import os
import pandas as pd


def _read_csv_if_exists(path):
    return pd.read_csv(path) if os.path.exists(path) else None


def _read_json_if_exists(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r') as fh:
        return json.load(fh)


def _nest_by_subset_distance(df):
    out = {}
    if df is None or len(df) == 0:
        return out
    for (subset, dist), grp in df.groupby(['subset', 'distance_threshold_m']):
        out.setdefault(subset, {})[float(dist)] = grp.drop(
            columns=['subset', 'distance_threshold_m']
        ).reset_index(drop=True)
    return out


def load_results(directory='.'):
    episodes_df = _read_csv_if_exists(os.path.join(directory, 'proximity_episodes.csv'))
    distances_df = _read_csv_if_exists(os.path.join(directory, 'dyad_distances.csv'))
    dyad_prox_df = _read_csv_if_exists(os.path.join(directory, 'dyad_proximity.csv'))
    metrics_df = _read_csv_if_exists(os.path.join(directory, 'metrics_summary.csv'))

    metrics_nested = {}
    if metrics_df is not None:
        for _, row in metrics_df.iterrows():
            metrics_nested.setdefault(row['subset'], {})[float(row['distance_threshold_m'])] = (
                row.drop(['subset', 'distance_threshold_m']).to_dict()
            )

    return {
        'episodes': _nest_by_subset_distance(episodes_df),
        'distances': _nest_by_subset_distance(distances_df),
        'dyad_proximity': _nest_by_subset_distance(dyad_prox_df),
        'metrics': metrics_nested,
        'trajectories': _read_csv_if_exists(os.path.join(directory, 'cleaned_trajectories.csv')),
        'stationary': _read_csv_if_exists(os.path.join(directory, 'stationary_time.csv')),
        'config': _read_json_if_exists(os.path.join(directory, 'config_used.json')),
        'merge_diagnostics': _read_json_if_exists(
            os.path.join(directory, 'merge_diagnostics.json')
        ),
    }


if __name__ == '__main__':
    r = load_results()
    print(f"Loaded {sum(len(v) for v in r['episodes'].values())} episode tables")
    print(f"Subsets: {list(r['episodes'].keys())}")
"""


_LOADER_R = """\
# Load a TrackLab-Companion export bundle into a nested list structure.
#
# Usage:
#   source('load_results.R')
#   results <- load_results()              # uses current directory
#   results <- load_results('path/to')     # uses specified directory
#
# Returns a named list:
#   $episodes    : list[[subset]][[distance_chr]] -> data.frame
#   $distances   : list[[subset]][[distance_chr]] -> data.frame
#   $dyad_proximity: list[[subset]][[distance_chr]] -> data.frame (v12 exports)
#   $metrics     : list[[subset]][[distance_chr]] -> named numeric vector
#   $trajectories: data.frame (if cleaned_trajectories.csv present)
#   $stationary  : data.frame (if stationary_time.csv present)
#   $config      : list (parsed from config_used.json)
#   $merge_diagnostics: list or NULL
#
# Distance keys are character strings (e.g. "1.5") because R names cannot be
# numeric. Convert with as.numeric(names(results$episodes[[subset]])) when
# needed.
#
# Dependencies: readr (for fast CSV) and jsonlite. Both are widely available
# tidyverse / CRAN packages. Falls back to base read.csv if readr is absent.

.read_csv_if_exists <- function(path) {
  if (!file.exists(path)) return(NULL)
  if (requireNamespace("readr", quietly = TRUE)) {
    readr::read_csv(path, show_col_types = FALSE)
  } else {
    read.csv(path, stringsAsFactors = FALSE)
  }
}

.read_json_if_exists <- function(path) {
  if (!file.exists(path)) return(NULL)
  if (!requireNamespace("jsonlite", quietly = TRUE)) {
    stop("Loading JSON requires the 'jsonlite' package. install.packages('jsonlite').")
  }
  jsonlite::fromJSON(path, simplifyVector = FALSE)
}

.nest_by_subset_distance <- function(df) {
  if (is.null(df) || nrow(df) == 0) return(list())
  out <- list()
  for (subset_name in unique(df$subset)) {
    sub <- df[df$subset == subset_name, , drop = FALSE]
    by_dist <- list()
    for (d in unique(sub$distance_threshold_m)) {
      slice <- sub[sub$distance_threshold_m == d, , drop = FALSE]
      slice$subset <- NULL
      slice$distance_threshold_m <- NULL
      by_dist[[as.character(d)]] <- slice
    }
    out[[subset_name]] <- by_dist
  }
  out
}

load_results <- function(directory = ".") {
  episodes_df  <- .read_csv_if_exists(file.path(directory, "proximity_episodes.csv"))
  distances_df <- .read_csv_if_exists(file.path(directory, "dyad_distances.csv"))
  dyad_prox_df <- .read_csv_if_exists(file.path(directory, "dyad_proximity.csv"))
  metrics_df   <- .read_csv_if_exists(file.path(directory, "metrics_summary.csv"))

  metrics_nested <- list()
  if (!is.null(metrics_df) && nrow(metrics_df) > 0) {
    for (i in seq_len(nrow(metrics_df))) {
      row <- as.list(metrics_df[i, ])
      subset_name <- row$subset
      d <- as.character(row$distance_threshold_m)
      row$subset <- NULL
      row$distance_threshold_m <- NULL
      if (is.null(metrics_nested[[subset_name]])) metrics_nested[[subset_name]] <- list()
      metrics_nested[[subset_name]][[d]] <- row
    }
  }

  list(
    episodes          = .nest_by_subset_distance(episodes_df),
    distances         = .nest_by_subset_distance(distances_df),
    dyad_proximity    = .nest_by_subset_distance(dyad_prox_df),
    metrics           = metrics_nested,
    trajectories      = .read_csv_if_exists(file.path(directory, "cleaned_trajectories.csv")),
    stationary        = .read_csv_if_exists(file.path(directory, "stationary_time.csv")),
    config            = .read_json_if_exists(file.path(directory, "config_used.json")),
    merge_diagnostics = .read_json_if_exists(file.path(directory, "merge_diagnostics.json"))
  )
}
"""


_README_TEMPLATE = """\
TrackLab-Companion export bundle
================================
Generated: {generated_at}

Contents
--------
- proximity_episodes.csv    Per-episode proximity events (long format)
- dyad_distances.csv        Per-dyad distance summaries (long format)
- metrics_summary.csv       One row per (subset x distance) summary
{dyad_line}- cleaned_trajectories.csv  Processed positions actually used in analysis
{stationary_line}{merge_diag_line}- config_used.json          Full configuration dict (reproducibility)
- column_dictionary.md      Column-by-column reference for every CSV
{loader_block}

Loading the data
----------------
{loader_instructions}

Notes
-----
- All distances are in meters. Times are in seconds unless suffix says otherwise.
- The 'subset' and 'distance_threshold_m' columns encode the nesting; results
  for a single (subset, distance) can be obtained by filtering on these two.
- Multi-tag mode (if used) renames TagId columns to Subject (e.g. Subject_A,
  Subject_B). Column names in this bundle reflect what was used at run time.
"""


_LOADER_INSTRUCTIONS_PYTHON = """\
Python:
    from load_results import load_results
    r = load_results('.')
    r['episodes']['Full Recording'][1.5]   # episodes for that subset & distance"""

_LOADER_INSTRUCTIONS_R = """\
R:
    source('load_results.R')
    r <- load_results('.')
    r$episodes[['Full Recording']][['1.5']]   # episodes for that subset & distance"""


def _safe_concat(frames, extra_cols):
    """Concatenate per-(subset, distance) frames, prepending the subset and
    distance columns. `extra_cols` is a list of (subset_name, distance, df).
    Returns an empty DataFrame if all input frames are empty.
    """
    pieces = []
    for subset_name, distance, df in extra_cols:
        if df is None or len(df) == 0:
            continue
        piece = df.copy()
        piece.insert(0, 'subset', subset_name)
        piece.insert(1, 'distance_threshold_m', distance)
        pieces.append(piece)
    if not pieces:
        return pd.DataFrame()
    return pd.concat(pieces, ignore_index=True)


def build_export_bundle(subset_results,
                        subset_metrics,
                        df_proc=None,
                        config=None,
                        stationary_df=None,
                        merge_diagnostics=None,
                        format_pref='both',
                        dyad_proximity=None):
    """Assemble a downloadable ZIP containing all pipeline outputs.

    Parameters
    ----------
    subset_results : dict
        {subset_name: {distance: {'prox': DataFrame, 'dist': DataFrame, ...}}}
        Built by page 3 from run_analysis / run_analysis_multi_distance.
    subset_metrics : dict
        {subset_name: {distance: {metric_name: value, ...}}}
    df_proc : pd.DataFrame or None
        The cleaned trajectory data. Skipped if None.
    config : dict or None
        Full config dict. Skipped if None.
    stationary_df : pd.DataFrame or None
        Stationary time per subject. Skipped if None or empty.
    merge_diagnostics : dict or None
        Multi-tag merge diagnostics export-ready dict. Skipped if None or empty.
    format_pref : {'python', 'r', 'both'}
        Which loader script(s) to include.
    dyad_proximity : pd.DataFrame or None
        v12: long table from build_dyad_proximity_table (column names as
        they should appear in the export). Written as dyad_proximity.csv
        when given; skipped if None.

    Returns
    -------
    bytes : the bundle as raw ZIP bytes, ready to hand to st.download_button.
    """
    if format_pref not in ('python', 'r', 'both'):
        raise ValueError(f"format_pref must be 'python', 'r', or 'both' (got {format_pref!r})")

    # ── Flatten nested dicts into long-format CSVs ──────────────────────────
    prox_inputs = []
    dist_inputs = []
    metric_rows = []

    for subset_name, by_dist in (subset_results or {}).items():
        for distance, results in by_dist.items():
            prox = results.get('prox') if isinstance(results, dict) else None
            dist = results.get('dist') if isinstance(results, dict) else None
            prox_inputs.append((subset_name, distance, prox))
            dist_inputs.append((subset_name, distance, dist))

    for subset_name, by_dist in (subset_metrics or {}).items():
        for distance, m in by_dist.items():
            row = {'subset': subset_name, 'distance_threshold_m': distance}
            row.update(m if isinstance(m, dict) else {})
            metric_rows.append(row)

    prox_df = _safe_concat(None, prox_inputs)
    dist_df = _safe_concat(None, dist_inputs)
    metrics_df = pd.DataFrame(metric_rows) if metric_rows else pd.DataFrame()

    # ── Build the ZIP in memory ────────────────────────────────────────────
    buf = io.BytesIO()
    has_stationary = stationary_df is not None and len(stationary_df) > 0
    has_merge_diag = bool(merge_diagnostics)

    with zipfile.ZipFile(buf, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:

        zf.writestr('proximity_episodes.csv', prox_df.to_csv(index=False))
        zf.writestr('dyad_distances.csv',     dist_df.to_csv(index=False))
        zf.writestr('metrics_summary.csv',    metrics_df.to_csv(index=False))
        if dyad_proximity is not None:
            zf.writestr('dyad_proximity.csv', dyad_proximity.to_csv(index=False))

        if df_proc is not None and len(df_proc) > 0:
            traj = df_proc.reset_index() if isinstance(df_proc.index, pd.MultiIndex) \
                                          else df_proc.copy()
            zf.writestr('cleaned_trajectories.csv', traj.to_csv(index=False))

        if has_stationary:
            zf.writestr('stationary_time.csv', stationary_df.to_csv(index=False))

        if has_merge_diag:
            zf.writestr('merge_diagnostics.json',
                        json.dumps(merge_diagnostics, indent=2, default=str))

        if config is not None:
            zf.writestr('config_used.json',
                        json.dumps(config, indent=2, default=str))

        zf.writestr('column_dictionary.md', _COLUMN_DICTIONARY_MD)

        loader_lines = []
        if format_pref in ('python', 'both'):
            zf.writestr('load_results.py', _LOADER_PYTHON)
            loader_lines.append('- load_results.py           Python loader (uses pandas)')
        if format_pref in ('r', 'both'):
            zf.writestr('load_results.R', _LOADER_R)
            loader_lines.append('- load_results.R            R loader (uses readr/jsonlite)')

        loader_block = ('\n' + '\n'.join(loader_lines) + '\n') if loader_lines else '\n'

        if format_pref == 'python':
            loader_instructions = _LOADER_INSTRUCTIONS_PYTHON
        elif format_pref == 'r':
            loader_instructions = _LOADER_INSTRUCTIONS_R
        else:
            loader_instructions = _LOADER_INSTRUCTIONS_PYTHON + '\n\n' + _LOADER_INSTRUCTIONS_R

        readme = _README_TEMPLATE.format(
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            stationary_line='- stationary_time.csv      Per-subject stationary time estimate\n' if has_stationary else '',
            merge_diag_line='- merge_diagnostics.json   Multi-tag merge quality per subject\n' if has_merge_diag else '',
            dyad_line=('- dyad_proximity.csv        Per-pair proximity relative to joint observed time\n'
                       if dyad_proximity is not None else ''),
            loader_block=loader_block,
            loader_instructions=loader_instructions,
        )
        zf.writestr('README.txt', readme)

    return buf.getvalue()
