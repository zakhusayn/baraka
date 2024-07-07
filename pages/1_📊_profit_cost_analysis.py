import streamlit as st
import altair as alt
import pandas as pd
from utils import *

st.set_page_config(
    page_title="Profit & Cost Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

alt.themes.enable("dark")

data = pd.read_excel(
    "data/baraka_hygienics_2023-24.xlsx", sheet_name="Expenditure per year"
)
dataframe = (
    data.groupby("Years")
    .apply(
        lambda x: pd.Series(
            {
                "Cost": x["Total"].sum(),
                "Sales": x["Sales"].sum(),
                "Profit": x["Profit"].sum(),
            }
        ),
        include_groups=False,
    )
    .reset_index()
    .rename(columns={"Years": "Month"})
)

with st.sidebar:
    st.title("Profit-Cost Dashboard")

    year_list = ["All"] + list(dataframe["Month"].dt.year.unique())[::-1]

    selected_year = st.selectbox("Select a year", year_list)
    if selected_year != "All":
        dataframe = dataframe[dataframe["Month"].dt.year == selected_year]

    selected_color_theme = st.selectbox("choose color theme", color_palettes)


col = st.columns((0.2, 0.6, 0.2), gap="medium")

with col[0]:
    st.markdown("#### Metrics")

    def compute_metrics(df):
        year = df["Month"].dt.year.max() if selected_year == "All" else selected_year

        filtered_df = df[df["Month"].dt.year.isin([year, year - 1])]

        annual_profit = (
            filtered_df.groupby(filtered_df["Month"].dt.year)["Profit"]
            .sum()
            .reset_index(name="Profit")
        )
        annual_profit["profit_change"] = annual_profit["Profit"].pct_change() * 100

        annual_cost = (
            filtered_df.groupby(filtered_df["Month"].dt.year)["Cost"]
            .sum()
            .reset_index(name="Cost")
        )
        annual_cost["cost_change"] = annual_cost["Cost"].pct_change() * 100

        return annual_profit.tail(1).fillna(0), annual_cost.tail(1).fillna(0)

    metrics = compute_metrics(dataframe)
    st.metric(
        label="Profit",
        value=format_number(metrics[0]["Profit"].iloc[0]),
        delta=f"{metrics[0]['profit_change'].iloc[0]:.1f}%",
    )

    st.metric(
        label="Cost",
        value=format_number(metrics[1]["Cost"].iloc[0]),
        delta=f"{metrics[1]['cost_change'].iloc[0]:.1f}%",
        delta_color="inverse",
    )


with col[1]:
    st.markdown(
        "<h5 style='text-align: center;'>Cost, Sales and Profit Over Time</h5> &nbsp;",
        unsafe_allow_html=True,
    )

    df_melted = dataframe.melt(id_vars="Month", var_name="Category", value_name="Value")

    chart = (
        alt.Chart(df_melted)
        .mark_bar()
        .encode(
            x=alt.X("yearmonth(Month):T", title="Month"),
            y=alt.Y("sum(Value):Q", title="Amount($)"),
            color=alt.Color(
                "Category:N",
                scale=alt.Scale(scheme=selected_color_theme),
                legend=alt.Legend(title="Category"),
            ),
            tooltip=[
                alt.Tooltip("Month:T", title="Month"),
                alt.Tooltip("Category:N", title="Category"),
                alt.Tooltip("Value:Q", title="Amount"),
            ],
        )
        .properties(
            width=800,
            height=400,
        )
        .configure_axis(labelFontSize=12, titleFontSize=14)
        .configure_title(fontSize=18, anchor="middle")
        .configure_legend(labelFontSize=12, titleFontSize=14)
    )

    st.altair_chart(chart, use_container_width=True)


with col[2]:
    st.markdown("<h5 style='text-align: center;'>Sales</h5>", unsafe_allow_html=True)

    selected_df = dataframe[["Month", "Sales"]]

    st.dataframe(
        selected_df,
        column_order=("Month", "Sales"),
        hide_index=True,
        width=None,
        column_config={
            "Month": st.column_config.DateColumn(
                "Month",
            ),
            "Sales": st.column_config.ProgressColumn(
                "Sales", format="%f", min_value=0, max_value=max(dataframe["Sales"])
            ),
        },
    )


_, col2, col3 = st.columns([0.1, 0.7, 0.3], gap="medium")

with col2:
    df_melted = dataframe.melt(id_vars="Month", var_name="Category", value_name="Value")

    line_chart = (
        alt.Chart(df_melted)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "Month:T", title="Month", axis=alt.Axis(format="%Y-%m", labelAngle=-45)
            ),
            y=alt.Y("Value:Q", title="Amount ($)"),
            color=alt.Color(
                "Category:N",
                scale=alt.Scale(scheme=selected_color_theme),
                legend=alt.Legend(title="Metric"),
            ),
            strokeDash=alt.StrokeDash("Category:N", legend=None),
        )
        .properties(
            width=800,
            height=300,
        )
        .configure_legend(titleFontSize=14, labelFontSize=12)
    )
    st.altair_chart(line_chart, use_container_width=True)


with col3:
    st.markdown(
        "<h5 style='text-align: center;'>Expenditure Distribution</h5>",
        unsafe_allow_html=True,
    )

    df = data.groupby("Expenditure")["Expenses"].sum().reset_index()
    df = df.reset_index()
    df = df.sort_values(["Expenses"], ascending=False)
    df = df.iloc[:5, :]

    donut_chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=50)
        .encode(
            theta=alt.Theta(field="Expenses", type="quantitative"),
            color=alt.Color(
                field="Expenditure",
                type="nominal",
                legend=alt.Legend(title="Expenditure Type"),
                scale=alt.Scale(scheme=selected_color_theme),
            ),
            tooltip=["Expenditure", "Expenses"],
        )
        .properties(
            width=700,
            height=250,
        )
        .configure_legend(titleFontSize=12, labelFontSize=10)
    )

    st.altair_chart(donut_chart, use_container_width=True)
