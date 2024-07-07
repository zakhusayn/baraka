import streamlit as st
import altair as alt
import pandas as pd
from utils import *

st.set_page_config(
    page_title="Product Analysis",
    page_icon="🧴",
    layout="wide",
    initial_sidebar_state="expanded",
)

alt.themes.enable("dark")

data = pd.read_excel(
    "data/baraka_hygienics_2023-24.xlsx", sheet_name="Expenditure per year"
)

with st.sidebar:
    st.title("Product Dashboard")

    year_list = ["All"] + list(data["Years"].dt.year.unique())[::-1]

    selected_year = st.selectbox("Select a year", year_list)
    if selected_year != "All":
        data = data[data["Years"].dt.year == selected_year]

    selected_color_theme = st.selectbox("choose color theme", color_palettes)


col1, col2 = st.columns([0.7, 0.3], gap="medium")

with col1:
    st.markdown(
        "<h5 style='text-align: center;'>Product Overview Over Time</h5> &nbsp;",
        unsafe_allow_html=True,
    )

    df = (
        data.groupby(["Years", "Product Category"])["Revenue"]
        .sum()
        .reset_index(name="Sales")
    )

    brush = alt.selection_interval(encodings=["x"])
    click = alt.selection_multi(encodings=["color"])

    area = (
        alt.Chart(df)
        .mark_area(interpolate="basis")
        .encode(
            alt.X("yearmonth(Years):T", title="Months"),
            alt.Y("Sales:Q", title="Amount($)"),
            color=alt.condition(
                brush,
                "Product Category:N",
                alt.value("lightgray"),
                scale=alt.Scale(scheme=selected_color_theme),
            ),
        )
        .properties(width=550, height=300)
        .add_selection(brush)
        .transform_filter(click)
    )

    df = (
        data.groupby(["Years", "Product Category"])["Revenue"]
        .count()
        .reset_index(name="Count")
    )

    # Bottom panel is a bar chart of count vs product category
    category_bars = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x="Count",
            y=alt.Y("Product Category", sort="-x"),
            color=alt.condition(
                click,
                "Product Category:N",
                alt.value("lightgray"),
                scale=alt.Scale(scheme=selected_color_theme),
            ),
        )
        .transform_filter(brush)
        .properties(
            width=700,
        )
        .add_selection(click)
    )

    chart = alt.vconcat(area, category_bars)
    st.altair_chart(chart, use_container_width=True)


with col2:
    st.markdown(
        "<h5 style='text-align: center;'>Sales (Last 6 Months)</h5>",
        unsafe_allow_html=True,
    )

    df = (
        data.groupby(["Years", "Product Category"])["Revenue"]
        .sum()
        .reset_index(name="revenue")
    )
    df = df.drop_duplicates().sort_values("revenue", ascending=False)

    # Filter data for the last 6 months
    end_date = df["Years"].max()
    start_date = end_date - pd.DateOffset(months=6)
    filtered_df = df[(df["Years"] >= start_date) & (df["Years"] <= end_date)]

    monthly_sales = (
        filtered_df.groupby([pd.Grouper(key="Years", freq="M"), "Product Category"])
        .sum()
        .reset_index()
    )
    pivot_table = monthly_sales.pivot(
        index="Product Category", columns="Years", values="revenue"
    ).fillna(0)

    data_df = pivot_table.reset_index()
    data_df["sales"] = data_df.apply(lambda row: row[1:].tolist(), axis=1)
    data_df = data_df[["Product Category", "sales"]].sort_values(
        "sales", ascending=False
    )

    st.data_editor(
        data_df,
        column_config={
            "sales": st.column_config.AreaChartColumn(
                "Sales (last 6 months)",
                width="medium",
                help="The sales volume in the last 6 months",
                y_min=0,
                y_max=data_df["sales"].apply(lambda x: max(x)).max(),
            ),
        },
        hide_index=True,
    )


with col2:
    st.markdown(
        "<h5 style='text-align: center;'>Sales Distribution </h5>",
        unsafe_allow_html=True,
    )

    df = data.groupby("Product Category")["Revenue"].sum().reset_index(name="Sales")

    # Altair Horizontal Bar Chart
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            y=alt.Y(
                "Product Category", sort="-x"
            ),  # Sort bars based on Sales and display on y-axis
            x="Sales",
            color=alt.Color(
                field="Product Category",
                type="nominal",
                legend=None,
                scale=alt.Scale(scheme=selected_color_theme),
            ),
            tooltip=["Product Category", "Sales"],
        )
        .properties(
            width=800,
            height=400,
        )
        .configure_axisX(labelAngle=0)  # No need to tilt labels in horizontal layout
        .configure_title(fontSize=20)
    )

    st.altair_chart(chart, use_container_width=True)
