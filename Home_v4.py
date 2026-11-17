"""
TrackLab - Companion — Social Interaction Analysis Tool
Main entry point for the Streamlit application.

Run with: streamlit run Home_v4.py

2026-10-18: data-format table now says times without fractional seconds are
accepted (page 1 change of the same date). Text only.

v4 changes: added beta feedback block at bottom of page linking to the
external user feedback form. No changes to workflow content or session
status block.

v3 changes: reflects merged feature set (multi-distance sensitivity sweep,
stationary time estimation, multi-tag subject merging, dead zone impact
preview). Three-page workflow preserved.
"""

import streamlit as st

st.set_page_config(
    page_title="TrackLab - Companion",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("TrackLab - Companion")
st.subheader("A digital companion for analysis of UWB-tracking data")

st.markdown("---")

st.markdown("""
### How to use this tool

The workflow is organised into three stages, one per page in the sidebar:

**1. Upload & Inspect** — Load your tracking CSV files and get an overview
of what's in them: how many tags, over what period, spatial coverage,
per-tag sample counts.

**2. Clean & Configure** — Set processing parameters (resampling rate,
velocity filter, spatial bounds), define dead zones to exclude with a
live impact preview, map tags to subjects if using multi-tag setups,
select which tags to include, and choose one or more critical distance
thresholds for sensitivity analysis.

**3. Define Analysis & Run** — Define named subsets of your recording
to compare (e.g. group work vs. free play), run the full processing
pipeline, inspect multi-distance comparisons, stationary-time estimates,
and multi-tag merge diagnostics, and download the results.

---

### Expected data format

| Column | Type | Description |
|--------|------|-------------|
| `TimeStamp` | datetime | Common formats auto-detected: `DD/MM/YYYY`, `DD-MM-YYYY`, `MM/DD/YYYY`, `YYYY-MM-DD`, with the time as `HH:MM:SS.fff` or `HH:MM:SS` |
| `TagId` | string/int | Unique identifier per tracked individual |
| `X` | float | X position in meters |
| `Y` | float | Y position in meters |

CSV files should be semicolon-delimited (`;`) with `.` as decimal separator.

The timestamp format is detected automatically on upload. When a date is
ambiguous (e.g. `05/04/2025` could be 5 April or 4 May), you will be warned
and asked to confirm — always check that the previewed dates look correct.

---

### Analysis approach

The pipeline detects **proximity episodes**: periods where two UWB-devices
are within a configurable distance threshold for at least a minimum duration.

Rather than classifying episodes by inferred movement state (which is unreliable
at typical UWB position errors of ~0.3m), the tool lets you define **named subsets**
based on known activity periods. You can also sweep multiple distance thresholds
in a single run to check how robust your findings are to the threshold choice.

---

👈 **Use the sidebar to navigate between pages — start with Upload & Inspect.**
""")

st.markdown("---")
st.markdown("### Current session status")

col1, col2, col3 = st.columns(3)

with col1:
    if "raw_data" in st.session_state:
        raw = st.session_state["raw_data"]
        st.success(
            f"✅ **Data loaded**\n\n"
            f"{len(raw):,} rows · {raw['TagId'].nunique()} tags"
        )
    else:
        st.info("⬜ **No data loaded**\n\nStart on page 1.")

with col2:
    if "config" in st.session_state:
        cfg = st.session_state["config"]
        n_dists = len(cfg.get("critical_distances", []))
        if n_dists > 1:
            st.success(f"✅ **Configuration set**\n\n{n_dists} distance thresholds.")
        else:
            st.success("✅ **Configuration set**\n\nProcessing parameters saved.")
    else:
        st.info("⬜ **No configuration**\n\nSet parameters on page 2.")

with col3:
    if "subset_results" in st.session_state:
        n_subsets = len(st.session_state["subset_results"])
        st.success(f"✅ **Results available**\n\n{n_subsets} subset(s) analysed.")
    else:
        st.info("⬜ **No results yet**\n\nRun pipeline on page 3.")


st.markdown("---")

FEEDBACK_FORM_URL = "https://forms.gle/REPLACE_WITH_REAL_FORM_LINK"

st.info(
    f"""
    ### 📝 Help shape the next version

    TrackLab - Companion is currently in development. Your feedback directly
    informs what gets built in the final development phase.

    If you've tried the tool — even partially — please take ~5 minutes to
    fill in the short feedback form:

    👉 Press [here](https://forms.gle/eAJjM5V3iZCXLD738)  to go to the feedback form

    The form covers what worked, what got in the way, and which improvements
    would matter most for your workflow.
    """
)
