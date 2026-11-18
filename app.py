from __future__ import annotations

from io import BytesIO

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="CSV Insight | Data Profiler", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem;}
    [data-testid="stMetric"] {
        background: var(--secondary-background-color, transparent);
        color: var(--text-color);
        border: 1px solid color-mix(in srgb, var(--text-color) 18%, transparent);
        padding: 16px;
        border-radius: 12px;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {color: var(--text-color);}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 CSV Insight")
st.caption("A practical data-quality and exploratory analysis workspace for CSV files.")


@st.cache_data(show_spinner=False)
def load_csv(file_bytes: bytes, separator: str, encoding: str) -> pd.DataFrame:
    return pd.read_csv(BytesIO(file_bytes), sep=separator, encoding=encoding, low_memory=False)


def format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024**2:
        return f"{size / 1024:.1f} KB"
    return f"{size / 1024**2:.1f} MB"


def build_profile(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        series = df[col]
        non_null = series.dropna()
        counts = non_null.value_counts(dropna=True)
        repeated_values = int((counts > 1).sum())
        duplicate_occurrences = int((counts - 1).clip(lower=0).sum())
        rows.append(
            {
                "Column": str(col),
                "Data type": str(series.dtype),
                "Rows": len(df),
                "Missing values": int(series.isna().sum()),
                "Missing %": round(float(series.isna().mean() * 100), 2) if len(df) else 0.0,
                "Distinct values": int(non_null.nunique()),
                "Repeated values": repeated_values,
                "Extra repeats in column": duplicate_occurrences,
                "Unique %": round(float(non_null.nunique() / len(non_null) * 100), 2) if len(non_null) else 0.0,
            }
        )
    return pd.DataFrame(rows)


with st.sidebar:
    st.header("Load your data")
    upload = st.file_uploader("Choose a CSV file", type=["csv", "txt"])
    separator_label = st.selectbox("Delimiter", ["Comma ,", "Semicolon ;", "Tab", "Pipe |"])
    separator = {"Comma ,": ",", "Semicolon ;": ";", "Tab": "\t", "Pipe |": "|"}[separator_label]
    encoding = st.selectbox("Text encoding", ["utf-8", "utf-8-sig", "latin-1"])
    st.divider()
    st.caption("Your file is processed in this app session. No data is uploaded to a separate service.")

if not upload:
    st.info("Upload a CSV from the sidebar to start exploring it.")
    st.subheader("What you can explore")
    a, b, c, d = st.columns(4)
    a.markdown("**Data quality**\n\nMissing values, repeated values, duplicate rows, and data types.")
    b.markdown("**Column profiles**\n\nNumeric distributions, category frequencies, and summary statistics.")
    c.markdown("**Relationships**\n\nNumeric correlation heatmap and pairwise comparisons.")
    d.markdown("**Downloads**\n\nExport the profile report or a copy with duplicate rows removed.")
    st.stop()

try:
    df = load_csv(upload.getvalue(), separator, encoding)
except Exception as exc:
    st.error(f"Could not read this file: {exc}")
    st.stop()

if df.empty or len(df.columns) == 0:
    st.warning("This CSV has no rows or columns to analyze.")
    st.stop()

profile = build_profile(df)
duplicate_rows = int(df.duplicated().sum())
missing_cells = int(df.isna().sum().sum())
total_cells = int(df.shape[0] * df.shape[1])
numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
categorical_cols = [c for c in df.columns if c not in numeric_cols]

st.caption(f"**{upload.name}** · {format_bytes(upload.size)} · {len(df):,} rows · {len(df.columns):,} columns")
tab_overview, tab_quality, tab_columns, tab_relationships, tab_data = st.tabs(
    ["Overview", "Data quality", "Column explorer", "Relationships", "Data preview"]
)

with tab_overview:
    st.subheader("At a glance")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Rows", f"{len(df):,}")
    m2.metric("Columns", f"{len(df.columns):,}")
    m3.metric("Missing cells", f"{missing_cells:,}", f"{missing_cells / total_cells * 100:.1f}% of all cells" if total_cells else "0%", delta_color="off")
    m4.metric("Fully duplicate rows", f"{duplicate_rows:,}", f"{duplicate_rows / len(df) * 100:.1f}% of rows" if len(df) else "0%", delta_color="off")
    m5.metric("Numeric columns", f"{len(numeric_cols):,}")

    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("#### Missing values by column")
        missing_chart = profile.loc[profile["Missing values"] > 0].sort_values("Missing %", ascending=True)
        if missing_chart.empty:
            st.success("No missing values found.")
        else:
            fig = px.bar(missing_chart, x="Missing %", y="Column", orientation="h", text="Missing values", color="Missing %", color_continuous_scale="Reds")
            fig.update_layout(height=max(300, 32 * len(missing_chart)), coloraxis_showscale=False, yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("#### Column types")
        type_counts = profile["Data type"].value_counts().rename_axis("Type").reset_index(name="Columns")
        fig = px.pie(type_counts, names="Type", values="Columns", hole=0.55, color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(height=360, legend_title="")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Numeric summary")
    if numeric_cols:
        st.dataframe(df[numeric_cols].describe().T, use_container_width=True)
    else:
        st.info("No numeric columns detected.")

with tab_quality:
    st.subheader("Data quality report")
    st.markdown("**Missing values** count blank/NA cells. **Extra repeats in column** counts non-null entries after the first appearance of each value in that column. **Repeated values** counts distinct values that appear more than once. **Fully duplicate rows** match an earlier row across every column, so repeated values in one column do not necessarily mean duplicate rows.")
    st.dataframe(profile, use_container_width=True, hide_index=True)
    st.markdown("#### Duplicate rows")
    if duplicate_rows:
        st.warning(f"Found {duplicate_rows:,} rows that duplicate an earlier row across all columns.")
        with st.expander("Preview duplicate rows"):
            st.dataframe(df.loc[df.duplicated(keep=False)].head(500), use_container_width=True)
    else:
        st.success("No fully duplicated rows found.")
        st.caption("This checks whether every value in a row matches an earlier row. Repeated values in individual columns are reported separately above.")
    st.download_button("Download column profile (CSV)", profile.to_csv(index=False).encode("utf-8-sig"), "csv_profile_report.csv", "text/csv")

with tab_columns:
    st.subheader("Explore a column")
    selected = st.selectbox("Select a column", options=df.columns, format_func=str)
    series = df[selected]
    non_null = series.dropna()
    counts = non_null.value_counts()
    repeated = counts[counts > 1]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Data type", str(series.dtype))
    c2.metric("Missing", f"{series.isna().sum():,} ({series.isna().mean() * 100:.1f}%)")
    c3.metric("Distinct non-null", f"{non_null.nunique():,}")
    c4.metric(
        "Extra repeats in this column",
        f"{int((counts - 1).clip(lower=0).sum()):,}",
        help="Counts non-missing entries after the first appearance of each value in this column. It does not count fully duplicated rows.",
    )
    if pd.api.types.is_numeric_dtype(series):
        lcol, rcol = st.columns(2)
        with lcol:
            st.markdown("#### Distribution")
            fig = px.histogram(non_null, x=selected, nbins=35, marginal="box", color_discrete_sequence=["#457b9d"])
            st.plotly_chart(fig, use_container_width=True)
        with rcol:
            st.markdown("#### Summary statistics")
            st.dataframe(series.describe().to_frame("Value"), use_container_width=True)
    else:
        st.markdown("#### Most frequent values")
        if counts.empty:
            st.info("No non-missing values to chart.")
        else:
            top = counts.head(20).rename_axis("Value").reset_index(name="Count")
            fig = px.bar(top.sort_values("Count"), x="Count", y="Value", orientation="h", color="Count", color_continuous_scale="Blues")
            fig.update_layout(height=max(350, 28 * len(top)), coloraxis_showscale=False, yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
    if not repeated.empty:
        with st.expander("Values repeated in this column"):
            rep = repeated.rename_axis("Value").reset_index(name="Count").sort_values("Count", ascending=False)
            st.dataframe(rep.head(500), use_container_width=True, hide_index=True)

with tab_relationships:
    st.subheader("Relationships")
    if len(numeric_cols) >= 2:
        st.markdown("#### Numeric correlation")
        corr = df[numeric_cols].corr(numeric_only=True)
        fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="auto")
        fig.update_layout(height=max(400, 45 * len(numeric_cols)))
        st.plotly_chart(fig, use_container_width=True)
        if len(numeric_cols) > 2:
            st.markdown("#### Compare two numeric columns")
            x_col, y_col = st.columns(2)
            x_choice = x_col.selectbox("X axis", numeric_cols, key="scatter_x")
            y_default = numeric_cols[1] if numeric_cols[1] != x_choice else numeric_cols[0]
            y_choice = y_col.selectbox("Y axis", numeric_cols, index=numeric_cols.index(y_default), key="scatter_y")
            fig = px.scatter(df, x=x_choice, y=y_choice, opacity=0.65, render_mode="webgl")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("At least two numeric columns are needed to calculate correlations.")
    if len(categorical_cols) >= 2:
        with st.expander("Categorical cross-tabulation"):
            cat_x, cat_y = st.columns(2)
            x_cat = cat_x.selectbox("Rows", categorical_cols, key="cat_rows")
            y_cat = cat_y.selectbox("Columns", categorical_cols, index=1, key="cat_cols")
            cross = pd.crosstab(df[x_cat], df[y_cat], dropna=False)
            st.dataframe(cross.head(100), use_container_width=True)

with tab_data:
    st.subheader("Data preview")
    st.caption("Showing the first 500 rows. Use the profile and charts above to inspect the full file.")
    st.dataframe(df.head(500), use_container_width=True, height=520)
    st.download_button("Download data without duplicate rows", df.drop_duplicates().to_csv(index=False).encode("utf-8-sig"), "data_without_duplicate_rows.csv", "text/csv")

