import streamlit as st
import altair as alt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from  utils import *
import warnings
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import SimpleExpSmoothing, Holt
from statsmodels.graphics.tsaplots import plot_acf
from sklearn.linear_model import LinearRegression
from statsmodels.tools.sm_exceptions import ConvergenceWarning

warnings.filterwarnings("ignore", category=ConvergenceWarning)

st.set_page_config(
    page_title="Predictive Analysis",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

data      = pd.read_excel("data/baraka_hygienics_2023-24.xlsx", sheet_name="Expenditure per year" )
dataframe = data.groupby('Years').apply(lambda x: pd.Series({'Cost' :   x['Total'].sum(),
                                                             'Sales' :  x['Sales'].sum(),
                                                             'Profit':  x['Profit'].sum()
                                                             }), 
                                                             include_groups=False).reset_index().rename(columns ={'Years': 'Month'});

selected_color_theme = "tableau10" 
col1, col2 = st.columns([0.3, 0.7], gap = "medium")

with st.sidebar:
    st.markdown("""
    <h3 style='text-align: center; color: black;'>Trend Analysis and Forecasting Dashboard</h3>
    """, unsafe_allow_html=True)

with col1:

    period = st.number_input("Specify Forecast Months", value = 3, step = 1, min_value = 1)
    var = st.selectbox("Select Forecast Variable", ("Sales", "Cost", "Profit"))

    model_type = ("Simple Exponential Smoothing (SES)", "Holt's Linear Trend Model", "ARIMA", "Compare All Models")
    predictive_alg = st.selectbox("Select Predictive Algorithm", model_type)

    df = dataframe.copy()
    df.set_index('Month', inplace=True)
    df.index.freq = 'MS'  # Setting the monthly start frequency

    future_mnth = pd.date_range(start=df.index.max() + pd.DateOffset(months=1), periods=period, freq='MS')

    # ses_forecast_df = pd.DataFrame(ses_forecast, index=future_months, columns=[var])
    ses_model = SimpleExpSmoothing(df[var], initialization_method="heuristic").fit(optimized=True)
    ses_forecast = ses_model.forecast(period)
    ses_forecast_df = pd.DataFrame(ses_forecast, index=future_mnth, columns=[var])

    # Holt's Linear Trend Model Forecasting
    holt_model = Holt(df[var], initialization_method="estimated").fit(optimized=True)
    holt_forecast = holt_model.forecast(period)
    holt_forecast_df = pd.DataFrame(holt_forecast, index=future_mnth, columns=[var])

    # ARIMA Forecasting
    arima_order = (1, 1, 1)  # This is a common starting point, but may need tuning based on AIC/BIC criteria
    arima_model = ARIMA(df[var], order=arima_order).fit()
    arima_forecast = arima_model.forecast(steps=period)
    arima_forecast_df = pd.DataFrame(arima_forecast, index=future_mnth).rename(columns = {'predicted_mean': var})

    forecast_dataframe = dict(zip(model_type, [ses_forecast_df, holt_forecast_df, arima_forecast_df]))


with col2:
    tab1, tab2 = st.tabs([" Chart", " Data"])
    
    with tab1:
        def prepare_chart_data(df, forecast_df, var, method):
            df_forecast = pd.concat([df[[var]], forecast_df])
            df_forecast.reset_index(inplace=True)
            df_forecast.columns = ['Date', var]
            df_forecast['Type'] = ['Historical'] * len(df) + [f"{method} Forecast"] * len(forecast_df)
            return df_forecast
        
        _ = {"Smoothing": "SES", "Trend": "Holt's", "ARIMA": "ARIMA"}

        def plot_forecast(df, forecast_df, title):
            df_forecast = prepare_chart_data(df, forecast_df, var, _[title.split(' ')[-1]])
            chart = alt.Chart(df_forecast).mark_line(point=True).encode(
                x='Date:T',
                y=f'{var}:Q',
                tooltip=['Date:T', f'{var}:Q'],
                color=alt.Color('Type', scale= alt.Scale(scheme=selected_color_theme)),
            ).properties(
                title=title
            )
            return chart
        
        def rename_col(df, pos, name):
            colnames = df.columns.tolist()
            colnames[pos] ="{} {}".format(colnames[pos], name)      
            df.columns = colnames
            return df

        
        if predictive_alg == 'Simple Exponential Smoothing (SES)':
            st.altair_chart(plot_forecast(df, ses_forecast_df, f'{var} Forecast using Simple Exponential Smoothing'), use_container_width=True)
        elif predictive_alg == "Holt's Linear Trend Model":
            st.altair_chart(plot_forecast(df, holt_forecast_df, f'{var} Forecast using Holt\'s Linear Trend'), use_container_width=True)
        elif predictive_alg == "ARIMA":
            st.altair_chart(plot_forecast(df, arima_forecast_df, f'{var} Forecast using ARIMA'), use_container_width=True)
        elif predictive_alg == "Compare All Models":

            combined_forecast_df = pd.concat([prepare_chart_data(df, ses_forecast_df, var, 'SES'),
                                            prepare_chart_data(df, holt_forecast_df, var, 'Holt'),
                                            prepare_chart_data(df, arima_forecast_df, var, 'ARIMA')
                                            ])
            chart = alt.Chart(combined_forecast_df).mark_line(point=True).encode(
                x='Date:T',
                y=f'{var}:Q',
                tooltip=['Date:T', f'{var}:Q'],
                color=alt.Color('Type', scale= alt.Scale(scheme=selected_color_theme)),

            ).properties(
                title=f'{var} Forecast using SES, Holt, and ARIMA'
            )

            st.altair_chart(chart, use_container_width=True)
    with tab2:
        modelname = {"(SES)": "(SES)", "Model": "(Holt)", "ARIMA": "(ARIMA)"}

        if predictive_alg == "Compare All Models":
            dfs = []
            for modeltype, forecast_df in forecast_dataframe.items():
                dfs.append(rename_col(forecast_df, 0, f"{modelname[modeltype.split(' ')[-1]]} Forecast"))
            forecast_df = pd.concat(dfs, axis = 1)
        else:
            forecast_df = rename_col(forecast_dataframe[predictive_alg], 0, f"{modelname[predictive_alg.split(' ')[-1]]} Forecast")

        st.dataframe(forecast_df.round(2))

        

col1, col2 = st.columns([0.3, 0.7], gap = "medium")
    
with col2:
    tab1, tab2, tab3 = st.tabs([" Chart", " Data", " Correlogram"])

    dataframe = df.copy()
    dataframe = dataframe.reset_index()
    dataframe = dataframe.set_index('Month')

    def calculate_seasonal_index(df, column):
        """Calculate and normalize median seasonal index."""
        median_index = df.groupby(df.index.month)[column].median()
        normalized_index = 100 * median_index / median_index.mean()
        return normalized_index

    def deseasonalize(df, original_col, index_series):
        """Deseasonalize the data using seasonal indices."""
        month_series = df.index.month  # Extract month from index
        df[f'{original_col}_Deseasonalized'] = df[original_col] * 100 / index_series[month_series].values

    def compute_trend_and_cycle_corrected(df, column, time_index):
        """Correct computation of trend and cyclic effects using linear regression."""
        model = LinearRegression()
        deseasonalized_data = df[column].dropna().values.reshape(-1, 1)
        valid_time_index = time_index[:len(deseasonalized_data)]
        model.fit(valid_time_index, deseasonalized_data)
        trend_values = model.predict(time_index)
        df[f'{column}_Trend'] = trend_values.ravel()  # Flatten array to fit into DataFrame
        cyclic_effect = df[column] / df[f'{column}_Trend'] * 100
        df[f'{column}_Cyclic'] = cyclic_effect

    
    dataframe[f'{var}_MA']    = dataframe[f'{var}'].rolling(window=2, center=True).mean()
    dataframe[f'{var}_CMA']   = dataframe[f'{var}_MA'].rolling(window=2).mean().shift(-1)
    dataframe[f'{var}_Ratio'] = (dataframe[f'{var}'] / dataframe[f'{var}_CMA']) * 100

    seasonal_index = calculate_seasonal_index(dataframe, f'{var}_Ratio')
    seasonal_indices = pd.DataFrame({
        'Month': seasonal_index.index,
        f'{var} Seasonal Index': seasonal_index.values
    })
    seasonal_indices.set_index('Month', inplace=True)
    deseasonalize(dataframe, f'{var}', seasonal_index)

    time_index = np.arange(len(dataframe)).reshape(-1, 1)
    compute_trend_and_cycle_corrected(dataframe, f'{var}_Deseasonalized', time_index)

    components = []
    components.append(var)
    components.append(f"{var}_Deseasonalized")
    components.append(f"{var}_Deseasonalized_Trend")

    with tab1:
        dataframe = dataframe[components].reset_index()
        dataframe = dataframe.melt(id_vars='Month', var_name='Component', value_name='Value')

        selection = alt.selection_single(name = "interval", 
                                        fields=['Component'], 
                                        on='click',
                                        clear = False
                                        )

        line_chart = alt.Chart(dataframe).mark_line(point=True).encode(
                x=alt.X('Month:T', title='Month'),
                y=alt.Y('Value:Q', title='Amount ($)'),
                color=alt.Color('Component:N', scale= alt.Scale(scheme=selected_color_theme)),
                opacity=alt.condition(selection, alt.value(1), alt.value(0.2))

            ).properties(
                width=800,
                height=300,
                title=f'Financial Decomposition Analysis'
            ).configure_legend(
            titleFontSize=14,  
            labelFontSize=12  
        ).add_selection(selection)

        st.altair_chart(line_chart, use_container_width=True) 
    with tab2:
        wide_df = dataframe.pivot(index='Month', columns='Component', values='Value')
        wide_df.reset_index(inplace=True)
        st.dataframe(wide_df)
        
    with tab3:
        fig, ax = plt.subplots(figsize=(8, 3))
        plot_acf(df[f'{var}'], ax=ax, lags=12, title=f"Autocorrelation for {var}")
        ax.set_title("Autocorrelation for Sales", fontsize=10)
        ax.set_xlabel("Lags", fontsize=6)
        ax.set_ylabel("Autocorrelation", fontsize=6)
        ax.tick_params(axis='both', which='major', labelsize=7)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.grid(True, linestyle='--', linewidth=0.2)
        plt.tight_layout()
        st.pyplot(fig)
        


with col1:
    dataframe = df.copy()
    dataframe = dataframe.reset_index()

    correlation_matrix = dataframe.drop(columns='Month').corr()
    correlation_df = correlation_matrix.reset_index().melt('index')
    correlation_df.columns = ['x', 'y', 'Correlation']

    heatmap = alt.Chart(correlation_df).mark_rect().encode(
    x='x:N',
    y='y:N',
    color=alt.Color('Correlation:Q', legend=alt.Legend(title=None)),
    tooltip=['x', 'y', 'Correlation']
    ).properties(
    title='Correlation Matrix',
    width=400,
    height=300
    )

    st.altair_chart(heatmap, use_container_width=True)