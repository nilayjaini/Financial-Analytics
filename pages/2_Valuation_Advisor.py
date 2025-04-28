import streamlit as st
import pandas as pd
import numpy as np

# Set File Path
file_path = 'data/Master data price eps etc.xlsx'

# Load company data with cache
@st.cache_data
def load_company_data():
    df = pd.read_excel(file_path, sheet_name='Company Dta', header=None)
    headers = df.iloc[3]
    df.columns = headers
    df = df.iloc[4:].reset_index(drop=True)
    return df

# Load EPS and Price data
@st.cache_data
def load_eps_price_data():
    df = pd.read_excel(file_path, sheet_name='Company Dta', header=None)
    headers = df.iloc[3]
    df.columns = headers
    df = df.iloc[4:].reset_index(drop=True)

    eps_data = df.iloc[:, 9:24].apply(pd.to_numeric, errors='coerce')
    price_data = df.iloc[:, 24:39].apply(pd.to_numeric, errors='coerce')
    eps_data.columns = list(range(2010, 2025))
    price_data.columns = list(range(2010, 2025))

    ticker_data = df['Ticker'].reset_index(drop=True)
    gsubind_data = df['gsubind'].reset_index(drop=True)

    return eps_data, price_data, ticker_data, gsubind_data

# Load Data
company_data = load_company_data()
eps_data, price_data, ticker_data, gsubind_data = load_eps_price_data()

# Streamlit Input
st.title("💸 Peer-Based Valuation Advisor")
ticker_input = st.text_input("Enter Ticker (e.g., AAPL, DELL, etc.)").upper()

if ticker_input and ticker_input in ticker_data.values:
    idx = ticker_data[ticker_data == ticker_input].index[0]
    company_gsubind = gsubind_data[idx]

    peer_indices = gsubind_data[gsubind_data == company_gsubind].index
    peers = ticker_data.loc[peer_indices].tolist()

    st.markdown(f"**Peers (Same gsubind):** {', '.join(peers)}")

    # Calculate Median PE of all peers
    pe_ratio = price_data.divide(eps_data)
    pe_ratio_with_gsubind = pe_ratio.copy()
    pe_ratio_with_gsubind['gsubind'] = gsubind_data.values

    peer_pe_ratios = pe_ratio_with_gsubind.loc[peer_indices]
    industry_pe_avg = peer_pe_ratios[2024].median()

    # Proceed with valuation
    eps = eps_data.loc[idx, 2024]
    current_price = price_data.loc[idx, 2024]
    implied_price = eps * industry_pe_avg

    # Display results
    st.metric("EPS (2024)", f"{eps:.2f}")
    st.metric("Median P/E (Peers)", f"{industry_pe_avg:.2f}")
    st.metric("Current Price (2024)", f"${current_price:.2f}")
    st.metric("Implied Price (Valuation)", f"${implied_price:.2f}")

    if implied_price > current_price:
        st.success("📈 Likely Undervalued — Consider Buying")
    else:
        st.warning("📉 Likely Overvalued — Exercise Caution")
else:
    st.warning("Ticker not found. Please check and try again.")
