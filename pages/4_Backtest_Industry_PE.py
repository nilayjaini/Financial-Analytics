import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from helpers.compustat_loader import load_compustat_data

# Page config
st.set_page_config(
    page_title="Industry Median P/E × EPS Backtest",
    layout="wide"
)

# Paths and keys
DATA_PATH = "data/"
PRICE_FILE = os.path.join(DATA_PATH, "compustat_price.csv")
KEYS = ["fyear", "tic"]

# Load merged data for EPS, PE, Market Cap, Price (same fiscal year)
data = load_compustat_data(data_path=DATA_PATH)

# Load raw price-only data to access actual future prices
price_only = pd.read_csv(PRICE_FILE, usecols=KEYS + ["Price"])

# Sidebar inputs
st.sidebar.header("Backtest Inputs")
ticker  = st.sidebar.selectbox(
    "Select ticker:", options=sorted(data['tic'].unique())
)
horizon = st.sidebar.slider(
    "Forecast horizon (years):", 1, 5, 1
)

# Retrieve sub-industry for selected ticker
ticker_df = data[data['tic'] == ticker]
if ticker_df.empty:
    st.error(f"No data found for ticker {ticker}")
    st.stop()

sub_ind = ticker_df['gsubind'].iloc[0]

# Filter merged data for the same sub-industry
sub_df = data[data['gsubind'] == sub_ind]

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

    # Actual price from raw price data at year + horizon
    actual_row = price_only[
        (price_only['tic'] == ticker) &
        (price_only['fyear'] == year + horizon)
    ]
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
columns = ['Year', 'EPS', 'Median P/E', 'Predicted', 'Actual', 'Hit']
results_df = pd.DataFrame(results, columns=columns)

# Display results table
st.header(f"Backtest for {ticker} (Sub-industry: {sub_ind})")
st.dataframe(results_df)

if results_df.empty:
    st.warning("No backtest results to display. Try a different ticker or horizon.")
else:
    # Scatter plot Predicted vs Actual
    st.subheader("Predicted vs. Actual Prices")
    fig, ax = plt.subplots()
    ax.scatter(results_df['Predicted'], results_df['Actual'], alpha=0.7)
    # 45-degree reference line
    min_val = min(results_df['Predicted'].min(), results_df['Actual'].min())
    max_val = max(results_df['Predicted'].max(), results_df['Actual'].max())
    ax.plot([min_val, max_val], [min_val, max_val], linestyle='--')
    ax.set_xlabel('Predicted Price')
    ax.set_ylabel('Actual Price')
    st.pyplot(fig)

    # Overall hit-rate
    hit_rate = results_df['Hit'].mean() * 100
    st.metric(label="Hit Rate", value=f"{hit_rate:.1f}%")
