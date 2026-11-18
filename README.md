# CSV Insight

A local Streamlit dashboard for CSV data quality checks and exploratory data analysis.

## Features

- Upload CSV files and choose delimiter and text encoding
- Show row and column counts, missing cells, and fully duplicated rows
- Profile every column with data type, missing count and percentage, distinct values, repeated values, and duplicate occurrences
- Explore numeric distributions and summary statistics, plus the most frequent categorical values
- Review numeric correlations, compare numeric columns, and inspect categorical cross-tabs
- Download the column profile report and a copy with fully duplicated rows removed

## Run locally

1. Install Python 3.10 or newer.
2. Create and activate a virtual environment (recommended).
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the dashboard:

   ```bash
   streamlit run app.py
   ```

The app opens in your browser. Upload a CSV using the sidebar. The file is read in the app session; the app does not save it to a database.

On Windows, you can also double-click `run_dashboard.bat` after setup. `sample_sales.csv` is included for a quick walkthrough.

## Metric definitions

- **Missing values:** cells pandas recognizes as null, such as blank fields and common NA markers.
- **Repeated values:** distinct non-null values that occur more than once in a column.
- **Extra repeats in column:** non-null entries beyond the first occurrence of each value in that column.
- **Fully duplicate rows:** rows whose values across every column match a previous row. Repeated values in one column do not necessarily make a row a duplicate.
