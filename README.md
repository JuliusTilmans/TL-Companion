# TrackLab - Companion

A Streamlit application for analysing UWB position-tracking data (TrackLab exports): cleaning trajectories, building subsets, and computing proximity-based social interaction measures such as dyad distances, proximity episodes and summary metrics.

Developed as part of a master's thesis.

Current version: **v1.2.2**

## Quick start (Windows, no installation)

1. Download the latest release zip from the **Releases** page and unzip it.
2. Double-click `TrackLab - Companion - Start.bat`.
3. Keep the black window open. If your browser does not open by itself, go to <http://localhost:8501>.
4. Upload your CSV files, configure the analysis, and click **Run Full Pipeline**.
5. Download the results (`tracklab_companion_export.zip`).

Close the black command window to stop the application. Stopping the tool or refreshing the browser page clears all loaded data and results, so download your results first.

The release zip includes a bundled Python runtime, so nothing else needs to be installed. Requirements: Windows 10 or 11 and a modern browser (Chrome, Firefox or Edge).

## Running from source

Requires Python 3.11.

```bash
git clone <repository-url>
cd <repository-folder>
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
streamlit run Home.py
```

## Input data format

Semicolon-delimited (`;`) CSV files with the columns:

| Column      | Description |
|-------------|-------------|
| `TimeStamp` | Format is auto-detected from DD/MM/YYYY, DD-MM-YYYY, MM/DD/YYYY or YYYY-MM-DD, with the time as HH:MM:SS.fff or HH:MM:SS. Ambiguous dates (day ≤ 12) ask for confirmation. |
| `TagId`     | Unique identifier per tracked individual |
| `X`         | X position in metres |
| `Y`         | Y position in metres |

## Project structure

```
Home.py                     Entry page
pages/
  1_Upload_and_Inspect.py   Upload and inspect CSV data
  2_Clean_and_Configure.py  Cleaning settings and configuration
  3_Analysis_and_Run.py     Run the pipeline and export results
social_analysis.py          Core analysis pipeline
streamlit_subsets.py        Subset builder and shared UI helpers
.streamlit/config.toml      Streamlit settings
TrackLab - Companion - Start.bat   Windows launcher (uses the bundled runtime)
```

## Data

No tracking data is included in this repository, and none should be committed. `.gitignore` blocks common data formats as a safeguard.

## Troubleshooting

- If the browser doesn't open, navigate to <http://localhost:8501>.
- If you see "port already in use", close any other TrackLab - Companion windows first.
- For issues, contact the author or use the feedback form on the Home page.
