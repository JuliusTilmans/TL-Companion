============================================
  TrackLab - Companion  v1.2.2
  Social Interaction Analysis Tool
============================================

Full instructions: see the user guide (PDF) on the GitHub release page
                   where you downloaded this tool

HOW TO USE:
  1. Double-click "TrackLab - Companion - Start.bat"
  2. Keep the black window open. If your browser does not open the tool
     by itself, go to: http://localhost:8501
  3. Upload your CSV data files and configure the analysis
  4. Click "Run Full Pipeline" to process
  5. Download the results (tracklab_companion_export.zip)

To stop the application, close the black command window.
Stopping the tool or refreshing the browser page clears all loaded data
and results: download your results first.

REQUIREMENTS:
  - Windows 10 or 11
  - A modern web browser (Chrome, Firefox, or Edge)
  - No other software installation needed

DATA FORMAT:
  CSV files should be semicolon-delimited (;) with columns:
    TimeStamp  — format auto-detected from: DD/MM/YYYY, DD-MM-YYYY,
                 MM/DD/YYYY, YYYY-MM-DD, with the time as
                 HH:MM:SS.fff or HH:MM:SS.
                 Ambiguous dates (day <= 12) prompt for confirmation.
    TagId      — unique identifier per tracked individual
    X          — X position in meters
    Y          — Y position in meters

TROUBLESHOOTING:
  - If the browser doesn't open, navigate to: http://localhost:8501
  - If you see "port already in use", close any other TrackLab-Companion windows first
  - For issues, contact the thesis author or use the feedback form on the Home page
