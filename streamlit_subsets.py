"""
Streamlit Subset Builder Component v6.

v6 (2026-10-17): identical to v5 except that it imports from
social_analysis_v13 instead of social_analysis_v12 (so the app loads one
backend only). v5 is kept unchanged for the previous pages.

v5 (2026-10-17): identical to v4 except that it imports from
social_analysis_v12 instead of social_analysis_v11 (so the app loads one
backend only). v4 is kept unchanged for the previous pages.

v4 (2026-10-07): identical to v3 except that it imports from
social_analysis_v11 instead of social_analysis_v10 (so the app loads one
backend only). v3 is kept unchanged for the old pages.

--- v3 notes below ---

Identical to v2 in behavior — renamed to match new version numbering
after the social_analysis_v7 / UI_v2 backend merge. No functional changes.
Playlist pattern, inline editing, row counts, timeline preview.

Key changes from v1:
- "Playlist" pattern: create a named subset first, then add windows to it.
  No more two-phase pending/commit flow.
- Single-row window adder: [Add to ▾] [Start] [End] [Label] [+ Add]
- Date auto-filled for single-day recordings (the common case).
- Live row count per subset from raw data for immediate feedback.
- Compact card layout replaces nested expanders.
- Inline window editing (adjust times without delete/recreate).
- Window mode defaults to "include", changeable per subset.
- Integrated timeline preview updates live with subset changes.

Return contract is identical to v1 for backward compatibility:
    [{'name': str, 'windows': list, 'window_mode': str|None}, ...]

USAGE:
    from streamlit_subsets import render_subset_builder_v3, render_tag_selector

    subsets = render_subset_builder_v3(available_dates, raw_df)
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import time as dt_time

from social_analysis import _time_of_day_us, _clock_us, parse_timestamps


def parsed_timestamps(raw_df):
    """`raw_df['TimeStamp']` parsed (dayfirst), cached for the current upload.

    Streamlit reruns the whole page on every click, and parsing the raw
    timestamp strings takes seconds on a large recording, so parse once and
    reuse. Unparseable values become NaT; the upload page has already dropped
    those rows, so for loaded data this is the same as a strict parse. The
    cache key includes the frame identity, its length and its first and last
    raw timestamp, so a new upload never gets a stale result.
    """
    col = raw_df['TimeStamp']
    key = (id(raw_df), len(col),
           col.iloc[0] if len(col) else None, col.iloc[-1] if len(col) else None)
    cached = st.session_state.get('_parsed_ts_cache')
    if cached is not None and cached[0] == key:
        return cached[1]
    ts = parse_timestamps(col, errors='coerce')
    st.session_state['_parsed_ts_cache'] = (key, ts)
    return ts


def cached_for_upload(name, raw_df, params, compute):
    """Return `compute()` for the current upload, recomputing only when the
    data or `params` change. Same key rules as `parsed_timestamps`; callers
    must treat the returned object as read-only."""
    col = raw_df['TimeStamp']
    key = (id(raw_df), len(col), params,
           col.iloc[0] if len(col) else None, col.iloc[-1] if len(col) else None)
    store = st.session_state.setdefault('_upload_cache', {})
    hit = store.get(name)
    if hit is not None and hit[0] == key:
        return hit[1]
    value = compute()
    store[name] = (key, value)
    return value


# =============================================================================
# ROW COUNT ESTIMATION
# =============================================================================

def _estimate_row_count(raw_df, windows, window_mode, date_str):
    """Estimate how many raw rows a subset's windows would capture.

    Uses the raw DataFrame (before processing) for fast feedback.
    The actual processed row count may differ slightly, but this is
    directionally accurate and catches obvious errors (wrong time range,
    wrong date, typos).

    Parameters
    ----------
    raw_df : pd.DataFrame
        Raw data with 'TimeStamp' column.
    windows : list of dict
        Time windows with 'date', 'start', 'end'.
    window_mode : str
        'include' or 'exclude'.
    date_str : str
        Default date string (DD-MM-YYYY) for windows missing a date.

    Returns
    -------
    int
        Estimated row count.
    """
    if raw_df is None or len(windows) == 0:
        return None

    ts = parsed_timestamps(raw_df)
    day = ts.dt.normalize()
    tod = _time_of_day_us(ts)

    mask = np.zeros(len(raw_df), dtype=bool)
    for w in windows:
        w_date = w.get('date', date_str)
        target_date = pd.to_datetime(w_date, dayfirst=True).date()
        start_us = _clock_us(pd.to_datetime(w['start']).time())
        end_us = _clock_us(pd.to_datetime(w['end']).time())
        mask |= (
            (day == pd.Timestamp(target_date)).to_numpy()
            & (tod >= start_us) & (tod <= end_us)
        )
    return int(mask.sum()) if window_mode == 'include' else int((~mask).sum())


def _get_recording_time_range(raw_df):
    """Get the min and max time from the raw data.

    Returns
    -------
    tuple of (str, str)
        (earliest_time, latest_time) as HH:MM strings.
    """
    if raw_df is None:
        return None, None
    ts = parsed_timestamps(raw_df)
    return ts.min().strftime('%H:%M:%S'), ts.max().strftime('%H:%M:%S')


# =============================================================================
# MAIN SUBSET BUILDER
# =============================================================================

def render_subset_builder_v3(available_dates, raw_df=None, key_prefix="sub"):
    """Render the redesigned subset builder UI.

    Parameters
    ----------
    available_dates : list of str or datetime
        Dates present in the dataset.
    raw_df : pd.DataFrame or None
        Raw data for live row count estimation. If None, row counts
        are not shown.
    key_prefix : str
        Prefix for Streamlit widget keys.

    Returns
    -------
    list of dict
        Same contract as v1. Each dict has:
        - 'name': str
        - 'windows': list of dict (each has date, start, end, label)
        - 'window_mode': str or None
    """

    st.subheader("📋 Analysis Subsets")

    # ── Normalize dates ──
    date_strings = []
    for d in available_dates:
        if isinstance(d, str):
            date_strings.append(d)
        elif hasattr(d, 'strftime'):
            date_strings.append(d.strftime('%d-%m-%Y'))
        else:
            date_strings.append(str(d))

    single_date = date_strings[0] if len(date_strings) == 1 else None

    # Show recording time range for reference
    t_min, t_max = _get_recording_time_range(raw_df)
    if t_min and t_max:
        date_display = date_strings[0] if single_date else f"{len(date_strings)} days"
        st.caption(
            f"Recording: **{date_display}** — "
            f"**{t_min}** to **{t_max}** — "
            f"{len(raw_df):,} rows"
        )
    else:
        st.caption(
            "Define named subsets of your recording to compare. "
            "**Full Recording** always runs on all data."
        )

    # ── Initialize session state ──
    state_key = f"{key_prefix}_subsets_v2"
    if state_key not in st.session_state:
        st.session_state[state_key] = []

    # Key for tracking which subset is being edited
    edit_key = f"{key_prefix}_editing_window"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = None  # (subset_idx, window_idx) or None

    custom_subsets = st.session_state[state_key]

    # ── Section 1: Create New Subset ──
    st.markdown("---")
    st.markdown("**Create a new subset**")

    cr_col1, cr_col2 = st.columns([3, 1])
    with cr_col1:
        new_name = st.text_input(
            "Subset name",
            placeholder="e.g., Group Work, Free Play, Morning Session...",
            key=f"{key_prefix}_create_name",
            label_visibility="collapsed",
        )
    with cr_col2:
        if st.button("Create subset", key=f"{key_prefix}_create_btn",
                      type="primary", use_container_width=True):
            name = new_name.strip() if new_name else ""
            if not name:
                st.error("Enter a subset name.")
            else:
                existing = [s['name'] for s in custom_subsets]
                if name in existing or name == "Full Recording":
                    st.error(f"'{name}' already exists.")
                else:
                    custom_subsets.append({
                        'name': name,
                        'windows': [],
                        'window_mode': 'include',
                    })
                    st.rerun()

    # ── Section 2: Add Window to Existing Subset ──
    if custom_subsets:
        st.markdown("---")
        st.markdown("**Add a time window**")

        subset_names = [s['name'] for s in custom_subsets]

        # Date selector — only show if multi-day
        if single_date:
            add_date = single_date
        else:
            add_date = st.selectbox(
                "Date",
                options=date_strings,
                key=f"{key_prefix}_add_date",
            )

        # All on one row: [subset] [start] [end] [label] [+ button]
        aw_col1, aw_col2, aw_col3, aw_col4, aw_col5 = st.columns(
            [2.5, 1.2, 1.2, 1.5, 0.8]
        )

        with aw_col1:
            target_subset = st.selectbox(
                "Add to",
                options=subset_names,
                index=len(subset_names) - 1,
                key=f"{key_prefix}_add_target",
            )

        with aw_col2:
            add_start = st.time_input(
                "Start",
                value=dt_time(9, 0),
                key=f"{key_prefix}_add_start",
            )

        with aw_col3:
            add_end = st.time_input(
                "End",
                value=dt_time(9, 30),
                key=f"{key_prefix}_add_end",
            )

        with aw_col4:
            add_label = st.text_input(
                "Label",
                placeholder="(optional)",
                key=f"{key_prefix}_add_label",
            )

        with aw_col5:
            st.markdown("<br>", unsafe_allow_html=True)  # align with inputs
            add_clicked = st.button("➕", key=f"{key_prefix}_add_window_btn",
                                     help="Add window to subset",
                                     use_container_width=True)

        if add_clicked:
            if add_start >= add_end:
                st.error("Start time must be before end time.")
            else:
                for s in custom_subsets:
                    if s['name'] == target_subset:
                        s['windows'].append({
                            'date': add_date,
                            'start': add_start.strftime('%H:%M'),
                            'end': add_end.strftime('%H:%M'),
                            'label': add_label.strip() if add_label else '',
                        })
                        break
                st.rerun()

    # ── Section 3: Subset Cards ──
    st.markdown("---")

    # Full Recording card
    full_row_count = f"{len(raw_df):,}" if raw_df is not None else "all"
    st.markdown(f"**🟢 Full Recording** — {full_row_count} rows (always computed)")

    # Validate edit state (indices may be stale after deletions)
    if st.session_state[edit_key] is not None:
        e_idx, e_w_idx = st.session_state[edit_key]
        if (e_idx >= len(custom_subsets)
                or e_w_idx >= len(custom_subsets[e_idx]['windows'])):
            st.session_state[edit_key] = None

    # Custom subset cards
    for idx, subset in enumerate(custom_subsets):
        n_windows = len(subset['windows'])
        mode_label = subset['window_mode']

        # Row count
        row_count_str = ""
        if raw_df is not None and n_windows > 0:
            est = _estimate_row_count(
                raw_df, subset['windows'], subset['window_mode'],
                single_date or date_strings[0],
            )
            if est is not None:
                if est == 0:
                    row_count_str = f" — ⚠️ **0 rows** (check your time ranges!)"
                elif est < 100:
                    row_count_str = f" — ⚠️ ~{est:,} rows (very few)"
                else:
                    row_count_str = f" — ~{est:,} rows"
        elif n_windows == 0:
            row_count_str = " — no windows defined yet"

        with st.expander(
            f"🔵 {subset['name']} ({n_windows} window{'s' if n_windows != 1 else ''}, "
            f"{mode_label}){row_count_str}",
            expanded=(n_windows == 0),
        ):
            # ── Window list ──
            if n_windows == 0:
                st.caption("No windows yet — use the form above to add time windows.")
            else:
                for w_idx, w in enumerate(subset['windows']):
                    is_editing = (
                        st.session_state[edit_key] == (idx, w_idx)
                    )

                    if is_editing:
                        # ── Inline edit mode ──
                        ec1, ec2, ec3, ec4, ec5 = st.columns([1.2, 1.2, 2, 0.5, 0.5])
                        with ec1:
                            edit_start = st.time_input(
                                "Start",
                                value=pd.to_datetime(w['start']).time(),
                                key=f"{key_prefix}_edit_start_{idx}_{w_idx}",
                            )
                        with ec2:
                            edit_end = st.time_input(
                                "End",
                                value=pd.to_datetime(w['end']).time(),
                                key=f"{key_prefix}_edit_end_{idx}_{w_idx}",
                            )
                        with ec3:
                            edit_label = st.text_input(
                                "Label",
                                value=w.get('label', ''),
                                key=f"{key_prefix}_edit_label_{idx}_{w_idx}",
                            )
                        with ec4:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("✓", key=f"{key_prefix}_save_{idx}_{w_idx}",
                                          help="Save"):
                                if edit_start >= edit_end:
                                    st.error("Start must be before end.")
                                else:
                                    w['start'] = edit_start.strftime('%H:%M')
                                    w['end'] = edit_end.strftime('%H:%M')
                                    w['label'] = edit_label.strip()
                                    st.session_state[edit_key] = None
                                    st.rerun()
                        with ec5:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("✕", key=f"{key_prefix}_cancel_{idx}_{w_idx}",
                                          help="Cancel"):
                                st.session_state[edit_key] = None
                                st.rerun()
                    else:
                        # ── Display mode — compact row ──
                        label_str = f" — *{w['label']}*" if w.get('label') else ""
                        date_str = f"`{w['date']}` " if not single_date else ""

                        dc1, dc2, dc3 = st.columns([8, 0.6, 0.6])
                        with dc1:
                            st.markdown(
                                f"{date_str}"
                                f"**{w['start']}** → **{w['end']}**"
                                f"{label_str}"
                            )
                        with dc2:
                            if st.button("✏️", key=f"{key_prefix}_edit_{idx}_{w_idx}",
                                          help="Edit"):
                                st.session_state[edit_key] = (idx, w_idx)
                                st.rerun()
                        with dc3:
                            if st.button("🗑️", key=f"{key_prefix}_del_w_{idx}_{w_idx}",
                                          help="Delete"):
                                subset['windows'].pop(w_idx)
                                st.rerun()

            # ── Subset actions: Delete always visible, settings collapsed ──
            del_col, spacer_col = st.columns([1, 4])
            with del_col:
                if st.button("🗑️ Delete subset", key=f"{key_prefix}_del_sub_{idx}",
                              type="secondary", use_container_width=True):
                    custom_subsets.pop(idx)
                    st.rerun()

            with st.expander("⚙️ Subset settings", expanded=False):
                set_col1, set_col2 = st.columns(2)

                with set_col1:
                    new_mode = st.selectbox(
                        "Window mode",
                        options=["include", "exclude"],
                        index=0 if subset['window_mode'] == 'include' else 1,
                        key=f"{key_prefix}_mode_{idx}",
                        format_func={
                            "include": "Include — only these windows",
                            "exclude": "Exclude — everything except these",
                        }.get,
                    )
                    if new_mode != subset['window_mode']:
                        subset['window_mode'] = new_mode
                        st.rerun()

                with set_col2:
                    rename_val = st.text_input(
                        "Rename subset",
                        value=subset['name'],
                        key=f"{key_prefix}_rename_{idx}",
                    )
                    if rename_val.strip() and rename_val.strip() != subset['name']:
                        existing = [s['name'] for s in custom_subsets if s is not subset]
                        if rename_val.strip() in existing or rename_val.strip() == "Full Recording":
                            st.error("Name already exists.")
                        else:
                            subset['name'] = rename_val.strip()
                            st.rerun()

                if n_windows > 0:
                    if st.button("📋 Duplicate subset", key=f"{key_prefix}_dup_{idx}",
                                  help="Create a copy of this subset"):
                        base_name = subset['name']
                        copy_name = f"{base_name} (copy)"
                        counter = 2
                        existing = [s['name'] for s in custom_subsets]
                        while copy_name in existing:
                            copy_name = f"{base_name} (copy {counter})"
                            counter += 1
                        import copy
                        new_subset = copy.deepcopy(subset)
                        new_subset['name'] = copy_name
                        custom_subsets.append(new_subset)
                        st.rerun()

    # ── Section 4: Timeline Preview ──
    result = _build_return_value(custom_subsets)
    _render_timeline_preview_inline(raw_df, result, date_strings)

    return result


def _build_return_value(custom_subsets):
    """Build the return value list, always starting with Full Recording."""
    result = [{'name': 'Full Recording', 'windows': [], 'window_mode': None}]
    for s in custom_subsets:
        result.append({
            'name': s['name'],
            'windows': list(s['windows']),
            'window_mode': s['window_mode'],
        })
    return result


# =============================================================================
# INTEGRATED TIMELINE PREVIEW
# =============================================================================

def _render_timeline_preview_inline(raw_df, subsets, date_strings):
    """Render timeline preview directly below the subset cards.

    Only shown when there are custom subsets with windows.
    """
    import plotly.graph_objects as go

    custom = [s for s in subsets if s['window_mode'] is not None and len(s['windows']) > 0]
    if not custom or raw_df is None:
        return

    st.markdown("---")
    st.markdown("**📊 Timeline Preview**")

    timestamps = parsed_timestamps(raw_df)
    days = timestamps.dt.normalize()
    unique_dates = sorted(pd.Timestamp(d).date() for d in days.dropna().unique())

    colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336',
              '#00BCD4', '#795548', '#607D8B']

    fig = go.Figure()

    date_labels = [d.strftime('%d/%m/%Y') for d in unique_dates]

    # Grey bar for full recording span per date
    for date, label in zip(unique_dates, date_labels):
        day_data = timestamps[days == pd.Timestamp(date)]
        t_min = day_data.min()
        t_max = day_data.max()

        x_start = t_min.hour + t_min.minute / 60 + t_min.second / 3600
        x_end = t_max.hour + t_max.minute / 60 + t_max.second / 3600

        fig.add_trace(go.Bar(
            y=[label],
            x=[x_end - x_start],
            base=[x_start],
            orientation='h',
            marker=dict(color='#E0E0E0'),
            name='Full Recording',
            showlegend=(date == unique_dates[0]),
            legendgroup='full',
            hovertemplate=(
                f"Full Recording<br>"
                f"{t_min.strftime('%H:%M')} → {t_max.strftime('%H:%M')}"
                "<extra></extra>"
            ),
        ))

    # Overlay subset windows
    legend_shown = set()
    for s_idx, subset in enumerate(custom):
        color = colors[s_idx % len(colors)]
        mode_tag = "incl" if subset['window_mode'] == 'include' else "excl"
        legend_name = f"{subset['name']} ({mode_tag})"

        for w in subset['windows']:
            target_date_str = w['date']
            matching = [d for d in unique_dates if d.strftime('%d-%m-%Y') == target_date_str]
            if not matching:
                continue
            date = matching[0]
            label = date.strftime('%d/%m/%Y')

            h_start, m_start = map(int, w['start'].split(':'))
            h_end, m_end = map(int, w['end'].split(':'))
            x_start = h_start + m_start / 60
            x_end = h_end + m_end / 60

            window_label = w.get('label', '')
            hover_text = (
                f"{subset['name']}<br>"
                f"{w['start']} → {w['end']}"
                + (f"<br>{window_label}" if window_label else "")
                + "<extra></extra>"
            )

            show_legend = legend_name not in legend_shown
            legend_shown.add(legend_name)

            fig.add_trace(go.Bar(
                y=[label],
                x=[x_end - x_start],
                base=[x_start],
                orientation='h',
                marker=dict(color=color, opacity=0.7),
                name=legend_name,
                showlegend=show_legend,
                legendgroup=legend_name,
                hovertemplate=hover_text,
                text=window_label if window_label else None,
                textposition='inside',
                textfont=dict(size=11, color='white'),
            ))

    fig.update_layout(
        barmode='overlay',
        height=max(200, 80 * len(unique_dates)),
        xaxis=dict(
            title='Time of day',
            tickmode='linear',
            dtick=1,
            tickformat='',
            ticksuffix=':00',
        ),
        yaxis=dict(
            title='',
            autorange='reversed',
        ),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
        margin=dict(l=80, r=20, t=40, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# TAG SELECTOR (carried forward from v1, unchanged)
# =============================================================================

def render_tag_selector(raw_df, key_prefix="tags"):
    """Render a tag include/exclude selector.

    Parameters
    ----------
    raw_df : pd.DataFrame
        Raw data with 'TagId' column.
    key_prefix : str
        Prefix for widget keys.

    Returns
    -------
    list or None
        List of selected TagIds to include, or None for all tags.
    """
    st.subheader("🏷️ Tag Selection")

    all_tags = sorted(raw_df["TagId"].unique(), key=str)

    tag_mode = st.radio(
        "Which tags to analyze?",
        options=["all", "select"],
        format_func={
            "all": f"All tags ({len(all_tags)})",
            "select": "Select specific tags",
        }.get,
        horizontal=True,
        key=f"{key_prefix}_mode",
    )

    if tag_mode == "all":
        return None

    tag_info = raw_df.groupby("TagId").agg(
        samples=("X", "size"),
        nan_pct=("X", lambda s: f"{s.isna().mean() * 100:.1f}%"),
    ).reset_index()

    with st.expander("Tag data quality (for reference)", expanded=False):
        st.dataframe(tag_info, use_container_width=True, hide_index=True)

    selected_tags = st.multiselect(
        "Select tags to include in analysis",
        options=all_tags,
        default=all_tags,
        format_func=str,
        key=f"{key_prefix}_select",
    )

    if not selected_tags:
        st.error("You must select at least 2 tags for pairwise analysis.")
        return None

    n_excluded = len(all_tags) - len(selected_tags)
    if n_excluded > 0:
        excluded = [t for t in all_tags if t not in selected_tags]
        st.caption(
            f"**{len(selected_tags)}** tags selected, "
            f"**{n_excluded}** excluded: {', '.join(str(t) for t in excluded)}"
        )

    return selected_tags if len(selected_tags) < len(all_tags) else None
