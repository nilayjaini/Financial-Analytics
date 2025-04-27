# pages/4_Backtest_Industry_PE.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from helpers.compustat_loader import load_compustat_data

# Page config
st.set_page_config(
    page_title="Industry Median P/E × EPS Backtest",
    layout="wide"
)

# Load data
data = load_compustat_data(data_path="data/")

# Sidebar inputs
st.sidebar.header("Backtest Inputs")
ticker  = st.sidebar.selectbox("Select ticker:", options=sorted(data['tic'].unique()))
horizon = st.sidebar.slider("Forecast horizon (years):", 1, 5, 1)

# Retrieve sub-industry for selected ticker
ticker_df = data[data['tic'] == ticker]
if ticker_df.empty:
    st.error(f"No data found for ticker {ticker}")
    st.stop()

gsubind = ticker_df['gsubind'].iloc[0]

# Filter data for the same sub-industry
sub_df = data[data['gsubind'] == gsubind]

# Backtest loop for years 2015–2023
results = []
for year in range(2015, 2024):
    # EPS for ticker in base year
    eps_row = ticker_df[ticker_df['fyear'] == year]
    if eps_row.empty:
        continue
    eps_val = eps_row['eps'].iloc[0]

    # Median P/E for sub-industry in base year
    med_pe = sub_df[sub_df['fyear'] == year]['PE'].median()
    if pd.isna(med_pe):
        continue

    # Predicted price at year + horizon
    predicted = eps_val * med_pe

    # Actual price at target year
    actual_row = ticker_df[ticker_df['fyear'] == year + horizon]
    if actual_row.empty:
        continue
    actual = actual_row['Price'].iloc[0]

    # Hit if within ±10%
    hit = abs(actual - predicted) / predicted <= 0.10

    results.append({
        'Year': year,
        'EPS': eps_val,
        'Median P/E': med_pe,
        'Predicted': predicted,
        'Actual': actual,
        'Hit': hit
    })

# Convert to DataFrame
results_df = pd.DataFrame(results)

# Display results table
st.header(f"Backtest for {ticker} (Sub-industry: {gsubind})")
st.dataframe(results_df)

# Scatter plot Predicted vs Actual
st.subheader("Predicted vs. Actual Prices")
fig, ax = plt.subplots()
ax.scatter(results_df['Predicted'], results_df['Actual'], alpha=0.7)
# 45-degree reference line
data_min = min(results_df['Predicted'].min(), results_df['Actual'].min())
data_max = max(results_df['Predicted'].max(), results_df['Actual'].max())
ax.plot([data_min, data_max], [data_min, data_max], linestyle='--')
ax.set_xlabel('Predicted Price')
ax.set_ylabel('Actual Price')
st.pyplot(fig)

# Overall hit-rate
hit_rate = results_df['Hit'].mean() * 100 if not results_df.empty else 0
st.metric(label="Hit Rate", value=f"{hit_rate:.1f}%")
