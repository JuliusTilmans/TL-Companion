"""
Page 3: Define Analysis & Run (v5)

2026-10-18 (UI cleanup):
- Episode Details: the three tabs are shown whenever pairs were observed
  together, not only when there are episodes, so the Pair Summary (and its
  within-distance fraction) is visible for a subset / distance without
  episodes. Display only; results and exports unchanged.
- A custom subset without time windows is skipped (it used to be analysed as
  the full recording under its own name). Skipped subsets, and subsets with no
  data inside their windows, are listed in a warning above the results
  (session key 'skipped_subsets', cleared by page 1 on new data).
- Export ZIP renamed tracklab_assist_export.zip -> tracklab_companion_export.zip.
Previous version: _removed_backup/before_ui_cleanup/pages/.

2026-10-17 (time within distance): switched to backend social_analysis_v13 and
streamlit_subsets_v6. Pair Summary and Metrics Summary now show the
within-distance fraction (time closer than the threshold / time both were
observed, no minimum duration) next to the episode-based fraction, which is
relabelled "Episode fraction". Pair Summary is sorted by the within-distance
fraction. Every existing result is unchanged. Previous version of this file:
_removed_backup/before_within_distance/pages/. See FILE_DEPENDENCIES_v1.md.

2026-10-17 (pair proximity): switched to backend social_analysis_v12 and
streamlit_subsets_v5. New: proximity relative to observed time.
- Results > Episode Details has a third tab, "Pair Summary": per pair the
  proximity fraction (time in proximity / time both were observed), proximity
  time, joint observed time, episodes, episodes per joint hour and a
  low-joint-time flag; sorted by fraction; per day or whole subset.
- Metrics Summary table shows the herd/group-level proximity fraction.
- Export bundle gains dyad_proximity.csv; metrics_summary.csv gains three
  columns at the end. Individual downloads gain a pair-proximity CSV.
- compute_metrics now receives the timestep (needed for the new keys).
Every existing number, table and file is unchanged. Previous version of this
file: _removed_backup/before_dyad_proximity/pages/. See FILE_DEPENDENCIES_v1.md.

2026-10-07: switched to backend social_analysis_v11 and streamlit_subsets_v4
(memory release, identical results). Previous version of this file:
_removed_backup/before_v11/pages/. See FILE_DEPENDENCIES_v1.md.

v5 changes (bugfix pass — see bugs_and_issues_v1.txt):
- A1 fix (read side): detect `selected_tags == []` (error sentinel from
  page 2 v6) and block the Run button. Previously, an empty/error tag
  selection in page 2 saved `None`, which is the same sentinel as
  "use all tags" — the pipeline silently ran on tags the user had
  explicitly excluded.
- A3 fix: `groupby(...).apply(...)` for child_nan now passes
  `include_groups=False` to silence pandas 2.2+ deprecation and stay
  forward-compatible with pandas 3.x.
- M1 fix: empty df_proc after filtering now raises a clear error and
  stops the pipeline instead of triggering ZeroDivisionError on the
  data quality metrics. Triggered by overly-aggressive combinations
  of tag filter / spatial bounds / dead zones.

v4 changes:
- BACKEND: imports from social_analysis_v9 (was v8). v9 adds
  `build_export_bundle(...)` — pure additive; all v8 signatures unchanged.
- NEW: "📦 Download complete export bundle (ZIP)" button at the top of the
  Download Results section. One ZIP containing all CSVs (proximity events,
  dyad distances, metrics, cleaned trajectories, optional stationary time,
  optional merge diagnostics), a config snapshot, a column dictionary, and
  the loader script(s) selected on page 1 via `export_format_pref`. The
  intent is that researchers in the pilot can hand a single ZIP to their
  preferred environment and load it with one command.
- KEPT: the per-(subset, distance) individual CSV download buttons remain
  below the bundle button as a fallback, in case a user wants only one
  piece. They are unchanged from v3.

v3 changes:
- BACKEND: imports from social_analysis_v8 (was v7). v8 adds optional
  smoothing kwargs to process_all with backward-compatible defaults.
- Threads `smoothing_enabled` and `smoothing_window_sec` from cfg into
  both process_all call sites (single-tag and multi-tag). Both default
  to off via cfg.get(...) fallbacks.

v2 changes (merged from two forked lineages):
- NEW: Multi-distance pipeline using run_analysis_multi_distance
  (computes distance matrix once, thresholds N times — efficient)
- NEW: Stationary time estimation and display
- NEW: Dead zone comparison mode (run analysis with and without DZ)
- NEW: Multi-distance comparison charts (episode count, time by threshold)
- PRESERVED: Multi-tag diagnostics (merge quality, inter-tag distances)
- PRESERVED: Entity label switching (Subject vs Tag column names)

Results structure:
  subset_results[subset_name][distance] = {'prox': ..., 'dist': ...}
  subset_metrics[subset_name][distance] = {metrics dict}

Upstream: requires st.session_state["raw_data"] and st.session_state["config"].
"""

import streamlit as st
import pandas as pd
import numpy as np
import copy
import time
import sys
import os
import plotly.express as px
import plotly.graph_objects as go
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from social_analysis_v13 import (
    apply_dead_zones, process_all,
    run_analysis, run_analysis_multi_distance,
    compute_metrics, filter_subset_windows,
    calc_stationary_time,
    build_export_bundle,
    refresh_velocity,
    build_dyad_proximity_table,
)
from streamlit_subsets_v6 import render_subset_builder_v3, parsed_timestamps


st.set_page_config(page_title="Define Analysis & Run", page_icon="▶️", layout="wide")
st.title("▶️ Define Analysis & Run")
st.caption("Stage 3 of 3 — define subsets, run the pipeline, view results.")

# ─────────────────────────────────────────────────────────────────────────────
# PREREQUISITE CHECKS
# ─────────────────────────────────────────────────────────────────────────────

if "raw_data" not in st.session_state:
    st.warning("No data loaded. Go to **Upload & Inspect** first.")
    st.stop()

if "config" not in st.session_state:
    st.warning("No configuration found. Go to **Clean & Configure** first.")
    st.stop()

raw = st.session_state["raw_data"]
cfg = st.session_state["config"]

# ── Determine mode ──
multi_tag = cfg.get("multi_tag_enabled", False)
subject_mapping = cfg.get("subject_mapping") if multi_tag else None
entity_label = "Subject" if multi_tag else "Tag"

# Backward compat: single critical_distance → list
critical_distances = cfg.get("critical_distances", [cfg.get("critical_distance", 1.2)])
if isinstance(critical_distances, (int, float)):
    critical_distances = [critical_distances]
use_multi_dist = len(critical_distances) > 1

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

with st.expander("📋 Configuration summary", expanded=True):
    col1, col2, col3 = st.columns(3)
    col1.metric("Timestep", f"{cfg['timestep_ms']} ms")
    col1.metric("Max interpolation", f"{cfg['max_interpolation']} samples")
    col2.metric("Critical distances", ", ".join(f"{d}m" for d in critical_distances))
    col2.metric("Min duration", f"{cfg['critical_duration_s']} s")
    col3.metric("Tags", raw["TagId"].nunique())
    col3.metric("Rows", f"{len(raw):,}")

    if multi_tag and subject_mapping:
        n_multi = sum(1 for t in subject_mapping.values() if len(t) > 1)
        n_single = sum(1 for t in subject_mapping.values() if len(t) == 1)
        st.markdown(
            f"**Multi-tag mode:** {len(subject_mapping)} subjects "
            f"({n_multi} multi-tag, {n_single} single-tag) · "
            f"Inter-tag threshold: {cfg.get('inter_tag_threshold', 1.0)}m · "
            f"Dead zone mode: {cfg.get('dz_mode', 'permissive')}"
        )

    n_dz = len(cfg.get("dead_zones", []))
    if n_dz:
        st.markdown(f"**Dead zones:** {n_dz} defined")

    if cfg.get("selected_tags"):
        st.markdown(f"**Tag filter:** {len(cfg['selected_tags'])} tags selected")

    st.markdown(
        f"**Stationary time:** displacement < {cfg.get('displacement_threshold', 0.3)}m "
        f"over {cfg.get('stationary_window_sec', 3.0)}s window"
    )

# ─────────────────────────────────────────────────────────────────────────────
# NAMED SUBSETS
# ─────────────────────────────────────────────────────────────────────────────

st.header("1. Define Analysis Subsets")

ts = parsed_timestamps(raw)
avail_dates = sorted(pd.Timestamp(d).date() for d in ts.dt.normalize().dropna().unique())

subsets = render_subset_builder_v3(avail_dates, raw_df=raw)

cfg["subsets"] = subsets
st.session_state["config"] = cfg

# ─────────────────────────────────────────────────────────────────────────────
# RUN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

st.header("2. Run Pipeline")

has_dead_zones = bool(cfg.get("dead_zones"))
compare_dz = False
if has_dead_zones:
    compare_dz = st.checkbox(
        "Compare episodes with and without dead zones",
        value=False,
        help="Runs the proximity analysis twice: once before and once after "
             "applying dead zones, so you can see how many false episodes "
             "the dead zones prevent. Only meaningful in single-tag mode — "
             "ignored when multi-tag is active (dead zones are applied "
             "before the merge there).",
    )
    if compare_dz and multi_tag:
        st.info(
            "ℹ️ Dead zone comparison is disabled in multi-tag mode because "
            "dead zones are applied per-tag *before* merging into subjects. "
            "The comparison will be skipped."
        )
        compare_dz = False
    elif compare_dz:
        st.warning(
            "⚠️ This will approximately **double the analysis time** because "
            "episode detection runs on both the unfiltered and filtered data."
        )

# A1 fix (v5): detect the empty-list error sentinel from page 2 v6.
# `selected_tags == []` means the user is in a tag-selection error state on
# page 2 (e.g., excluded too many tags). We block the Run button rather than
# silently running on all tags.
_st_value = cfg.get("selected_tags")
_tag_selection_error = isinstance(_st_value, list) and len(_st_value) == 0
if _tag_selection_error:
    st.error(
        "⛔ **Tag selection is in an error state on the Clean & Configure page.** "
        "Pairwise analysis requires at least 2 tags. Go back to page 2, "
        "section 5, and select more tags before running the pipeline."
    )

if st.button(
    "🚀 Run Full Pipeline",
    type="primary",
    use_container_width=True,
    disabled=_tag_selection_error,
):

    progress = st.progress(0, text="Starting...")
    status = st.empty()
    t_start = time.time()

    try:
        # ── Step 1: Prepare data ──
        progress.progress(5, text="Step 1: Preparing data...")
        df_work = raw.copy()

        if cfg.get("selected_tags"):
            before_tags = df_work["TagId"].nunique()
            df_work = df_work[df_work["TagId"].isin(cfg["selected_tags"])].copy()
            after_tags = df_work["TagId"].nunique()
            status.info(f"Tag filter: {before_tags} → {after_tags} tags ({len(df_work):,} rows)")

        # ── Step 2: Spatial bounds ──
        progress.progress(10, text="Step 2: Computing spatial bounds...")
        margin = cfg["spatial_margin"]
        if cfg.get("manual_x_bounds") is not None:
            x_bounds = cfg["manual_x_bounds"]
        else:
            x_bounds = (
                df_work["X"].quantile(0.001) - margin,
                df_work["X"].quantile(0.999) + margin,
            )

        if cfg.get("manual_y_bounds") is not None:
            y_bounds = cfg["manual_y_bounds"]
        else:
            y_bounds = (
                df_work["Y"].quantile(0.001) - margin,
                df_work["Y"].quantile(0.999) + margin,
            )

        in_bounds = (
            (df_work["X"].isna() | ((df_work["X"] >= x_bounds[0]) & (df_work["X"] <= x_bounds[1]))) &
            (df_work["Y"].isna() | ((df_work["Y"] >= y_bounds[0]) & (df_work["Y"] <= y_bounds[1])))
        )
        removed_oob = (~in_bounds).sum()
        df_work = df_work[in_bounds].copy()
        status.info(
            f"Bounds: X=[{x_bounds[0]:.1f}, {x_bounds[1]:.1f}], "
            f"Y=[{y_bounds[0]:.1f}, {y_bounds[1]:.1f}] — removed {removed_oob:,} OOB points"
        )

        # ── Step 3: Process (resample, filter, maybe merge) ──
        if multi_tag and subject_mapping:
            progress.progress(15, text="Step 3: Processing (resample → filter → merge)...")
            status.info("Running process_all() with multi-tag merge — this may take a minute...")

            # In multi-tag mode, dead zones are handled INSIDE process_all
            df_proc, tags_dict, dates_list, merge_diag = process_all(
                [df_work],
                timestep_ms=cfg["timestep_ms"],
                max_velocity=cfg["max_velocity"],
                x_bounds=x_bounds,
                y_bounds=y_bounds,
                max_gap_factor=cfg["max_gap_factor"],
                max_interpolation=cfg["max_interpolation"],
                subject_mapping=subject_mapping,
                inter_tag_threshold=cfg.get("inter_tag_threshold", 1.0),
                dead_zones=cfg.get("dead_zones", []),
                dz_mode=cfg.get("dz_mode", "permissive"),
                smoothing_enabled=cfg.get("smoothing_enabled", False),
                smoothing_window_sec=cfg.get("smoothing_window_sec", None),
            )

            # Measure NaN rates after everything
            nan_pos_before_dz = None  # Not meaningful in multi-tag mode
            nan_pos_after_dz = df_proc["X"].isna().mean() * 100
            dz_impact_info = None
        else:
            progress.progress(15, text="Step 3: Processing (resample → filter)...")
            status.info("Running process_all() — this may take a minute...")

            df_proc, tags_dict, dates_list, merge_diag = process_all(
                [df_work],
                timestep_ms=cfg["timestep_ms"],
                max_velocity=cfg["max_velocity"],
                x_bounds=x_bounds,
                y_bounds=y_bounds,
                max_gap_factor=cfg["max_gap_factor"],
                max_interpolation=cfg["max_interpolation"],
                smoothing_enabled=cfg.get("smoothing_enabled", False),
                smoothing_window_sec=cfg.get("smoothing_window_sec", None),
            )

            # In single-tag mode, dead zones applied AFTER process_all
            dz_impact_info = None
            if cfg.get("dead_zones"):
                progress.progress(35, text="Step 4: Applying dead zones...")

                nan_pos_before_dz = df_proc["X"].isna().mean() * 100
                nan_vel_before_dz = df_proc["Velocity"].isna().mean() * 100

                # Run episode analysis WITHOUT dead zones if comparison requested
                no_dz_metrics = None
                if compare_dz:
                    progress.progress(37, text="Step 4: Analysing episodes WITHOUT dead zones...")
                    status.info("Running episode analysis on data before dead zone removal...")
                    if use_multi_dist:
                        no_dz_results = run_analysis_multi_distance(
                            df_proc,
                            critical_distances=critical_distances,
                            min_episode_samples=cfg["min_episode_samples"],
                            timestep_ms=cfg["timestep_ms"],
                        )
                        no_dz_metrics = {
                            d: compute_metrics(r, timestep_ms=cfg["timestep_ms"])
                            for d, r in no_dz_results.items()
                        }
                    else:
                        d = critical_distances[0]
                        no_dz_res = run_analysis(
                            df_proc,
                            critical_distance=d,
                            min_episode_samples=cfg["min_episode_samples"],
                            timestep_ms=cfg["timestep_ms"],
                        )
                        no_dz_metrics = {d: compute_metrics(no_dz_res, timestep_ms=cfg["timestep_ms"])}

                df_proc = apply_dead_zones(df_proc, cfg["dead_zones"])
                # apply_dead_zones only blanks X/Y; recompute Velocity so it is
                # NaN wherever the position is, and the velocity stats are real.
                df_proc = refresh_velocity(df_proc, cfg["timestep_ms"], cfg["max_gap_factor"])

                nan_pos_after_dz = df_proc["X"].isna().mean() * 100
                nan_vel_after_dz = df_proc["Velocity"].isna().mean() * 100

                dz_impact_info = {
                    "nan_pos_before": nan_pos_before_dz,
                    "nan_pos_after": nan_pos_after_dz,
                    "nan_vel_before": nan_vel_before_dz,
                    "nan_vel_after": nan_vel_after_dz,
                    "no_dz_metrics": no_dz_metrics,
                }
                status.info(
                    f"Dead zones: position NaN {nan_pos_before_dz:.1f}% → {nan_pos_after_dz:.1f}%, "
                    f"velocity NaN {nan_vel_before_dz:.1f}% → {nan_vel_after_dz:.1f}%"
                )

        # ── Step 5: Stationary time ──
        progress.progress(45, text="Step 5: Estimating stationary time...")
        stationary_df = calc_stationary_time(
            df_proc,
            timestep_ms=cfg["timestep_ms"],
            displacement_threshold=cfg.get("displacement_threshold", 0.3),
            window_sec=cfg.get("stationary_window_sec", 3.0),
        )

        progress.progress(50, text="Step 6: Running analysis per subset...")
        n_entities = len(tags_dict)
        status.info(
            f"Processed: {len(df_proc):,} rows, {n_entities} {entity_label.lower()}(s), "
            f"{len(dates_list)} date(s)"
        )

        # ── Data quality metrics ──
        n_total = len(df_proc)
        # M1 fix (v5): hard stop on empty df_proc rather than ZeroDivisionError.
        # An empty processed DataFrame means filtering was too aggressive
        # (combination of tag filter, spatial bounds, and dead zones removed
        # everything). Better to fail loudly with actionable guidance than
        # to silently divide by zero or produce a meaningless empty result.
        if n_total == 0:
            progress.empty()
            status.empty()
            st.error(
                "⛔ **No data left after processing.** All rows were removed "
                "by the combined filters (tag selection, spatial bounds, dead "
                "zones, gap filtering). Go back to **Clean & Configure** and:\n"
                "- Widen the spatial bounds (or switch to auto-detect)\n"
                "- Remove or shrink dead zones\n"
                "- Include more tags in section 5\n"
                "- Increase max gap factor / max interpolation"
            )
            st.stop()
        nan_pos_pct = df_proc["X"].isna().sum() / n_total * 100
        nan_vel_pct = df_proc["Velocity"].isna().sum() / n_total * 100

        # A3 fix (v5): include_groups=False silences pandas 2.2+ deprecation
        # warning and stays forward-compatible with pandas 3.x. The kwarg
        # was added in 2.2.0; on older pandas we fall back to the legacy
        # call. This try/except is defensive against unknown collaborator
        # environments — remove once pandas ≥2.2 is pinned in requirements.
        def _child_nan_agg(g):
            return pd.Series({
                "nan_pos_pct": g["X"].isna().sum() / len(g) * 100,
                "nan_vel_pct": g["Velocity"].isna().sum() / len(g) * 100,
                "n_samples": len(g),
            })
        try:
            child_nan = df_proc.reset_index().groupby("TagId").apply(
                _child_nan_agg, include_groups=False
            )
        except TypeError:
            # pandas < 2.2 doesn't support include_groups
            child_nan = df_proc.reset_index().groupby("TagId").apply(_child_nan_agg)

        # ── Run analysis per subset ──
        subsets_list = cfg.get(
            "subsets",
            [{"name": "Full Recording", "windows": [], "window_mode": None}],
        )

        # subset_results[name][distance] = {'prox': ..., 'dist': ...}
        subset_results = {}
        subset_metrics = {}
        # 2026-10-18: subsets that are not analysed, with the reason; shown
        # in the results (the status line below is overwritten by later steps).
        skipped_subsets = []

        for s_idx, subset in enumerate(subsets_list):
            pct = 50 + int(45 * (s_idx + 1) / len(subsets_list))
            progress.progress(pct, text=f"Analyzing subset: {subset['name']}...")

            # 2026-10-18: a custom subset without time windows used to fall
            # through to the full recording (a silent copy of Full Recording
            # under another name). It is now skipped. Full Recording itself
            # has window_mode None and is not affected.
            if subset["window_mode"] is not None and not subset["windows"]:
                skipped_subsets.append((subset["name"], "no time windows defined"))
                status.warning(f"  {subset['name']}: no time windows defined — skipping")
                continue

            if subset["windows"] and subset["window_mode"]:
                df_subset = filter_subset_windows(df_proc, subset["windows"], subset["window_mode"])
                status.info(f"  {subset['name']}: {len(df_subset):,} rows after time filtering")
            else:
                df_subset = df_proc

            if len(df_subset) == 0:
                skipped_subsets.append((subset["name"], "no data inside its time windows"))
                status.warning(f"  {subset['name']}: no data after filtering — skipping")
                continue

            if use_multi_dist:
                multi_results = run_analysis_multi_distance(
                    df_subset,
                    critical_distances=critical_distances,
                    min_episode_samples=cfg["min_episode_samples"],
                    timestep_ms=cfg["timestep_ms"],
                )
                subset_results[subset["name"]] = multi_results
                subset_metrics[subset["name"]] = {
                    d: compute_metrics(r, timestep_ms=cfg["timestep_ms"])
                    for d, r in multi_results.items()
                }
            else:
                d = critical_distances[0]
                results = run_analysis(
                    df_subset,
                    critical_distance=d,
                    min_episode_samples=cfg["min_episode_samples"],
                    timestep_ms=cfg["timestep_ms"],
                )
                subset_results[subset["name"]] = {d: results}
                subset_metrics[subset["name"]] = {
                    d: compute_metrics(results, timestep_ms=cfg["timestep_ms"])
                }

        elapsed = time.time() - t_start
        progress.progress(100, text=f"✅ Complete in {elapsed:.1f}s")

        # Build dead zone episode comparison (Full Recording only, single-tag only)
        dz_episode_comparison = None
        if (compare_dz and dz_impact_info is not None
                and dz_impact_info.get("no_dz_metrics")
                and "Full Recording" in subset_metrics):
            no_dz_metrics = dz_impact_info["no_dz_metrics"]
            dz_episode_comparison = {}
            with_dz = subset_metrics["Full Recording"]
            for d in critical_distances:
                if d in with_dz and d in no_dz_metrics:
                    dz_episode_comparison[d] = {
                        "without_dz": no_dz_metrics[d],
                        "with_dz": with_dz[d],
                    }

        # Store everything
        st.session_state["run_config"] = copy.deepcopy(cfg)
        st.session_state["df_proc"] = df_proc
        st.session_state["tags_dict"] = tags_dict
        st.session_state["dates_list"] = dates_list
        st.session_state["subset_results"] = subset_results
        st.session_state["subset_metrics"] = subset_metrics
        st.session_state["stationary_df"] = stationary_df
        st.session_state["critical_distances"] = critical_distances
        st.session_state["child_nan"] = child_nan
        st.session_state["x_bounds"] = x_bounds
        st.session_state["y_bounds"] = y_bounds
        st.session_state["nan_pos_pct"] = nan_pos_pct
        st.session_state["nan_vel_pct"] = nan_vel_pct
        st.session_state["dz_impact"] = dz_impact_info
        st.session_state["dz_episode_comparison"] = dz_episode_comparison
        st.session_state["merge_diagnostics"] = merge_diag
        st.session_state["skipped_subsets"] = skipped_subsets

        st.success(
            f"Pipeline completed in {elapsed:.1f}s — "
            f"{len(subset_results)} subset(s), {len(critical_distances)} distance threshold(s)."
        )

    except Exception as e:
        progress.progress(0, text="❌ Error")
        st.error(f"Pipeline failed: {e}")
        st.exception(e)
        st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# DISPLAY RESULTS
# ─────────────────────────────────────────────────────────────────────────────

if "subset_results" in st.session_state:
    subset_results = st.session_state["subset_results"]
    subset_metrics = st.session_state["subset_metrics"]
    critical_distances = st.session_state["critical_distances"]
    use_multi_dist = len(critical_distances) > 1
    merge_diag = st.session_state.get("merge_diagnostics")

    # Everything below describes the RUN that produced these results, so read the
    # settings snapshotted at run time, not whatever page 2 holds right now.
    run_cfg = st.session_state.get("run_config", cfg)
    multi_tag = run_cfg.get("multi_tag_enabled", False)
    subject_mapping = run_cfg.get("subject_mapping") if multi_tag else None
    entity_label = "Subject" if multi_tag else "Tag"
    changed = [k for k in run_cfg
               if k != "subsets" and run_cfg.get(k) != cfg.get(k)]

    # Per-pair proximity relative to joint observed time (v12), for every
    # subset and distance of this run. Cheap (group-bys on the episode and
    # dyad tables), so it is rebuilt from the stored results on each rerun.
    dyad_prox_all = build_dyad_proximity_table(subset_results, run_cfg["timestep_ms"])

    st.markdown("---")
    st.header("3. Results")
    if changed:
        st.warning(
            "⚠️ Settings on Clean & Configure changed since this run "
            f"({', '.join(sorted(changed))}). The results below, and the export, "
            "use the settings the run was made with. Re-run to apply the new ones."
        )
    _skipped = st.session_state.get("skipped_subsets") or []
    if _skipped:
        st.warning(
            "⚠️ Not analysed in this run: "
            + "; ".join(f"**{_n}** ({_why})" for _n, _why in _skipped)
            + ". These subsets have no results and are not in the downloads."
        )
    cfg = run_cfg

    # ── Multi-tag diagnostics ──
    if merge_diag:
        st.subheader("🔗 Multi-Tag Merge Diagnostics")

        if subject_mapping:
            has_multi = any(len(t) > 1 for t in subject_mapping.values())
            has_single = any(len(t) == 1 for t in subject_mapping.values())
            if has_multi and has_single:
                st.warning(
                    "⚠️ **NaN rate comparability warning:** This dataset contains both "
                    "multi-tag and single-tag subjects. Multi-tag subjects will generally "
                    "have **lower** NaN rates because one tag can cover when the other "
                    "drops out. NaN statistics are therefore **not directly comparable** "
                    "between multi-tag and single-tag subjects."
                )

        diag_rows = []
        any_high_fail = False
        for subj_name, d in merge_diag.items():
            total = d["n_total"]
            if total == 0:
                continue

            pct_centroid = d["n_centroid"] / total * 100
            pct_fallback = d["n_fallback"] / total * 100
            pct_fail = d["n_consistency_fail"] / total * 100
            pct_nan = d["n_all_nan"] / total * 100

            inter_dists = d["inter_tag_distances"]
            if inter_dists:
                arr = np.array(inter_dists)
                med_dist = np.median(arr)
                p95_dist = np.percentile(arr, 95)
            else:
                med_dist = 0.0
                p95_dist = 0.0

            if pct_fail > 20:
                any_high_fail = True

            diag_rows.append({
                entity_label: subj_name,
                "Timesteps": total,
                "Centroid %": f"{pct_centroid:.1f}",
                "Fallback %": f"{pct_fallback:.1f}",
                "Consistency Fail %": f"{pct_fail:.1f}",
                "All NaN %": f"{pct_nan:.1f}",
                "Inter-tag Median (m)": f"{med_dist:.3f}",
                "Inter-tag P95 (m)": f"{p95_dist:.3f}",
            })

        if diag_rows:
            st.dataframe(pd.DataFrame(diag_rows), use_container_width=True, hide_index=True)

        if any_high_fail:
            st.error(
                "🚨 **One or more subjects have >20% consistency failures.** "
                "This strongly suggests an incorrect tag-to-subject mapping, "
                "or one tag has physically detached. Check the mapping on the "
                "Clean & Configure page."
            )

        with st.expander("Inter-tag distance distributions", expanded=False):
            for subj_name, d in merge_diag.items():
                dists = d["inter_tag_distances"]
                if not dists:
                    continue
                fig = px.histogram(
                    x=dists,
                    nbins=50,
                    title=f"Inter-tag distance: {subj_name}",
                    labels={"x": "Distance (m)", "y": "Count"},
                )
                threshold_val = cfg.get("inter_tag_threshold", 1.0)
                fig.add_vline(
                    x=threshold_val, line_dash="dash", line_color="red",
                    annotation_text=f"Threshold ({threshold_val}m)",
                )
                fig.update_layout(height=300, margin=dict(t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)

    # ── Data Quality ──
    st.subheader("Data Quality")

    q1, q2, q3 = st.columns(3)
    q1.metric("Processed rows", f"{len(st.session_state['df_proc']):,}")
    q2.metric("NaN position rate", f"{st.session_state['nan_pos_pct']:.1f}%")
    q3.metric("NaN velocity rate", f"{st.session_state['nan_vel_pct']:.1f}%")

    # Dead zone cleanup stats (single-tag only)
    dz_impact = st.session_state.get("dz_impact")
    if dz_impact is not None:
        pos_nullified = dz_impact['nan_pos_after'] - dz_impact['nan_pos_before']
        vel_nullified = dz_impact['nan_vel_after'] - dz_impact['nan_vel_before']
        pos_useful = 100 - dz_impact['nan_pos_after']
        vel_useful = 100 - dz_impact['nan_vel_after']

        st.markdown("**Dead zone cleanup:**")
        dz1, dz2, dz3, dz4 = st.columns(4)
        dz1.metric("Positions nullified by DZ", f"{pos_nullified:.1f}%")
        dz2.metric("Useful position data", f"{pos_useful:.1f}%",
                   help=f"Before DZ: {100 - dz_impact['nan_pos_before']:.1f}%")
        dz3.metric("Velocity affected by DZ", f"{vel_nullified:.1f}%")
        dz4.metric("Useful velocity data", f"{vel_useful:.1f}%",
                   help=f"Before DZ: {100 - dz_impact['nan_vel_before']:.1f}%")

    # Dead zone episode comparison
    dz_ep_comp = st.session_state.get("dz_episode_comparison")
    if dz_ep_comp:
        st.markdown("**🔍 Dead zone effect on proximity episodes (Full Recording):**")
        comp_rows = []
        for d, comp in sorted(dz_ep_comp.items()):
            wo = comp["without_dz"]
            wi = comp["with_dz"]
            ep_diff = wo["proximity_episodes"] - wi["proximity_episodes"]
            time_diff = wo["proximity_time_sec"] - wi["proximity_time_sec"]
            comp_rows.append({
                "Distance (m)": d,
                "Episodes without DZ": wo["proximity_episodes"],
                "Episodes with DZ": wi["proximity_episodes"],
                "False episodes removed": ep_diff,
                "Time without DZ (s)": f"{wo['proximity_time_sec']:.1f}",
                "Time with DZ (s)": f"{wi['proximity_time_sec']:.1f}",
                "Time removed (s)": f"{time_diff:.1f}",
            })
        st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

        for d, comp in sorted(dz_ep_comp.items()):
            wo = comp["without_dz"]
            wi = comp["with_dz"]
            ep_diff = wo["proximity_episodes"] - wi["proximity_episodes"]
            if ep_diff > 0:
                pct = ep_diff / wo["proximity_episodes"] * 100 if wo["proximity_episodes"] > 0 else 0
                dist_label = f" at {d}m" if len(dz_ep_comp) > 1 else ""
                st.caption(
                    f"Dead zones prevented **{ep_diff}** false episodes{dist_label} "
                    f"({pct:.1f}% of total without dead zones)."
                )

    with st.expander(f"Per-{entity_label.lower()} data quality", expanded=False):
        child_nan = st.session_state["child_nan"]
        display_nan = child_nan.copy()
        display_nan.index.name = entity_label
        st.dataframe(
            display_nan.style.background_gradient(subset=["nan_pos_pct"], cmap="Reds"),
            use_container_width=True,
        )

        fig_nan = px.bar(
            child_nan.reset_index(),
            x="TagId", y="nan_pos_pct",
            title=f"NaN Position Rate per {entity_label}",
            labels={"nan_pos_pct": "NaN Position %", "TagId": entity_label},
            color="nan_pos_pct", color_continuous_scale="Reds",
        )
        fig_nan.update_xaxes(type="category")
        st.plotly_chart(fig_nan, use_container_width=True)

    # ── Stationary Time ──
    st.subheader("🧍 Stationary Time Estimation")
    stationary_df = st.session_state.get("stationary_df", pd.DataFrame())

    if len(stationary_df) > 0:
        disp_thresh = cfg.get("displacement_threshold", 0.3)
        win_sec = cfg.get("stationary_window_sec", 3.0)
        st.caption(
            f"Stationary = displacement < {disp_thresh}m over {win_sec}s rolling window. "
            "This measures lack of movement, not posture (sitting vs standing cannot be "
            "distinguished from XY position data alone)."
        )

        display_stat = stationary_df.copy()
        if multi_tag:
            display_stat = display_stat.rename(columns={"TagId": entity_label})

        st.dataframe(
            display_stat.style.background_gradient(
                subset=["stationary_pct"], cmap="Blues"
            ),
            use_container_width=True, hide_index=True,
        )

        fig_stat = px.bar(
            stationary_df.sort_values("stationary_pct", ascending=False),
            x="TagId", y="stationary_pct",
            title=f"Stationary Time per {entity_label} (%)",
            labels={"stationary_pct": "Stationary %", "TagId": entity_label},
            color="stationary_pct", color_continuous_scale="Blues",
        )
        fig_stat.update_xaxes(type="category")
        fig_stat.update_yaxes(range=[0, 100])
        st.plotly_chart(fig_stat, use_container_width=True)
    else:
        st.info("No stationary time data available.")

    # ── Metrics Summary Table ──
    st.subheader("Metrics Summary")

    selected_dist_display = None
    if use_multi_dist:
        selected_dist_display = st.selectbox(
            "Select distance threshold for detailed view",
            options=critical_distances,
            format_func=lambda d: f"{d} m",
            key="detail_dist_select",
        )

    metrics_table = []
    for name, dist_metrics in subset_metrics.items():
        for d, m in dist_metrics.items():
            metrics_table.append({
                "Subset": name,
                "Distance (m)": d,
                "Wgt. Mean Dist (m)": f"{m['mean_distance_m']:.2f}",
                "Episodes": m["proximity_episodes"],
                "Proximity Time (s)": f"{m['proximity_time_sec']:.1f}",
                "Within Distance (%)": (
                    f"{m['within_distance_fraction'] * 100:.2f}"
                    if pd.notna(m.get("within_distance_fraction")) else "–"
                ),
                "Episode Fraction (%)": (
                    f"{m['proximity_fraction'] * 100:.2f}"
                    if pd.notna(m.get("proximity_fraction")) else "–"
                ),
                "Mean Duration (s)": f"{m['proximity_mean_dur_sec']:.1f}",
            })

    st.dataframe(pd.DataFrame(metrics_table), use_container_width=True, hide_index=True)
    st.caption(
        "Within Distance = time pairs were closer than the threshold ÷ time they "
        "were observed together (both had a valid position), over all pairs, with "
        "no minimum duration. Episode Fraction = the same, counting only proximity "
        "episodes of at least the minimum duration."
    )

    # ── Multi-distance comparison charts ──
    if use_multi_dist:
        st.subheader("📏 Distance Threshold Comparison")

        for subset_name, dist_metrics in subset_metrics.items():
            st.markdown(f"**{subset_name}**")

            distances = sorted(dist_metrics.keys())
            episodes_by_dist = [dist_metrics[d]["proximity_episodes"] for d in distances]
            time_by_dist = [dist_metrics[d]["proximity_time_sec"] for d in distances]

            col_a, col_b = st.columns(2)

            with col_a:
                fig_ep = go.Figure()
                fig_ep.add_trace(go.Bar(
                    x=[f"{d}m" for d in distances],
                    y=episodes_by_dist,
                    marker_color="#42A5F5",
                ))
                fig_ep.update_layout(
                    title=f"Episode Count by Distance — {subset_name}",
                    xaxis_title="Critical Distance",
                    yaxis_title="Number of Episodes",
                    height=350,
                )
                st.plotly_chart(fig_ep, use_container_width=True)

            with col_b:
                fig_time = go.Figure()
                fig_time.add_trace(go.Bar(
                    x=[f"{d}m" for d in distances],
                    y=time_by_dist,
                    marker_color="#66BB6A",
                ))
                fig_time.update_layout(
                    title=f"Total Proximity Time by Distance — {subset_name}",
                    xaxis_title="Critical Distance",
                    yaxis_title="Total Time (s)",
                    height=350,
                )
                st.plotly_chart(fig_time, use_container_width=True)

    # ── Subset comparison (at a single distance) ──
    if len(subset_metrics) > 1:
        st.subheader("Subset Comparison")
        comp_dist = selected_dist_display if use_multi_dist else critical_distances[0]

        episode_counts = {}
        for name, dist_metrics in subset_metrics.items():
            if comp_dist in dist_metrics:
                episode_counts[name] = dist_metrics[comp_dist]["proximity_episodes"]

        fig_episodes = px.bar(
            x=list(episode_counts.keys()),
            y=list(episode_counts.values()),
            labels={"x": "Subset", "y": "Number of Episodes"},
            title=f"Proximity Episodes by Subset (at {comp_dist}m)",
            color=list(episode_counts.keys()),
        )
        st.plotly_chart(fig_episodes, use_container_width=True)

    # ── Episode Details per subset ──
    st.subheader("Episode Details")

    subset_names = list(subset_results.keys())
    selected_subset = st.selectbox("Select subset", subset_names)

    detail_dist = selected_dist_display if use_multi_dist else critical_distances[0]

    results = subset_results[selected_subset].get(detail_dist, {})
    prox_df = results.get("prox", pd.DataFrame())
    dist_df = results.get("dist", pd.DataFrame())

    # 2026-10-18: the tabs are shown whenever pairs were observed together
    # (dyad rows exist), not only when there are episodes. Before, a subset /
    # distance without episodes hid the Pair Summary, including its
    # within-distance fraction (which counts time below the threshold without
    # a minimum duration, so it can be > 0 when there are no episodes).
    if len(prox_df) > 0 or len(dist_df) > 0:
        tab_prox, tab_dist, tab_pairs = st.tabs(
            ["Proximity Episodes", "Distance Metrics", "Pair Summary"]
        )

        display_prox = prox_df.copy()
        display_dist = dist_df.copy()
        if multi_tag:
            rename_map = {"TagId_A": f"{entity_label}_A", "TagId_B": f"{entity_label}_B"}
            display_prox = display_prox.rename(columns=rename_map)
            display_dist = display_dist.rename(columns=rename_map)

        with tab_prox:
            if len(prox_df) > 0:
                st.write(
                    f"**{len(prox_df)} episodes** in subset: {selected_subset} "
                    f"(distance: {detail_dist}m)"
                )
                st.dataframe(display_prox, use_container_width=True)

                fig_dur = px.histogram(
                    prox_df, x="duration_sec", nbins=30,
                    title=f"Episode Duration Distribution ({selected_subset}, {detail_dist}m)",
                    labels={"duration_sec": "Duration (seconds)"},
                )
                st.plotly_chart(fig_dur, use_container_width=True)
            else:
                st.info(
                    f"No proximity episodes in subset: {selected_subset} at "
                    f"{detail_dist}m. Pairs may still have been closer than "
                    f"{detail_dist} m for stretches shorter than the minimum "
                    "episode duration — see **Within distance** in the Pair Summary tab."
                )

        with tab_dist:
            st.write(f"**{len(dist_df)} dyad distance records**")
            st.dataframe(display_dist, use_container_width=True)

        with tab_pairs:
            st.caption(
                "**Within distance** = time the pair was closer than the threshold "
                "÷ time both were observed (both had a valid position), with no "
                "minimum duration. Use it to compare pairs: total proximity time also "
                "grows with how long both tags were recorded. **Episode fraction** "
                "counts only proximity episodes of at least the minimum duration; "
                "gaps in the data split episodes, so it is slightly lower for pairs "
                "with many gaps. **Low joint time** marks pairs observed together "
                "for less than 25 % of the median pair's joint time; their fractions "
                "rest on little data."
            )
            pairs_here = dyad_prox_all[
                (dyad_prox_all["subset"] == selected_subset)
                & (dyad_prox_all["distance_threshold_m"] == detail_dist)
            ]
            periods = ["all"] + [p for p in pairs_here["Date"].unique() if p != "all"]
            period = st.selectbox(
                "Period", periods,
                format_func=lambda p: "Whole subset" if p == "all" else p,
                key="pair_summary_period",
            )
            view = pairs_here[pairs_here["Date"] == period]
            pair_table = pd.DataFrame({
                f"{entity_label} A": view["TagId_A"].to_numpy(),
                f"{entity_label} B": view["TagId_B"].to_numpy(),
                "Within distance (%)": (view["within_distance_fraction"] * 100).round(2).to_numpy(),
                "Episode fraction (%)": (view["proximity_fraction"] * 100).round(2).to_numpy(),
                "Proximity time (min)": (view["proximity_time_sec"] / 60).round(1).to_numpy(),
                "Joint observed (min)": (view["joint_observed_sec"] / 60).round(1).to_numpy(),
                "Episodes": view["n_episodes"].to_numpy(),
                "Episodes per joint hour": view["episodes_per_joint_hour"].round(2).to_numpy(),
                "Low joint time": view["low_joint_time"].to_numpy(),
            }).sort_values("Within distance (%)", ascending=False, kind="stable")
            n_low = int(pair_table["Low joint time"].sum())
            st.write(
                f"**{len(pair_table)} pairs** observed together in subset: "
                f"{selected_subset} (distance: {detail_dist}m)"
                + (f" — {n_low} with low joint time" if n_low else "")
            )
            st.dataframe(pair_table, use_container_width=True, hide_index=True)
    else:
        st.info(
            f"No pairs were observed together in subset: {selected_subset} "
            f"(no moment at which two {entity_label.lower()}s both had a valid position)."
        )

    # ── Download Results ──
    st.subheader("Download Results")

    # ─────────────────────────────────────────────────────────────────────
    # v4: complete export bundle (one ZIP containing everything + loader).
    # The format preference is set on page 1; default to "both" if missing.
    # ─────────────────────────────────────────────────────────────────────
    # Apply the same multi-tag column rename used by the individual buttons
    # below, so the bundle's CSVs and the per-subset CSVs stay consistent.
    def _rename_for_export(df):
        if df is None or len(df) == 0 or not multi_tag:
            return df
        return df.rename(columns={
            "TagId_A": f"{entity_label}_A",
            "TagId_B": f"{entity_label}_B",
        })

    subset_results_for_bundle = {}
    for _name, _by_dist in subset_results.items():
        subset_results_for_bundle[_name] = {}
        for _d, _r in _by_dist.items():
            subset_results_for_bundle[_name][_d] = {
                "prox": _rename_for_export(_r.get("prox", pd.DataFrame())),
                "dist": _rename_for_export(_r.get("dist", pd.DataFrame())),
            }

    # Build merge diagnostics export-ready dict once; reused below for
    # the standalone JSON button so we only compute this in one place.
    diag_export = None
    if merge_diag:
        diag_export = {}
        for subj_name, d in merge_diag.items():
            total = d["n_total"]
            inter_dists = d["inter_tag_distances"]
            diag_export[subj_name] = {
                "n_total": total,
                "n_centroid": d["n_centroid"],
                "n_fallback": d["n_fallback"],
                "n_consistency_fail": d["n_consistency_fail"],
                "n_all_nan": d["n_all_nan"],
                "pct_centroid": round(d["n_centroid"] / total * 100, 1) if total else 0,
                "pct_fallback": round(d["n_fallback"] / total * 100, 1) if total else 0,
                "pct_consistency_fail": round(d["n_consistency_fail"] / total * 100, 1) if total else 0,
                "pct_all_nan": round(d["n_all_nan"] / total * 100, 1) if total else 0,
                "inter_tag_median_m": round(float(np.median(inter_dists)), 4) if inter_dists else None,
                "inter_tag_p95_m": round(float(np.percentile(inter_dists, 95)), 4) if inter_dists else None,
            }

    fmt_pref = st.session_state.get("export_format_pref", "both")
    try:
        bundle_bytes = build_export_bundle(
            subset_results=subset_results_for_bundle,
            subset_metrics=subset_metrics,
            df_proc=st.session_state.get("df_proc"),
            config=run_cfg,
            stationary_df=stationary_df if len(stationary_df) > 0 else None,
            merge_diagnostics=diag_export,
            format_pref=fmt_pref,
            dyad_proximity=_rename_for_export(dyad_prox_all),
        )
        _fmt_label = {"python": "Python", "r": "R", "both": "Python + R"}[fmt_pref]
        st.download_button(
            f"📦 Download complete export bundle (ZIP, includes {_fmt_label} loader)",
            bundle_bytes,
            file_name="tracklab_companion_export.zip",
            mime="application/zip",
            key="dl_bundle",
            type="primary",
        )
        st.caption(
            "Bundle contains all CSVs, a column dictionary, a config snapshot, "
            "and a `load_results` script in your chosen language. "
            "Format selected on **page 1 → Export Preferences** "
            f"(currently: **{_fmt_label}**)."
        )
    except Exception as e:
        st.error(f"Could not build export bundle: {type(e).__name__}: {e}")

    st.markdown("**Individual downloads** (use these if you only want one piece):")

    for name, dist_results in subset_results.items():
        safe_name = name.lower().replace(" ", "_")
        for d, results in dist_results.items():
            safe_dist = str(d).replace(".", "_")
            dist_label = f" ({d}m)" if use_multi_dist else ""

            prox = results.get("prox", pd.DataFrame())
            if len(prox) > 0:
                dl_prox = prox.copy()
                if multi_tag:
                    dl_prox = dl_prox.rename(columns={
                        "TagId_A": f"{entity_label}_A",
                        "TagId_B": f"{entity_label}_B",
                    })
                csv = dl_prox.to_csv(index=False)
                st.download_button(
                    f"📥 {name}{dist_label} episodes ({len(prox)} rows)",
                    csv,
                    file_name=f"episodes_{safe_name}_{safe_dist}m.csv",
                    mime="text/csv",
                    key=f"dl_ep_{safe_name}_{safe_dist}",
                )

            dist = results.get("dist", pd.DataFrame())
            if len(dist) > 0:
                dl_dist = dist.copy()
                if multi_tag:
                    dl_dist = dl_dist.rename(columns={
                        "TagId_A": f"{entity_label}_A",
                        "TagId_B": f"{entity_label}_B",
                    })
                csv_dist = dl_dist.to_csv(index=False)
                st.download_button(
                    f"📥 {name}{dist_label} dyad distances ({len(dist)} rows)",
                    csv_dist,
                    file_name=f"dyad_distances_{safe_name}_{safe_dist}m.csv",
                    mime="text/csv",
                    key=f"dl_dist_{safe_name}_{safe_dist}",
                )

            pairs_dl = dyad_prox_all[
                (dyad_prox_all["subset"] == name)
                & (dyad_prox_all["distance_threshold_m"] == d)
            ].drop(columns=["subset", "distance_threshold_m"])
            if len(pairs_dl) > 0:
                n_pairs = int((pairs_dl["Date"] == "all").sum())
                csv_pairs = _rename_for_export(pairs_dl).to_csv(index=False)
                st.download_button(
                    f"📥 {name}{dist_label} pair proximity ({n_pairs} pairs)",
                    csv_pairs,
                    file_name=f"dyad_proximity_{safe_name}_{safe_dist}m.csv",
                    mime="text/csv",
                    key=f"dl_pairs_{safe_name}_{safe_dist}",
                )

    # Stationary time download
    if len(stationary_df) > 0:
        csv_stat = stationary_df.to_csv(index=False)
        st.download_button(
            f"📥 Stationary time ({len(stationary_df)} {entity_label.lower()}s)",
            csv_stat,
            file_name="stationary_time.csv",
            mime="text/csv",
        )

    # Multi-tag diagnostics download (uses diag_export computed above)
    if diag_export is not None:
        diag_json = json.dumps(diag_export, indent=2)
        st.download_button(
            "📥 Multi-tag merge diagnostics (JSON)",
            diag_json,
            file_name="merge_diagnostics.json",
            mime="application/json",
        )

    config_json = json.dumps(run_cfg, default=str, indent=2)
    st.download_button(
        "📥 Configuration (JSON)",
        config_json,
        file_name="tracklab_config.json",
        mime="application/json",
    )

else:
    st.info(
        "Define subsets above (or use just Full Recording) and click "
        "**Run Full Pipeline** to process the data."
    )
